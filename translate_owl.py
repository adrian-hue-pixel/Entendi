"""Optional maintainer tool: regenerate only the fixed owl lines with Gemini."""

from argparse import ArgumentParser
import json
import os
from urllib.parse import quote
from urllib.request import Request, urlopen

from i18n import LOCALES, OWL_HELP, OWL_WELCOME, catalogue_code
from letter_reader import LANGUAGES

PHRASES = (OWL_WELCOME, OWL_HELP)


def translate_fixed_lines(language: str, key: str, model: str) -> dict:
    instructions = (
        f"Translate these two fixed app strings into {language}. Use warm, natural language, "
        "preserve the meaning and the Entendi name. Return a JSON object keyed by the exact English originals: "
        + json.dumps(PHRASES, ensure_ascii=False)
    )
    payload = {"contents": [{"parts": [{"text": instructions}]}],
               "generationConfig": {"responseMimeType": "application/json"}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    request = Request(url, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    translated = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
    if set(translated) != set(PHRASES) or any(not isinstance(line, str) or not 0 < len(line) < 250
                                           for line in translated.values()):
        raise ValueError("Unexpected shape or length for the fixed phrases.")
    return translated


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--language", action="append", required=True, choices=[lang for lang in LANGUAGES if lang != "English"])
    args = parser.parse_args()
    key = os.getenv("GEMINI_LOCALE_API_KEY")
    model = os.getenv("GEMINI_LOCALE_MODEL")
    if not key or not model:
        parser.error("Set GEMINI_LOCALE_API_KEY and GEMINI_LOCALE_MODEL in the shell.")
    for language in dict.fromkeys(args.language):
        path = LOCALES / f"{catalogue_code(language)}.json"
        content = json.loads(path.read_text(encoding="utf-8"))
        content["strings"].update(translate_fixed_lines(language, key, model))
        content["owl_review"] = "Machine translated with Gemini; meaning review pending."
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
