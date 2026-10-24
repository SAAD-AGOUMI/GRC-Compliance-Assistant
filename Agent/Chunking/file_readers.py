"""
Lecture des documents (PDF, DOCX, TXT) et découpage en SECTIONS.

Une section = un titre + tout le texte qui le suit jusqu'au titre suivant.
Exemple :
    5. Durée de conservation
    Sauvegardes quotidiennes : 30 jours.
    Sauvegardes hebdomadaires : 3 mois.
    Sauvegardes mensuelles : 1 an.

Pourquoi : un titre seul (« 5. Durée de conservation ») ou une ligne seule
(« Sauvegardes quotidiennes : 30 jours. ») n'a pas de sens isolément.
Regroupés, ils forment un passage compréhensible, que la recherche retrouve
et que le LLM peut citer.

Format de sortie (inchangé pour le reste du pipeline) :
    [{"page_number": int, "text": str}, ...]
où « text » contient les sections séparées par une ligne vide ("\n\n")
et les lignes d'une section séparées par "\n".
Le texte des documents n'est jamais modifié : seules les lignes sont regroupées.
"""

import re
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

# Taille maximale d'une section (au-delà, elle est coupée en plusieurs parties,
# chacune précédée de son titre).
MAX_SECTION_CHARS = 2000

# Titre numéroté : « 5. Durée de conservation », « 3.2 Rôles », « Article 4 », « Annexe A »
HEADING_RE = re.compile(r"^(\d+(\.\d+)*\.?|[IVX]+\.|Article\s+\d+|Annexe\s+\w+)\s+\S", re.IGNORECASE)


# ---------------------------------------------------------
# Détection des titres
# ---------------------------------------------------------
def _level_from_text(text: str) -> int:
    """Niveau d'un titre numéroté (« 5. » → 1, « 5.2 » → 2), 0 si ce n'est pas un titre."""
    text = text.strip()
    if len(text) > 120 or text.endswith((".", ";", ":", ",")) or not HEADING_RE.match(text):
        return 0
    numero = text.split()[0].rstrip(".")
    return numero.count(".") + 1 if numero[0].isdigit() else 1


def _level_from_style(style_name: str) -> int:
    """Niveau d'un titre Word (« Heading 2 » / « Titre 2 » → 2), 0 sinon."""
    m = re.match(r"(heading|titre)\s*(\d)", (style_name or "").lower())
    return int(m.group(2)) if m else 0


# ---------------------------------------------------------
# Regroupement en sections
# ---------------------------------------------------------
class SectionBuilder:
    """Regroupe une suite de lignes (titres et texte) en sections."""

    def __init__(self):
        self.titres = {}    # niveau -> titre en cours (ex. {1: "3. Rôles", 2: "3.1 RSSI"})
        self.lignes = []    # lignes de texte de la section en cours
        self.sections = []  # sections terminées

    def _entete(self):
        return " > ".join(self.titres[k] for k in sorted(self.titres))

    def flush(self):
        """Termine la section en cours (coupée si elle dépasse MAX_SECTION_CHARS)."""
        if not self.lignes:
            return
        entete = self._entete()
        partie, taille = [], 0
        for ligne in self.lignes:
            if partie and taille + len(ligne) > MAX_SECTION_CHARS:
                self.sections.append("\n".join(([entete] if entete else []) + partie))
                partie, taille = [], 0
            partie.append(ligne)
            taille += len(ligne) + 1
        if partie:
            self.sections.append("\n".join(([entete] if entete else []) + partie))
        self.lignes = []

    def add(self, text: str, level: int = 0):
        # Une ligne ne doit pas contenir de saut de ligne (réservé à la structure).
        text = re.sub(r"\s*\n\s*", " ", text or "").strip()
        if not text:
            return
        if level > 0:
            self.flush()
            self.titres = {k: v for k, v in self.titres.items() if k < level}
            self.titres[level] = text
        else:
            self.lignes.append(text)

    def pop_text(self) -> str:
        """Renvoie les sections terminées (séparées par une ligne vide) et les oublie."""
        text = "\n\n".join(self.sections)
        self.sections = []
        return text


# ---------------------------------------------------------
# Lecteurs
# ---------------------------------------------------------
def read_docx(path: Path):
    """
    Lit un DOCX dans l'ordre du document (paragraphes ET tableaux).
    Le DOCX n'ayant pas de pagination fiable, tout est associé à la page 1.
    """
    doc = Document(str(path))
    builder = SectionBuilder()

    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            level = _level_from_style(p.style.name if p.style is not None else "")
            builder.add(p.text, level or _level_from_text(p.text))
        elif tag == "tbl":
            for row in Table(child, doc).rows:
                cellules = []
                for cell in row.cells:  # les cellules fusionnées apparaissent plusieurs fois
                    t = cell.text.strip()
                    if t and t not in cellules:
                        cellules.append(t)
                builder.add(" | ".join(cellules))

    builder.flush()
    return [{"page_number": 1, "text": builder.pop_text()}]


def read_pdf(path: Path):
    """Lit un PDF page par page ; les titres numérotés délimitent les sections."""
    pages = []
    builder = SectionBuilder()
    with fitz.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            for ligne in page.get_text("text").splitlines():
                builder.add(ligne, _level_from_text(ligne))
            builder.flush()  # une section est rattachée à la page où elle se trouve
            text = builder.pop_text()
            if text:
                pages.append({"page_number": i, "text": text})
    return pages


def read_txt(path: Path):
    """Lit un fichier texte ; les titres numérotés délimitent les sections."""
    builder = SectionBuilder()
    for ligne in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        builder.add(ligne, _level_from_text(ligne))
    builder.flush()
    return [{"page_number": 1, "text": builder.pop_text()}]


def load_text_from_file(path: Path):
    """Choisit le lecteur selon l'extension du fichier."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        print(f"📘 Lecture PDF : {path.name}")
        return read_pdf(path)
    if ext == ".docx":
        print(f"📄 Lecture DOCX : {path.name}")
        return read_docx(path)
    if ext == ".txt":
        print(f"📜 Lecture TXT : {path.name}")
        return read_txt(path)
    raise ValueError(f"Format non supporté : {ext}")