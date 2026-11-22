"""Entendi's six Streamlit pages."""

from datetime import date
from hashlib import sha256
import json
import os
from urllib.parse import quote
from uuid import uuid4

import streamlit as st

import benefits
from country_profiles import benefits_location, formatted_date
from i18n import LOCAL_NAMES, OWL_HELP, OWL_WELCOME, translate, ui_text as tr
from owl_audio import pending_phrase
from trust import display_amount
import letter_data as data
from letter_reader import (LANGUAGES, SAMPLES, LetterError, Notice, explain_letter, prepare_image,
                           sample_letter, speech_engine, speech_wav)
import ui

PAGES = {
    "home": ("Home", ""),
    "understand": ("Understand a Letter", "Read an official letter in the language you choose."),
    "letters": ("My Letters", "Open saved explanations and see what still needs your attention."),
    "deadlines": ("Deadlines", "See what is due and add a reminder to your phone."),
    "benefits": ("Benefits Check", "Check selected NHS eligibility routes for England."),
    "help": ("Help & About", "How Entendi works, privacy, and feedback."),
}
FEATURES = {
    "understand": "Upload or photograph a letter and see what it asks you to do.",
    "deadlines": "Keep due dates together and add them to your phone calendar.",
    "benefits": "Check two NHS benefits in England and see which rule applies.",
}


def today() -> date:
    return date.today()


def go(page: str) -> None:
    st.session_state.page = page


def markup(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=64)
def _fixed_audio(language: str, phrase: str) -> tuple[bytes, str]:
    return pending_phrase(language, phrase).result()


def owl_message(phrase: str, area: str) -> None:
    local = st.session_state.get("interface_language", "English")
    languages = ("English",) if local == "English" else ("English", local)
    with st.container(border=True, key=f"owl_message_{area}"):
        for language in languages:
            text_column, audio_column = st.columns([3, 1], gap="small", vertical_alignment="center")
            with text_column:
                label = (f'<small class="owl-language">{ui.esc(LOCAL_NAMES[language])}</small>'
                         if len(languages) > 1 else "")
                markup(f'{label}<p class="owl-line">{ui.esc(translate(phrase, language))}</p>')
            with audio_column:
                audio_key = f"owl_listen_{area}_{language}"
                if st.button(translate("Listen", language), key=audio_key, icon=":material/volume_up:",
                             help=LOCAL_NAMES[language]):
                    try:
                        audio, mime = _fixed_audio(language, phrase)
                    except LetterError as exc:
                        st.error(tr(str(exc)))
                    else:
                        st.session_state["owl_audio"] = (area, language, audio, mime)
                        st.session_state[f"owl_play_{area}"] = True
        if (audio := st.session_state.get("owl_audio")) and audio[0] == area and audio[1] in languages:
            st.audio(audio[2], format=audio[3], autoplay=bool(st.session_state.pop(f"owl_play_{area}", False)))


def selected_country() -> str:
    return st.session_state.entendi_data["profile"].get("country", "")


def page_header(page: str) -> None:
    title, tagline = PAGES[page]
    markup(ui.page_header(page, tr(title), tr(tagline)))
    owl_message(OWL_HELP, page)


def saved_entries(category: str | None = None) -> list[dict]:
    entries = st.session_state.entendi_data["records"]
    return entries if category is None else [entry for entry in entries if entry["category"] == category]


def find_entry(entry_id: str) -> dict | None:
    return next((entry for entry in saved_entries() if entry["id"] == entry_id), None)


def start_letter(sample: str | None = None) -> None:
    state = st.session_state
    state.pop("current_letter", None)
    state.pop("letter_error", None)
    state["input_version"] = state.get("input_version", 0) + 1
    if sample:
        state["reading_job"] = {"sample": sample, "sample_day": today(), "id": uuid4().hex,
                                "language": state.language}
    go("understand")


