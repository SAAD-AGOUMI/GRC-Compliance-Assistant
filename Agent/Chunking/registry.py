"""
Ce fichier fournit des fonctions utilitaires pour gérer un registre persistant
stocké sous forme de fichier JSON.

Le registre est utilisé pour mémoriser un ensemble de valeurs uniques (set),
par exemple des identifiants déjà traités, afin d'éviter les doublons lors
de traitements successifs.
"""

import json
from pathlib import Path


def load_registry(path: Path) -> set:
    """
    Charge un registre depuis un fichier JSON.
    Retourne un set vide si le fichier est inexistant ou vide/corrompu.
    """
    if path.exists():
        try:
            content = path.read_text(encoding="utf-8").strip()
            if content:
                return set(json.loads(content))
        except json.JSONDecodeError:
            print(f"⚠️ Fichier registre corrompu : {path}. Recréation.")
    return set()


def save_registry(path: Path, registry: set):
    """
    Sauvegarde un registre dans un fichier JSON.

    Les éléments du registre sont triés pour garantir une écriture stable
    et lisible dans le fichier.

    Args:
        path (Path): chemin vers le fichier JSON du registre
        registry (set): ensemble des éléments à sauvegarder
    """
    path.write_text(json.dumps(sorted(registry), indent=4), encoding="utf-8")
