"""
Salary parsing, INR conversion, and target-salary classification.

Classification against the target is done in the LOCAL currency (using the
per-country thresholds in settings) to avoid compounding FX-conversion error.
The INR figure shown to the user is a separate, clearly-labelled estimate
using configurable approximate FX rates -- it is informational only and never
drives accept/reject decisions.
"""
from __future__ import annotations

import re
from typing import Optional

CURRENCY_ALIASES = {
    "AED": "AED", "DHS": "AED", "DIRHAM": "AED", "DIRHAMS": "AED",
    "QAR": "QAR", "RIYAL": None,  # ambiguous (QAR or SAR) -- resolved by context below
    "OMR": "OMR", "RIAL": None,
    "KWD": "KWD", "DINAR": None,
    "BHD": "BHD",
    "SAR": "SAR", "SR": "SAR",
    "USD": "USD", "$": "USD",
    "INR": "INR", "RS": "INR", "RS.": "INR", "₹": "INR",
}

_NUMBER = r"\d[\d,]*(?:\.\d+)?"

PERIOD_KEYWORDS = {
    "year": "YEARLY", "annum": "YEARLY", "annual": "YEARLY", "yearly": "YEARLY",
    "month": "MONTHLY", "monthly": "MONTHLY", "pm": "MONTHLY",
    "week": "WEEKLY", "weekly": "WEEKLY",
    "day": "DAILY", "daily": "DAILY",
    "hour": "HOURLY", "hourly": "HOURLY",
}


def _find_currency(text: str, country_hint: Optional[str] = None) -> Optional[str]:
    upper = text.upper()
    country_currency = {
        "United Arab Emirates": "AED", "Qatar": "QAR", "Oman": "OMR",
        "Kuwait": "KWD", "Bahrain": "BHD", "Saudi Arabia": "SAR",
    }
    for token, code in CURRENCY_ALIASES.items():
        if code and re.search(rf"\b{re.escape(token)}\b", upper):
            return code
    if "RIYAL" in upper or "RIAL" in upper or "DINAR" in upper:
        # Ambiguous local word -- fall back to the country's own currency.
        return country_currency.get(country_hint)
    return country_currency.get(country_hint)


def _find_period(text: str) -> str:
    lower = text.lower()
    for kw, period in PERIOD_KEYWORDS.items():
        if re.search(rf"\b{kw}\b", lower):
            return period
    return "MONTHLY"  # most GCC job ads quote monthly figures by convention


def parse_salary(text: str, country_hint: Optional[str] = None):
    """
    Best-effort extraction from free text. Returns
    (salary_min, salary_max, currency, period) with None for anything that
    cannot be reliably determined. Never invents a number that isn't present.
    """
    if not text or not text.strip():
        return None, None, None, None

    numbers = [float(n.replace(",", "")) for n in re.findall(_NUMBER, text)]
    numbers = [n for n in numbers if n > 0]
    if not numbers:
        return None, None, None, None

    currency = _find_currency(text, country_hint)
    period = _find_period(text)

    if len(numbers) >= 2:
        return min(numbers[:2]), max(numbers[:2]), currency, period
    return numbers[0], numbers[0], currency, period


def to_inr_monthly(salary_min, salary_max, currency, period, fx_to_inr: dict) -> Optional[float]:
    if salary_min is None and salary_max is None:
        return None
    value = salary_max if salary_max is not None else salary_min
    if value is None:
        return None
    rate = fx_to_inr.get((currency or "").upper())
    if rate is None:
        return None

    period_to_monthly = {
        "YEARLY": lambda v: v / 12,
        "MONTHLY": lambda v: v,
        "WEEKLY": lambda v: v * 4.33,
        "DAILY": lambda v: v * 26,
        "HOURLY": lambda v: v * 26 * 8,
    }
    monthly_local = period_to_monthly.get(period or "MONTHLY", lambda v: v)(value)
    return round(monthly_local * rate, 2)


def classify_salary_status(salary_min, salary_max, currency, period, country: Optional[str],
                            salary_thresholds: dict) -> str:
    """
    Returns one of MEETS_TARGET / PARTIALLY_MEETS_TARGET / BELOW_TARGET /
    NOT_DISCLOSED / UNKNOWN.
    A missing salary is NEVER treated as a rejection -- see NOT_DISCLOSED.
    """
    if salary_min is None and salary_max is None:
        return "NOT_DISCLOSED"

    threshold_info = salary_thresholds.get(country) if country else None
    if not threshold_info or not currency or currency != threshold_info.get("currency"):
        # We have a number but can't reliably compare it to a threshold in
        # the same currency/country -- don't guess.
        return "UNKNOWN"

    threshold = threshold_info["min_monthly"]
    period = period or "MONTHLY"
    monthly_min = salary_min
    monthly_max = salary_max if salary_max is not None else salary_min
    if period == "YEARLY":
        monthly_min, monthly_max = monthly_min / 12, monthly_max / 12
    elif period == "WEEKLY":
        monthly_min, monthly_max = monthly_min * 4.33, monthly_max * 4.33
    elif period == "DAILY":
        monthly_min, monthly_max = monthly_min * 26, monthly_max * 26
    elif period == "HOURLY":
        monthly_min, monthly_max = monthly_min * 26 * 8, monthly_max * 26 * 8

    if monthly_min >= threshold:
        return "MEETS_TARGET"
    if monthly_max >= threshold:
        return "PARTIALLY_MEETS_TARGET"
    return "BELOW_TARGET"
