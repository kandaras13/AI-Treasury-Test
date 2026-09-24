from src.normalize import compact_text, parse_abv, parse_proof, normalize_net_contents
from src.verify import TTB_WARNING, check_warning, check_abv

def test_loose_brand_normalization():
    assert compact_text("STONE'S THROW") == compact_text("Stone's Throw")

def test_abv_parsing():
    assert parse_abv("45% Alc./Vol. (90 Proof)") == 45.0
    assert parse_proof("45% Alc./Vol. (90 Proof)") == 90.0

def test_net_contents_normalization():
    assert normalize_net_contents("0.75 L") == "750.0 ML"
    assert normalize_net_contents("750 mL") == "750.0 ML"

def test_exact_warning_passes():
    r = check_warning(TTB_WARNING)
    assert r.status == "PASS"

def test_changed_warning_needs_review_or_fails():
    bad = TTB_WARNING.replace("birth defects", "pregnancy complications")
    assert check_warning(bad).status != "PASS"

def test_abv_match():
    assert check_abv(45, "45% Alc./Vol. (90 Proof)").status == "PASS"
