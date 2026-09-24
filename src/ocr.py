from __future__ import annotations
from io import BytesIO
from typing import Tuple
import numpy as np
import cv2
from PIL import Image, ImageOps
import pytesseract
from pytesseract import Output

def load_image(data: bytes) -> Image.Image:
    img = Image.open(BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    # Guardrail for very large phone photos: enough detail for OCR without excessive latency.
    max_side = 2200
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img

def preprocess(img: Image.Image) -> np.ndarray:
    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    # Increase local contrast, useful for glare/shadows without an expensive multi-pass OCR.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray

def run_ocr(data: bytes) -> Tuple[str, float, list[dict], Image.Image]:
    img = load_image(data)
    processed = preprocess(img)
    result = pytesseract.image_to_data(
        processed,
        config="--oem 3 --psm 6",
        output_type=Output.DICT,
    )
    words = []
    boxes = []
    confs = []
    for i, raw in enumerate(result.get("text", [])):
        word = (raw or "").strip()
        try:
            conf = float(result["conf"][i])
        except Exception:
            conf = -1
        if word:
            words.append(word)
            boxes.append({
                "text": word,
                "conf": conf,
                "left": int(result["left"][i]),
                "top": int(result["top"][i]),
                "width": int(result["width"][i]),
                "height": int(result["height"][i]),
            })
            if conf >= 0:
                confs.append(conf)
    text = " ".join(words)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return text, avg_conf, boxes, img
