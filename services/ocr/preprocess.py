"""
Module de prétraitement d'images pour l'OCR.
Corrige les défauts courants des documents scannés.
"""
import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("ocr-service.preprocess")


class ImagePreprocessor:
    """Prépare les images de documents pour l'extraction OCR."""

    @staticmethod
    def _to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convertit en niveaux de gris si nécessaire."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def _denoise(image: np.ndarray) -> np.ndarray:
        """Supprime le bruit de l'image."""
        return cv2.fastNlMeansDenoising(image, h=10)

    @staticmethod
    def _enhance_contrast(image: np.ndarray) -> np.ndarray:
        """Améliore le contraste avec CLAHE."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)

    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """Corrige l'inclinaison via la transformée de Hough."""
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=100, maxLineGap=10,
        )
        if lines is None:
            return image

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x2 - x1) > 0:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Filtrer les lignes quasi-horizontales (±30°)
                if abs(angle) < 30:
                    angles.append(angle)

        if not angles:
            return image

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.5:
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        logger.info("Deskew appliqué : angle=%.2f°", median_angle)
        return rotated

    @staticmethod
    def _binarize(image: np.ndarray) -> np.ndarray:
        """Binarisation adaptative gaussienne."""
        return cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=8,
        )

    @staticmethod
    def _crop_borders(image: np.ndarray, margin: int = 5) -> np.ndarray:
        """Supprime les bordures noires potentielles."""
        h, w = image.shape[:2]
        if h > 2 * margin and w > 2 * margin:
            return image[margin:h - margin, margin:w - margin]
        return image

    @staticmethod
    def _upscale_if_low_res(image: np.ndarray, min_dpi_equivalent: int = 200) -> np.ndarray:
        """Augmente la résolution si l'image semble basse résolution."""
        h, w = image.shape[:2]
        # Heuristique : si la hauteur < 1500px pour un A4, on considère < 200 DPI
        if h < 1500:
            scale = 2
            new_w = w * scale
            new_h = h * scale
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logger.info("Upscale ×%d appliqué (hauteur originale : %dpx)", scale, h)
        return image

    def preprocess(self, image_path: str) -> np.ndarray:
        """
        Pipeline complet de prétraitement d'une image pour l'OCR.

        Args:
            image_path: chemin vers le fichier image

        Returns:
            Image numpy prête pour l'OCR (niveaux de gris, binarisée)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Impossible de charger l'image : {image_path}")

        gray = self._to_grayscale(image)
        denoised = self._denoise(gray)
        enhanced = self._enhance_contrast(denoised)
        deskewed = self._deskew(enhanced)
        binarized = self._binarize(deskewed)
        cropped = self._crop_borders(binarized)
        result = self._upscale_if_low_res(cropped)

        logger.info("Prétraitement terminé : %s → shape=%s", image_path, result.shape)
        return result

    def preprocess_from_array(self, image: np.ndarray) -> np.ndarray:
        """Prétraite une image déjà chargée en mémoire."""
        gray = self._to_grayscale(image)
        denoised = self._denoise(gray)
        enhanced = self._enhance_contrast(denoised)
        deskewed = self._deskew(enhanced)
        binarized = self._binarize(deskewed)
        cropped = self._crop_borders(binarized)
        result = self._upscale_if_low_res(cropped)
        return result

    @staticmethod
    def pdf_to_images(pdf_path: str) -> list[np.ndarray]:
        """
        Convertit un PDF en liste d'images (une par page).

        Args:
            pdf_path: chemin vers le fichier PDF

        Returns:
            Liste d'images numpy (BGR)
        """
        try:
            from pdf2image import convert_from_path
            pil_images = convert_from_path(pdf_path, dpi=300)
            images = []
            for pil_img in pil_images:
                arr = np.array(pil_img)
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                images.append(bgr)
            return images
        except ImportError:
            pass

        # Fallback PyMuPDF
        import fitz
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n,
            )
            if pix.n == 4:
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            else:
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            images.append(bgr)
        doc.close()
        return images
