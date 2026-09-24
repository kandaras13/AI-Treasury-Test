import re
import unicodedata
from typing import Optional

PUNCT_RE = re.compile(r"[^A-Z0-9]+")

def ascii_upper(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    return value.encode("ascii", "ignore").decode("ascii").upper()

def loose_text(value: str) -> str:
    """Case/punctuation-insensitive text used for human-equivalent matching."""
    return PUNCT_RE.sub(" ", ascii_upper(value)).strip()

def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", loose_text(value)).strip()

def strict_warning_text(value: str) -> str:
    """Normalize whitespace only; preserve words/punctuation/case for exact warning checks."""
    value = (value or "").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", value).strip()

def parse_abv(text: str) -> Optional[float]:
    candidates = [
        r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:ALC(?:OHOL)?\.?\s*/?\s*VOL\.?|ABV)",
        r"(?:ALC(?:OHOL)?\.?\s*)?(\d{1,2}(?:\.\d+)?)\s*%\s*(?:BY\s*VOL(?:UME)?\.?)?",
    ]
    upper = ascii_upper(text)
    for pattern in candidates:
        m = re.search(pattern, upper)
        if m:
            try:
                value = float(m.group(1))
                if 0 <= value <= 100:
                    return value
            except ValueError:
                pass
    return None

def parse_proof(text: str) -> Optional[float]:
    m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*PROOF", ascii_upper(text))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

def normalize_net_contents(value: str) -> str:
    upper = ascii_upper(value)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(ML|MILLILITERS?|L|LITERS?|FL\.?\s*OZ\.?|FLUID\s*OUNCES?)", upper)
    if not m:
        return compact_text(value)
    amount = float(m.group(1))
    unit = m.group(2).replace(".", "").replace(" ", "")
    if unit in {"ML", "MILLILITER", "MILLILITERS"}:
        ml = amount
    elif unit in {"L", "LITER", "LITERS"}:
        ml = amount * 1000
    elif unit in {"FLOZ", "FLUIDOUNCE", "FLUIDOUNCES"}:
        ml = amount * 29.5735
    else:
        return compact_text(value)
    return f"{round(ml, 1)} ML"
