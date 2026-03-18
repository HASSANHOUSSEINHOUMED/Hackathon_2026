"""
Moteur OCR hybride : Tesseract + EasyOCR avec fallback automatique.
"""
import logging
import time

import cv2
import numpy as np
import pytesseract

logger = logging.getLogger("ocr-service.engine")

# Seuils de qualité
MIN_CONFIDENCE: float = 0.6
MIN_TEXT_LENGTH: int = 50


class OCREngine:
    """Moteur OCR hybride Tesseract/EasyOCR avec fallback automatique."""

    def __init__(self) -> None:
        # Configuration Tesseract
        self.tesseract_config: str = "--oem 3 --psm 6 -l fra"

        # Initialisation EasyOCR (lazy loading pour économiser la mémoire)
        self._easyocr_reader = None

        logger.info("OCREngine initialisé (Tesseract config: %s)", self.tesseract_config)

    @property
    def easyocr_reader(self):
        """Chargement paresseux du reader EasyOCR."""
        if self._easyocr_reader is None:
            import easyocr
            self._easyocr_reader = easyocr.Reader(["fr", "en"], gpu=False)
            logger.info("EasyOCR reader chargé (fr, en)")
        return self._easyocr_reader

    def extract_text_tesseract(self, image: np.ndarray) -> dict:
        """
        Extraction via Tesseract avec scores de confiance par mot.

        Returns:
            {"text": str, "confidence": float, "boxes": list}
        """
        start = time.time()

        # Extraction avec données détaillées
        data = pytesseract.image_to_data(
            image, config=self.tesseract_config, output_type=pytesseract.Output.DICT,
        )

        words = []
        confidences = []
        boxes = []

        for i, text in enumerate(data["text"]):
            text = text.strip()
            if not text:
                continue
            conf = int(data["conf"][i])
            if conf < 0:
                continue
            words.append(text)
            confidences.append(conf / 100.0)
            boxes.append({
                "text": text,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "confidence": conf / 100.0,
            })

        full_text = " ".join(words)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "Tesseract : %d mots, confiance=%.2f, durée=%dms",
            len(words), avg_confidence, duration_ms,
        )

        return {
            "text": full_text,
            "confidence": round(avg_confidence, 4),
            "boxes": boxes,
            "engine": "tesseract",
            "duration_ms": duration_ms,
        }

    def extract_text_easyocr(self, image: np.ndarray) -> dict:
        """
        Extraction via EasyOCR avec filtrage par confiance.

        Returns:
            {"text": str, "confidence": float, "boxes": list}
        """
        start = time.time()

        results = self.easyocr_reader.readtext(image)

        words = []
        confidences = []
        boxes = []

        for bbox, text, conf in results:
            if conf < 0.4:
                continue
            text = text.strip()
            if not text:
                continue
            words.append(text)
            confidences.append(conf)
            # bbox est une liste de 4 points
            x_min = int(min(p[0] for p in bbox))
            y_min = int(min(p[1] for p in bbox))
            x_max = int(max(p[0] for p in bbox))
            y_max = int(max(p[1] for p in bbox))
            boxes.append({
                "text": text,
                "x": x_min,
                "y": y_min,
                "w": x_max - x_min,
                "h": y_max - y_min,
                "confidence": round(conf, 4),
            })

        full_text = " ".join(words)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "EasyOCR : %d mots, confiance=%.2f, durée=%dms",
            len(words), avg_confidence, duration_ms,
        )

        return {
            "text": full_text,
            "confidence": round(avg_confidence, 4),
            "boxes": boxes,
            "engine": "easyocr",
            "duration_ms": duration_ms,
        }

    def extract_text(self, image: np.ndarray) -> dict:
        """
        Stratégie hybride d'extraction OCR :
        1. Tesseract en premier (plus rapide)
        2. Fallback EasyOCR si confiance < 0.6 ou texte trop court
        3. Retourne le meilleur des deux

        Returns:
            {"text": str, "confidence": float, "boxes": list, "engine": str}
        """
        # 1. Essayer Tesseract
        tess_result = self.extract_text_tesseract(image)

        # 2. Vérifier la qualité
        if (
            tess_result["confidence"] >= MIN_CONFIDENCE
            and len(tess_result["text"]) >= MIN_TEXT_LENGTH
        ):
            logger.info("Tesseract suffisant (conf=%.2f)", tess_result["confidence"])
            return tess_result

        # 3. Fallback EasyOCR
        logger.info(
            "Tesseract insuffisant (conf=%.2f, len=%d), fallback EasyOCR",
            tess_result["confidence"], len(tess_result["text"]),
        )
        easy_result = self.extract_text_easyocr(image)

        # 4. Retourner le meilleur
        if easy_result["confidence"] > tess_result["confidence"]:
            logger.info("EasyOCR retenu (conf=%.2f)", easy_result["confidence"])
            return easy_result

        logger.info("Tesseract retenu malgré la faible confiance (conf=%.2f)", tess_result["confidence"])
        return tess_result
