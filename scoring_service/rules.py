"""Lead qualification rules.

Pure functions, no I/O, so the logic is easy to test and to change.
The thresholds live in rules.json so a non-developer can edit them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

RULES_PATH = Path(__file__).with_name("rules.json")

# Fields we need before we can make any decision.
REQUIRED_FIELDS = ("credit_score", "months_in_business", "monthly_revenue", "requested_amount")


@dataclass
class Decision:
    decision: str  # "approve", "fix", "reject" or "needs_info"
    reasons: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"decision": self.decision, "reasons": self.reasons, "unknown": self.unknown}


def load_rules(path: Path = RULES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _number(value):
    """Return a float, or None when the value is missing or not a number."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_lead(lead: dict, rules: dict) -> Decision:
    """Decide what to do with a lead and explain why.

    Missing or unreadable fields are reported as unknown and never guessed.
    """
    values = {name: _number(lead.get(name)) for name in REQUIRED_FIELDS}
    unknown = [name for name, value in values.items() if value is None]
    if unknown:
        return Decision(
            decision="needs_info",
            reasons=["Missing information, so no decision was made."],
            unknown=unknown,
        )

    credit = values["credit_score"]
    months = values["months_in_business"]
    revenue = values["monthly_revenue"]
    amount = values["requested_amount"]

    reasons: list[str] = []
    hard_fail = False

    if credit < rules["fixable_credit_score"]:
        reasons.append(f"Credit score {credit:.0f} is below {rules['fixable_credit_score']}.")
        hard_fail = True
    if months < rules["min_months_in_business"]:
        reasons.append(f"{months:.0f} months in business, minimum is {rules['min_months_in_business']}.")
        hard_fail = True
    if revenue < rules["min_monthly_revenue"]:
        reasons.append(f"Monthly revenue {revenue:,.0f} is below {rules['min_monthly_revenue']:,}.")
        hard_fail = True
    ratio = amount / revenue if revenue else float("inf")
    if ratio > rules["max_amount_to_monthly_revenue"]:
        reasons.append(
            f"Requested amount is {ratio:.1f}x monthly revenue, maximum is {rules['max_amount_to_monthly_revenue']}x."
        )
        hard_fail = True

    if hard_fail:
        return Decision(decision="reject", reasons=reasons)

    if credit < rules["min_credit_score"]:
        return Decision(
            decision="fix",
            reasons=[
                f"Credit score {credit:.0f} is between {rules['fixable_credit_score']} and {rules['min_credit_score']}: "
                "qualifies after credit improvement."
            ],
        )

    return Decision(decision="approve", reasons=["Meets every qualification rule."])
