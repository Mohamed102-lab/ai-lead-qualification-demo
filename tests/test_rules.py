import json
from pathlib import Path

import pytest

from scoring_service.rules import load_rules, score_lead

RULES = load_rules()
LEADS = json.loads((Path(__file__).parent.parent / "sample-data" / "leads.json").read_text(encoding="utf-8"))


def lead(**overrides):
    base = {
        "booking_id": "demo-1",
        "credit_score": 700,
        "months_in_business": 24,
        "monthly_revenue": 40000,
        "requested_amount": 50000,
    }
    base.update(overrides)
    return base


def test_good_lead_is_approved():
    result = score_lead(lead(), RULES)
    assert result.decision == "approve"


def test_missing_field_is_unknown_not_guessed():
    result = score_lead(lead(monthly_revenue=None), RULES)
    assert result.decision == "needs_info"
    assert result.unknown == ["monthly_revenue"]


def test_unreadable_number_counts_as_unknown():
    result = score_lead(lead(credit_score="n/a"), RULES)
    assert result.decision == "needs_info"
    assert "credit_score" in result.unknown


def test_borderline_credit_is_fixable():
    result = score_lead(lead(credit_score=600), RULES)
    assert result.decision == "fix"


@pytest.mark.parametrize(
    "overrides",
    [
        {"credit_score": 500},
        {"months_in_business": 2},
        {"monthly_revenue": 5000},
        {"requested_amount": 200000},
    ],
)
def test_hard_rules_reject_with_a_reason(overrides):
    result = score_lead(lead(**overrides), RULES)
    assert result.decision == "reject"
    assert result.reasons


def test_every_sample_lead_matches_its_expected_decision():
    for item in LEADS:
        assert score_lead(item, RULES).decision == item["expected_decision"], item["booking_id"]
