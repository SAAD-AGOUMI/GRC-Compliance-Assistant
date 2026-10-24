"""
📚 Indexation de chunks de documents dans Qdrant avec embeddings vectoriels

Ce script :
- Charge un fichier `chunks.json` contenant des segments (chunks) de documents
- Vérifie l'intégrité et la structure des données attendues
- Génère des embeddings vectoriels à l'aide du modèle EMBEDDING_MODEL
- (Re)crée une collection Qdrant dédiée aux chunks
- Insère chaque chunk dans Qdrant avec ses métadonnées associées

Objectif :
Permettre une recherche sémantique efficace sur des documents découpés
via une base vectorielle (Qdrant).
"""

import os
import uuid
from pathlib import Path

import pandas as pd
import torch
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from sentence_transformers import SentenceTransformer

# Détermination du dossier racine du projet (2 niveaux au-dessus du fichier courant)
ROOT_DIR = Path(__file__).resolve().parents[1]

# Chemin vers le fichier JSON contenant les chunks
CHUNKS_PATH = ROOT_DIR / "Chunking/data_chunking/chunks.json"

# Vérification de l'existence du fichier chunks.json
if not CHUNKS_PATH.exists():
    raise FileNotFoundError(f"❌ chunks.json introuvable : {CHUNKS_PATH}")

# Chargement des données JSON dans un DataFrame pandas
df = pd.read_json(CHUNKS_PATH)

# Colonnes obligatoires attendues dans chunks.json
expected_cols = {"text", "document_name", "page_number", "parent_paragraph_id"}
missing = expected_cols - set(df.columns)

# Vérification de la présence de toutes les colonnes requises
if missing:
    raise ValueError(f"⚠️ Colonnes manquantes dans chunks.json : {missing}")

# Affichage d'un résumé du chargement
print(f"✅ {len(df)} chunks chargés depuis {CHUNKS_PATH.name}")
print(df.head(3))


# Normalisation et renommage des colonnes utilisées par la suite
df["Chunk"] = df["text"].astype(str)
df["Doc"] = df["document_name"]
df["Page"] = df["page_number"].astype(int)
df["Parent"] = df["parent_paragraph_id"]

# Détection automatique du périphérique
device = "cuda" if torch.cuda.is_available() else "cpu"

# Chargement du modèle d'embeddings
load_dotenv()
embedding_model = os.getenv("EMBEDDING_MODEL")
print(f"🧠 Chargement du modèle {embedding_model}...")
model = SentenceTransformer(embedding_model, device=device)

# Connexion au serveur Qdrant local
client = QdrantClient(host="qdrant-server", port=6333)
collection_name = "documents_chunks"

# Créer la collection uniquement si elle n’existe pas
try:
    client.get_collection(collection_name)
except UnexpectedResponse:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1024,  # Dimension des embeddings du modèle d'embedding
            distance=models.Distance.COSINE,  # Mesure de similarité
        ),
    )

# Liste qui contiendra tous les points à insérer
points = []

# Parcours de chaque chunk pour encodage et préparation des points
for idx, row in df.iterrows():

    # Génération d'un ID unique pour chaque chunk
    unique_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{row['Doc']}|{row['Page']}|{row['Parent']}|{row['Chunk']}",
        )
    )

    # Génération de l'embedding du chunk
    emb = model.encode(row["Chunk"]).tolist()

    # Création du point Qdrant avec vecteur + métadonnées
    point = models.PointStruct(
        id=unique_id,
        vector=emb,
        payload={
            "Chunk": row["Chunk"],
            "Doc": row["Doc"],
            "Page": row["Page"],
            "ParentID": row["Parent"],
        },
    )
    points.append(point)

    # Affichage de la progression tous les 50 chunks
    if (idx + 1) % 50 == 0 or idx == len(df) - 1:
        print(f"→ Encodé {idx + 1}/{len(df)} chunks")

# Insertion par paquets (Qdrant refuse les requêtes de plus de 32 Mo)
BATCH_SIZE = 256  # environ 5 Mo par requête
print(f"🚀 Insertion dans Qdrant ({len(points)} points, par paquets de {BATCH_SIZE})...")
for start in range(0, len(points), BATCH_SIZE):
    batch = points[start:start + BATCH_SIZE]
    client.upsert(collection_name=collection_name, points=batch, wait=True)
    print(f"→ Inséré {start + len(batch)}/{len(points)} points")

# Confirmation de fin de traitement
print("✅ Tous les chunks ont été insérés avec succès dans Qdrant")
