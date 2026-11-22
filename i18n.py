"""Static, editable interface catalogues and owl lines."""

from functools import cache
import json
from pathlib import Path

import streamlit as st

from letter_reader import LANGUAGES

LOCALES = Path(__file__).with_name("locales")
LOCAL_NAMES = dict(zip(LANGUAGES, (
    "English", "Español", "Français", "Deutsch", "Português", "Italiano", "Русский",
    "Polski", "Nederlands", "Türkçe", "简体中文", "日本語", "한국어", "Tiếng Việt", "Bahasa Indonesia", "ไทย",
    "हिन्दी",
)))
OWL_WELCOME = "Welcome to Entendi."
OWL_HELP = "I’ll help you read your letter, one step at a time."


def catalogue_code(language: str) -> str:
    locale = LANGUAGES.get(language, "en-GB")
    return "zh-CN" if language == "Chinese (Simplified)" else locale.split("-")[0]


@cache
def catalogue(language: str) -> dict:
    return json.loads((LOCALES / f"{catalogue_code(language)}.json").read_text(encoding="utf-8"))


def translate(text: str, language: str) -> str:
    return catalogue(language)["strings"].get(text, text)


def ui_text(text: str) -> str:
    return translate(text, st.session_state.get("interface_language", "English"))
