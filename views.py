"""Workspace pages and their shared display and data helpers."""
import csv
from datetime import date
from io import StringIO
import json
from uuid import uuid4

import streamlit as st

import ui

PAGES = {
    "home": ("Home", ""),
    "dashboard": ("My Dashboard", "See what is open and what is coming up."),
    "workspace": ("My Workspace", "Set up your profile, add items, and export your work."),
    "updates": ("Updates & Alerts", "See recent changes and record an update."),
    "review": ("File Review", "Attach a file and record what you want to review."),
    "ask": ("Voice Notes", "Record your voice or type a note."),
    "calendar": ("Calendar", "Plan your tasks and see when they are due."),
    "compare": ("Compare Items", "Put the options side by side."),
    "journal": ("Journal", "Keep a dated record of your work."),
    "plan": ("Planning", "Capture a goal, its scope, and the next steps."),
    "resources": ("Resources", "Keep track of references and supporting material."),
    "workflow": ("Workflows", "Write down a process you want to repeat."),
    "issue": ("Issue Reports", "Describe a problem and record what you observed."),
    "guides": ("Guides & Offline", "Export your records and find saved notes."),
    "lab": ("Comparison Lab", "Place two drafts side by side and record your observations."),
    "about": ("About & Feedback", "Learn how the workspace works and leave feedback."),
}
TOOLS = ("updates", "review", "ask", "calendar", "plan", "compare", "journal", "resources", "workflow")
FORMS = {
    "plan": (("Goal *", None), ("Category", ("Personal", "Study", "Project")), ("Owner", None),
             ("Priority", ("Normal", "High", "Low")), ("Time frame", ("This week", "This month", "Later")),
             ("Status", ("Planned", "In progress", "Done")), ("Next steps", "long")),
    "resources": (("Resource title *", None), ("Category", ("Reference", "Tool", "Document")), ("Source", None),
                  ("Format", ("Link", "File", "Other")), ("Link or location", None), ("Notes", "long")),
    "workflow": (("Workflow title *", None), ("Category", ("Personal", "Study", "Project")),
                 ("Used for", ("One-time", "Weekly", "As needed")), ("Owner", None), ("Steps", "long")),
    "issue": (("Issue title *", None), ("Area", None), ("Context", None), ("What happened?", "long"),
              ("Affected areas", ["Interface", "Data", "Workflow"]), ("Priority", ("Normal", "High", "Low"))),
    "manual": (("Update title *", None), ("Category", ("General", "Milestone", "Alert")), ("Related item", None),
               ("Status", ("Open", "In progress", "Done")), ("Source", None), ("Details", "long")),
}
RECORD_FIELDS = {"id", "category", "title", "details", "date", "done"}


def new_workspace() -> dict:
    return {"profile": {}, "records": []}


def read_workspace(raw: bytes) -> dict:
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("profile"), dict) or not isinstance(data.get("records"), list):
        raise ValueError("Invalid workspace")
    profile = data["profile"]
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in profile.items()):
        raise ValueError("Invalid profile")
    ids = set()
    for record in data["records"]:
        if (not isinstance(record, dict) or set(record) != RECORD_FIELDS
                or any(not isinstance(record[key], str) for key in RECORD_FIELDS - {"done"})
                or not isinstance(record["done"], bool) or not record["id"] or record["id"] in ids):
            raise ValueError("Invalid record")
        date.fromisoformat(record["date"])
        ids.add(record["id"])
    return data


def records(category=None) -> list:
    items = st.session_state.workspace["records"]
    return items if category is None else [item for item in items if item["category"] == category]


def save(category: str, title: str, details: str = "", due: date | None = None) -> bool:
    if not title.strip():
        st.error("Enter a title.")
        return False
    records().insert(0, {"id": uuid4().hex, "category": category, "title": title.strip(),
                         "details": details.strip(), "date": (due or date.today()).isoformat(), "done": False})
    st.success("Saved to your workspace.")
    return True


def go(page: str) -> None:
    st.session_state.page = page