def home() -> None:
    markup(ui.hero_html(tr("Understand any official letter,"), tr("in your language."),
                        tr("See what the letter is about, what to do next, and when it’s due.")))
    owl_message(OWL_WELCOME, "home")
    left, right = st.columns(2, gap="small")
    left.button(tr("Upload a letter"), on_click=start_letter, type="primary", width="stretch")
    right.button(tr("Try a sample letter"), on_click=start_letter, args=("water",), width="stretch")
    st.caption(tr("Your photo isn't stored. Entendi explains; it doesn't give legal advice."))
    upcoming = [(due, entry) for entry in saved_entries("letter")
                if not entry["done"] and (due := data.deadline_for(entry)) and due >= today()]
    if upcoming:
        due, entry = min(upcoming, key=lambda pair: pair[0])
        markup(ui.callout_html(f"{tr('Next deadline')}: {formatted_date(due, selected_country())} · {entry['title']}"))
    markup(ui.steps_html(tr))
    for column, (page, tagline) in zip(st.columns(3, gap="medium"), FEATURES.items()):
        with column, st.container(key=f"fcard_home_{page}"):
            markup(ui.feature_card_html(page, tr(PAGES[page][0]), tr(tagline)))
            st.button(tr("Open") + " ›", key=f"home_{page}", on_click=go, args=(page,))


def _service_options() -> dict:
    config = {}
    for name, field in (("LETTER_API_URL", "endpoint"), ("LETTER_API_MODEL", "model"), ("LETTER_API_KEY", "api_key")):
        try:
            value = st.secrets.get(name, "")
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            value = ""
        config[field] = str(os.getenv(name) or value).strip()
    return config


def _run_reading() -> None:
    state = st.session_state
    job = state.pop("reading_job")
    previous = state.get("current_letter", {})
    with st.container(key="letter_loading"):
        markup(f'<div class="letter-loading">{ui.mascot(88)}<strong>{ui.esc(tr("Reading your letter..."))}</strong></div>')
        try:
            photo = job.get("photo") or previous.get("photo")
            if sample := job.get("sample"):
                notice, photo = sample_letter(sample, job["language"], today=job["sample_day"],
                                              simpler=job.get("simpler", False))
            else:
                notice = explain_letter(
                    language=job["language"], **_service_options(),
                    photo=job.get("photo"), transcription=job.get("transcription", ""),
                    simpler=job.get("simpler", False), country=job.get("country", selected_country()),
                )
        except LetterError as exc:
            state["letter_error"] = str(exc)
        else:
            state["current_letter"] = {
                "id": job["id"], "notice": notice, "photo": photo, "sample": job.get("sample"),
                "sample_day": job.get("sample_day"), "country": job.get("country", selected_country()),
            }
            state["language_update"] = notice.language
    st.rerun()


def _sync_input_language() -> None:
    st.session_state.language = st.session_state.letter_input_language
    st.session_state.entendi_data["profile"]["explanation_language"] = st.session_state.language


def _letter_input() -> None:
    state = st.session_state
    if state.get("letter_input_language") != state.language:
        state.letter_input_language = state.language
    st.selectbox(tr("Explanation language"), list(LANGUAGES), key="letter_input_language",
                 on_change=_sync_input_language, format_func=LOCAL_NAMES.__getitem__)
    with st.container(border=True):
        mode = st.radio(tr("How would you like to add your letter?"), ("Upload", "Take photo"), horizontal=True, key="letter_input_mode", format_func=lambda value, lang=st.session_state.interface_language: translate(value, lang))
        field_key = state.get("input_version", 0)
        if mode == "Upload":
            file = st.file_uploader(tr("Upload a photo of your letter"), type=("jpg", "jpeg", "png", "webp"),
                                    key=f"letter_upload_{field_key}")
        else:
            file = st.camera_input(tr("Take a photo of your letter"), key=f"letter_camera_{field_key}")
        st.caption(tr("Lay it flat, use good light, and include all four corners."))
        photo = None
        if file is not None:
            try:
                photo = prepare_image(file.getvalue())
            except LetterError as exc:
                st.error(str(exc))
            else:
                st.image(photo, caption="Your letter preview", width=440)
        st.caption(tr("Real photos go to the configured reading service for processing. Entendi does not save the photo to My Letters."))
        if st.button(tr("Explain my letter"), type="primary", disabled=photo is None):
            state["reading_job"] = {"photo": photo, "language": state.language, "id": uuid4().hex}
            st.rerun()
    with st.expander(tr("Try a sample letter")):
        for sample, label in SAMPLES.items():
            st.button(label, key=f"sample_{sample}", on_click=start_letter, args=(sample,))


