from src.config.settings import DEFAULT_CANDIDATE_PROFILE
from src.matching.qualification import detect_qualification_status


def test_bed_required_marks_not_eligible():
    status, evidence = detect_qualification_status(
        "We are hiring a Computer Science Teacher.",
        "B.Ed is required for this role.",
        DEFAULT_CANDIDATE_PROFILE,
    )
    assert status == "LIKELY_NOT_ELIGIBLE"
    assert "b.ed" in evidence.lower() or "bed" in evidence.lower()


def test_pgce_required_marks_not_eligible():
    status, _ = detect_qualification_status(
        "", "PGCE required.", DEFAULT_CANDIDATE_PROFILE,
    )
    assert status == "LIKELY_NOT_ELIGIBLE"


def test_teaching_license_mandatory_marks_not_eligible():
    status, _ = detect_qualification_status(
        "", "Teaching license mandatory.", DEFAULT_CANDIDATE_PROFILE,
    )
    assert status == "LIKELY_NOT_ELIGIBLE"


def test_bed_preferred_does_not_reject():
    status, _ = detect_qualification_status(
        "", "B.Ed preferred but not essential.", DEFAULT_CANDIDATE_PROFILE,
    )
    assert status != "LIKELY_NOT_ELIGIBLE"


def test_computer_science_degree_marks_eligible():
    status, evidence = detect_qualification_status(
        "Bachelor's degree in Computer Science, IT, or related field required.",
        "", DEFAULT_CANDIDATE_PROFILE,
    )
    assert status == "LIKELY_ELIGIBLE"


def test_no_qualification_info_requires_check():
    status, _ = detect_qualification_status("Great team, great pay.", "", DEFAULT_CANDIDATE_PROFILE)
    assert status == "REQUIRES_CHECK"
