"""Entendi's Streamlit entry point."""

import json

import streamlit as st

from i18n import LOCAL_NAMES, translate, ui_text as tr
import letter_data
from letter_reader import LANGUAGES
import onboarding
from owl_audio import prewarm
import ui
import views

st.set_page_config(page_title="Entendi", page_icon="✦", layout="wide")

state = st.session_state
state.setdefault("entendi_data", letter_data.new_data())
profile = state.entendi_data["profile"]
state.interface_language = profile.get("interface_language", "English")
state.setdefault("language", profile.get("explanation_language", state.interface_language))
if language_update := state.pop("language_update", None):
    state.language = language_update
    profile["explanation_language"] = language_update
if state.get("page", "home") not in views.PAGES:
    state.page = "home"

dark = state.get("dark_mode", False)
low_data = state.get("low_data", False)
st.markdown(
    ui.global_css(dark, state.get("large_text", False), low_data, navigation=tuple(views.PAGES))
    + ui.background_fx(dark, low_data=low_data),
    unsafe_allow_html=True,
)


def import_data() -> None:
    uploaded = state.get("data_upload")
    if uploaded is None:
        return
    try:
        imported = letter_data.read_data(uploaded.getvalue())
    except (ValueError, UnicodeError):
        state["import_message"] = ("error", "This is not a valid Entendi data file. Your current letters are still here.")
    else:
        state.entendi_data = imported
        prefs = imported["profile"]
        state.language_update = prefs.get("explanation_language", prefs.get("interface_language", "English"))
        for key in ("open_letter", "checklist_marks", "current_letter", "benefits_answers", "edit_profile",
                    "onboarding_country", "onboarding_nation"):
            state.pop(key, None)
        for key in list(state):
            if key.startswith("onboarding_language_"):
                state.pop(key, None)
        state["import_message"] = ("success", "Your data was loaded.")


def save_language() -> None:
    state.entendi_data["profile"]["explanation_language"] = state.language


ready = onboarding.profile_ready(profile)
if ready and state.get("_owl_prepared") != state.interface_language:
    state["_owl_prepared"] = state.interface_language
    prewarm(state.interface_language)
editing = state.get("edit_profile", False)

with st.sidebar:
    st.markdown(ui.sidebar_brand(), unsafe_allow_html=True)
    if ready and not editing:
        st.markdown(ui.nav_label(tr("My Letters")), unsafe_allow_html=True)
        st.radio("Menu", list(views.PAGES), key="page",
                 format_func=lambda page, language=state.interface_language: translate(views.PAGES[page][0], language), label_visibility="collapsed")
        st.selectbox(tr("Explanation language"), list(LANGUAGES), key="language",
                     format_func=LOCAL_NAMES.__getitem__, on_change=save_language)
        if st.button(tr("Country and language"), key="edit_preferences"):
            state.edit_profile = True
            st.rerun()
    with st.expander(tr("Appearance and accessibility")):
        st.toggle(tr("Large text"), key="large_text")
        st.toggle(tr("Low-data mode"), key="low_data")
        st.toggle(tr("Dark appearance"), key="dark_mode")
    with st.expander(tr("My data"), expanded=not ready):
        st.caption(tr("Loading a file replaces the letters and answers in this session."))
        st.file_uploader(tr("Load my data"), type=["json"], key="data_upload", on_change=import_data)
        if message := state.pop("import_message", None):
            getattr(st, message[0])(tr(message[1]))
        st.download_button(tr("Save my data"), json.dumps(state.entendi_data, indent=2, ensure_ascii=False),
                           file_name="entendi-data.json", mime="application/json", on_click="ignore")
    st.caption(tr("Your letters stay in this browser session."))

if ready and not editing:
    views.render(state.page)
else:
    onboarding.show(profile, editing=editing)
