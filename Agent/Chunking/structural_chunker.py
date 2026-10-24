"""
Découpage d'une section en chunks, par le code (sans LLM).

Règles :
- une section courte (≤ MAX_CHUNK_CHARS) donne un seul chunk : la section entière ;
- une section longue est coupée entre deux lignes (jamais au milieu d'une phrase),
  et chaque chunk commence par le titre de la section pour garder le contexte.

Le texte n'est jamais modifié : un chunk est toujours une suite de lignes
du document (plus son titre).
"""

MAX_CHUNK_CHARS = 700


def chunk_section(section_text: str, max_chars: int = MAX_CHUNK_CHARS) -> list:
    lignes = [l for l in section_text.split("\n") if l.strip()]
    if not lignes:
        return []
    if len(section_text) <= max_chars or len(lignes) == 1:
        return [section_text.strip()]

    titre, corps = lignes[0], lignes[1:]
    chunks, courant = [], [titre]
    for ligne in corps:
        if len(courant) > 1 and len("\n".join(courant + [ligne])) > max_chars:
            chunks.append("\n".join(courant))
            courant = [titre]
        courant.append(ligne)
    if len(courant) > 1:
        chunks.append("\n".join(courant))
    return chunks