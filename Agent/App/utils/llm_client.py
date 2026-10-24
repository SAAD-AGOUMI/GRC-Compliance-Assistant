"""
🌐 Gestion de la connexion à mistral et requêtes LLM

Ce module fournit :
1. La configuration du client mistral pour un environnement conteneurisé
2. La définition de la variable d'environnement appropriée pour le client mistral
3. Une fonction pour interroger le modèle LLM avec un prompt utilisateur
4. Un message système sécurisant pour éviter les hallucinations et protéger
la vie privée
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.mistral_client import chat

# Charger la configuration depuis le fichier .env
load_dotenv()

# -----------------------------
# 🛡️ Message système pour éviter les hallucinations et protéger la vie privée
# -----------------------------
SYSTEM_PROMPT = (
    "RÔLE\n"
    "Tu es un assistant factuel et non spéculatif.\n\n"
    "RÈGLES GÉNÉRALES\n"
    "- Réponds uniquement à partir des informations explicitement fournies par"
    "l'utilisateur ou par le contexte du prompt.\n"
    "- N'invente aucune information.\n"
    "- N'ajoute aucun détail qui ne figure pas dans les données fournies.\n"
    "- Si l'information demandée n'est pas présente, dis-le clairement.\n\n"
    "CONFIDENTIALITÉ\n"
    "- Tu ne fais aucune référence à des utilisateurs, conversations ou données non"
    "présentes dans le prompt.\n"
    "- Si une question porte sur des données non fournies, réponds que l'information"
    "n'est pas disponible.\n\n"
    "STYLE DE RÉPONSE\n"
    "- Réponse directe et concise.\n"
    "- Pas d'explication sur ton fonctionnement interne.\n"
    "- Pas de mention de règles ou de politiques."
)


# -----------------------------
# 💬 Fonction pour interroger le modèle LLM
# -----------------------------
def query_llm(prompt: str, history: Optional[list] = None):
    """
    Envoie un prompt au LLM mistral et retourne la réponse générée.

    Paramètres :
    - prompt (str) : message utilisateur à envoyer au modèle.
    - history (list | None) : historique optionnel de la conversation,
    sous la forme d'une liste de tuples (role, content, timestamp).
    Si None ou vide, le modèle est interrogé sans contexte conversationnel.

    Retour :
    - str : réponse générée par le modèle ou message d'erreur en cas d'échec.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for role, content, _ in history:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": prompt})

    model_name = os.getenv("LLM_RAG")
    if model_name is None:
        raise RuntimeError("LLM_RAG is not set")

    try:
        return chat(model_name, messages)
    except Exception as e:
        return f"⚠️ Erreur de l'API Mistral ({model_name}).\n\nDétails : {e}"
