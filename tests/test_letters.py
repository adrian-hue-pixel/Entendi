import json
from datetime import date
import unittest
from unittest.mock import MagicMock, patch

from letter_data import add_entry, deadline_groups, make_calendar, new_data, read_data
from letter_reader import LANGUAGES, SAMPLES, LetterError, explain_letter, prepare_image, sample_letter
from benefits import check

TODAY = date(2026, 11, 22)


class LetterTests(unittest.TestCase):
    def test_samples_render_and_verify_in_all_supported_languages(self):
        for sample in SAMPLES:
            for language in LANGUAGES:
                with self.subTest(sample=sample, language=language):
                    notice, photo = sample_letter(sample, language, today=TODAY)
                    simple, _ = sample_letter(sample, language, today=TODAY, simpler=True)
                    self.assertTrue(prepare_image(photo))
                    self.assertEqual(notice.language, language)
                    self.assertNotEqual(simple.explanation, notice.explanation)
                    self.assertTrue(all(quote.verified for quote in notice.quotes))
                    self.assertEqual(notice.needs_human_check, sample == "school")
                    self.assertEqual(notice.deadline is None, sample == "school")

    def test_bad_photo_and_unconfigured_provider_have_friendly_errors(self):
        with self.assertRaisesRegex(LetterError, "could not be opened"):
            prepare_image(b"invalid")
        with self.assertRaisesRegex(LetterError, "isn’t set up"):
            explain_letter(language="English", endpoint="", model="", api_key="", photo=b"demo")

    def test_provider_request_and_unverified_quote(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"choices": [{"message": {"content":
            json.dumps({"issuer": "Local office", "document_type": "Reminder", "language": "English",
                        "explanation": "The form needs an update.", "deadline": "2026-12-04",
                        "deadline_quote": "Submit by 4 December.", "quotes": [{"text": "invented quote"}],
                        "transcription": "The office requests that you update your form.",
                        "readable_letter": True})}}]}).encode()
        with patch("letter_reader.build_opener") as opener:
            opener.return_value.open.return_value = response
            notice = explain_letter(language="English", endpoint="https://api.example.test/v1/chat/completions",
                                    model="test-vision", api_key="demo", photo=b"photo")
            sent = json.loads(opener.return_value.open.call_args.args[0].data)
        self.assertTrue(sent["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertIsNone(notice.deadline)
        self.assertFalse(notice.quotes[0].verified)
        self.assertTrue(notice.needs_human_check)

    def test_saved_letter_survives_export_without_source_text(self):
        notice, _ = sample_letter("water", "English", today=TODAY)
        saved = new_data()
        entry = add_entry(saved, "letter", "Water reminder", notice.saved_json(), TODAY)
        self.assertNotIn("transcription", json.loads(entry["details"]))
        self.assertNotIn("quotes", json.loads(entry["details"]))
        restored = read_data(json.dumps(saved).encode())
        self.assertEqual(restored, saved)
        self.assertEqual(len(deadline_groups(restored["records"], TODAY)["This week"]), 1)

    def test_calendar_escapes_and_folds_unicode(self):
        calendar = make_calendar([(TODAY, "A,B;C\n" + "அ" * 60, "event")])
        self.assertIn(b"DTSTART;VALUE=DATE:20261122\r\n", calendar)
        self.assertIn(b"SUMMARY:A\\,B\\;C\\n", calendar)
        self.assertTrue(all(len(line) <= 75 for line in calendar.split(b"\r\n")))

    def test_benefits_prioritize_the_matching_rule(self):
        profile = {"age": "29", "state": "Tamil Nadu", "bpl": "Yes", "gender": "Woman", "widowed": "No",
                   "monthly_income": "₹15,000 or less", "pension_exclusion": "No", "occupation": "Unorganised worker"}
        self.assertIn("Maan-dhan", check(profile)[0].name)
        self.assertTrue(check(profile)[0].likely)
        profile["pension_exclusion"] = "Not sure"
        self.assertFalse(any(scheme.likely for scheme in check(profile)))


if __name__ == "__main__":
    unittest.main()