def understand() -> None:
    page_header("understand")
    if "reading_job" in st.session_state:
        _run_reading()
    if error := st.session_state.pop("letter_error", None):
        st.error(error)
    if current := st.session_state.get("current_letter"):
        st.button(tr("Read another letter"), on_click=start_letter)
        letter_result(current["notice"], current["id"], current=current)
    else:
        _letter_input()


def _speak(notice: Notice, key: str) -> None:
    sentence = " ".join((notice.explanation, *notice.actions_required, *notice.documents_to_bring))
    if engine := speech_engine():
        audio_id = sha256(f"{notice.language}\0{sentence}".encode()).hexdigest()
        requested = st.button(tr("Listen"), key=f"listen_{key}")
        if requested:
            try:
                audio = speech_wav(sentence, notice.language, engine)
            except LetterError as exc:
                st.error(str(exc))
            else:
                st.session_state["letter_audio"] = (audio_id, audio)
        cached = st.session_state.get("letter_audio")
        if cached and cached[0] == audio_id:
            st.audio(cached[1], format="audio/wav", autoplay=requested)
        return
    config = json.dumps({"text": sentence, "lang": LANGUAGES.get(notice.language, "en-GB")},
                        ensure_ascii=True).replace("<", "\\u003c")
    st.iframe(f"""<!doctype html><html lang="en"><meta charset="utf-8">
    <style>
      body{{margin:2px;font:600 14px system-ui;color-scheme:light dark}}
      button{{border:1px solid #9880c8;border-radius:100px;padding:8px 16px;background:#eee6fa;color:#392361;cursor:pointer}}
      button:focus-visible{{outline:2px solid #aa8be3;outline-offset:2px}}
      span{{margin-left:10px;font-size:12px;color:#7960a9}}
      @media(prefers-color-scheme:dark){{span{{color:#c5acf4}}}}
    </style>
    <button id="listen" type="button">▶ Listen</button><span id="status" role="status"></span>
    <script>
      const options = {config};
      const button = document.getElementById('listen');
      const status = document.getElementById('status');
      let speaking = false;
      button.addEventListener('click', () => {{
        if (!('speechSynthesis' in window)) {{
          status.textContent = 'Audio is unavailable in this browser.'; return;
        }}
        if (speaking) {{
          speechSynthesis.cancel(); speaking = false; button.textContent = '▶ Listen'; status.textContent = ''; return;
        }}
        const language = options.lang.split('-')[0];
        const voices = speechSynthesis.getVoices().filter(voice => voice.localService && voice.lang.startsWith(language));
        const voice = voices.find(voice => voice.lang.toLowerCase() === options.lang.toLowerCase()) || voices[0];
        if (!voice) {{
          status.textContent = 'No on-device voice found for this language.'; return;
        }}
        const utterance = new SpeechSynthesisUtterance(options.text);
        utterance.lang = options.lang;
        utterance.voice = voice;
        utterance.rate = 0.88;
        utterance.onend = () => {{ speaking = false; button.textContent = '▶ Listen'; status.textContent = ''; }};
        utterance.onerror = () => {{
          if (!speaking) return;
          speaking = false; button.textContent = '▶ Listen'; status.textContent = 'Audio could not start.';
        }};
        speaking = true; button.textContent = '■ Stop'; status.textContent = 'Playing…';
        speechSynthesis.speak(utterance);
      }});
    </script></html>""", height=52, alt="Listen to the letter explanation")


