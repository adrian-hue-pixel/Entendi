"""Entendi's Streamlit entry point."""
import json

import streamlit as st

import ui
import views

st.set_page_config(page_title="Entendi", page_icon="✦", layout="wide")

state = st.session_state
state.setdefault("workspace", views.new_workspace())
st.markdown(ui.global_css(state.get("dark_mode", False), state.get("large_text", False), state.get("low_data", False))
            + ui.background_fx(state.get("dark_mode", False), low_data=state.get("low_data", False)), unsafe_allow_html=True)


def import_workspace() -> None:
    uploaded = state.get("workspace_upload")
    if uploaded is None:
        return
    try:
        state.workspace = views.read_workspace(uploaded.getvalue())
    except (ValueError, UnicodeError):
        state["import_message"] = ("error", "This is not a valid Entendi workspace file.")
    else:
        state["import_message"] = ("success", "Workspace loaded.")


with st.sidebar:
    st.markdown(ui.sidebar_brand(), unsafe_allow_html=True)
    st.radio("Menu", list(views.PAGES), key="page",
             format_func=lambda page: views.PAGES[page][0], label_visibility="collapsed")
    with st.expander("My workspace file"):
        st.file_uploader("Load saved workspace", type=["json"], key="workspace_upload", on_change=import_workspace)
        message = state.pop("import_message", None)
        if message:
            getattr(st, message[0])(message[1])
        st.download_button("Save my workspace", json.dumps(state.workspace, indent=2),
                           file_name="entendi_workspace.json", mime="application/json")
    with st.expander("Appearance and accessibility"):
        st.toggle("Large text", key="large_text")
        st.toggle("Low-data mode", key="low_data", help="Disables the web font and animations.")
        st.toggle("Dark appearance", key="dark_mode")
    st.success("Workspace ready")
    st.caption("Export your workspace to keep a copy after you close the app.")

views.render(state.page)
