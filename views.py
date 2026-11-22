"""Entendi's six Streamlit pages."""

from datetime import date, datetime
import json
import os
from urllib.parse import quote
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

import benefits
import letter_data as data
from letter_reader import LANGUAGES, SAMPLES, LetterError, Notice, explain_letter, prepare_image, sample_letter
import ui

PAGES = {
    "home": ("Home", ""),
    "understand": ("Understand a Letter", "Read an official letter in the language you choose."),
    "letters": ("My Letters", "Open saved explanations and see what still needs your attention."),
    "deadlines": ("Deadlines", "See what is due and add a reminder to your phone."),
    "benefits": ("Benefits Check", "Check the basic rules for selected central schemes in India."),
    "help": ("Help & About", "How Entendi works, privacy, and feedback."),
}
FEATURES = {
    "understand": "Upload or photograph a letter and see what it asks you to do.",
    "deadlines": "Keep due dates together and add them to your phone calendar.",
    "benefits": "See which of three Indian government schemes you may qualify for.",
}


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def go(page: str) -> None:
    st.session_state.page = page


def markup(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


def page_header(page: str) -> None:
    title, tagline = PAGES[page]
    markup(ui.page_header(page, title, tagline, title))


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
    markup(ui.hero_html())
    left, right = st.columns(2, gap="small")
    left.button("Upload a letter", on_click=start_letter, type="primary", width="stretch")
    right.button("Try a sample letter", on_click=start_letter, args=("water",), width="stretch")
    st.caption("Your photo isn't stored. Entendi explains; it doesn't give legal advice.")
    upcoming = [(due, entry) for entry in saved_entries("letter")
                if not entry["done"] and (due := data.deadline_for(entry)) and due >= today()]
    if upcoming:
        due, entry = min(upcoming, key=lambda pair: pair[0])
        markup(ui.callout_html(f"Next deadline: {due:%d %b %Y} · {entry['title']}"))
    markup(ui.steps_html())
    for column, (page, tagline) in zip(st.columns(3, gap="medium"), FEATURES.items()):
        with column, st.container(key=f"fcard_home_{page}"):
            markup(ui.feature_card_html(page, PAGES[page][0], tagline))
            st.button("Open ›", key=f"home_{page}", on_click=go, args=(page,))


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
        markup(f'<div class="letter-loading">{ui.mascot(88)}<strong>Reading your letter...</strong></div>')
        try:
            photo = job.get("photo") or previous.get("photo")
            if sample := job.get("sample"):
                notice, photo = sample_letter(sample, job["language"], today=job["sample_day"],
                                              simpler=job.get("simpler", False))
            else:
                notice = explain_letter(
                    language=job["language"], **_service_options(),
                    photo=job.get("photo"), transcription=job.get("transcription", ""),
                    simpler=job.get("simpler", False),
                )
        except LetterError as exc:
            state["letter_error"] = str(exc)
        else:
            state["current_letter"] = {
                "id": job["id"], "notice": notice, "photo": photo, "sample": job.get("sample"),
                "sample_day": job.get("sample_day"),
            }
            state["language_update"] = notice.language
    st.rerun()


def _sync_input_language() -> None:
    st.session_state.language = st.session_state.letter_input_language


def _letter_input() -> None:
    state = st.session_state
    if state.get("letter_input_language") != state.language:
        state.letter_input_language = state.language
    st.selectbox("Explanation language", list(LANGUAGES), key="letter_input_language",
                 on_change=_sync_input_language)
    with st.container(border=True):
        mode = st.radio("How would you like to add your letter?", ("Upload", "Take photo"), horizontal=True, key="letter_input_mode")
        field_key = state.get("input_version", 0)
        if mode == "Upload":
            file = st.file_uploader("Upload a photo of your letter", type=("jpg", "jpeg", "png", "webp"),
                                    key=f"letter_upload_{field_key}")
        else:
            file = st.camera_input("Take a photo of your letter", key=f"letter_camera_{field_key}")
        st.caption("Lay it flat, use good light, and include all four corners.")
        photo = None
        if file is not None:
            try:
                photo = prepare_image(file.getvalue())
            except LetterError as exc:
                st.error(str(exc))
            else:
                st.image(photo, caption="Your letter preview", width=440)
        st.caption("Real photos go to the configured reading service for processing. Entendi does not save the photo to My Letters.")
        if st.button("Explain my letter", type="primary", disabled=photo is None):
            state["reading_job"] = {"photo": photo, "language": state.language, "id": uuid4().hex}
            st.rerun()
    with st.expander("Try a sample letter"):
        for sample, label in SAMPLES.items():
            st.button(label, key=f"sample_{sample}", on_click=start_letter, args=(sample,))


def understand() -> None:
    page_header("understand")
    if "reading_job" in st.session_state:
        _run_reading()
    if error := st.session_state.pop("letter_error", None):
        st.error(error)
    if current := st.session_state.get("current_letter"):
        st.button("Read another letter", on_click=start_letter)
        letter_result(current["notice"], current["id"], current=current)
    else:
        _letter_input()


def _speak(notice: Notice) -> None:
    sentence = " ".join((notice.explanation, *notice.actions_required, *notice.documents_to_bring))
    config = json.dumps({"text": sentence, "lang": LANGUAGES.get(notice.language, "en-IN")},
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
    st.download_button(label, data.make_calendar([(day, title, entry_id)]), file_name="entendi-deadline.ics",
                       mime="text/calendar", key=key, on_click="ignore")


def _translate(current: dict, language: str, simpler: bool = False) -> None:
    job = {key: current[key] for key in ("id", "sample", "sample_day")}
    job.update(language=language, transcription=current["notice"].transcription, simpler=simpler)
    st.session_state["reading_job"] = job
    st.rerun()


def _add_feedback(title: str, value: dict) -> None:
    data.add_entry(st.session_state.entendi_data, "feedback", title, json.dumps(value, ensure_ascii=False), today())
    st.success("Feedback saved in this session. It’s included if you download My data.")


def letter_result(notice: Notice, entry_id: str, *, current: dict | None = None) -> None:
    prefix = f"{'current' if current else 'saved'}_{entry_id}"
    title = f"{notice.issuer} · {notice.document_type}"
    if current and current.get("sample"):
        st.info("Fictional sample letter for demonstration.")
    if notice.needs_human_check:
        with st.container(border=True, key=f"confirm_{entry_id}"):
            st.markdown("**Please confirm with the official office**")
            for text in notice.unclear_parts or ["Some details or source quotes could not be verified."]:
                st.text(f"• {text}")
    else:
        markup(ui.badge_html("Read clearly", "quiet"))
    st.subheader("What this is")
    markup(f'<p class="letter-summary">{ui.esc(notice.explanation)}</p>')
    markup(f'<div class="letter-badges">{ui.badge_html(notice.issuer)}{ui.badge_html(notice.document_type)}</div>')
    _speak(notice)
    facts = [("Do by", notice.deadline.strftime("%d %b %Y") if notice.deadline else "No deadline found",
              data.days_left(notice.deadline, today()) if notice.deadline else "Confirm the date if you’re unsure."),
             ("Amount", notice.amount or "Not stated", "")]
    if notice.if_ignored:
        facts.append(("If ignored", notice.if_ignored, ""))
    for col, (label, value, footnote) in zip(st.columns(3, gap="small"), facts):
        with col:
            markup(ui.fact_html(label, value, footnote))

    st.subheader("What you need to do")
    _checklist(notice.actions_required, f"{prefix}_{notice.language}_actions", "No actions were stated.")
    st.subheader("Bring these")
    _checklist(notice.documents_to_bring, f"{prefix}_{notice.language}_documents", "No documents were stated.")
    st.subheader("Proof from your letter")
    original, explanation = st.columns(2, gap="medium")
    with original, st.container(border=True):
        st.markdown("**Your letter**")
        if current and current.get("photo"):
            st.image(current["photo"], width="stretch")
        else:
            st.caption("The original photo isn’t kept in My Letters.")
    with explanation, st.container(border=True):
        st.markdown("**Entendi’s explanation**")
        if not notice.quotes:
            st.caption("Source text isn’t retained in My Letters." if not current else "No readable excerpts were identified.")
        for index, excerpt in enumerate(notice.quotes, start=1):
            label = "✓ Found in letter" if excerpt.verified else "⚑ Couldn’t verify"
            with st.expander(f"Quote {index} · {label}"):
                st.text(excerpt.text)
        if notice.quotes:
            st.caption("Quotes are matched against the transcription. Check the original if anything looks wrong.")

    calendar, save, share = st.columns(3, gap="small")
    with calendar:
        if notice.deadline:
            _calendar_button(notice.deadline, title, entry_id, "Add to calendar", f"ics_{prefix}")
        else:
            st.button("Add to calendar", disabled=True, key=f"no_ics_{prefix}", help="No deadline was found in this letter.")
    with save:
        letter = find_entry(entry_id)
        if st.button("Saved to My Letters" if letter else "Save to My Letters", disabled=bool(letter),
                     key=f"save_{prefix}", type="primary"):
            data.add_entry(st.session_state.entendi_data, "letter", title, notice.saved_json(), today(), entry_id=entry_id)
            st.rerun()
    with share:
        summary = f"{title}\n{notice.explanation}"
        if notice.deadline:
            summary += f"\nDo by: {notice.deadline:%d %b %Y}"
        st.link_button("Share on WhatsApp", "https://wa.me/?text=" + quote(summary, safe=""),
                       help="Opens WhatsApp with the explanation so you can review it before sending.")
    if current:
        with st.expander("Explain in another language"):
            language = st.selectbox("Choose a language", list(LANGUAGES), index=list(LANGUAGES).index(notice.language),
                                    key=f"translate_{prefix}")
            if st.button("Explain in this language", disabled=language == notice.language, key=f"run_{prefix}"):
                _translate(current, language)
        if st.button("Use simpler words", key=f"simpler_{prefix}"):
            _translate(current, notice.language, simpler=True)
    with st.expander("Something looks wrong"):
        with st.form(f"report_{prefix}", clear_on_submit=True):
            issue = st.text_area("What looked wrong?", max_chars=500,
                                 help="Leave out names, reference numbers and other personal details.")
            if st.form_submit_button("Save report"):
                if issue.strip():
                    _add_feedback("Letter explanation issue", {"comment": issue.strip()})
                else:
                    st.warning("Describe what looked wrong before saving.")
    st.button("Check my benefits", key=f"to_benefits_{prefix}", on_click=go, args=("benefits",))


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
    st.caption("Saved letters keep only the explanation and facts. Photos, full transcriptions and source quotes are left out, including when you download My data.")
    if entry := find_entry(st.session_state.get("open_letter", "")):
        st.button("Back to My Letters", on_click=close_letter)
        letter_result(Notice.model_validate_json(entry["details"]), entry["id"])
        return
    status = st.selectbox("Status", ("All", "Open", "Done"), key="letter_filter")
    letters = [entry for entry in saved_entries("letter") if status == "All" or entry["done"] == (status == "Done")]
    if not letters:
        markup(ui.empty_html("No letters here yet", "Save a letter’s explanation to find it here later."))
        st.button("Understand a Letter", on_click=go, args=("understand",))
    for entry in letters:
        notice = Notice.model_validate_json(entry["details"])
        with st.container(border=True):
            st.subheader(notice.document_type)
            st.text(f"{notice.issuer} · Saved {date.fromisoformat(entry['date']):%d %b %Y}")
            chips = ui.badge_html("Done" if entry["done"] else "Open")
            if notice.deadline:
                chips += ui.badge_html(f"Due {notice.deadline:%d %b %Y}")
            markup(f'<div class="letter-badges">{chips}</div>')
            left, middle, right = st.columns(3)
            left.button("Open", key=f"open_{entry['id']}", on_click=open_letter, args=(entry["id"],))
            middle.button("Mark open" if entry["done"] else "Mark done", key=f"mark_{entry['id']}",
                          on_click=_set_done, args=(entry["id"], not entry["done"]))
            right.button("Delete", key=f"delete_{entry['id']}", on_click=_remove_letter, args=(entry["id"],))


def _set_done(entry_id: str, done: bool | str) -> None:
    if entry := find_entry(entry_id):
        entry["done"] = st.session_state[done] if isinstance(done, str) else done


def deadlines() -> None:
    page_header("deadlines")
    groups = data.deadline_groups(saved_entries(), today())
    events = [(day, entry["title"], entry["id"]) for group, pairs in groups.items() if group != "Done" for day, entry in pairs]
    st.download_button("Download all (.ics)", data.make_calendar(events), file_name="entendi-deadlines.ics",
                       mime="text/calendar", disabled=not events, on_click="ignore")
    for group, rows in groups.items():
        markup(ui.group_heading(group))
        if not rows:
            st.caption("No deadlines here.")
        for due, entry in rows:
            with st.container(border=True):
                key = entry["id"]
                left, middle, right = st.columns([1.55, 1, 1.25])
                with left:
                    label = data.days_left(due, today()) if not entry["done"] else f"Due {due:%d %b %Y}"
                    markup(ui.badge_html(label, "warm" if group == "Overdue" else ""))
                    if entry["category"] == "letter":
                        st.button(entry["title"], key=f"deadline_open_{key}", on_click=open_letter, args=(key,))
                    else:
                        st.text(entry["title"])
                with middle:
                    done_key = f"deadline_done_{key}"
                    st.checkbox("Done", value=entry["done"], key=done_key, on_change=_set_done, args=(key, done_key))
                with right:
                    _calendar_button(due, entry["title"], key, "Add to phone calendar", f"deadline_calendar_{key}")
    with st.expander("Add my own reminder"):
        with st.form("reminder", clear_on_submit=True):
            title = st.text_input("Reminder title", max_chars=120)
            due = st.date_input("Due date", value=today())
            if st.form_submit_button("Add reminder", type="primary"):
                if not title.strip():
                    st.warning("Enter a reminder title.")
                else:
                    data.add_entry(st.session_state.entendi_data, "reminder", title, "{}", due)
                    st.rerun()


def _selection(field: str, label: str, options: tuple[str, ...], profile: dict) -> str:
    existing = profile.get(field)
    return st.selectbox(label, options, index=options.index(existing) if existing in options else 0)


def _number(profile: dict, field: str, default: int, maximum: int) -> int:
    try:
        return max(0, min(int(profile.get(field, default)), maximum))
    except ValueError:
        return default


def benefits_check() -> None:
    page_header("benefits")
    st.info("This check uses fixed rules, not AI. It covers three central schemes in India. The office makes the final decision.")
    profile = st.session_state.entendi_data["profile"]
    unknown = ("Not sure", "Yes", "No")
    with st.form("eligibility"):
        first, second = st.columns(2)
        with first:
            age = st.number_input("Age", min_value=0, max_value=125, value=_number(profile, "age", 18, 125))
            income = st.number_input("Annual income (₹)", min_value=0, max_value=100_000_000,
                                     value=_number(profile, "income", 0, 100_000_000), step=1000)
            occupation = _selection("occupation", "Occupation",
                                    ("Select occupation", "Unorganised worker", "Salaried worker", "Student", "Retired", "Other"),
                                    profile)
        with second:
            state = _selection("state", "State or union territory", ("Select state", *benefits.STATES), profile)
            bpl = _selection("bpl", "Listed below the poverty line (BPL)?", unknown, profile)
            gender = _selection("gender", "Gender", ("Prefer not to say", "Woman", "Man", "Another gender"), profile)
        with st.expander("More details for pension checks"):
            widowed = _selection("widowed", "Are you widowed?", unknown, profile)
            monthly_income = _selection("monthly_income", "Usual monthly income",
                                        ("Not sure", "₹15,000 or less", "Above ₹15,000"), profile)
            excluded = _selection("pension_exclusion", "Covered by NPS, ESIC or EPFO, or pay income tax?", unknown, profile)
        submitted = st.form_submit_button("Check my benefits", type="primary")
        if submitted:
            if state == "Select state" or occupation == "Select occupation":
                st.warning("Choose a state or union territory and an occupation to run the check.")
            else:
                profile.update(age=str(age), state=state, income=str(income), occupation=occupation, bpl=bpl, gender=gender,
                               widowed=widowed, pension_exclusion=excluded, monthly_income=monthly_income)
    if not data.PROFILE_FIELDS <= profile.keys() or profile["state"] not in benefits.STATES:
        return
    try:
        schemes = benefits.check(profile)
    except ValueError:
        st.warning("Some saved answers are invalid. Check the form and submit it again.")
        return
    st.caption("A ‘Not likely’ result can also mean an answer is missing or uncertain. The PM-SYM rule uses monthly income.")
    for index, scheme in enumerate(schemes):
        with st.container(border=True):
            st.subheader(scheme.name)
            markup(ui.badge_html("Likely" if scheme.likely else "Not likely", "quiet"))
            st.caption(scheme.criteria)
            st.markdown("**Documents to bring**")
            _checklist(scheme.documents, f"scheme_{index}_{scheme.name[:30]}", "")
            st.text(scheme.office)
            st.link_button("Official scheme information", scheme.url)
            st.caption("The office makes the final decision.")


def help_about() -> None:
    page_header("help")
    st.subheader("How it works")
    markup(ui.steps_html())
    st.subheader("What Entendi can’t do")
    st.markdown("- It may misread a blurry photo. Confirm dates, amounts and next steps with the official office.\n"
                "- It doesn’t give legal advice or decide whether a letter is genuine.\n"
                "- Benefits Check follows fixed rules. The office makes the final decision.")
    st.subheader("Privacy")
    st.markdown("Entendi keeps the photo temporarily in your session so you can compare it. Real photos are sent to the "
                "configured reading service for processing. Saved letters and downloads omit the photo, full transcription "
                "and source quotes. My data can contain your explanations and benefits answers, so keep the download private.")
    st.subheader("Keep an offline copy")
    paragraphs = ["Entendi · Saved letters", "For important details, check your original letter or ask the official office."]
    for entry in saved_entries("letter"):
        notice = Notice.model_validate_json(entry["details"])
        lines = [entry["title"], notice.explanation]
        if notice.deadline:
            lines.append(f"Do by: {notice.deadline:%d %b %Y}")
        lines.extend(f"• {line}" for line in notice.actions_required)
        paragraphs.append("\n".join(lines))
    st.download_button("Download offline copy", "\n\n".join(paragraphs), file_name="entendi-letters.txt",
                       mime="text/plain", disabled=len(paragraphs) == 2, on_click="ignore")
    if len(paragraphs) == 2:
        st.caption("Save a letter first to download an offline copy.")
    st.subheader("Feedback")
    with st.form("feedback", clear_on_submit=True):
        rating = st.radio("Rating", (1, 2, 3, 4, 5), index=3, horizontal=True)
        comment = st.text_area("Comment", max_chars=500)
        if st.form_submit_button("Save feedback"):
            _add_feedback("Feedback", {"rating": rating, "comment": comment.strip()})
    st.caption("Built for EvoHacks 2.")


ROUTES = {
    "home": home, "understand": understand, "letters": my_letters, "deadlines": deadlines,
    "benefits": benefits_check, "help": help_about,
}


def render(page: str) -> None:
    ROUTES.get(page, home)()
