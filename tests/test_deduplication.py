from src.jobs.deduplicator import compute_duplicate_hash


def test_same_job_different_case_and_spacing_same_hash():
    h1 = compute_duplicate_hash("Careem", "AI Trainer", "Dubai, United Arab Emirates")
    h2 = compute_duplicate_hash("careem", "  ai   trainer ", "dubai, united arab emirates")
    assert h1 == h2


def test_different_company_different_hash():
    h1 = compute_duplicate_hash("Careem", "AI Trainer", "Dubai")
    h2 = compute_duplicate_hash("Tamara", "AI Trainer", "Dubai")
    assert h1 != h2


def test_different_title_different_hash():
    h1 = compute_duplicate_hash("Careem", "AI Trainer", "Dubai")
    h2 = compute_duplicate_hash("Careem", "Data Scientist", "Dubai")
    assert h1 != h2
