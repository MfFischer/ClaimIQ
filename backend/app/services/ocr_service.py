"""
ClaimIQ — OCR Service
Primary: Tesseract (free, local, German + English).
Fallback: Google Vision when confidence < threshold.
Handles German Umlaute (ä ö ü ß) and scanned document quirks.
"""
import io
import logging
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

# Prefer German+English; fall back to English-only if deu pack not installed
def _resolve_lang() -> str:
    try:
        available = pytesseract.get_languages()
        if "deu" in available:
            return "deu+eng"
    except Exception:
        pass
    logger.warning("Tesseract 'deu' language pack not found — using 'eng' only. "
                   "Install it for better German OCR accuracy.")
    return "eng"

TESSERACT_LANG = _resolve_lang()


def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Pre-process scanned insurance documents for better OCR.
    German Kfz forms are often faxed/scanned — low contrast, skewed.
    """
    img = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold — better than global for uneven lighting
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Deskew if rotation detected
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) > 0.5:
            h, w = thresh.shape
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            thresh = cv2.warpAffine(
                thresh, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )

    return thresh


class OcrResult:
    def __init__(self, text: str, confidence: float, engine: str):
        self.text = text
        self.confidence = confidence
        self.engine = engine


def _run_tesseract_sync(image: Image.Image) -> tuple[str, float]:
    """Blocking Tesseract call — must run in a thread pool, not the async event loop."""
    processed = preprocess_image(image)
    pil = Image.fromarray(processed)

    data = pytesseract.image_to_data(
        pil,
        lang=TESSERACT_LANG,
        output_type=pytesseract.Output.DICT,
        config="--psm 3 --oem 3",
    )
    confs = [int(c) for c in data["conf"] if int(c) != -1]
    avg_conf = (sum(confs) / len(confs) / 100) if confs else 0.0

    text = pytesseract.image_to_string(
        pil, lang=TESSERACT_LANG, config="--psm 3 --oem 3"
    )
    return text.strip(), avg_conf


async def run_tesseract(image: Image.Image) -> OcrResult:
    """Run Tesseract in a thread pool — pytesseract spawns a subprocess and must
    not be called directly in the async event loop on Windows."""
    import asyncio
    try:
        text, avg_conf = await asyncio.to_thread(_run_tesseract_sync, image)
        return OcrResult(text=text, confidence=avg_conf, engine="tesseract")
    except Exception as e:
        logger.error(f"Tesseract error: {e}", exc_info=True)
        return OcrResult(text="", confidence=0.0, engine="tesseract")


async def run_google_vision(image_bytes: bytes) -> OcrResult:
    """Google Cloud Vision fallback."""
    try:
        from google.cloud import vision

        if settings.google_vision_api_key:
            client = vision.ImageAnnotatorClient(
                client_options={"api_key": settings.google_vision_api_key}
            )
        else:
            client = vision.ImageAnnotatorClient()

        image = vision.Image(content=image_bytes)
        response = client.document_text_detection(
            image=image,
            image_context=vision.ImageContext(language_hints=["de", "en"]),
        )
        if response.error.message:
            raise Exception(response.error.message)

        text = response.full_text_annotation.text
        return OcrResult(text=text.strip(), confidence=0.95, engine="google_vision")

    except Exception as e:
        logger.error(f"Google Vision error: {e}")
        return OcrResult(text="", confidence=0.0, engine="google_vision_error")


def load_images_from_bytes(file_bytes: bytes, content_type: str) -> list[Image.Image]:
    """Convert uploaded file to list of PIL Images. Handles PDF (multi-page) and images."""
    ct = (content_type or "").lower()
    if "pdf" in ct or file_bytes[:4] == b"%PDF":
        try:
            import fitz  # PyMuPDF
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            images = []
            for page in pdf:
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom → better OCR quality
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            return images
        except ImportError:
            logger.warning("PyMuPDF not installed. pip install pymupdf")
            return []
        except Exception as e:
            logger.error(f"PDF load error: {e}")
            return []
    else:
        try:
            return [Image.open(io.BytesIO(file_bytes))]
        except Exception as e:
            logger.error(f"Image load error: {e}")
            return []


async def extract_text(file_bytes: bytes, content_type: str) -> OcrResult:
    """
    Main OCR entry point.
    1. Load image(s)
    2. Tesseract on each page
    3. Fallback to Google Vision if confidence too low
    """
    images = load_images_from_bytes(file_bytes, content_type)
    if not images:
        return OcrResult(text="", confidence=0.0, engine="none")

    all_texts: list[str] = []
    min_confidence = 1.0

    for img in images:
        result = await run_tesseract(img)
        if result.text:
            all_texts.append(result.text)
        min_confidence = min(min_confidence, result.confidence)

    combined = "\n\n--- Seite / Page ---\n\n".join(all_texts)
    primary = OcrResult(text=combined, confidence=min_confidence, engine="tesseract")

    # Fallback to Google Vision if confidence too low and key is set
    if (
        primary.confidence < settings.ocr_confidence_threshold
        and settings.google_vision_api_key
    ):
        logger.info(
            f"Tesseract confidence {min_confidence:.2f} < threshold "
            f"{settings.ocr_confidence_threshold} — using Google Vision"
        )
        return await run_google_vision(file_bytes)

    return primary
