import os
import time

import requests
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")


def wait_for_services():
    while True:
        try:
            # Test Qdrant (endpoint valide)
            qdrant_resp = requests.get(f"{QDRANT_URL}/collections", timeout=2)
            qdrant_resp.raise_for_status()

            print("✅ Qdrant est prêt")
            break

        except Exception as e:
            print(f"⏳ En attente de Qdrant... ({e})")
            time.sleep(2)
