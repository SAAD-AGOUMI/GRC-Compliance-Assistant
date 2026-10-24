"""
📁 Gestion des noms de fichiers d'historique de conversation

Ce module fournit des fonctions utilitaires pour :
- Transformer un texte libre en identifiant compatible fichier (slug)
- Générer automatiquement un nom de fichier JSON pour stocker
  l'historique d'une session de chat
- Organiser les fichiers par date avec une numérotation automatique

Les fichiers générés suivent le format :
YYYY-MM-DD_titre.json
ou
YYYY-MM-DD_chat_XX.json
"""

import os
import re
from datetime import datetime


def slugify(text):
    """
    🔤 Convertit un texte libre en une chaîne compatible avec un nom de fichier.

    Étapes :
    - Met le texte en minuscules
    - Supprime les espaces en début et fin
    - Remplace tous les caractères non alphanumériques par des underscores
    - Supprime les underscores inutiles en début et fin

    Exemple :
    "Mon Premier Chat !" → "mon_premier_chat"
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def new_history_filename(folder, title=None):
    """
    🗂️ Génère un nouveau nom de fichier pour l'historique d'une session de chat.

    Fonctionnement :
    - Crée automatiquement le dossier s'il n'existe pas
    - Utilise la date du jour comme préfixe (YYYY-MM-DD)
    - Si un titre est fourni par l'utilisateur :
        → le nom du fichier est basé sur ce titre
    - Sinon :
        → une numérotation automatique est appliquée (chat_01, chat_02, etc.)

    Paramètres :
    - folder (str) : dossier où stocker les fichiers d'historique
    - title (str | None) : titre optionnel fourni par l'utilisateur

    Retour :
    - str : nom du fichier JSON à créer
    """
    # 📅 Date du jour (format standard)
    date = datetime.now().strftime("%Y-%m-%d")

    # 📂 Création du dossier s'il n'existe pas
    os.makedirs(folder, exist_ok=True)

    # 📄 Liste de tous les fichiers du dossier correspondant à la date du jour
    existing = [f for f in os.listdir(folder) if f.startswith(date)]

    # 🔢 Numérotation automatique des sessions de chat
    count = sum(1 for f in existing if "_chat_" in f) + 1

    # ✏️ Cas où l'utilisateur a fourni un titre
    if title:
        title = slugify(title)
        return f"{date}_{title}.json"

    # 🤖 Cas par défaut : session numérotée automatiquement
    return f"{date}_chat_{count:02d}.json"
