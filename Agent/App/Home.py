"""
Page d'accueil de l'application Streamlit.

Cette page :
- Affiche une bannière de bienvenue centrée,
- Invite l'utilisateur à se connecter ou créer un compte,
- Intègre le formulaire d'authentification local via login_form_inside_page,
- Redirige vers la page du chatbot si l'utilisateur est authentifié.

Les emojis et le style HTML sont utilisés pour l'interface visuelle.
"""

import streamlit as st
from utils.auth_local import login_form_inside_page

# -------------------------------------------------
# Configuration de la page
# -------------------------------------------------
st.set_page_config(page_title="Accueil", page_icon="🏠", layout="wide")

# -------------------------------------------------
# Bannière de bienvenue centrale
# -------------------------------------------------
st.markdown(
    """
    <div style='text-align:center; margin-top:30px;'>
        <h1 style='font-size:40px;'>🏠Bienvenue</h1>
        <h2 style='color:#4A90E2;'>
            INEO Defense × Chatbot d'analyse de conformité ISO 27001
        </h2>
        <p style='font-size:18px; margin-top:10px;'>
            Veuillez vous connecter ou créer un compte pour continuer.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Formulaire d'authentification intégré
# -------------------------------------------------
if login_form_inside_page():
    st.switch_page("pages/Chatbot.py")
