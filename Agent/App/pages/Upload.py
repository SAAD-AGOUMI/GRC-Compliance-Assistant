"""
Page Streamlit "Documents (Admin)" pour la gestion des documents.

Ce fichier permet à l'administrateur de :
1. Ajouter de nouveaux documents à la base.
2. Lancer le processus de chunking sur les nouveaux documents.
3. Re-vectoriser tous les chunks dans Qdrant.
4. Visualiser les logs des opérations.

🔒 L'accès est strictement réservé à l'utilisateur "admin".
"""

import subprocess
import sys
import time
from pathlib import Path

import streamlit as st
from utils.auth_local import require_login

# ============================================================
# Config page + Auth globale
# ============================================================
st.set_page_config(page_title="Documents (Admin)", page_icon="📂")
require_login()  # Vérifie que l'utilisateur est connecté

st.title("📂 Gestion des documents – Admin")

# ============================================================
# 🔐 Restriction ADMIN UNIQUEMENT
# ============================================================
username = st.session_state.get("username")

if username != "admin":
    st.error("⛔ Accès réservé à l'administrateur.")
    st.stop()

st.success("✅ Accès administrateur autorisé")

# ============================================================
# Définition explicite de la racine du projet (Agent/)
# ============================================================
ROOT_DIR = Path(__file__).resolve().parents[2]

# ============================================================
# Import propre du pipeline de chunking
# ============================================================
sys.path.insert(0, str(ROOT_DIR))

from Chunking.main_chunking import main as chunking_main

# ============================================================
# Dossiers de chunking (chemins corrects)
# ============================================================
DATA_CHUNKING_DIR = ROOT_DIR / "Chunking" / "data_chunking"

NEW_DOCS_DIR = DATA_CHUNKING_DIR / "Nouveaux_documents"
PROCESSED_DOCS_DIR = DATA_CHUNKING_DIR / "Documents_traités"

NEW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Upload de documents
# ============================================================
if "pending_upload" not in st.session_state:
    st.session_state["pending_upload"] = None

st.subheader("📥 Ajouter un document à la base")

uploaded_file = st.file_uploader(
    "Formats supportés : PDF, DOCX, TXT", type=["pdf", "docx", "txt"]
)

if uploaded_file:
    st.session_state["pending_upload"] = uploaded_file

pending = st.session_state.get("pending_upload")
if pending:
    st.info(f"📄 Fichier sélectionné : `{pending.name}`")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmer l'ajout"):
            save_path = NEW_DOCS_DIR / pending.name
            processed_path = PROCESSED_DOCS_DIR / pending.name

            if processed_path.exists():
                st.warning("⚠️ Ce fichier a déjà été traité auparavant.")
            elif save_path.exists():
                st.warning("⚠️ Ce fichier est déjà présent.")
            else:
                with open(save_path, "wb") as f:
                    f.write(pending.getbuffer())

                st.success(f"✅ `{pending.name}` ajouté à la base")

            st.session_state["pending_upload"] = None

    with col2:
        if st.button("❌ Annuler"):
            st.session_state["pending_upload"] = None
            st.info("⏸️ Ajout annulé")

st.divider()

# ============================================================
# 🔄 Chunking incrémental
# ============================================================
st.subheader("🔄 Chunking incrémental")

if st.button("Lancer le chunking des nouveaux documents"):
    with st.spinner("🧠 Chunking en cours..."):
        start = time.time()
        chunking_main()  # Appelle la fonction de chunking principal
        elapsed = time.time() - start

    st.success("✅ Chunking terminé")
    st.info(f"⏱️ Temps de traitement : **{elapsed:.2f} secondes**")

st.divider()

# ============================================================
# 🧠 Re-vectorisation (Qdrant)
# ============================================================
st.subheader("🧠 Re-vectorisation des chunks (Qdrant)")

if st.button("Re-vectoriser tous les chunks"):
    with st.spinner("📡 Vectorisation + insertion Qdrant en cours..."):
        start = time.time()

        # Appel du script d'indexation externe
        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "Embedding" / "indexation_database.py")],
            capture_output=True,
            text=True,
        )

        elapsed = time.time() - start

    if result.returncode == 0:
        st.success("✅ Re-vectorisation terminée avec succès")
        st.info(f"⏱️ Temps de traitement : **{elapsed:.2f} secondes**")
        st.text_area("📄 Logs", result.stdout, height=200)
    else:
        st.error("❌ Erreur lors de la re-vectorisation")
        st.text_area("📄 Logs d'erreur", result.stderr, height=200)
