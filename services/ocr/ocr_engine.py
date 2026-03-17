"""
ocr_engine.py — Moteur OCR hybride Tesseract + EasyOCR
Classe : OCREngine
"""

import logging
from typing import Any

import cv2
import numpy as np
import pytesseract
import easyocr

logger = logging.getLogger(__name__)


class OCREngine:
    """Moteur OCR hybride : Tesseract en priorité, EasyOCR en fallback."""

    def __init__(self) -> None:
        # Configuration Tesseract : OEM 3 (LSTM), PSM 6 (bloc de texte uniforme), français
        self._tesseract_config = "--oem 3 --psm 6 -l fra"

        # Initialisation EasyOCR (CPU uniquement, chargement des modèles différé)
        self._reader: easyocr.Reader | None = None
        logger.info("OCREngine initialisé (EasyOCR chargé à la première utilisation)")

    @property
    def reader(self) -> easyocr.Reader:
        """Chargement paresseux d'EasyOCR pour éviter le délai au démarrage."""
        if self._reader is None:
            logger.info("Chargement du modèle EasyOCR (fr + en)…")
            self._reader = easyocr.Reader(["fr", "en"], gpu=False)
            logger.info("EasyOCR chargé.")
        return self._reader

    # ------------------------------------------------------------------
    # Tesseract
    # ------------------------------------------------------------------

    def extract_text_tesseract(self, image: np.ndarray) -> dict[str, Any]:
        """
        Extrait le texte via Tesseract et calcule la confiance moyenne par mot.

        Args:
            image: Image prétraitée (niveaux de gris, NumPy).

        Returns:
            {"text": str, "confidence": float, "boxes": list}
        """
        data = pytesseract.image_to_data(
            image,
            config=self._tesseract_config,
            output_type=pytesseract.Output.DICT,
        )

        words = []
        confidences = []
        boxes = []

        for i, word in enumerate(data["text"]):
            conf = int(data["conf"][i])
            # Tesseract retourne -1 pour les blocs sans confiance (séparateurs)
            if conf < 0 or not word.strip():
                continue
            words.append(word)
            confidences.append(conf)
            boxes.append({
                "word": word,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
                "confidence": conf / 100.0,
            })

        text = " ".join(words)
        avg_confidence = float(np.mean(confidences) / 100.0) if confidences else 0.0

        return {
            "text": text,
            "confidence": round(avg_confidence, 4),
            "boxes": boxes,
        }

    # ------------------------------------------------------------------
    # EasyOCR
    # ------------------------------------------------------------------

    def extract_text_easyocr(self, image: np.ndarray) -> dict[str, Any]:
        """
        Extrait le texte via EasyOCR, en filtrant les résultats peu fiables.

        Args:
            image: Image prétraitée (niveaux de gris ou BGR, NumPy).

        Returns:
            {"text": str, "confidence": float, "boxes": list}
        """
        results = self.reader.readtext(image)

        words = []
        confidences = []
        boxes = []

        for (bbox, text, conf) in results:
            # Filtrage des résultats avec confiance < 0.4
            if conf < 0.4:
                continue
            words.append(text)
            confidences.append(conf)
            boxes.append({
                "word": text,
                "bbox": bbox,
                "confidence": round(conf, 4),
            })

        full_text = " ".join(words)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        return {
            "text": full_text,
            "confidence": round(avg_confidence, 4),
            "boxes": boxes,
        }

    # ------------------------------------------------------------------
    # Stratégie hybride
    # ------------------------------------------------------------------

    def extract_text(self, image: np.ndarray) -> dict[str, Any]:
        """
        Stratégie hybride : Tesseract d'abord, EasyOCR en fallback.

        Règles de fallback :
        - Confiance Tesseract < 0.6
        - OU texte extrait < 50 caractères
        → On essaie EasyOCR et on retourne le meilleur résultat.

        Args:
            image: Image prétraitée (NumPy).

        Returns:
            {"text": str, "confidence": float, "boxes": list,
             "ocr_engine_used": str}
        """
        # Étape 1 : Tesseract
        tess_result = self.extract_text_tesseract(image)
        tess_conf = tess_result["confidence"]
        tess_text = tess_result["text"]

        logger.info(
            "Tesseract : confiance=%.3f, longueur_texte=%d",
            tess_conf, len(tess_text)
        )

        # Décision : résultat Tesseract suffisant ?
        if tess_conf >= 0.6 and len(tess_text) >= 50:
            logger.info("Moteur retenu : tesseract (confiance suffisante)")
            return {**tess_result, "ocr_engine_used": "tesseract"}

        # Étape 2 : Fallback EasyOCR
        logger.info(
            "Fallback EasyOCR (conf=%.3f, len=%d)", tess_conf, len(tess_text)
        )
        easy_result = self.extract_text_easyocr(image)
        easy_conf = easy_result["confidence"]

        logger.info("EasyOCR : confiance=%.3f, longueur_texte=%d", easy_conf, len(easy_result["text"]))

        # Étape 3 : Si les deux sont mauvais → retourner le meilleur
        if easy_conf >= tess_conf:
            logger.info("Moteur retenu : easyocr (meilleure confiance)")
            return {**easy_result, "ocr_engine_used": "easyocr"}
        else:
            logger.info("Moteur retenu : tesseract (meilleur malgré fallback)")
            return {**tess_result, "ocr_engine_used": "tesseract"}
