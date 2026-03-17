# OCR Service — Dockerfile
# Base : python:3.11-slim

FROM python:3.11-slim

# Métadonnées
LABEL service="ocr-service" \
      port="5001" \
      description="Service OCR & Extraction d'entités pour documents administratifs"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR + langue française
    tesseract-ocr \
    tesseract-ocr-fra \
    # OpenGL (requis par opencv-python-headless via libGL stub)
    libgl1 \
    # Poppler (pdf2image)
    poppler-utils \
    # libmagic (python-magic)
    libmagic1 \
    # Nettoyage du cache apt
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
# Forcer PyTorch CPU-only AVANT d'installer easyocr
# (sans ça, pip résout la version CUDA de torch = +5 GB inutiles en conteneur)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        torch==2.3.1+cpu \
        torchvision==0.18.1+cpu \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Télécharger le modèle spaCy français (installation directe pour éviter les erreurs d'URL)
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.7.0/fr_core_news_md-3.7.0-py3-none-any.whl

# Pré-télécharger les modèles EasyOCR dans l'image pour éviter le téléchargement
# au runtime (qui peut échouer ou corrompre les fichiers sous charge)
RUN python -c "import easyocr; easyocr.Reader(['fr', 'en'], gpu=False)" 2>&1 | grep -v "^Progress"

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /tmp/ocr_uploads /app/output

# Port exposé
EXPOSE 5001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/api/health')" || exit 1

# Lancement via Gunicorn (2 workers, bind 0.0.0.0:5001)
CMD ["gunicorn", "-w", "2", "--preload", "-b", "0.0.0.0:5001", "--timeout", "180", "--access-logfile", "-", "app:app"]
