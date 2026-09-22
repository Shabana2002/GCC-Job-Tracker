from src.config.settings import DEFAULT_FX_TO_INR, DEFAULT_SALARY_THRESHOLDS
from src.matching.salary import classify_salary_status, parse_salary, to_inr_monthly


def test_parse_salary_range_with_currency():
    s_min, s_max, currency, period = parse_salary("Salary: AED 6,000 - 8,000 per month")
    assert s_min == 6000
    assert s_max == 8000
    assert currency == "AED"
    assert period == "MONTHLY"


def test_parse_salary_single_value():
    s_min, s_max, currency, period = parse_salary("QAR 5500 monthly")
    assert s_min == s_max == 5500
    assert currency == "QAR"


def test_parse_salary_with_trailing_commas_in_surrounding_text():
    # Regression: stray commas elsewhere in the text (list punctuation, not
    # thousands separators) must not be picked up as bogus "numbers".
    s_min, s_max, currency, period = parse_salary(
        "AED 7000 per month, visa sponsorship provided, overseas candidates welcome"
    )
    assert s_min == s_max == 7000
    assert currency == "AED"


def test_parse_salary_missing_returns_none():
    s_min, s_max, currency, period = parse_salary("")
    assert s_min is None and s_max is None and currency is None and period is None


def test_parse_salary_yearly():
    s_min, s_max, currency, period = parse_salary("SAR 90,000 per annum")
    assert period == "YEARLY"
    assert s_min == 90000


def test_classify_not_disclosed():
    status = classify_salary_status(None, None, None, None, "United Arab Emirates", DEFAULT_SALARY_THRESHOLDS)
    assert status == "NOT_DISCLOSED"


def test_classify_meets_target():
    status = classify_salary_status(6000, 6000, "AED", "MONTHLY", "United Arab Emirates", DEFAULT_SALARY_THRESHOLDS)
    assert status == "MEETS_TARGET"


def test_classify_below_target():
    status = classify_salary_status(3000, 3000, "AED", "MONTHLY", "United Arab Emirates", DEFAULT_SALARY_THRESHOLDS)
    assert status == "BELOW_TARGET"


def test_classify_partially_meets():
    status = classify_salary_status(4000, 6000, "AED", "MONTHLY", "United Arab Emirates", DEFAULT_SALARY_THRESHOLDS)
    assert status == "PARTIALLY_MEETS_TARGET"


def test_classify_unknown_currency_mismatch():
    status = classify_salary_status(6000, 6000, "USD", "MONTHLY", "United Arab Emirates", DEFAULT_SALARY_THRESHOLDS)
    assert status == "UNKNOWN"


def test_to_inr_monthly_conversion():
    inr = to_inr_monthly(5500, 5500, "AED", "MONTHLY", DEFAULT_FX_TO_INR)
    assert inr == 5500 * DEFAULT_FX_TO_INR["AED"]


def test_to_inr_monthly_yearly_period():
    inr = to_inr_monthly(120000, 120000, "SAR", "YEARLY", DEFAULT_FX_TO_INR)
    assert round(inr) == round((120000 / 12) * DEFAULT_FX_TO_INR["SAR"])
