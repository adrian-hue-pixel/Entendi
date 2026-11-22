from datetime import date
import json
import unittest

from country_profiles import COUNTRIES, benefits_location, formatted_date, local_languages
from i18n import LOCAL_NAMES, OWL_HELP, OWL_WELCOME, catalogue, translate
from letter_data import read_data
from letter_reader import LANGUAGES
from onboarding import profile_ready
from trust import check_deadline, display_amount, redact


class OnboardingTests(unittest.TestCase):
    def test_languages_by_country(self):
        self.assertEqual(set(local_languages("Switzerland")), {"French", "German", "Italian"})
        self.assertEqual(set(local_languages("Belgium")), {"French", "German", "Dutch"})
        self.assertEqual(set(local_languages("Singapore")), {"English", "Chinese (Simplified)"})
        self.assertEqual(set(local_languages("India")), {"English", "Hindi"})
        for country in ("Ukraine", "Greece", "Sweden", "Malaysia", "Taiwan", "Macau"):
            self.assertIn(country, COUNTRIES)
            self.assertEqual(local_languages(country), ("English",))
        self.assertNotIn("Chinese (Simplified)", local_languages("Hong Kong"))
        self.assertEqual(local_languages("Cyprus"), ("Turkish",))

    def test_roundtrip_profile_and_legacy_data(self):
        entered = {"country": "Switzerland", "nation": "", "interface_language": "Italian",
                   "explanation_language": "German"}
        self.assertEqual(read_data(json.dumps({"profile": {**entered, "email": "example@example.net"},
                                               "records": []}).encode())["profile"], entered)
        self.assertTrue(profile_ready(entered))
        old = read_data(b'{"profile":{"country":"England (United Kingdom)"},"records":[]}')["profile"]
        self.assertEqual(old, {"country": "United Kingdom", "nation": "England"})
        self.assertIsNotNone(benefits_location("United Kingdom", "England"))
        self.assertIsNone(benefits_location("United Kingdom", "Scotland"))

    def test_bilingual_catalogues_have_fixed_phrases_and_status(self):
        self.assertEqual(set(LOCAL_NAMES), set(LANGUAGES))
        self.assertEqual(LOCAL_NAMES["Hindi"], "हिन्दी")
        for language in LANGUAGES:
            self.assertTrue(catalogue(language)["owl_review"])
            for phrase in (OWL_WELCOME, OWL_HELP, "Listen", "Continue"):
                self.assertTrue(translate(phrase, language))
                if language != "English":
                    self.assertNotEqual(translate(phrase, language), phrase)

    def test_country_formatting_never_infers_a_deadline(self):
        self.assertEqual(formatted_date(date(2026, 3, 12), "Japan"), "2026-03-12")
        self.assertEqual(formatted_date(date(2026, 3, 12), "United States"), "03/12/2026")
        self.assertEqual(display_amount("€1,234.56", "France"), "1\u202f234,56 €")
        self.assertEqual(display_amount("£48.50", "France"), "£48.50")
        self.assertEqual(check_deadline("Due 03/04/2026", "Due 03/04/2026", None, country="United States"),
                         "ambiguous")
        self.assertEqual(redact("DNI: 12345678Z", country="Spain"), "DNI: •••••678Z")
        self.assertEqual(redact("sort code: 12-34-56", country="United Kingdom"), "sort code: ••-34-56")


if __name__ == "__main__":
    unittest.main()
