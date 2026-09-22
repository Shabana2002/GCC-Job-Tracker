from src.config.settings import DEFAULT_CANDIDATE_PROFILE
from src.matching.experience import detect_experience_match


def test_ai_trainer_role_with_skills_is_strong():
    description = "Hiring an AI Trainer to teach Python, Machine Learning and Computer Vision."
    status, _ = detect_experience_match(description, "", DEFAULT_CANDIDATE_PROFILE)
    assert status in ("STRONG", "GOOD")


def test_mandatory_multi_year_school_teaching_is_weak():
    description = "ICT Teacher role."
    requirements = "Minimum 3 years of school teaching experience required, with lesson planning and curriculum delivery."
    status, _ = detect_experience_match(description, requirements, DEFAULT_CANDIDATE_PROFILE)
    assert status == "WEAK"


def test_preferred_teaching_experience_not_automatically_weak():
    description = "Python Instructor role."
    requirements = "School teaching experience preferred but not required. Python and AI skills valued."
    status, _ = detect_experience_match(description, requirements, DEFAULT_CANDIDATE_PROFILE)
    assert status != "WEAK"


def test_no_information_is_unknown():
    status, _ = detect_experience_match("", "", DEFAULT_CANDIDATE_PROFILE)
    assert status == "UNKNOWN"
