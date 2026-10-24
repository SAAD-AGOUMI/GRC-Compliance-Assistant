"""
Page Streamlit "Paramètres" pour visualiser la configuration actuelle.

Ce fichier permet à l'utilisateur authentifié de :
1. Accéder à la page des paramètres de l'application.
2. Voir les informations du modèle LLM utilisé (nom et host).
3. Garantir que l'accès est sécurisé via l'authentification.
"""

import os

import streamlit as st
from dotenv import load_dotenv
from utils.auth_local import require_login

# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------
# La configuration de la page doit être la première commande Streamlit
st.set_page_config(page_title="Paramètres", page_icon="⚙️", layout="wide")

# ---------------------------------------------------------
# Authentification obligatoire
# ---------------------------------------------------------
# L'utilisateur doit être connecté après la configuration de la page
require_login()

# ---------------------------------------------------------
# Titre et affichage des paramètres LLM
# ---------------------------------------------------------
st.title("⚙️ Paramètres")

# Récupérer les modèles LLM, Embedding et Re-ranker depuis .env
load_dotenv()
llm_rag = os.getenv("LLM_RAG")
llm_chunking = os.getenv("LLM_CHUNKING")
embedding_model = os.getenv("EMBEDDING_MODEL")
reranker_model = os.getenv("RERANKER_MODEL")

st.subheader("Modèle LLM (RAG)")
st.write(f"Modèle actuel : **{llm_rag}**")

st.subheader("Modèle LLM (Chunking)")
st.write(f"Modèle actuel : **{llm_chunking}**")

st.subheader("Modèle Embedding")
st.write(f"Modèle actuel : **{embedding_model}**")

st.subheader("Modèle Re-ranker")
st.write(f"Modèle actuel : **{reranker_model}**")
