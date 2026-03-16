# Image Python légère comme base
FROM python:3.11-slim

# Dossier de travail dans le conteneur
WORKDIR /app

# Copie et installation des dépendances en premier
# (Docker met en cache cette étape si requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Exécution du script d'initialisation des buckets au démarrage
CMD ["python", "init_buckets.py"]