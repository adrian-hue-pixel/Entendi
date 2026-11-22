"""Session data files and calendar exports."""

from datetime import date, datetime, timedelta, timezone
import json
from uuid import uuid4

from letter_reader import Notice

RECORD_FIELDS = {"id", "category", "title", "details", "date", "done"}
PROFILE_FIELDS = {
    "age", "state", "income", "occupation", "bpl", "gender", "widowed", "pension_exclusion", "monthly_income",
}


def new_data() -> dict:
    # Keep the existing file format so My data can open older Entendi exports.
    return {"profile": {}, "records": []}


def read_data(raw: bytes) -> dict:
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Data file too large.")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("profile"), dict) or not isinstance(data.get("records"), list):
        raise ValueError("Invalid data file.")
    profile = data["profile"]
    if any(not isinstance(value, str) for value in profile.values()):
        raise ValueError("Invalid answers.")
    result = new_data()
    result["profile"] = {key: value for key, value in profile.items() if key in PROFILE_FIELDS and len(value) < 100}
    ids = set()
    for record in data["records"]:
        if (not isinstance(record, dict) or set(record) != RECORD_FIELDS
                or any(not isinstance(record[key], str) for key in RECORD_FIELDS - {"done"})
                or not isinstance(record["done"], bool) or not record["id"] or record["id"] in ids
                or len(record["id"]) > 100 or len(record["title"]) > 400):
            raise ValueError("Invalid data entry.")
        ids.add(record["id"])
        date.fromisoformat(record["date"])
        if record["category"] not in {"letter", "reminder", "feedback"}:
            continue
        if record["category"] == "letter":
            notice = Notice.model_validate_json(record["details"])
            record = {**record, "details": notice.saved_json()}
        result["records"].append(record)
    return result


def add_entry(data: dict, category: str, title: str, details: str, day: date, *, entry_id: str | None = None) -> dict:
    entry = {"id": entry_id or uuid4().hex, "category": category, "title": title.strip(), "details": details,
             "date": day.isoformat(), "done": False}
    data["records"].insert(0, entry)
    return entry


def deadline_for(entry: dict) -> date | None:
    if entry["category"] == "letter":
        return Notice.model_validate_json(entry["details"]).deadline
    return date.fromisoformat(entry["date"]) if entry["category"] == "reminder" else None


def days_left(deadline: date, today: date) -> str:
    days = (deadline - today).days
    if days == 0:
        return "Due today"
    if days < 0:
        return f"{abs(days)} {'day' if days == -1 else 'days'} overdue"
    return f"{days} {'day' if days == 1 else 'days'} left"


def deadline_groups(entries: list[dict], today: date) -> dict[str, list]:
    groups = {"Overdue": [], "This week": [], "Later": [], "Done": []}
    upcoming = [(day, entry) for entry in entries if (day := deadline_for(entry))]
    for day, entry in sorted(upcoming, key=lambda pair: pair[0]):
        days = (day - today).days
        group = "Done" if entry["done"] else "Overdue" if days < 0 else "This week" if days < 7 else "Later"
        groups[group].append((day, entry))
    return groups


def _ics_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n")
            .replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;"))


def _ics_fold(line: str) -> str:
    chunks = []
    current = ""
    for character in line:
        if len((current + character).encode("utf-8")) > 75:
            chunks.append(current)
            current = " "
        current += character
    chunks.append(current)
    return "\r\n".join(chunks)


def make_calendar(events: list[tuple[date, str, str]]) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Entendi//Letter deadlines//EN", "CALSCALE:GREGORIAN"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for day, title, event_id in events:
        lines.extend(("BEGIN:VEVENT", f"UID:{_ics_escape(event_id)}@entendi", f"DTSTAMP:{stamp}",
                      f"DTSTART;VALUE=DATE:{day:%Y%m%d}", f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}",
                      f"SUMMARY:{_ics_escape(title)}", "END:VEVENT"))
    return ("\r\n".join(map(_ics_fold, [*lines, "END:VCALENDAR"])) + "\r\n").encode()
