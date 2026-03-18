# Utils - DocuFlow

Utilitaires partagés entre les différents composants.

## 📁 Fichiers

| Fichier | Description |
|---------|-------------|
| `logger.py` | Configuration du logging JSON structuré |

## 🔧 Logger

Configuration du logging au format JSON pour faciliter l'agrégation (ELK, Datadog, etc.).

```python
from utils.logger import get_logger

logger = get_logger("mon-service")
logger.info("Message", extra={"document_id": "abc123"})
```

**Output :**
```json
{
  "timestamp": "2026-03-18T10:00:00",
  "service": "mon-service",
  "level": "INFO",
  "message": "Message",
  "document_id": "abc123"
}
```
