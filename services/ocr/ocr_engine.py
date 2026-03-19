"""
Moteur OCR hybride ameliore : Tesseract + EasyOCR avec fallback automatique.
Configuration adaptative et multi-pass pour meilleure extraction.
"""
import logging
import time
import os

import cv2
import numpy as np
import pytesseract

logger = logging.getLogger("ocr-service.engine")

# Seuils de qualite
MIN_CONFIDENCE: float = 0.55  # Abaisse pour plus de rappel
MIN_TEXT_LENGTH: int = 30     # Abaisse pour documents courts


class OCREngine:
    """
    Moteur OCR hybride Tesseract/EasyOCR avec fallback automatique.
    
    Ameliorations v2:
    - Configuration Tesseract adaptative (PSM 3/4/6)
    - Multi-pass avec differents pretraitements  
    - Meilleure fusion des resultats
    - Support GPU optionnel pour EasyOCR
    """

    # Configurations Tesseract par type/contexte
    TESSERACT_CONFIGS = {
        "default": "--oem 3 --psm 3 -l fra+eng",    # Auto-detect layout
        "single_block": "--oem 3 --psm 6 -l fra",   # Bloc uniforme
        "multi_column": "--oem 3 --psm 4 -l fra",   # Multi-colonnes (factures)
        "sparse": "--oem 3 --psm 11 -l fra+eng",    # Texte epars
    }

    def __init__(self) -> None:
        # Configuration par defaut
        self.default_config = self.TESSERACT_CONFIGS["default"]
        
        # Initialisation EasyOCR (lazy loading)
        self._easyocr_reader = None
        
        # Detection GPU
        self._use_gpu = self._detect_gpu()
        
        logger.info("OCREngine v2 initialise (GPU: %s)", self._use_gpu)

    def _detect_gpu(self) -> bool:
        """Detecte si un GPU est disponible pour EasyOCR."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @property
    def easyocr_reader(self):
        """Chargement paresseux du reader EasyOCR."""
        if self._easyocr_reader is None:
            import easyocr
            self._easyocr_reader = easyocr.Reader(
                ["fr", "en"],
                gpu=self._use_gpu,
                verbose=False
            )
            logger.info("EasyOCR reader charge (fr, en) GPU=%s", self._use_gpu)
        return self._easyocr_reader

    def extract_text_tesseract(self, image: np.ndarray, config: str = None) -> dict:
        """
        Extraction via Tesseract avec scores de confiance par mot.

        Args:
            image: Image preprocessee
            config: Configuration Tesseract (utilise default si None)

        Returns:
            {"text": str, "confidence": float, "boxes": list}
        """
        start = time.time()
        
        if config is None:
            config = self.default_config

        # Extraction avec donnees detaillees
        data = pytesseract.image_to_data(
            image, config=config, output_type=pytesseract.Output.DICT,
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
        logger.debug(
            "Tesseract : %d mots, confiance=%.2f, duree=%dms",
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

        results = self.easyocr_reader.readtext(image, paragraph=False)

        words = []
        confidences = []
        boxes = []

        for bbox, text, conf in results:
            if conf < 0.35:  # Seuil abaisse
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
        logger.debug(
            "EasyOCR : %d mots, confiance=%.2f, duree=%dms",
            len(words), avg_confidence, duration_ms,
        )

        return {
            "text": full_text,
            "confidence": round(avg_confidence, 4),
            "boxes": boxes,
            "engine": "easyocr",
            "duration_ms": duration_ms,
        }

    def extract_text_multipass(self, image: np.ndarray) -> dict:
        """
        Extraction multi-pass avec differentes configurations Tesseract.
        Fusionne les resultats pour maximiser la couverture.
        """
        results = []
        
        # Pass 1: Configuration par defaut (auto-detect)
        results.append(self.extract_text_tesseract(image, self.TESSERACT_CONFIGS["default"]))
        
        # Pass 2: Multi-colonnes (bon pour factures)
        results.append(self.extract_text_tesseract(image, self.TESSERACT_CONFIGS["multi_column"]))
        
        # Prendre le meilleur resultat base sur confiance * longueur
        def score(r):
            return r["confidence"] * len(r["text"])
        
        best = max(results, key=score)
        
        # Enrichir avec des mots manquants des autres passes
        best_words = set(best["text"].lower().split())
        for result in results:
            if result is best:
                continue
            for word in result["text"].split():
                if word.lower() not in best_words and len(word) > 2:
                    # Mot potentiellement manquant
                    pass  # Pour l'instant on garde juste le meilleur
        
        return best

    def extract_text(self, image: np.ndarray) -> dict:
        """
        Strategie hybride d'extraction OCR :
        1. Tesseract multi-pass en premier (plus rapide)
        2. Fallback EasyOCR si confiance < seuil ou texte trop court
        3. Retourne le meilleur des deux

        Returns:
            {"text": str, "confidence": float, "boxes": list, "engine": str}
        """
        # 1. Essayer Tesseract avec multi-pass
        tess_result = self.extract_text_multipass(image)

        # 2. Verifier la qualite
        if (
            tess_result["confidence"] >= MIN_CONFIDENCE
            and len(tess_result["text"]) >= MIN_TEXT_LENGTH
        ):
            logger.info("Tesseract suffisant (conf=%.2f, len=%d)", 
                       tess_result["confidence"], len(tess_result["text"]))
            return tess_result

        # 3. Fallback EasyOCR
        logger.info(
            "Tesseract insuffisant (conf=%.2f, len=%d), fallback EasyOCR",
            tess_result["confidence"], len(tess_result["text"]),
        )
        easy_result = self.extract_text_easyocr(image)

        # 4. Retourner le meilleur (score = confiance * sqrt(longueur))
        def quality_score(r):
            return r["confidence"] * (len(r["text"]) ** 0.5)
        
        if quality_score(easy_result) > quality_score(tess_result):
            logger.info("EasyOCR retenu (conf=%.2f)", easy_result["confidence"])
            return easy_result

        logger.info("Tesseract retenu malgre la faible confiance (conf=%.2f)", tess_result["confidence"])
        return tess_result

    def extract_text_combined(self, image: np.ndarray) -> dict:
        """
        Mode combine : lance Tesseract et EasyOCR et fusionne intelligemment.
        Plus lent mais plus precis.
        """
        tess = self.extract_text_multipass(image)
        easy = self.extract_text_easyocr(image)
        
        # Fusionner les textes
        tess_words = set(tess["text"].lower().split())
        combined_text = tess["text"]
        
        # Ajouter les mots EasyOCR manquants
        for word in easy["text"].split():
            if word.lower() not in tess_words and len(word) > 2:
                combined_text += " " + word
        
        # Confiance = moyenne ponderee
        combined_conf = (tess["confidence"] * 0.6 + easy["confidence"] * 0.4)
        
        return {
            "text": combined_text,
            "confidence": round(combined_conf, 4),
            "boxes": tess["boxes"] + easy["boxes"],
            "engine": "combined",
            "duration_ms": tess.get("duration_ms", 0) + easy.get("duration_ms", 0),
        }
