"""
preprocess.py — Prétraitement d'images pour l'OCR
Classe : ImagePreprocessor
Pipeline 8 étapes + conversion PDF
"""

import logging
import math
from typing import Optional

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Prépare les images pour maximiser la qualité OCR."""

    def preprocess(self, image_path: str) -> np.ndarray:
        """
        Applique un pipeline de 8 étapes de prétraitement sur une image.

        Args:
            image_path: Chemin vers le fichier image (JPG, PNG, etc.)

        Returns:
            Image prétraitée sous forme de tableau NumPy (niveaux de gris, binarisée).
        """
        # Étape 1 : Charger l'image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image : {image_path}")

        # Étape 2 : Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Étape 3 : Débruitage
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Étape 4 : Correction de luminosité via CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Étape 5 : Correction d'inclinaison (deskew)
        deskewed = self._deskew(enhanced)

        # Étape 6 : Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            deskewed,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )

        # Étape 7 : Rogner les bordures noires (5px chaque côté)
        cropped = binary[5:-5, 5:-5] if binary.shape[0] > 10 and binary.shape[1] > 10 else binary

        # Étape 8 : Upscale ×2 si résolution estimée < 200 DPI
        # Heuristique : image considérée < 200 DPI si largeur < 1600px (format A4 à 200dpi ≈ 1654px)
        upscaled = self._upscale_if_low_dpi(cropped)

        logger.debug(
            "Prétraitement terminé",
            extra={"shape_finale": upscaled.shape, "image_path": image_path}
        )
        return upscaled

    def preprocess_array(self, img: np.ndarray) -> np.ndarray:
        """
        Variante de preprocess() qui accepte directement un tableau NumPy
        (utile quand l'image vient de pdf_to_images).

        Args:
            img: Image BGR ou niveaux de gris sous forme de tableau NumPy.

        Returns:
            Image prétraitée (niveaux de gris, binarisée).
        """
        if img is None or img.size == 0:
            raise ValueError("Tableau NumPy vide ou None reçu.")

        # Étape 2 : Convertir en niveaux de gris si nécessaire
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Étapes 3 à 8 identiques à preprocess()
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        deskewed = self._deskew(enhanced)

        binary = cv2.adaptiveThreshold(
            deskewed,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )

        cropped = binary[5:-5, 5:-5] if binary.shape[0] > 10 and binary.shape[1] > 10 else binary
        upscaled = self._upscale_if_low_dpi(cropped)

        return upscaled

    def pdf_to_images(self, pdf_path: str) -> list[np.ndarray]:
        """
        Convertit toutes les pages d'un PDF en images NumPy.

        Args:
            pdf_path: Chemin vers le fichier PDF.

        Returns:
            Liste d'images (une par page), format BGR NumPy.
        """
        pil_images = convert_from_path(pdf_path, dpi=300)
        images = []
        for pil_img in pil_images:
            # Convertir PIL → NumPy BGR (format OpenCV)
            img_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            images.append(img_np)

        logger.debug(
            "PDF converti",
            extra={"pdf_path": pdf_path, "nb_pages": len(images)}
        )
        return images

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """
        Détecte et corrige l'angle d'inclinaison via la transformée de Hough
        probabiliste. La rotation n'est appliquée que si |angle| > 0.5°.

        Args:
            img: Image en niveaux de gris.

        Returns:
            Image corrigée (ou image d'origine si angle négligeable).
        """
        # Détection des contours pour alimenter Hough
        edges = cv2.Canny(img, threshold1=50, threshold2=150, apertureSize=3)

        # Transformée de Hough probabiliste
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10,
        )

        if lines is None:
            return img

        # Calcul de l'angle médian des lignes détectées
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                # Garder uniquement les angles proches de l'horizontale
                if -45 < angle < 45:
                    angles.append(angle)

        if not angles:
            return img

        median_angle = float(np.median(angles))

        # Rotation corrective uniquement si inclinaison significative
        if abs(median_angle) <= 0.5:
            return img

        logger.debug("Deskew : rotation de %.2f°", median_angle)

        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, scale=1.0)
        rotated = cv2.warpAffine(
            img,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated

    def _upscale_if_low_dpi(self, img: np.ndarray) -> np.ndarray:
        """
        Applique un upscale ×2 si la résolution estimée est inférieure à 200 DPI.
        Heuristique : largeur < 1654px (A4 à 200 DPI).

        Args:
            img: Image en niveaux de gris.

        Returns:
            Image redimensionnée ou image d'origine.
        """
        h, w = img.shape[:2]
        # Seuil : A4 à 200 DPI ≈ 1654 × 2339 px
        if w < 1654:
            upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            logger.debug("Upscale ×2 appliqué (%dx%d → %dx%d)", w, h, w * 2, h * 2)
            return upscaled
        return img
