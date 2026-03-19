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
    def _binarize(image: np.ndarray, blockSize: int = 25, C: int = 10) -> np.ndarray:
        """
        Binarisation adaptative gaussienne avec paramètres optimisés.
        
        Args:
            blockSize: Taille du bloc (doit être impair, plus grand = plus doux)
            C: Constante soustraite (plus petit = plus doux)
        """
        # S'assurer que blockSize est impair
        if blockSize % 2 == 0:
            blockSize += 1
        
        return cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=blockSize,
            C=C,
        )
    
    @staticmethod
    def _binarize_otsu(image: np.ndarray) -> np.ndarray:
        """Binarisation Otsu - meilleure pour documents de bonne qualité."""
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    @staticmethod
    def _binarize_sauvola(gray: np.ndarray, window_size: int = 25, k: float = 0.2) -> np.ndarray:
        """
        Binarisation de Sauvola - robuste pour éclairage non uniforme.
        Meilleure pour les documents scannés ou photographiés.
        """
        if gray.dtype != np.float64:
            gray_float = gray.astype(np.float64)
        else:
            gray_float = gray
        
        # Calculer la moyenne locale
        mean = cv2.blur(gray_float, (window_size, window_size))
        
        # Calculer l'écart-type local
        mean_sq = cv2.blur(gray_float * gray_float, (window_size, window_size))
        std = np.sqrt(np.maximum(mean_sq - mean * mean, 0))
        
        # Seuil de Sauvola
        R = 128.0  # Dynamic range
        threshold = mean * (1.0 + k * (std / R - 1.0))
        
        binary = np.zeros_like(gray, dtype=np.uint8)
        binary[gray > threshold] = 255
        
        return binary

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

    def _estimate_quality(self, gray: np.ndarray) -> dict:
        """
        Estime la qualité de l'image pour adapter le prétraitement.
        
        Returns:
            {
                "blur": float (variance du Laplacien),
                "noise": float (estimation du bruit),
                "contrast": float (contraste),
                "is_low_quality": bool,
            }
        """
        # Estimation du flou (variance du Laplacien)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = laplacian.var()
        
        # Estimation du contraste
        contrast = gray.std()
        
        # Estimation du bruit (sur une zone unie)
        # Utiliser la médiane des écarts-types de petits blocs
        h, w = gray.shape
        block_size = 16
        noise_estimates = []
        for y in range(0, h - block_size, block_size * 4):
            for x in range(0, w - block_size, block_size * 4):
                block = gray[y:y+block_size, x:x+block_size]
                if block.std() < 10:  # Zone relativement unie
                    noise_estimates.append(block.std())
        noise = np.median(noise_estimates) if noise_estimates else 0
        
        return {
            "blur": blur_score,
            "noise": noise,
            "contrast": contrast,
            "is_low_quality": blur_score < 100 or contrast < 30 or noise > 10,
        }
    
    def preprocess(self, image_path: str) -> np.ndarray:
        """
        Pipeline complet de prétraitement adaptatif pour l'OCR.

        Args:
            image_path: chemin vers le fichier image

        Returns:
            Image numpy prête pour l'OCR (niveaux de gris, binarisée)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Impossible de charger l'image : {image_path}")

        return self._preprocess_image(image, image_path)
    
    def _preprocess_image(self, image: np.ndarray, source: str = "array") -> np.ndarray:
        """Pipeline de prétraitement adaptatif."""
        # 1. Conversion grayscale
        gray = self._to_grayscale(image)
        
        # 2. Upscale AVANT traitement si basse résolution
        gray = self._upscale_if_low_res(gray)
        
        # 3. Analyser la qualité
        quality = self._estimate_quality(gray)
        logger.debug("Qualité image: blur=%.1f, noise=%.1f, contrast=%.1f",
                    quality["blur"], quality["noise"], quality["contrast"])
        
        # 4. Débruitage adaptatif
        if quality["noise"] > 8:
            gray = self._denoise(gray)
        elif quality["noise"] > 3:
            gray = cv2.fastNlMeansDenoising(gray, h=5)  # Léger
        
        # 5. Amélioration du contraste (si nécessaire)
        if quality["contrast"] < 50:
            gray = self._enhance_contrast(gray)
        
        # 6. Correction d'inclinaison
        gray = self._deskew(gray)
        
        # 7. Binarisation adaptative selon la qualité
        if quality["is_low_quality"]:
            # Utiliser Sauvola pour documents de mauvaise qualité
            binarized = self._binarize_sauvola(gray, window_size=31, k=0.15)
            logger.debug("Binarisation Sauvola appliquée (basse qualité)")
        else:
            # Utiliser binarisation adaptative standard avec paramètres doux
            binarized = self._binarize(gray, blockSize=31, C=12)
        
        # 8. Nettoyage des bordures
        result = self._crop_borders(binarized)
        
        logger.info("Prétraitement terminé : %s → shape=%s, qualité=%s",
                   source, result.shape, "basse" if quality["is_low_quality"] else "bonne")
        return result

    def preprocess_from_array(self, image: np.ndarray) -> np.ndarray:
        """Prétraite une image déjà chargée en mémoire."""
        return self._preprocess_image(image, "array")

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