def _checklist(lines: list[str] | tuple[str, ...], prefix: str, empty: str) -> None:
    if not lines:
        st.caption(empty)
    checks = st.session_state.setdefault("checklist_marks", {})
    for index, line in enumerate(lines):
        key = f"check_{prefix}_{index}"
        def remember(widget=key):
            checks[widget] = st.session_state[widget]
        st.checkbox(line, value=checks.get(key, False), key=key, on_change=remember)


def _calendar_button(day: date, title: str, entry_id: str, label: str, key: str) -> None:
    st.download_button(tr(label), data.make_calendar([(day, title, entry_id)]), file_name="entendi-deadline.ics",
                       mime="text/calendar", key=key, on_click="ignore")


def _translate(current: dict, language: str, simpler: bool = False) -> None:
    job = {key: current.get(key) for key in ("id", "sample", "sample_day", "country")}
    job.update(language=language, transcription=current["notice"].transcription, simpler=simpler)
    st.session_state["reading_job"] = job
    st.rerun()


def _add_feedback(title: str, value: dict) -> None:
    data.add_entry(st.session_state.entendi_data, "feedback", title, json.dumps(value, ensure_ascii=False), today())
    st.success(tr("Feedback saved in this session. It’s included if you download My data."))


def letter_result(notice: Notice, entry_id: str, *, current: dict | None = None) -> None:
    prefix = f"{'current' if current else 'saved'}_{entry_id}"
    title = f"{notice.issuer} · {notice.document_type}"
    if current and current.get("sample"):
        st.info(tr("Fictional sample letter for demonstration."))
    if notice.needs_human_check:
        with st.container(border=True, key=f"confirm_{entry_id}"):
            st.markdown(f"**{tr('Please confirm with the official office')}**")
            for text in notice.unclear_parts or ["Some details or source quotes could not be verified."]:
                st.text(f"• {text}")
    else:
        markup(ui.badge_html(tr("Read clearly"), "quiet"))
    with st.expander(tr("How Entendi checks this letter")):
        st.write(f"**Deadline:** {notice.deadline_check} · **Amount:** {notice.amount_check} · "
                 f"**Round-trip translation:** {notice.translation_check}")
        st.caption(tr("Date and amount patterns check the values against the printed excerpts read by the model. "
                   "This can catch a swapped day and month, a dropped decimal, or the wrong currency. "
                   "Ambiguous dates and unconfirmed amounts are left out."))
        st.caption(tr("For a translated letter, a second request translates the explanation back into English. "
                   "Entendi checks for changed dates, amounts, negation and wording. A match cannot guarantee accuracy. "
                   "Both checks depend on what the model could read from the photo."))
    st.subheader(tr("What this is"))
    markup(f'<p class="letter-summary">{ui.esc(notice.explanation)}</p>')
    markup(f'<div class="letter-badges">{ui.badge_html(notice.issuer)}{ui.badge_html(notice.document_type)}</div>')
    _speak(notice, prefix)
    facts = [("Do by", formatted_date(notice.deadline, selected_country()) if notice.deadline else "No deadline found",
              data.days_left(notice.deadline, today()) if notice.deadline else "Confirm the date if you’re unsure."),
             ("Amount", display_amount(notice.amount, selected_country()) if notice.amount else "Not stated", "")]
    if notice.if_ignored:
        facts.append(("If ignored", notice.if_ignored, ""))
    for col, (label, value, footnote) in zip(st.columns(3, gap="small"), facts):
        with col:
            markup(ui.fact_html(tr(label), tr(value), tr(footnote)))

    st.subheader(tr("What you need to do"))
    _checklist(notice.actions_required, f"{prefix}_{notice.language}_actions", "No actions were stated.")
    st.subheader(tr("Bring these"))
    _checklist(notice.documents_to_bring, f"{prefix}_{notice.language}_documents", "No documents were stated.")
    st.subheader(tr("Proof from your letter"))
    original, explanation = st.columns(2, gap="medium")
    with original, st.container(border=True):
        st.markdown(f"**{tr('Your letter')}**")
        if current and current.get("photo"):
            st.image(current["photo"], width="stretch")
        else:
            st.caption(tr("The original photo isn’t kept in My Letters."))
    with explanation, st.container(border=True):
        st.markdown(f"**{tr('Entendi’s explanation')}**")
        if not notice.quotes:
            st.caption("Source text isn’t retained in My Letters." if not current else "No readable excerpts were identified.")
        for index, excerpt in enumerate(notice.quotes, start=1):
            label = tr("✓ Found in letter" if excerpt.verified else "⚑ Couldn’t verify")
            with st.expander(f"Quote {index} · {label}"):
                st.text(excerpt.text)
        if notice.quotes:
            st.caption(tr("Quotes are matched against the transcription. Check the original if anything looks wrong."))

    calendar, save, share = st.columns(3, gap="small")
    with calendar:
        if notice.deadline:
            _calendar_button(notice.deadline, title, entry_id, "Add to calendar", f"ics_{prefix}")
        else:
            st.button(tr("Add to calendar"), disabled=True, key=f"no_ics_{prefix}", help="No deadline was found in this letter.")
    with save:
        letter = find_entry(entry_id)
        if st.button(tr("Saved to My Letters" if letter else "Save to My Letters"), disabled=bool(letter),
                     key=f"save_{prefix}", type="primary"):
            data.add_entry(st.session_state.entendi_data, "letter", title, notice.saved_json(), today(), entry_id=entry_id)
            st.rerun()
    with share:
        summary = f"{title}\n{notice.explanation}"
        if notice.deadline:
            summary += f"\nDo by: {notice.deadline:%d %b %Y}"
        st.link_button(tr("Share on WhatsApp"), "https://wa.me/?text=" + quote(summary, safe=""),
                       help="Opens WhatsApp with the explanation so you can review it before sending.")
    if current:
        with st.expander(tr("Explain in another language")):
            language = st.selectbox(tr("Choose a language"), list(LANGUAGES), index=list(LANGUAGES).index(notice.language) if notice.language in LANGUAGES else 0,
                                    key=f"translate_{prefix}", format_func=LOCAL_NAMES.__getitem__)
            if st.button(tr("Explain in this language"), disabled=language == notice.language, key=f"run_{prefix}"):
                _translate(current, language)
        if st.button(tr("Use simpler words"), key=f"simpler_{prefix}"):
            _translate(current, notice.language, simpler=True)
    with st.expander(tr("Something looks wrong")):
        with st.form(f"report_{prefix}", clear_on_submit=True):
            issue = st.text_area(tr("What looked wrong?"), max_chars=500,
                                 help="Leave out names, reference numbers and other personal details.")
            if st.form_submit_button(tr("Save report")):
                if issue.strip():
                    _add_feedback("Letter explanation issue", {"comment": issue.strip()})
                else:
                    st.warning(tr("Describe what looked wrong before saving."))
    st.button(tr("Check my benefits"), key=f"to_benefits_{prefix}", on_click=go, args=("benefits",))


