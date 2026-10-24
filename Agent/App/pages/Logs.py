"""
Page Streamlit pour afficher les logs et historiques des conversations.

Fonctionnalités :
1. Vérifie que l'utilisateur est authentifié avant d'accéder à la page.
2. Liste toutes les conversations sauvegardées pour l'utilisateur connecté.
3. Permet de sélectionner une conversation spécifique.
4. Affiche les messages de la conversation avec :
   - le rôle de l'expéditeur (utilisateur ou assistant)
   - l'horodatage de chaque message
5. Fournit un retour visuel clair si aucune conversation n'est enregistrée.
"""

import streamlit as st
from utils.auth_local import require_login
from utils.config_loader import list_history_files, load_history_for

# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------
st.set_page_config(page_title="Logs", page_icon="📜")

st.title("📜 Logs des conversations")

# ---------------------------------------------------------
# Authentification obligatoire
# ---------------------------------------------------------
require_login()
username = st.session_state["username"]

# ---------------------------------------------------------
# Liste des fichiers d'historique pour cet utilisateur
# ---------------------------------------------------------
files = list_history_files(username)

if not files:
    st.info("Aucune conversation enregistrée.")
    st.stop()  # Arrête l'exécution si pas d'historique

# ---------------------------------------------------------
# Sélection d'une conversation
# ---------------------------------------------------------
selected = st.selectbox("Sélectionner une conversation :", files)

# ---------------------------------------------------------
# Chargement des messages depuis le fichier sélectionné
# ---------------------------------------------------------
messages = load_history_for(username, selected)

st.write(f"### 💬 Conversation : {selected}")
st.markdown("---")

# ---------------------------------------------------------
# Affichage des messages
# ---------------------------------------------------------
for role, content, timestamp in messages:
    with st.chat_message(role):
        st.write(content)
        st.caption(f"⏰ {timestamp}")
