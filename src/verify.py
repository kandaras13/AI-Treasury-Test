from __future__ import annotations
import re
import time
from rapidfuzz.fuzz import ratio, partial_ratio
from .models import ApplicationData, FieldResult, VerificationResult
from .normalize import (
    compact_text, strict_warning_text, parse_abv, parse_proof, normalize_net_contents
)
from .ocr import run_ocr

TTB_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not "
    "drink alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)

# OCR-normalized version: intended to tolerate line breaks/case noise while requiring every prescribed word.
TTB_WARNING_LOOSE = compact_text(TTB_WARNING)

def _field(field, expected, observed, status, detail, confidence=0.0):
    return FieldResult(field, str(expected or ""), str(observed or ""), status, detail, confidence)

def fuzzy_required(field: str, expected: str, observed_text: str, pass_at=94, review_at=82) -> FieldResult:
    if not expected:
        return _field(field, "", "", "N/A", "No expected value supplied.")
    expected_n = compact_text(expected)
    observed_n = compact_text(observed_text)
    score = max(ratio(expected_n, observed_n), partial_ratio(expected_n, observed_n))
    if score >= pass_at:
        status, detail = "PASS", f"Matched with {score:.0f}% normalized similarity."
    elif score >= review_at:
        status, detail = "REVIEW", f"Likely match ({score:.0f}%); human confirmation recommended."
    else:
        status, detail = "FAIL", f"Expected value not confidently found ({score:.0f}% similarity)."
    return _field(field, expected, expected if status == "PASS" else "See OCR text", status, detail, score)

def check_abv(expected: float | None, text: str) -> FieldResult:
    if expected is None:
        return _field("ABV", "", "", "N/A", "No expected ABV supplied.")
    observed = parse_abv(text)
    proof = parse_proof(text)
    if observed is None:
        return _field("ABV", f"{expected:g}%", "", "FAIL", "No alcohol percentage detected.", 0)
    delta = abs(observed - float(expected))
    if delta <= 0.05:
        status = "PASS"
        detail = "Alcohol percentage matches the application."
        if proof is not None and abs(proof - (observed * 2)) > 0.2:
            status = "REVIEW"
            detail += f" Proof ({proof:g}) is inconsistent with 2× ABV."
        return _field("ABV", f"{expected:g}%", f"{observed:g}%", status, detail, 100)
    return _field("ABV", f"{expected:g}%", f"{observed:g}%", "FAIL", f"ABV differs by {delta:g} percentage points.", 0)

def check_net_contents(expected: str, text: str) -> FieldResult:
    if not expected:
        return _field("Net contents", "", "", "N/A", "No expected net contents supplied.")
    expected_n = normalize_net_contents(expected)
    observed_n = normalize_net_contents(text)
    # If a full OCR blob was passed, search for likely package sizes.
    if expected_n and expected_n in observed_n:
        return _field("Net contents", expected, expected, "PASS", "Net contents match.", 100)
    # fallback loose substring
    score = partial_ratio(compact_text(expected), compact_text(text))
    status = "PASS" if score >= 95 else ("REVIEW" if score >= 82 else "FAIL")
    return _field("Net contents", expected, "See OCR text", status, f"{score:.0f}% similarity.", score)

def check_warning(text: str) -> FieldResult:
    loose_text = compact_text(text)
    similarity = partial_ratio(TTB_WARNING_LOOSE, loose_text)
    header_upper = "GOVERNMENT WARNING" in text.upper()
    exact_header = bool(re.search(r"\bGOVERNMENT\s+WARNING\s*:", text))
    if similarity >= 96 and header_upper and exact_header:
        return _field(
            "Government warning",
            TTB_WARNING,
            "Detected",
            "PASS",
            "Prescribed warning wording and uppercase header detected. Bold weight should still be visually confirmed.",
            similarity,
        )
    if similarity >= 86:
        return _field(
            "Government warning",
            TTB_WARNING,
            "Possible warning detected",
            "REVIEW",
            f"Warning is close ({similarity:.0f}%) but OCR cannot confirm exact text/formatting. Review punctuation, capitalization, and bold header.",
            similarity,
        )
    return _field(
        "Government warning",
        TTB_WARNING,
        "Not confidently detected",
        "FAIL",
        f"Prescribed warning not confidently found ({similarity:.0f}% similarity).",
        similarity,
    )

def verify_bytes(filename: str, data: bytes, app: ApplicationData) -> VerificationResult:
    start = time.perf_counter()
    text, ocr_conf, boxes, _ = run_ocr(data)
    fields = [
        fuzzy_required("Brand name", app.brand_name, text, pass_at=94, review_at=82),
        fuzzy_required("Class / type", app.class_type, text, pass_at=91, review_at=80),
        check_abv(app.abv, text),
        check_net_contents(app.net_contents, text),
        fuzzy_required("Producer / bottler", app.producer, text, pass_at=90, review_at=78),
        fuzzy_required("Country of origin", app.country_of_origin, text, pass_at=92, review_at=80),
        check_warning(text),
    ]
    relevant = [f for f in fields if f.status != "N/A"]
    points = {"PASS": 100, "REVIEW": 60, "FAIL": 0}
    score = sum(points[f.status] for f in relevant) / max(len(relevant), 1)
    if any(f.status == "FAIL" for f in relevant):
        overall = "FAIL"
    elif any(f.status == "REVIEW" for f in relevant):
        overall = "REVIEW"
    else:
        overall = "PASS"
    elapsed = time.perf_counter() - start
    return VerificationResult(filename, overall, score, elapsed, ocr_conf, fields, text)