def open_letter(entry_id: str) -> None:
    st.session_state["open_letter"] = entry_id
    go("letters")


def close_letter() -> None:
    st.session_state.pop("open_letter", None)


def _remove_letter(entry_id: str) -> None:
    entries = saved_entries()
    entries[:] = [entry for entry in entries if entry["id"] != entry_id]
    if st.session_state.get("open_letter") == entry_id:
        close_letter()


def my_letters() -> None:
    page_header("letters")
    st.caption(tr("Saved letters keep only the explanation and facts. Photos, full transcriptions and source quotes are left out, including when you download My data."))
    if entry := find_entry(st.session_state.get("open_letter", "")):
        st.button(tr("Back to My Letters"), on_click=close_letter)
        letter_result(Notice.model_validate_json(entry["details"]), entry["id"])
        return
    status = st.selectbox(tr("Status"), ("All", "Open", "Done"), key="letter_filter", format_func=lambda value, lang=st.session_state.interface_language: translate(value, lang))
    letters = [entry for entry in saved_entries("letter") if status == "All" or entry["done"] == (status == "Done")]
    if not letters:
        markup(ui.empty_html(tr("No letters here yet"), "Save a letter’s explanation to find it here later."))
        st.button(tr("Understand a Letter"), on_click=go, args=("understand",))
    for entry in letters:
        notice = Notice.model_validate_json(entry["details"])
        with st.container(border=True):
            st.subheader(notice.document_type)
            st.text(f"{notice.issuer} · Saved {date.fromisoformat(entry['date']):%d %b %Y}")
            chips = ui.badge_html("Done" if entry["done"] else "Open")
            if notice.deadline:
                chips += ui.badge_html(f"{tr('Do by')} {formatted_date(notice.deadline, selected_country())}")
            markup(f'<div class="letter-badges">{chips}</div>')
            left, middle, right = st.columns(3)
            left.button(tr("Open"), key=f"open_{entry['id']}", on_click=open_letter, args=(entry["id"],))
            middle.button(tr("Mark open" if entry["done"] else "Mark done"), key=f"mark_{entry['id']}",
                          on_click=_set_done, args=(entry["id"], not entry["done"]))
            right.button(tr("Delete"), key=f"delete_{entry['id']}", on_click=_remove_letter, args=(entry["id"],))


