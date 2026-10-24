"""
Gestion de la configuration et des historiques utilisateurs.

Ce fichier fournit les fonctions suivantes :

1. Charger la configuration globale depuis `config.toml` avec cache.
2. Créer un dossier stable pour chaque utilisateur (hashé).
3. Lister les fichiers d'historique d'un utilisateur.
4. Charger l'historique des messages depuis un fichier JSON.
5. Récupérer uniquement le titre d'une discussion.
6. Sauvegarder une discussion avec messages et titre.

📂 Tous les fichiers JSON sont stockés dans `utils/history/<hash_utilisateur>/`.
"""

import hashlib
import json
import os
from functools import lru_cache

import toml

# Répertoire racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


@lru_cache(maxsize=1)
def load_config():
    """
    🔧 Charger la configuration globale depuis le fichier `config.toml`.

    Utilise un cache pour éviter de recharger le fichier à chaque appel.

    Retour :
        dict : Contenu du fichier TOML sous forme de dictionnaire.
    """
    config_path = os.path.join(BASE_DIR, "config.toml")
    return toml.load(os.path.abspath(config_path))


def user_folder(username: str) -> str:
    """
    🔐 Créer ou récupérer un dossier stable pour un utilisateur.

    Chaque utilisateur reçoit un hash SHA-256 basé sur son nom,
    tronqué à 16 caractères pour former le nom du dossier.

    Args:
        username (str) : Nom de l'utilisateur.

    Returns:
        str : Chemin complet vers le dossier de l'utilisateur.
    """
    uname = username.strip() or "anonymous"
    uid_hash = hashlib.sha256(uname.encode("utf-8")).hexdigest()[:16]
    folder = os.path.join(BASE_DIR, "utils", "history", uid_hash)
    os.makedirs(folder, exist_ok=True)
    return folder


def list_history_files(username: str):
    """
    📁 Lister tous les fichiers d'historique JSON d'un utilisateur.

    Args:
        username (str) : Nom de l'utilisateur.

    Returns:
        list[str] : Liste triée des fichiers JSON (ex. ["chat1.json", "chat2.json"]).
    """
    folder = user_folder(username)
    if not os.path.exists(folder):
        return []
    return sorted([f for f in os.listdir(folder) if f.endswith(".json")])


def load_history_for(username: str, filename: str):
    """
    🧠 Charger les messages d'une discussion pour un utilisateur.

    Compatible avec :
      - anciens fichiers : simple liste de messages [(role, content, timestamp), ...]
      - nouveaux fichiers : dictionnaire {"title": ..., "messages": [...]}

    Args:
        username (str) : Nom de l'utilisateur.
        filename (str) : Nom du fichier JSON à charger.

    Returns:
        list : Liste des messages [(role, content, timestamp), ...]
    """
    folder = user_folder(username)
    path = os.path.join(folder, filename)

    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ancien format : liste de messages
            if isinstance(data, list):
                return data

            # Nouveau format : dict avec "messages"
            if isinstance(data, dict):
                return data.get("messages", [])
        except json.JSONDecodeError:
            return []
    return []


def get_history_title(username: str, filename: str) -> str:
    """
    🔎 Récupérer uniquement le titre d'une discussion.

    Compatibilité :
      - anciens fichiers : pas de titre → "(Ancienne discussion)"
      - nouveaux fichiers : {"title": "...", "messages": [...]}

    Args:
        username (str) : Nom de l'utilisateur.
        filename (str) : Nom du fichier JSON.

    Returns:
        str : Titre de la discussion ou texte par défaut si absent/corrompu.
    """
    folder = user_folder(username)
    path = os.path.join(folder, filename)

    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        return "(Discussion)"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ancien format : pas de titre
        if isinstance(data, list):
            return "(Ancienne discussion)"

        if isinstance(data, dict):
            title = data.get("title")
            if title and isinstance(title, str) and title.strip():
                return title.strip()
            return "(Discussion sans titre)"
    except json.JSONDecodeError:
        return "(Discussion corrompue)"

    return "(Discussion)"


def save_history_for(username: str, messages, filename: str, title: str | None = None):
    """
    💾 Sauvegarder une discussion pour un utilisateur.

    Args:
        username (str) : Nom de l'utilisateur.
        messages (list | dict) : Liste de messages [(role, content, timestamp), ...]
                                 ou dict complet {"title": ..., "messages": [...]}
        filename (str) : Nom du fichier JSON à créer/modifier.
        title (str | None) : Titre de la discussion (optionnel).
                             Si None, le titre précédent sera utilisé.
    """
    folder = user_folder(username)
    path = os.path.join(folder, filename)
    os.makedirs(folder, exist_ok=True)

    # Si messages est déjà un dict complet, on le respecte
    if isinstance(messages, dict):
        data = messages
    else:
        data = {
            "title": title,
            "messages": messages,
        }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
