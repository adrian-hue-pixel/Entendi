"""Speech for two fixed, public owl phrases. No letter text reaches gTTS."""

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from i18n import OWL_HELP, OWL_WELCOME, catalogue_code, translate
from letter_reader import LANGUAGES, LetterError, speech_engine, speech_wav

ASSETS = Path(__file__).with_name("assets") / "owl_audio"


@cache
def _executor() -> ThreadPoolExecutor:
    return ThreadPoolExecutor(max_workers=3, thread_name_prefix="entendi-owl")


@cache
def pending_phrase(language: str, phrase: str):
    return _executor().submit(render_phrase, language, phrase)


def prewarm(language: str) -> None:
    for code in dict.fromkeys(("English", language)):
        for phrase in (OWL_WELCOME, OWL_HELP):
            pending_phrase(code, phrase)


def asset_path(language: str, phrase: str) -> Path:
    return ASSETS / f"{catalogue_code(language)}-{sha256(translate(phrase, language).encode()).hexdigest()[:10]}.mp3"


def render_phrase(language: str, phrase: str) -> tuple[bytes, str]:
    path = asset_path(language, phrase)
    if path.exists():
        return path.read_bytes(), "audio/mpeg"
    text = translate(phrase, language)
    try:
        from gtts import gTTS

        code = catalogue_code(language)
        output = BytesIO()
        gTTS(text=text, lang=code, tld="co.uk" if code == "en" else "com",
             timeout=(2, 4)).write_to_fp(output)
        if output.getbuffer().nbytes:
            return output.getvalue(), "audio/mpeg"
    except Exception:
        pass
    if engine := speech_engine():
        return speech_wav(text, language, engine), "audio/wav"
    raise LetterError("Audio could not start. Try Listen again.")


def main():
    parser = ArgumentParser(description="Generate reusable audio for Entendi’s two public phrases.")
    parser.add_argument("--language", action="append", choices=list(LANGUAGES))
    args = parser.parse_args()
    languages = args.language or list(LANGUAGES)
    ASSETS.mkdir(exist_ok=True)
    for language in languages:
        for phrase in (OWL_WELCOME, OWL_HELP):
            audio, mime = render_phrase(language, phrase)
            if mime != "audio/mpeg":
                raise SystemExit(f"gTTS returned no MP3 for {language}; check network access and retry.")
            asset_path(language, phrase).write_bytes(audio)


if __name__ == "__main__":
    main()
