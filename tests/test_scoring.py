from src.config.settings import DEFAULT_CANDIDATE_PROFILE, DEFAULT_JOB_TITLES, DEFAULT_SCORING_WEIGHTS
from src.matching.scoring import compute_profile_match


def _base_job(**overrides):
    job = {
        "title": "AI Trainer",
        "description": "AI Trainer needed with Python and Machine Learning skills.",
        "requirements": "",
        "qualification_status": "LIKELY_ELIGIBLE",
        "salary_status": "MEETS_TARGET",
        "visa_status": "CONFIRMED",
        "overseas_status": "OVERSEAS_WELCOME",
        "experience_match": "STRONG",
        "job_freshness": "TODAY",
    }
    job.update(overrides)
    return job


def test_strong_match_scores_high():
    score, reasons = compute_profile_match(_base_job(), DEFAULT_CANDIDATE_PROFILE, DEFAULT_SCORING_WEIGHTS, DEFAULT_JOB_TITLES)
    assert score > 50
    assert len(reasons) > 0


def test_bed_required_reduces_score():
    good_score, _ = compute_profile_match(_base_job(), DEFAULT_CANDIDATE_PROFILE, DEFAULT_SCORING_WEIGHTS, DEFAULT_JOB_TITLES)
    bad_score, reasons = compute_profile_match(
        _base_job(qualification_status="LIKELY_NOT_ELIGIBLE"),
        DEFAULT_CANDIDATE_PROFILE, DEFAULT_SCORING_WEIGHTS, DEFAULT_JOB_TITLES,
    )
    assert bad_score < good_score
    assert any("teaching qualification" in r for r in reasons)


def test_local_only_penalizes_score():
    score, reasons = compute_profile_match(
        _base_job(overseas_status="LOCAL_ONLY"),
        DEFAULT_CANDIDATE_PROFILE, DEFAULT_SCORING_WEIGHTS, DEFAULT_JOB_TITLES,
    )
    assert any("local" in r.lower() for r in reasons)
