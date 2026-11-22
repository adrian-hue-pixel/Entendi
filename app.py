"""Entendi's Streamlit entry point."""

import json

import streamlit as st

import letter_data
from letter_reader import LANGUAGES
import ui
import views

st.set_page_config(page_title="Entendi", page_icon="✦", layout="wide")

state = st.session_state
state.setdefault("entendi_data", letter_data.new_data())
state.setdefault("language", "English")
if language_update := state.pop("language_update", None):
    state.language = language_update
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
        for key in ("open_letter", "checklist_marks"):
            state.pop(key, None)
        state["import_message"] = ("success", "Your data was loaded.")


with st.sidebar:
    st.markdown(ui.sidebar_brand(), unsafe_allow_html=True)
    st.markdown(ui.nav_label("Letters"), unsafe_allow_html=True)
    st.radio("Menu", list(views.PAGES), key="page",
             format_func=lambda page: views.PAGES[page][0], label_visibility="collapsed")
    st.selectbox("Language", list(LANGUAGES), key="language", help="Changes the language of the letter explanation.")
    with st.expander("Appearance and accessibility"):
        st.toggle("Large text", key="large_text")
        st.toggle("Low-data mode", key="low_data", help="Disables the web font and animations.")
        st.toggle("Dark appearance", key="dark_mode")
    with st.expander("My data"):
        st.caption("Loading a file replaces the letters and answers in this session.")
        st.file_uploader("Load my data", type=["json"], key="data_upload", on_change=import_data)
        if message := state.pop("import_message", None):
            getattr(st, message[0])(message[1])
        st.download_button("Save my data", json.dumps(state.entendi_data, indent=2, ensure_ascii=False),
                           file_name="entendi-data.json", mime="application/json", on_click="ignore")
    st.caption("Your letters stay in this browser session.")

views.render(state.page)
