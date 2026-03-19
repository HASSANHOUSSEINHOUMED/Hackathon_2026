"""
Moteur de dégradation d'images pour simuler des scans de mauvaise qualité.
"""
import random

import cv2
import numpy as np
from PIL import Image


class ImageDegrader:
    """Applique des dégradations réalistes à des images de documents."""

    @staticmethod
    def rotate(image: np.ndarray, angle: float | None = None) -> np.ndarray:
        """Rotation de l'image (simule un scan de travers)."""
        if angle is None:
            angle = random.uniform(-5, 5)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, matrix, (w, h),
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated

    @staticmethod
    def blur(image: np.ndarray, kernel: int | None = None) -> np.ndarray:
        """Flou gaussien (simule un scan flou)."""
        if kernel is None:
            kernel = random.choice([3, 5, 7])
        return cv2.GaussianBlur(image, (kernel, kernel), 0)

    @staticmethod
    def noise(image: np.ndarray, sigma: float | None = None) -> np.ndarray:
        """Bruit gaussien (simule du grain de scanner)."""
        if sigma is None:
            sigma = random.uniform(10, 40)
        gauss = np.random.normal(0, sigma, image.shape).astype(np.float32)
        noisy = np.clip(image.astype(np.float32) + gauss, 0, 255).astype(np.uint8)
        return noisy

    @staticmethod
    def reduce_dpi(image: np.ndarray, target_dpi: int = 150) -> np.ndarray:
        """Réduit la résolution (simule un scan basse qualité)."""
        scale = target_dpi / 300  # on suppose image originale à 300 DPI
        h, w = image.shape[:2]
        small = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        back = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
        return back

    @staticmethod
    def brightness(image: np.ndarray, factor: float | None = None) -> np.ndarray:
        """Variation de luminosité (simule un éclairage inégal)."""
        if factor is None:
            factor = random.uniform(0.6, 1.4)
        adjusted = np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        return adjusted

    @staticmethod
    def fold_shadow(image: np.ndarray) -> np.ndarray:
        """Ombre de pliure (simule un document plié)."""
        h, w = image.shape[:2]
        result = image.copy().astype(np.float32)
        # Position de la pliure (verticale aléatoire)
        fold_x = random.randint(w // 4, 3 * w // 4)
        shadow_width = random.randint(20, 60)
        for x in range(max(0, fold_x - shadow_width), min(w, fold_x + shadow_width)):
            dist = abs(x - fold_x)
            darkness = 1.0 - 0.4 * (1.0 - dist / shadow_width)
            result[:, x] = result[:, x] * darkness
        return np.clip(result, 0, 255).astype(np.uint8)

    @staticmethod
    def jpeg_compress(image: np.ndarray, quality: int = 85) -> np.ndarray:
        """Compression JPEG avec perte (artefacts de compression)."""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded = cv2.imencode(".jpg", image, encode_param)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR if len(image.shape) == 3 else cv2.IMREAD_GRAYSCALE)
        return decoded

    @staticmethod
    def perspective_warp(image: np.ndarray) -> np.ndarray:
        """Déformation perspective (simule une photo prise en angle)."""
        h, w = image.shape[:2]
        margin = int(min(w, h) * 0.05)
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst = np.float32([
            [random.randint(0, margin), random.randint(0, margin)],
            [w - random.randint(0, margin), random.randint(0, margin)],
            [w - random.randint(0, margin), h - random.randint(0, margin)],
            [random.randint(0, margin), h - random.randint(0, margin)],
        ])
        matrix = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(image, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)
        return warped

    def apply_random_degradation(
        self, image: np.ndarray, level: str = "medium"
    ) -> np.ndarray:
        """
        Applique une combinaison de dégradations selon le niveau.

        Args:
            image: image source (numpy array BGR ou niveaux de gris)
            level: 'light', 'medium' ou 'heavy'
        """
        result = image.copy()

        if level == "light":
            result = self.rotate(result, angle=random.uniform(-1.5, 1.5))
            result = self.blur(result, kernel=3)
            result = self.jpeg_compress(result, quality=85)
            result = self.brightness(result, factor=random.uniform(0.85, 1.15))

        elif level == "medium":
            result = self.rotate(result, angle=random.uniform(-3, 3))
            result = self.blur(result, kernel=5)
            result = self.noise(result, sigma=15)
            result = self.reduce_dpi(result, target_dpi=150)
            result = self.jpeg_compress(result, quality=65)

        elif level == "heavy":
            result = self.rotate(result, angle=random.uniform(-6, 6))
            result = self.blur(result, kernel=7)
            result = self.noise(result, sigma=35)
            result = self.reduce_dpi(result, target_dpi=72)
            result = self.fold_shadow(result)
            result = self.perspective_warp(result)
            result = self.jpeg_compress(result, quality=40)
            result = self.brightness(result, factor=random.uniform(0.6, 1.3))

        return result


def pdf_to_clean_image(pdf_path: str, output_path: str) -> str:
    """
    Convertit un PDF en image propre (sans dégradation) → simule un bon scanner.

    Args:
        pdf_path: chemin du PDF source
        output_path: chemin de sortie (JPG ou PNG)

    Returns:
        chemin du fichier image créé
    """
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        doc.close()
    except ImportError:
        raise ImportError(
            "Installez PyMuPDF : pip install PyMuPDF"
        )
    cv2.imwrite(output_path, image)
    return output_path


def degrade_pdf_to_image(
    pdf_path: str, output_path: str, level: str = "medium"
) -> str:
    """
    Convertit un PDF en image puis applique une dégradation.

    Args:
        pdf_path: chemin du PDF source
        output_path: chemin de sortie (JPG)
        level: niveau de dégradation

    Returns:
        chemin du fichier dégradé
    """
    # Convertir le PDF en image via reportlab/PIL
    # On utilise pdf2image si disponible, sinon PIL
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
        image = np.array(images[0])
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    except (ImportError, Exception) as _pdf2img_err:
        # Fallback : utiliser PyMuPDF (fitz) si pdf2image ou poppler unavailable
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            if pix.n == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            doc.close()
        except ImportError:
            raise ImportError(
                "Installez pdf2image ou PyMuPDF pour la conversion PDF→image : "
                "pip install pdf2image PyMuPDF"
            )

    degrader = ImageDegrader()
    # Réduire la taille avant dégradation pour accélérer le traitement
    h, w = image.shape[:2]
    if w > 1200:
        scale = 1200 / w
        image = cv2.resize(image, (1200, int(h * scale)), interpolation=cv2.INTER_AREA)
    degraded = degrader.apply_random_degradation(image, level=level)
    cv2.imwrite(output_path, degraded)
    return output_path


if __name__ == "__main__":
    # Test rapide : dégrader une image existante
    import sys
    if len(sys.argv) > 1:
        img = cv2.imread(sys.argv[1])
        if img is not None:
            degrader = ImageDegrader()
            for lvl in ["light", "medium", "heavy"]:
                result = degrader.apply_random_degradation(img, level=lvl)
                out = sys.argv[1].rsplit(".", 1)[0] + f"_{lvl}.jpg"
                cv2.imwrite(out, result)
                print(f"  → {out}")
        else:
            print(f"Impossible de charger : {sys.argv[1]}")
    else:
        print("Usage : python degrade.py <image_path>")
