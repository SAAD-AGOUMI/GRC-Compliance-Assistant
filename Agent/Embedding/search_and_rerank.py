"""
🔎 Recherche et re-ranking de chunks de documents

Ce fichier :
- Initialise les modèles nécessaires :
    - SentenceTransformer EMBEDDING_MODEL pour les embeddings
    - Cross-encoder RERANKER_MODEL pour le re-ranking
- Connecte au serveur Qdrant local
- Fournit une fonction `search_and_rerank` qui :
    - Effectue une recherche sémantique sur les chunks indexés
    - Applique un re-ranking basé sur un modèle cross-encoder
    - Filtre et renvoie les meilleurs résultats avec leurs parents
"""

import os
from pathlib import Path

import pandas as pd
import torch
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ---- Initialisation ----
print("Initialisation des modèles et connexion à Qdrant...")

ROOT_DIR = Path(__file__).resolve().parents[1]
PAR_PATH = ROOT_DIR / "Chunking/data_chunking/paragraphs.json"
_parents_cache = {"mtime": None, "df": None}


def load_parents():
    """Recharge paragraphs.json seulement s'il a été modifié depuis le dernier chargement."""
    mtime = PAR_PATH.stat().st_mtime if PAR_PATH.exists() else None
    if mtime != _parents_cache["mtime"]:
        df = pd.read_json(PAR_PATH, orient="records") if mtime else pd.DataFrame()
        if "paragraph_id" not in df.columns:
            df = pd.DataFrame(columns=["paragraph_id", "text"])
        _parents_cache.update(mtime=mtime, df=df)
    return _parents_cache["df"]

device = "cuda" if torch.cuda.is_available() else "cpu"

# Connexion Qdrant
client = QdrantClient(host="qdrant-server", port=6333)

# Embeddings
load_dotenv()
embedding_model = os.getenv("EMBEDDING_MODEL")
embedder = SentenceTransformer(embedding_model, device=device)

# Cross-encoder reranker
reranker_model = os.getenv("RERANKER_MODEL")
if reranker_model is None:
    raise RuntimeError("RERANKER_MODEL is not set")

tokenizer = AutoTokenizer.from_pretrained(reranker_model)
reranker = (
    AutoModelForSequenceClassification.from_pretrained(reranker_model).to(device).eval()
)

print("✅ Modèles chargés et connexion à Qdrant établie.")


# ---- Fonction de recherche et re-ranking ----
def search_and_rerank(
    query: str, top_k: int = 20, final_k: int = 3, threshold: float = -7.0
):
    """
    Recherche les chunks les plus pertinents pour une requête donnée,
    puis applique un re-ranking via cross-encoder.

    Retour :
    - results : liste de dictionnaires avec chunks et métadonnées
    - parents : mapping parent_id -> texte complet du paragraphe parent
    """
    if not query.strip():
        return [], {}
    df_parents = load_parents()
    # Embedding de la requête
    query_emb = embedder.encode(query, normalize_embeddings=True).tolist()

    # Recherche vectorielle dans Qdrant
    hits_obj = client.query_points(
        collection_name="documents_chunks",
        query=query_emb,
        limit=top_k,
        with_payload=True,
    )

    # Récupération des points depuis l'objet renvoyé par Qdrant
    points = (
        getattr(hits_obj, "result", None)
        or getattr(hits_obj, "points", None)
        or hits_obj
    )
    if not points:
        return [], {}

    # Préparation des textes pour le reranker
    normalized_points = []

    for p in points:
        if isinstance(p, tuple):
            p = p[1]
        normalized_points.append(p)

    docs = [p.payload["Chunk"] for p in normalized_points]

    inputs = tokenizer(
        [query] * len(docs),
        docs,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        logits = reranker(**inputs).logits.squeeze(dim=1)

    scores = logits.detach().cpu().numpy().tolist()

    # Tri et filtrage selon le seuil
    pairs = list(zip(points, scores))
    kept = [(p, s) for (p, s) in pairs if s >= threshold]
    kept.sort(key=lambda x: x[1], reverse=True)

    # Construction des résultats et mapping des parents
    results = []
    parents = {}

    for i, (p, s) in enumerate(kept[:final_k]):
        payload = p.payload
        similarity_score = float(getattr(p, "score", 0))

        dict_chunk = {
            "rank": i + 1,
            "rerank_score": float(s),
            "doc": payload.get("Doc"),
            "page": payload.get("Page"),
            "parent_id": payload.get("ParentID"),
            "chunk": payload.get("Chunk"),
            "similarity_score": similarity_score,
        }

        results.append(dict_chunk)

        parent_id = dict_chunk["parent_id"]
        if parent_id not in parents:
            parent_row = df_parents[df_parents["paragraph_id"] == parent_id]
            if not parent_row.empty:
                parents[parent_id] = parent_row.iloc[0]["text"]

    return results, parents