def _set_done(entry_id: str, done: bool | str) -> None:
    if entry := find_entry(entry_id):
        entry["done"] = st.session_state[done] if isinstance(done, str) else done


def deadlines() -> None:
    page_header("deadlines")
    groups = data.deadline_groups(saved_entries(), today())
    events = [(day, entry["title"], entry["id"]) for group, pairs in groups.items() if group != "Done" for day, entry in pairs]
    st.download_button(tr("Download all (.ics)"), data.make_calendar(events), file_name="entendi-deadlines.ics",
                       mime="text/calendar", disabled=not events, on_click="ignore")
    for group, rows in groups.items():
        markup(ui.group_heading(tr(group)))
        if not rows:
            st.caption(tr("No deadlines here."))
        for due, entry in rows:
            with st.container(border=True):
                key = entry["id"]
                left, middle, right = st.columns([1.55, 1, 1.25])
                with left:
                    label = data.days_left(due, today()) if not entry["done"] else f"{tr('Do by')} {formatted_date(due, selected_country())}"
                    markup(ui.badge_html(label, "warm" if group == "Overdue" else ""))
                    if entry["category"] == "letter":
                        st.button(entry["title"], key=f"deadline_open_{key}", on_click=open_letter, args=(key,))
                    else:
                        st.text(entry["title"])
                with middle:
                    done_key = f"deadline_done_{key}"
                    st.checkbox(tr("Done"), value=entry["done"], key=done_key, on_change=_set_done, args=(key, done_key))
                with right:
                    _calendar_button(due, entry["title"], key, "Add to phone calendar", f"deadline_calendar_{key}")
    with st.expander(tr("Add my own reminder")):
        with st.form("reminder", clear_on_submit=True):
            title = st.text_input(tr("Reminder title"), max_chars=120)
            due = st.date_input(tr("Due date"), value=today())
            if st.form_submit_button(tr("Add reminder"), type="primary"):
                if not title.strip():
                    st.warning(tr("Enter a reminder title."))
                else:
                    data.add_entry(st.session_state.entendi_data, "reminder", title, "{}", due)
                    st.rerun()


