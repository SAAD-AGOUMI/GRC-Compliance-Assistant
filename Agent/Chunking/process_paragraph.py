"""
Traitement d'un paragraphe (ici, une section : titre + texte) du pipeline de chunking.

Pour chaque section :
- un identifiant unique est généré (c'est le « parent » des chunks) ;
- la section est découpée en chunks par le code (structural_chunker), sans LLM :
  rapide, gratuit, et le texte n'est jamais déformé ;
- la section et ses chunks sont renvoyés avec leurs métadonnées.
"""

from uuid import uuid4

from Chunking.structural_chunker import chunk_section


def process_paragraph(args):
    """
    Args:
        args (tuple): (texte de la section, nom du document, numéro de page)

    Returns:
        dict: {"paragraph": {...}, "chunks": [...]}
    """
    paragraph_text, file_name, page_number = args
    paragraph_id = str(uuid4())[:8]

    chunks = [
        {
            "parent_paragraph_id": paragraph_id,
            "page_number": page_number,
            "document_name": file_name,
            "text": chunk_text,
        }
        for chunk_text in chunk_section(paragraph_text)
    ]

    return {
        "paragraph": {
            "paragraph_id": paragraph_id,
            "document_name": file_name,
            "page_number": page_number,
            "text": paragraph_text,
        },
        "chunks": chunks,
    }