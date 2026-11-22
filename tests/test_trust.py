from datetime import date
from decimal import Decimal
import unittest

from benchmark.generate import fixtures
from benchmark.evaluate import evaluate
from trust import amounts, check_amount, check_deadline, dates, redact, roundtrip_status


class TrustTests(unittest.TestCase):
    def test_date_formats_and_ambiguity(self):
        for text in ("２０２６年３月１２日", "12.03.2026", "12 mars 2026", "12 de marzo de 2026", "2026-03-12"):
            self.assertEqual(dates(text), ({date(2026, 3, 12)}, False), text)
        self.assertEqual(dates("03/04/2026"), (set(), True))
        self.assertEqual(dates("03/04/2026", context="Format DD/MM/YYYY"), ({date(2026, 4, 3)}, False))
        self.assertEqual(dates("03/04/2026", context="Format MM/DD/YYYY"), ({date(2026, 3, 4)}, False))
        self.assertEqual(dates("Pay EUR 48 by 2026-03-12"), ({date(2026, 3, 12)}, False))
        self.assertEqual(dates("२०२६-०३-१२"), (set(), False))

    def test_money_notation_and_currency(self):
        for value in ("1.234,56 €", "EUR 1,234.56", "€1\u202f234,56"):
            self.assertEqual(amounts(value), {("EUR", Decimal("1234.56"))})
        self.assertEqual(amounts("１，２００円"), {("JPY", Decimal(1200))})
        self.assertEqual(amounts("20,50 zł"), {("PLN", Decimal("20.50"))})
        self.assertEqual(amounts("₩12,000"), {("KRW", Decimal(12000))})
        self.assertEqual(check_amount("Due: €48.", "Due: €48.", "£48"), "mismatch")

    def test_quote_selection_and_ambiguous_deadlines(self):
        self.assertEqual(check_deadline("Issued: 2026-03-12.", "Issued: 2026-03-12.", date(2026, 3, 12)), "mismatch")
        self.assertEqual(check_deadline("Due: 03/04/2026.", "Due: 03/04/2026.", None), "ambiguous")
        self.assertEqual(check_deadline("Due: 2026-03-12.", "Due: 2026-03-14.", date(2026, 3, 14)), "mismatch")

    def test_sensitive_text_preserves_only_last_four_alphanumeric_characters(self):
        pairs = [
            ("mail: person@example.com", "ecom"), ("IBAN: GB29 NWBK 6016 1331 9268 19", "6819"),
            ("phone: +44 7700 900123", "0123"), ("card: 4111-1111-1111-1111", "1111"),
            ("passport no. : X12345678", "5678"), ("NI: QQ 12 34 56 B", "456B"),
            ("number: 123456789", "6789"), ("number: １２３４５６７８９", "6789"),
        ]
        for raw, suffix in pairs:
            with self.subTest(raw=raw):
                masked = redact(raw)
                self.assertNotEqual(masked, raw)
                self.assertIn("•", masked)
                self.assertTrue("".join(char for char in masked if char.isalnum()).endswith(suffix))
        self.assertEqual(redact("e\u0301 Due 2026-03-12, total £48.50."), "e\u0301 Due 2026-03-12, total £48.50.")

    def test_roundtrip_raises_when_date_or_negation_changes(self):
        first = "Do not pay EUR 48 by 2026-03-12."
        self.assertEqual(roundtrip_status(first, first), "passed")
        self.assertEqual(roundtrip_status(first, first.replace("03-12", "03-14")), "review")
        self.assertEqual(roundtrip_status(first, first.replace(" not", "")), "review")

    def test_deterministic_fixture_sizes_and_measured_languages(self):
        rows = list(fixtures())
        self.assertEqual(len(rows), 180)
        self.assertEqual(len({row["id"] for row in rows}), 180)
        report = evaluate([row for row in rows if row["split"] == "benchmark"])
        self.assertEqual(set(report["languages"]), {"en", "es", "fr", "de", "zh", "ja"})
        self.assertEqual(sum(language["n"] for language in report["languages"].values()), 144)


if __name__ == "__main__":
    unittest.main()