def markup(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


def heading(title: str) -> None:
    markup(ui.heading(title))


def empty(title: str, detail: str) -> None:
    markup(ui.empty_html(title, detail))


def header(page: str) -> None:
    title, subtitle = PAGES[page]
    markup(ui.page_header(page, title, subtitle, "Your workspace" if page == "dashboard" else title))


def card_grid(prefix: str, tools=TOOLS) -> None:
    for offset in range(0, len(tools), 3):
        for col, page in zip(st.columns(3, gap="medium"), tools[offset:offset + 3]):
            with col, st.container(key=f"fcard_{prefix}{page}"):
                markup(ui.feature_card_html(page, *PAGES[page]))
                st.button("Open  ›", key=f"open_{prefix}{page}", on_click=go, args=(page,))


def home() -> None:
    markup(ui.hero_html())
    _, dashboard_button, setup_button, _ = st.columns([2, 1.2, 1.2, 2])
    dashboard_button.button("Open my dashboard", on_click=go, args=("dashboard",), type="primary")
    setup_button.button("Set up my workspace", on_click=go, args=("workspace",))
    markup(ui.steps_html())
    heading("Workspace tools")
    card_grid("h_")


def record_rows(items: list, limit: int = 6) -> None:
    for item in items[:limit]:
        markup(ui.record_html(item["title"], item["date"], item["category"].title()))


def finish_task(task_id: str, widget_key: str) -> None:
    for item in records("task"):
        if item["id"] == task_id:
            item["done"] = st.session_state[widget_key]
            return


def task_list(items: list, prefix: str) -> None:
    for item in items:
        key = f"{prefix}_{item['id']}"
        st.checkbox(f"{item['date']} · {item['title']}", value=item["done"], key=key,
                    on_change=finish_task, args=(item["id"], key))


def dashboard() -> None:
    header("dashboard")
    today = date.today().isoformat()
    pending = sorted((item for item in records("task") if not item["done"]), key=lambda item: item["date"])
    recent = [item for item in records() if item["category"] not in {"task", "item", "feedback"}]
    counts = ((len(records("item")), "Active items"),
              (sum(item["date"] <= today for item in pending), "Tasks due now"), (len(recent), "Saved records"))
    for index, (col, (count, label)) in enumerate(zip(st.columns(3, gap="medium"), counts), 1):
        with col:
            markup(ui.stat_html(count, label, delay=index / 10))
    heading("Updates")
    if records("update"):
        record_rows(records("update"), 2)
    else:
        empty("No updates yet", "Updates you record will appear here.")
    st.button("Open updates", on_click=go, args=("updates",))
    heading("My items")
    if not records("item"):
        empty("No items yet", "Add your first item to the workspace.")
        st.button("Add an item", on_click=go, args=("workspace",))
    for item in records("item"):
        markup(ui.progress_html(item["title"], "Active", 0, item["details"]))
    heading("Coming up")
    if not pending:
        empty("Nothing due", "Add a task to put it on your calendar.")
        st.button("Open calendar", on_click=go, args=("calendar",))
    task_list(pending[:6], "dashboard")
    heading("Recent records")
    if not recent:
        empty("No records yet", "Use a tool to save your first record.")
    record_rows(recent, 3)
    heading("Quick tools")
    card_grid("d_", TOOLS[:3])


def workspace() -> None:
    header("workspace")
    profile = st.session_state.workspace["profile"]
    overview, details, items, export = st.tabs(["1. Overview", "2. My profile", "3. My items", "4. Keep my data"])
    with overview:
        st.markdown("Give your workspace a name so you can identify it later.")
        with st.form("workspace_name"):
            name = st.text_input("Workspace name", value=profile.get("Workspace name", ""))
            if st.form_submit_button("Save workspace", type="primary"):
                profile["Workspace name"] = name.strip()
                st.success("Workspace updated.")
    with details, st.form("profile"):
        fields = {"Display name": st.text_input("Display name", value=profile.get("Display name", ""))}
        for pair in (("Country", "Region"), ("Role", "Organization"), ("Time zone", "Website")):
            for column, label in zip(st.columns(2), pair):
                fields[label] = column.text_input(label, value=profile.get(label, ""))
        if st.form_submit_button("Save profile", type="primary"):
            profile.update(fields)
            st.success("Profile saved.")
    with items:
        st.markdown("Add the items you want to keep in view.")
        with st.form("item", clear_on_submit=True):
            left, right = st.columns(2)
            title = left.text_input("Item name *")
            created = right.date_input("Start date")
            left, right = st.columns(2)
            category = left.text_input("Category")
            priority = right.number_input("Priority", min_value=1, max_value=5, value=3)
            if st.form_submit_button("Add item", type="primary"):
                save("item", title, f"{category or 'General'} · Priority {priority}", created)
        if not records("item"):
            empty("No items yet", "Add your first item above.")
        for item in records("item"):
            markup(ui.progress_html(item["title"], "Active", 0, item["details"]))
    with export:
        st.markdown("Export your workspace to save a copy. You can import it from the sidebar.")
        st.download_button("Download workspace file", json.dumps(st.session_state.workspace, indent=2),
                           file_name="entendi_workspace.json", mime="application/json")
        st.caption("The file includes your profile and saved records.")
        st.divider()
        clear = st.checkbox("Clear everything saved in this session")
        if st.button("Clear workspace data", disabled=not clear):
            st.session_state.workspace = new_workspace()
            st.rerun()


def feature_form(page: str) -> None:
    left, right = st.columns([1.8, 1], gap="large")
    with right, st.container(key=f"aside_{page}"):
        markup(ui.aside_html())
    with left, st.form(f"form_{page}"):
        values = {}
        for label, kind in FORMS[page]:
            if kind == "long":
                values[label] = st.text_area(label, height=100)
            elif isinstance(kind, tuple):
                values[label] = st.selectbox(label, kind)
            elif isinstance(kind, list):
                values[label] = ", ".join(st.multiselect(label, kind))
            else:
                values[label] = st.text_input(label)
        if st.form_submit_button("Save record", type="primary"):
            title = values.pop(next(iter(values)))
            save("update" if page == "manual" else page, title,
                 "\n".join(f"{label}: {value}" for label, value in values.items() if value))


def updates() -> None:
    header("updates")
    items = records("update")
    if items:
        latest = items[0]
        markup(f'<div class="wx-hero"><div class="wx-place">Latest update</div>'
               f'<div class="wx-temp">{ui.esc(latest["title"])}</div>'
               f'<div class="wx-desc">{ui.esc(latest["date"])}</div></div>')
        heading("Recent updates")
        record_rows(items)
    else:
        empty("No updates yet", "Add an update to see it here and on your dashboard.")
    with st.expander("Record an update manually", expanded=not items):
        feature_form("manual")


def review() -> None:
    header("review")
    markup(ui.badge_html("1 · Add a file for review", "sky"))
    with st.form("review_intake"):
        title = st.text_input("Review title *")
        focus = st.multiselect("What should be checked?", ["Content", "Structure", "Presentation", "Other"])
        note = st.text_area("Review notes", height=90)
        upload = st.file_uploader("File (optional)", type=["pdf", "txt", "png", "jpg", "jpeg", "webp"])
        st.caption("The record saves the filename and your notes.")
        status = st.selectbox("Status", ("Pending", "Reviewed"))
        if st.form_submit_button("Save review", type="primary"):
            filename = f" · {upload.name}" if upload else ""
            save("review", title, f"{status}{filename}\n{', '.join(focus)}\n{note}")
    record_rows(records("review"))


def voice_notes() -> None:
    header("ask")
    audio = st.audio_input("Tap to record, tap again to stop")
    if audio:
        st.audio(audio.getvalue(), format=audio.type)
    st.caption("Playback is available during this session. You can save a written note below.")
    note = st.text_area("Your note", height=110)
    if st.button("Save note", type="primary"):
        save("note", note.splitlines()[0][:70] if note.strip() else "", note)
    record_rows(records("note"))


def calendar() -> None:
    header("calendar")
    heading("My schedule")
    if not records("task"):
        empty("No dates yet", "Add a task below.")
    with st.expander("Add a task or schedule a reminder", expanded=not records("task")):
        with st.form("calendar_form", clear_on_submit=True):
            title = st.text_input("Task name *")
            related = st.selectbox("Related item", ["General"] + [item["title"] for item in records("item")])
            left, right = st.columns(2)
            due = left.date_input("Due date")
            priority = right.selectbox("Priority", ("Normal", "High", "Low"))
            if st.form_submit_button("Add to calendar", type="primary"):
                save("task", title, f"{related} · {priority}", due)
    heading("My tasks")
    today = date.today().isoformat()
    tasks = sorted(records("task"), key=lambda item: item["date"])
    if not tasks:
        empty("No tasks yet", "Add a task to choose what happens next.")
    for label, subset in (
        ("Overdue", [item for item in tasks if not item["done"] and item["date"] < today]),
        ("Today and upcoming", [item for item in tasks if not item["done"] and item["date"] >= today]),
    ):
        if subset:
            markup(ui.group_heading(label))
            task_list(subset, "calendar")
    finished = [item for item in tasks if item["done"]]
    if finished:
        with st.expander(f"Finished tasks ({len(finished)})"):
            task_list(finished, "calendar")
    with st.expander("Add my own task"):
        with st.form("quick_task", clear_on_submit=True):
            title = st.text_input("What needs to be done? *")
            left, right = st.columns(2)
            when = left.date_input("Due date")
            note = right.text_input("Note")
            if st.form_submit_button("Add task") and save("task", title, note, when):
                st.rerun()


def compare() -> None:
    header("compare")
    references, mine, table = st.tabs(["References", "My items", "Compare items"])
    with references, st.form("comparison_reference"):
        left, right = st.columns(2)
        title = left.text_input("Reference name *")
        link = right.text_input("Link or reference")
        if st.form_submit_button("Save reference", type="primary"):
            save("reference", title, link)
        record_rows(records("reference"))
    with mine:
        with st.form("comparison_item", clear_on_submit=True):
            left, right = st.columns(2)
            title = left.text_input("Item name *")
            context = right.text_input("Category")
            left, center, right = st.columns(3)
            rating = left.number_input("Rating", min_value=0, max_value=10, value=0)
            date_added = center.date_input("Date")
            note = right.text_input("Note")
            if st.form_submit_button("Save item", type="primary"):
                save("comparison", title, f"{context} · Rating {rating} · {note}", date_added)
        if not records("comparison"):
            empty("No items saved", "Enter the items you want to compare.")
        record_rows(records("comparison"))
    with table:
        st.markdown("Enter the details for each option.")
        draft = st.data_editor([{"Item": "", "Score": 0, "Notes": ""} for _ in range(3)],
                               num_rows="dynamic", key="comparison_table", hide_index=True)
        items = [item for item in draft if item["Item"]]
        if items:
            st.dataframe(items, hide_index=True)
        else:
            st.caption("Enter an item to see it in the table.")
    with st.expander("Saved comparison references"):
        record_rows(records("reference"))


def journal() -> None:
    header("journal")
    with st.expander("Add a journal entry", expanded=not records("journal")):
        with st.form("journal", clear_on_submit=True):
            left, center, right = st.columns(3)
            entered = left.date_input("Date")
            category = center.selectbox("Type", ("Note", "Milestone", "Reflection"))
            title = right.text_input("Title *")
            note = st.text_area("Notes", height=90, max_chars=600)
            context = st.text_input("Context (optional)")
            left, center, right = st.columns(3)
            topic = left.text_input("Topic")
            time_spent = center.number_input("Minutes", min_value=0, value=0)
            mood = right.selectbox("Priority", ("Normal", "High", "Low"))
            upload = st.file_uploader("Attachment (optional)", type=["txt", "jpg", "png", "pdf"])
            if st.form_submit_button("Save entry", type="primary"):
                attached = f" · {upload.name}" if upload else ""
                save("journal", title, f"{category} · {context} · {topic} · {time_spent} min · {mood}{attached}\n{note}", entered)
    heading("My journal")
    items = records("journal")
    query = st.selectbox("Show", ["All entries"] + sorted({item["title"] for item in items}))
    if not items:
        empty("Nothing here yet", "Add a journal entry above.")
    for item in items:
        if query in ("All entries", item["title"]):
            entered = date.fromisoformat(item["date"])
            markup(ui.journal_item_html(str(entered.day), entered.strftime("%b %Y"), "Entry",
                                       item["title"], item["details"], ""))
    if items:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(("Date", "Title", "Details"))
        for item in items:
            cells = (item["date"], item["title"], item["details"])
            writer.writerow(["'" + cell if cell.lstrip().startswith(("=", "+", "-", "@")) else cell for cell in cells])
        st.download_button("Download journal (CSV)", buffer.getvalue(), file_name="entendi_journal.csv", mime="text/csv")


def guides() -> None:
    header("guides")
    heading("Take Entendi with you")
    st.markdown("Download a text copy of your saved records to read offline.")
    lines = [f"{item['date']} · {item['title']}\n{item['details']}" for item in records()]
    st.download_button("Download offline copy", "\n\n".join(lines), file_name="entendi_notes.txt")
    st.caption(f"{len(lines)} saved records.")
    heading("Key guides")
    for title, text in (
        ("Set up your workspace", "Open My Workspace to add a name and your first item."),
        ("Track your tasks", "Open Calendar to add tasks with due dates and mark them complete."),
        ("Save your data", "Export your workspace file from the sidebar to import it later."),
    ):
        with st.expander(title):
            st.write(text)
    heading("My saved records")
    if not records():
        empty("No saved records", "Records from workspace tools appear here.")
    for item in records():
        with st.expander(f"{item['title']} · {item['date']}"):
            st.text(item["details"])
    with st.expander("Tips for weak internet"):
        st.write("Turn on Low-data mode to disable the web font and animations.")


def lab() -> None:
    header("lab")
    sample = st.selectbox("Comparison type", ("Drafts", "Options", "Notes"))
    question = st.text_area("What are you comparing?")
    left, right = st.columns(2)
    first = left.text_area("Version A")
    second = right.text_area("Version B")
    if st.button("Run comparison", type="primary"):
        st.session_state.lab_result = sample, question, first, second
    if "lab_result" in st.session_state:
        title, prompt, a, b = st.session_state.lab_result
        st.subheader(prompt.strip() or title)
        for col, label, content in zip(st.columns(2), ("Version A", "Version B"), (a, b)):
            with col, st.container(border=True):
                st.markdown(f"**{label}**")
                st.text(content)
        st.subheader("Comparison notes")
        notes = st.text_area("What changed?")
        if st.button("Save to comparison log"):
            save("lab", prompt or title, f"A: {a}\nB: {b}\nNotes: {notes}")
    st.subheader(f"Comparison log ({len(records('lab'))} saved entries)")
    record_rows(records("lab"))


def about() -> None:
    header("about")
    st.markdown("Entendi keeps your workspace records in your current session. Use the export controls to keep a local copy.")
    with st.form("feedback"):
        rating = st.radio("Your rating", [1, 2, 3, 4, 5], index=3, horizontal=True)
        comment = st.text_area("Feedback")
        if st.form_submit_button("Save feedback"):
            save("feedback", f"Rating {rating}/5", comment)
    st.subheader("Feedback saved this session")
    if not records("feedback"):
        st.caption("No feedback yet.")
    record_rows(records("feedback"))


ROUTES = {
    "home": home, "dashboard": dashboard, "workspace": workspace, "updates": updates,
    "review": review, "ask": voice_notes, "calendar": calendar, "compare": compare,
    "journal": journal, "guides": guides, "lab": lab, "about": about,
}


def render(page: str) -> None:
    if page in ROUTES:
        ROUTES[page]()
    else:
        header(page)
        feature_form(page)
