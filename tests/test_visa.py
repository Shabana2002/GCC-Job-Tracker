from src.matching.visa import detect_visa_status


def test_visa_confirmed():
    status, evidence = detect_visa_status("We provide full visa sponsorship for the right candidate.")
    assert status == "CONFIRMED"
    assert "visa" in evidence.lower()


def test_visa_possible():
    status, _ = detect_visa_status("Relocation support is available for overseas hires.")
    assert status == "POSSIBLE"


def test_visa_not_provided():
    status, _ = detect_visa_status("Candidate must have their own valid UAE residence visa.")
    assert status == "NOT_PROVIDED"


def test_visa_not_mentioned():
    status, evidence = detect_visa_status("We are looking for a passionate Python teacher.")
    assert status == "NOT_MENTIONED"
    assert evidence is None


def test_visa_unclear():
    status, _ = detect_visa_status("Visa matters will be discussed at interview stage.")
    assert status == "UNCLEAR"
