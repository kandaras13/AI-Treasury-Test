from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class ApplicationData:
    brand_name: str
    class_type: str = ""
    abv: Optional[float] = None
    net_contents: str = ""
    producer: str = ""
    country_of_origin: str = ""

@dataclass
class FieldResult:
    field: str
    expected: str
    observed: str
    status: str
    detail: str
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class VerificationResult:
    filename: str
    overall_status: str
    score: float
    processing_seconds: float
    ocr_confidence: float
    fields: list[FieldResult]
    extracted_text: str

    def to_row(self) -> Dict[str, Any]:
        row = {
            "filename": self.filename,
            "overall_status": self.overall_status,
            "score": round(self.score, 1),
            "processing_seconds": round(self.processing_seconds, 2),
            "ocr_confidence": round(self.ocr_confidence, 1),
        }
        for f in self.fields:
            row[f"{f.field}_status"] = f.status
            row[f"{f.field}_observed"] = f.observed
        return row
