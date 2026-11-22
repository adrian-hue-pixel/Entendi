"""Session-only country and language preferences."""

import streamlit as st

from country_profiles import COUNTRIES, benefits_location, local_languages
from i18n import LOCAL_NAMES, ui_text as tr
from letter_reader import LANGUAGES
import ui

UK_NATIONS = ("England", "Scotland", "Wales", "Northern Ireland", "Not sure")


def profile_ready(profile: dict) -> bool:
    return profile.get("country") in COUNTRIES and profile.get("interface_language") in LANGUAGES


def regional_status(country: str, nation: str) -> str:
    return "Available in England" if benefits_location(country, nation) else "Not available for your country yet"


def show(profile: dict, *, editing: bool, welcome: bool = False) -> None:
    if welcome:
        st.markdown(ui.welcome_intro(), unsafe_allow_html=True)
    with st.container(key="onboarding_form"):
        _show_form(profile, editing=editing)


def _show_form(profile: dict, *, editing: bool) -> None:
    old_country = profile.get("country")
    st.markdown(f'<div class="setup-owl">{ui.mascot(86)}</div>', unsafe_allow_html=True)
    st.title(tr("Country and language"))
    st.caption(tr("Country and language are saved in your profile. No email is required."))
    country = st.selectbox(tr("Choose your country"), COUNTRIES,
                           index=COUNTRIES.index(old_country) if old_country in COUNTRIES else None,
                           placeholder=tr("Choose your country"), key="onboarding_country")
    if not country:
        return
    suggestions = local_languages(country)
    options = list(dict.fromkeys((*suggestions, *LANGUAGES)))
    current = profile.get("interface_language") if old_country == country else None
    default_index = options.index(current) if current in options else 0 if len(suggestions) == 1 else None
    language = st.selectbox(tr("Choose your language"), options, index=default_index,
                            format_func=LOCAL_NAMES.__getitem__, placeholder=tr("Choose a language"),
                            key=f"onboarding_language_{country}")
    if suggestions == ("English",) and country not in {"United Kingdom", "Ireland", "United States",
                                                       "Australia", "New Zealand", "Malta", "Philippines", "Hong Kong"}:
        st.caption(tr("English fallback"))
    nation = ""
    if country == "United Kingdom":
        old = profile.get("nation")
        nation = st.selectbox(tr("Select your UK nation"), UK_NATIONS,
                              index=UK_NATIONS.index(old) if old in UK_NATIONS else 4, key="onboarding_nation")
    with st.container(key="setup_summary"):
        st.subheader(tr("About your choices"))
        st.write(f"**{tr('Country')}:** {country}" + (f" · {nation}" if nation else ""))
        if language:
            st.write(f"**{tr('Interface language')}:** {LOCAL_NAMES[language]}")
        st.write(f"**{tr('Benefits Check')}:** {tr(regional_status(country, nation))}")
    if st.button(tr("Continue"), type="primary", disabled=language is None, width="stretch"):
        profile.update(country=country, nation=nation, interface_language=language)
        st.session_state.interface_language = language
        if not editing or not profile.get("explanation_language"):
            profile["explanation_language"] = language
            st.session_state.language_update = language
        st.session_state["edit_profile"] = False
        st.rerun()