def benefits_check() -> None:
    page_header("benefits")
    st.info(tr("This check uses fixed rules, not AI. It covers two NHS age and education routes in England. "
            "The official service makes the final decision."))
    preferences = st.session_state.entendi_data["profile"]
    country = benefits_location(preferences.get("country", ""), preferences.get("nation", ""))
    if not country:
        st.info(tr("Not available for your country yet"))
        return
    profile = st.session_state.setdefault("benefits_answers", {})
    try:
        default_age = min(125, max(0, int(profile.get("age", "18"))))
    except ValueError:
        default_age = 18
    with st.form("eligibility"):
        age = st.number_input(tr("Age"), min_value=0, max_value=125, value=default_age)
        studying = st.checkbox(tr("In full-time education"), value=profile.get("education") == "yes")
        if st.form_submit_button(tr("Check my benefits"), type="primary"):
            profile.update(country=country, age=str(age), education="yes" if studying else "no")
    if profile.get("country") != country:
        return
    try:
        schemes = benefits.check(country, int(profile["age"]), profile.get("education") == "yes")
    except (KeyError, ValueError):
        return
    st.caption(tr("Other NHS exemptions can apply even when these age and education rules do not match. "
               "Check the full criteria on the official site."))
    for index, scheme in enumerate(schemes):
        with st.container(border=True):
            st.subheader(scheme.name)
            markup(ui.badge_html("Likely" if scheme.likely else "This route did not match", "quiet"))
            st.text(scheme.explanation)
            st.markdown(f"**{tr('Evidence to ask about')}**")
            _checklist(scheme.documents, f"scheme_{index}", "")
            st.text(scheme.office)
            st.link_button(tr("Official scheme information"), scheme.url)
            st.caption(tr("The official service makes the final decision."))


def help_about() -> None:
    page_header("help")
    st.subheader(tr("How it works"))
    markup(ui.steps_html(tr))
    st.subheader(tr("What Entendi can’t do"))
    st.markdown(tr("- It may misread a blurry photo. Confirm dates, amounts and next steps with the official office.\n"
                "- It doesn’t give legal advice or decide whether a letter is genuine.\n"
                "- Benefits Check follows fixed rules. The office makes the final decision."))
    st.subheader(tr("Privacy"))
    st.markdown(tr("Entendi keeps the photo temporarily in your session so you can compare it. Real photos are sent to the "
                "configured reading service for processing. Entendi masks recognised numbers in extracted text before displaying or saving it. Saved letters and downloads omit the photo, full transcription "
                "and source quotes. My data can contain your explanations and benefits answers, so keep the download private."))
    st.subheader(tr("Keep an offline copy"))
    paragraphs = ["Entendi · Saved letters", "For important details, check your original letter or ask the official office."]
    for entry in saved_entries("letter"):
        notice = Notice.model_validate_json(entry["details"])
        lines = [entry["title"], notice.explanation]
        if notice.deadline:
            lines.append(f"Do by: {notice.deadline:%d %b %Y}")
        lines.extend(f"• {line}" for line in notice.actions_required)
        paragraphs.append("\n".join(lines))
    st.download_button(tr("Download offline copy"), "\n\n".join(paragraphs), file_name="entendi-letters.txt",
                       mime="text/plain", disabled=len(paragraphs) == 2, on_click="ignore")
    if len(paragraphs) == 2:
        st.caption(tr("Save a letter first to download an offline copy."))
    st.subheader(tr("Feedback"))
    with st.form("feedback", clear_on_submit=True):
        rating = st.radio(tr("Rating"), (1, 2, 3, 4, 5), index=3, horizontal=True)
        comment = st.text_area(tr("Comment"), max_chars=500)
        if st.form_submit_button(tr("Save feedback")):
            _add_feedback("Feedback", {"rating": rating, "comment": comment.strip()})
    st.caption(tr("Built for EvoHacks 2."))


ROUTES = {
    "home": home, "understand": understand, "letters": my_letters, "deadlines": deadlines,
    "benefits": benefits_check, "help": help_about,
}


def render(page: str) -> None:
    ROUTES.get(page, home)()
