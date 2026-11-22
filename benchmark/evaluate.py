"""Evaluate evidence checks, or run an opt-in end-to-end vision benchmark."""

import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path

from benchmark.generate import OUT
from letter_reader import LetterError, explain_letter, prepare_image
from trust import amount_matches, amounts, check_amount, check_deadline, dates, roundtrip_status

OUTPUT_LANGUAGES = {"en": "English", "es": "Spanish", "fr": "French", "de": "German",
                    "zh": "Chinese (Simplified)", "ja": "Japanese"}


def exact_amount(row):
    return {(row["currency"], Decimal(row["amount"]))} if row["amount"] is not None else set()


def rules_prediction(row):
    due_dates, ambiguous = dates(row["deadline_source"], context=row["text"])
    price = amounts(row["amount_source"])
    return (next(iter(due_dates)).isoformat() if len(due_dates) == 1 and not ambiguous else None,
            price, ambiguous)


def evaluate(rows, *, image_dir=None, endpoint="", model="", api_key=""):
    languages, failures = defaultdict(Counter), []
    for row in rows:
        scores = languages[row["language"]]
        scores["n"] += 1
        error = None
        if image_dir:
            try:
                response = explain_letter(language=OUTPUT_LANGUAGES[row["language"]], endpoint=endpoint,
                                          model=model, api_key=api_key,
                                          photo=prepare_image((image_dir / f"{row['id']}.jpg").read_bytes()))
                deadline = response.deadline.isoformat() if response.deadline else None
                amount = amounts(response.amount or "")
                ambiguous = response.deadline_check == "ambiguous"
                scores[f"roundtrip_{response.translation_check}"] += 1
            except (LetterError, OSError) as exc:
                scores["errors"] += 1
                error = type(exc).__name__
                deadline, amount, ambiguous = None, set(), False
        else:
            deadline, amount, ambiguous = rules_prediction(row)
            if row["deadline"]:
                gold = date.fromisoformat(row["deadline"])
                scores["wrong_date_probes"] += 1
                if check_deadline(row["text"], row["deadline_source"], gold + timedelta(days=1)) == "mismatch":
                    scores["wrong_date_rejected"] += 1
                # Deliberately present a genuine issue date and genuine proof for it.
                issue = date.fromisoformat(row["issue_date"])
                scores["issue_date_probes"] += 1
                if check_deadline(row["text"], row["text"].splitlines()[2], issue) == "mismatch":
                    scores["labelled_issue_dates_rejected"] += 1
                other = f"Internal note: {issue.isoformat()}."
                scores["unrelated_date_probes"] += 1
                if check_deadline(row["text"] + "\n" + other, other, issue) == "verified":
                    scores["unrelated_dates_wrongly_accepted"] += 1
            if row["amount"]:
                scores["amount_probes"] += 1
                wrong_amount = f"{row['currency']} {Decimal(row['amount']) + 1:.2f}"
                if check_amount(row["text"], row["amount_source"], wrong_amount) == "mismatch":
                    scores["wrong_amount_rejected"] += 1
        target_amount = exact_amount(row)
        amount_ok = not error and (amount_matches(target_amount, amount) if target_amount else not amount)
        deadline_ok = not error and row["deadline"] == deadline
        scores["deadline_correct"] += bool(deadline_ok)
        scores["amount_correct"] += bool(amount_ok)
        if row["scenario"] == "ambiguous_date":
            scores["ambiguous_n"] += 1
            scores["ambiguous_flagged"] += bool(ambiguous)
        if not deadline_ok or not amount_ok or (row["scenario"] == "ambiguous_date" and not ambiguous):
            failures.append({"id": row["id"], "scenario": row["scenario"], "deadline_expected": row["deadline"],
                             "deadline_predicted": deadline, "amount_correct": bool(amount_ok),
                             "ambiguous_flagged": ambiguous, "error": error})
    return {"mode": "vision" if image_dir else "source-text rules with gold evidence spans",
            "model": model if image_dir else None, "languages": dict(languages), "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=OUT)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--images", type=Path, help="Opt in to sending benchmark images to the configured vision provider.")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    rows = [row for row in rows if row["split"] == "benchmark"]
    endpoint, model = os.getenv("LETTER_API_URL", ""), os.getenv("LETTER_API_MODEL", "")
    if args.images and (not endpoint or not model):
        parser.error("Set LETTER_API_URL and LETTER_API_MODEL before running image evaluation.")
    report = evaluate(rows, image_dir=args.images, endpoint=endpoint, model=model,
                      api_key=os.getenv("LETTER_API_KEY", ""))
    if not args.images:
        anchor = "Pay EUR 48 by 2026-03-12. Do not send the form."
        report["roundtrip_logic_probes"] = {
            "identical": roundtrip_status(anchor, anchor),
            "date_shift": roundtrip_status(anchor, anchor.replace("03-12", "03-13")),
            "amount_shift": roundtrip_status(anchor, anchor.replace("48", "84")),
            "negation_loss": roundtrip_status(anchor, anchor.replace(" not", "")),
            "wrong_action_same_words": roundtrip_status(anchor, "Do not pay EUR 48 by 2026-03-12. Send the form."),
        }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
