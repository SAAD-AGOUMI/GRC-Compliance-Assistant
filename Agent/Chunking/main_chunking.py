"""
Ce script orchestre le pipeline complet de chunking de documents.

Fonctionnalités principales :
- Détection de nouveaux documents à traiter (PDF, DOCX, TXT)
- Lecture et extraction du texte par page
- Découpage des pages en paragraphes
- Traitement de chaque paragraphe via un LLM (chunking sémantique)
- Sauvegarde persistante des paragraphes et des chunks générés
- Gestion d'un registre pour éviter de retraiter les fichiers déjà traités
- Support du multiprocessing pour accélérer le traitement
"""

import json
import shutil
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path

from Chunking.file_readers import load_text_from_file
from Chunking.process_paragraph import process_paragraph
from Chunking.registry import load_registry, save_registry

# Extensions de fichiers supportées pour le chunking
SUPPORTED_EXT = [".pdf", ".docx", ".txt"]


def load_json_or_empty(path: Path):
    """
    Charge un fichier JSON s'il existe, sinon retourne une liste vide.

    Utile pour concaténer de nouveaux résultats avec des données déjà existantes
    sans lever d'erreur si le fichier n'a pas encore été créé.

    Args:
        path (Path): chemin vers le fichier JSON

    Returns:
        list: contenu du fichier JSON ou liste vide
    """
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def main(use_multiprocessing=True, max_processes=4):
    """
    Point d'entrée principal du pipeline de chunking.

    Étapes :
    - Préparation des dossiers de travail
    - Détection des nouveaux documents non encore traités
    - Extraction des paragraphes
    - Chunking via LLM (avec ou sans multiprocessing)
    - Sauvegarde des résultats
    - Mise à jour du registre des fichiers traités

    Args:
        use_multiprocessing (bool): active ou non le multiprocessing
        max_processes (int): nombre maximum de processus parallèles
    """
    root = Path(__file__).parent

    # Dossiers de travail
    new_docs = root / "data_chunking/Nouveaux_documents"
    processed_docs = root / "data_chunking/Documents_traités"

    # Fichiers de sortie et registre
    paragraphs_path = root / "data_chunking/paragraphs.json"
    chunks_path = root / "data_chunking/chunks.json"
    registry_path = root / "data_chunking/Fichiers_traités.json"

    # ----------------------------
    # Initialisation du registre
    # ----------------------------
    if not registry_path.exists() or registry_path.stat().st_size == 0:
        registry_path.write_text("[]", encoding="utf-8")

    # Création des dossiers s'ils n'existent pas
    for d in [processed_docs, new_docs]:
        d.mkdir(exist_ok=True)

    # Chargement du registre des fichiers déjà traités
    processed_registry = load_registry(registry_path)

    # Sélection des nouveaux fichiers à traiter
    new_files = [
        f
        for f in new_docs.iterdir()
        if f.suffix.lower() in SUPPORTED_EXT and f.name not in processed_registry
    ]

    if not new_files:
        print("ℹ️ Aucun nouveau document à chunker.")
        return

    print(f"📂 {len(new_files)} nouveau(x) document(s) détecté(s).")

    # Extraction des paragraphes à partir des documents
    paragraphs = []
    for file in new_files:
        pages = load_text_from_file(file)
        for page in pages:
            for p in page["text"].split("\n\n"):
                if p.strip():
                    paragraphs.append((p.strip(), file.name, page["page_number"]))

    print(f"📄 {len(paragraphs)} paragraphes à traiter.")

    start = time.time()

    # Traitement des paragraphes (avec ou sans multiprocessing)
    if use_multiprocessing:
        n_proc = min(max_processes, cpu_count())
        with Pool(n_proc) as pool:
            results = pool.map(process_paragraph, paragraphs)
    else:
        results = [process_paragraph(p) for p in paragraphs]

    # Chargement des données existantes
    existing_paragraphs = load_json_or_empty(paragraphs_path)
    existing_chunks = load_json_or_empty(chunks_path)

    # Séparation des nouveaux paragraphes et chunks
    new_paragraphs = [r["paragraph"] for r in results]
    new_chunks = [c for r in results for c in r["chunks"]]

    # Sauvegarde des paragraphes
    paragraphs_path.write_text(
        json.dumps(existing_paragraphs + new_paragraphs, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    # Sauvegarde des chunks
    chunks_path.write_text(
        json.dumps(existing_chunks + new_chunks, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    # Archivage des fichiers traités et mise à jour du registre
    for f in new_files:
        processed_registry.add(f.name)
        shutil.move(f, processed_docs / f.name)

    save_registry(registry_path, processed_registry)

    print(f"✅ Chunking terminé en {time.time() - start:.2f}s")
    print(f"🧩 Nouveaux chunks : {len(new_chunks)}")


if __name__ == "__main__":
    main()
