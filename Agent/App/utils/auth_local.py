"""
Module d'authentification locale pour une application Streamlit.

Ce fichier fournit un système d'authentification simple basé sur un fichier JSON local.
Il permet :
- la création de comptes utilisateurs (inscription),
- la connexion avec vérification sécurisée des mots de passe,
- la gestion de l'état d'authentification via `st.session_state`,
- l'affichage des formulaires de connexion dans une page.

Les mots de passe sont stockés de manière sécurisée à l'aide de bcrypt.
Ce module est conçu pour des applications locales, des POC ou des démonstrateurs,
et peut servir de base avant une intégration avec une solution IAM plus avancée
(Entra ID, OAuth, etc.).
"""

import json
import os

import bcrypt
import streamlit as st

# Chemin vers le fichier users.json
USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users", "users.json")


# ----------------------------------------------------------------------
# S'assurer que le fichier users.json existe
# ----------------------------------------------------------------------
def _ensure_file():
    """
    Vérifie l'existence du fichier users.json.

    Si le fichier n'existe pas, il est automatiquement créé
    avec une structure JSON vide (dictionnaire).
    Cette fonction garantit que les opérations de lecture/écriture
    ne provoqueront pas d'erreur liée à un fichier manquant.
    """
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)


# Charger les utilisateurs depuis le fichier JSON
def load_users():
    """
    Charge la liste des utilisateurs depuis le fichier users.json.

    - Crée le fichier s'il n'existe pas encore.
    - Retourne un dictionnaire de la forme :
      {
        "username": {
            "password": "<mot_de_passe_hashé>"
        }
      }

    En cas d'erreur de lecture ou de JSON invalide,
    un dictionnaire vide est retourné.
    """
    _ensure_file()
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


# Sauvegarder les utilisateurs dans le fichier JSON
def save_users(users: dict):
    """
    Sauvegarde le dictionnaire des utilisateurs dans users.json.

    :param users: dictionnaire contenant les utilisateurs et leurs mots de passe hashés
    """
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# Hachage du mot de passe
def hash_password(plain_password: str) -> str:
    """
    Transforme un mot de passe en clair en un hash sécurisé avec bcrypt.

    :param plain_password: mot de passe en clair fourni par l'utilisateur
    :return: mot de passe hashé (chaîne de caractères)
    """
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


# Vérification du mot de passe
def check_password(plain_password: str, hashed: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à un hash bcrypt.

    :param plain_password: mot de passe saisi par l'utilisateur
    :param hashed: mot de passe hashé stocké
    :return: True si le mot de passe est correct, False sinon
    """
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed.encode())
    except Exception:
        return False


# ----------------------------------------------------------------------
# Widget d'authentification (Connexion + Inscription)
# ----------------------------------------------------------------------
def login_form_inside_page():
    """
    Affiche un formulaire de connexion et d'inscription directement
    à l'intérieur d'une page Streamlit (et non dans la sidebar).

    Cette fonction est utile pour les pages d'accueil ou les pages
    nécessitant une authentification avant redirection.

    :return: True si l'utilisateur est authentifié, False sinon
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    # Si l'utilisateur est déjà connecté
    if st.session_state.authenticated:
        return True

    st.markdown("### 🔐 Connexion")

    username = st.text_input("Utilisateur")
    password = st.text_input("Mot de passe", type="password")
    login_btn = st.button("Se connecter")

    if login_btn:
        users = load_users()
        user = users.get(username)

        if user and check_password(password, user["password"]):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Identifiants incorrects")

    st.markdown("---")

    # SECTION INSCRIPTION
    st.markdown("### ➕ Créer un compte")

    new_user = st.text_input("Nouvel utilisateur")
    new_pwd = st.text_input("Nouveau mot de passe", type="password")
    signup_btn = st.button("Créer un compte")

    if signup_btn:
        if not new_user or not new_pwd:
            st.error("Veuillez remplir tous les champs.")
        else:
            users = load_users()
            if new_user in users:
                st.warning("❗ Cet utilisateur existe déjà.")
            else:
                users[new_user] = {"password": hash_password(new_pwd)}
                save_users(users)
                st.success(f"Utilisateur **{new_user}** créé avec succès !")

    return False


# ----------------------------------------------------------------------
# Exiger une authentification pour accéder à une page
# ----------------------------------------------------------------------
def require_login():
    """
    Bloque l'accès à une page Streamlit tant que l'utilisateur
    n'est pas authentifié.

    Si l'utilisateur n'est pas connecté, l'exécution de la page
    est arrêtée avec `st.stop()`.
    """
    if not login_form_inside_page():
        st.stop()
