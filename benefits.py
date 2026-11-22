"""Country-scoped eligibility rules with a trace of each checked pathway."""

from dataclasses import dataclass
import json
from pathlib import Path

COUNTRIES = ("England (United Kingdom)", "France", "Germany", "Spain", "Japan", "Other")
RULES = json.loads(Path(__file__).with_name("benefit_rules.json").read_text())


@dataclass(frozen=True)
class Scheme:
    name: str
    likely: bool
    explanation: str
    documents: tuple[str, ...]
    office: str
    url: str


def check(country: str, age: int, studying: bool) -> list[Scheme]:
    schemes = []
    for scheme in RULES.get(country, []):
        pathways = scheme["pathways"]
        match = next((row for row in pathways if row["min"] <= age <= row["max"]
                      and (not row.get("education") or studying)), None)
        text = f"Matched: {match['description']}." if match else "No age or education pathway matched your answers."
        schemes.append(Scheme(scheme["name"], bool(match), text, tuple(scheme["documents"]), scheme["office"], scheme["url"]))
    return sorted(schemes, key=lambda scheme: not scheme.likely)
