"""
Utilitaire de logging structuré JSON pour tous les services.
"""
import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formateur de logs en JSON structuré."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", record.name),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        extra_keys = set(record.__dict__.keys()) - set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())
        for key in extra_keys:
            if key not in ("service",):
                log_entry[key] = record.__dict__[key]
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Crée un logger structuré JSON.

    Args:
        service_name: nom du service
        level: niveau de log

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
