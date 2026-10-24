# Image de base : Python 3.11 version "slim"
FROM python:3.11-slim

# Définit le dossier de travail à l’intérieur du conteneur
# Toutes les commandes suivantes (COPY, RUN, CMD…) seront exécutées depuis /app
WORKDIR /app

# Copie uniquement le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances de compilation nécessaires pour certaines bibliothèques Python
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installe les dépendances Python listées dans requirements.txt
# --no-cache-dir évite de stocker les caches pip → image plus légère
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste du projet (code source, scripts, etc.) dans /app
COPY . .

# Commande exécutée automatiquement au démarrage du conteneur
# Lance le script principal de l’Agent
CMD ["python", "main.py"]