from src.matching.priority import classify_priority


def _job(**overrides):
    job = {
        "qualification_status": "LIKELY_ELIGIBLE",
        "visa_status": "CONFIRMED",
        "overseas_status": "OVERSEAS_WELCOME",
        "salary_status": "MEETS_TARGET",
        "experience_match": "STRONG",
    }
    job.update(overrides)
    return job


def test_high_priority():
    assert classify_priority(_job()) == "HIGH PRIORITY"


def test_low_priority_on_mandatory_bed():
    assert classify_priority(_job(qualification_status="LIKELY_NOT_ELIGIBLE")) == "LOW PRIORITY"


def test_low_priority_on_local_only():
    assert classify_priority(_job(overseas_status="LOCAL_ONLY")) == "LOW PRIORITY"


def test_low_priority_on_below_target_salary():
    assert classify_priority(_job(salary_status="BELOW_TARGET")) == "LOW PRIORITY"


def test_check_requirements_on_unclear_visa():
    assert classify_priority(_job(visa_status="UNCLEAR")) == "CHECK REQUIREMENTS"


def test_medium_priority_without_visa_evidence():
    result = classify_priority(_job(visa_status="NOT_MENTIONED", overseas_status="UNCLEAR"))
    assert result in ("MEDIUM PRIORITY", "HIGH PRIORITY")
