FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-fra libgl1 poppler-utils libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_md

COPY . .

EXPOSE 5001

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5001", "--timeout", "300", "app:app"]
