"""Conservative evidence checks used by the app and the benchmark."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re
import unicodedata

from country_profiles import region

_FULLWIDTH = str.maketrans("０１２３４５６７８９／．，＄￥", "0123456789/.,$¥")
_MONTHS = {}
for index, names in enumerate((
    "january jan janvier janvier enero ene januar",
    "february feb février fevrier febrero februar",
    "march mar mars marzo märz maerz",
    "april apr avril abril",
    "may mai mayo",
    "june jun juin junio juni",
    "july jul juillet julio juli",
    "august aug août aout agosto",
    "september sep sept septembre septiembre setiembre",
    "october oct octobre octubre oktober",
    "november nov novembre noviembre",
    "december dec décembre decembre diciembre dezember",
), 1):
    _MONTHS.update(dict.fromkeys(names.split(), index))

_YEAR = r"(?:19|20)[0-9]{2}"
_MONTH_NAMES = "|".join(re.escape(name) for name in sorted(_MONTHS, key=len, reverse=True))
_DATE = re.compile(
    rf"(?<![0-9])(?:(?P<cy>{_YEAR})年\s*(?P<cm>[0-9]{{1,2}})月\s*(?P<cd>[0-9]{{1,2}})日|"
    rf"(?P<iy>{_YEAR})-(?P<im>[0-9]{{1,2}})-(?P<id>[0-9]{{1,2}})|"
    rf"(?P<a>[0-9]{{1,2}})(?P<sep>[./-])(?P<b>[0-9]{{1,2}})(?P=sep)(?P<ny>{_YEAR})|"
    rf"(?P<td>[0-9]{{1,2}})\.?\s+(?:de\s+)?(?P<tm>{_MONTH_NAMES})\.?\s+(?:de\s+)?(?P<ty>{_YEAR}))"
    r"(?![0-9])", re.IGNORECASE,
)
_DMY = re.compile(r"\b(?:DD[/.-]MM[/.-]YYYY|day[/ -]month[/ -]year)\b", re.I)
_MDY = re.compile(r"\b(?:MM[/.-]DD[/.-]YYYY|month[/ -]day[/ -]year)\b", re.I)
_CURRENCY = r"(?:EUR|GBP|USD|JPY|CNY|RMB|KRW|PLN|€|£|\$|¥|円|元|₩|원|zł)"
_NUMBER = r"[0-9]+(?:[.,][0-9]+|[\u00a0\u202f ][0-9]{3}(?![0-9]))*"
_AMOUNT = re.compile(
    rf"(?<![A-Za-z0-9])(?:(?P<left>{_CURRENCY})\s*(?P<ln>{_NUMBER})|(?P<rn>{_NUMBER})\s*(?P<right>{_CURRENCY}))(?![A-Za-z0-9]|[.,][0-9])",
    re.IGNORECASE,
)
_CURRENCY_CODES = {
    "€": "EUR", "£": "GBP", "$": "DOLLAR", "¥": "YEN_YUAN", "円": "JPY", "元": "CNY",
    "RMB": "CNY", "₩": "KRW", "원": "KRW", "ZŁ": "PLN",
}


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).translate(_FULLWIDTH)


def compact(text: str) -> str:
    return " ".join(normalize(text).split())


def dates(text: str, *, context: str = "") -> tuple[set[date], bool]:
    parsed, ambiguous = set(), False
    hint = normalize(context or text)
    dmy, mdy = bool(_DMY.search(hint)), bool(_MDY.search(hint))
    for match in _DATE.finditer(normalize(text)):
        groups = match.groupdict()
        if groups["cy"]:
            values = groups["cy"], groups["cm"], groups["cd"]
        elif groups["iy"]:
            values = groups["iy"], groups["im"], groups["id"]
        elif groups["ty"]:
            month = _MONTHS.get(groups["tm"].casefold())
            if not month:
                continue
            values = groups["ty"], month, groups["td"]
        else:
            a, b = int(groups["a"]), int(groups["b"])
            if dmy != mdy:
                month, day = (b, a) if dmy else (a, b)
            elif groups["sep"] == "." or a > 12:
                month, day = b, a
            elif b > 12:
                month, day = a, b
            elif a == b:
                month, day = a, b
            else:
                ambiguous = ambiguous or (1 <= a <= 12 and 1 <= b <= 12)
                continue
            values = groups["ny"], month, day
        try:
            parsed.add(date(*map(int, values)))
        except ValueError:
            continue
    return parsed, ambiguous


def _decimal(raw: str) -> Decimal | None:
    value = re.sub(r"\s", "", raw)
    separators = {symbol for symbol in ".," if symbol in value}
    if len(separators) == 2:
        decimal = "." if value.rfind(".") > value.rfind(",") else ","
        thousands = "," if decimal == "." else "."
        if not re.fullmatch(rf"[0-9]{{1,3}}(?:{re.escape(thousands)}[0-9]{{3}})+{re.escape(decimal)}[0-9]{{1,2}}", value):
            return None
        value = value.replace(thousands, "").replace(decimal, ".")
    elif separators:
        sep = separators.pop()
        parts = value.split(sep)
        if len(parts) == 2 and len(parts[-1]) <= 2:
            value = ".".join(parts)
        elif len(parts[0]) <= 3 and all(len(part) == 3 for part in parts[1:]):
            value = "".join(parts)
        else:
            return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def amounts(text: str) -> set[tuple[str, Decimal]]:
    result = set()
    for match in _AMOUNT.finditer(normalize(text)):
        currency = (match["left"] or match["right"]).upper()
        value = _decimal(match["ln"] or match["rn"])
        if value is not None:
            result.add((_CURRENCY_CODES.get(currency, currency), value))
    return result


def amount_matches(source: set, proposed: set) -> bool:
    if len(source) != 1 or len(proposed) != 1:
        return False
    (a, x), (b, y) = next(iter(source)), next(iter(proposed))
    return x == y and (a == b or {a, b} in ({"YEN_YUAN", "JPY"}, {"YEN_YUAN", "CNY"}))


_ISSUE = re.compile(
    r"^\s*(?:issued(?: on)?|date of issue|emisi[oó]n|fecha de emisi[oó]n|[ée]mis le|date d.[ée]mission|"
    r"ausgestellt am|ausstellungsdatum|签发日期|発行日)\s*[:：]", re.IGNORECASE,
)


def check_deadline(source: str, evidence: str, proposed: date | None, *, country: str = "") -> str:
    if _ISSUE.search(evidence):
        return "mismatch" if proposed else "missing"
    found, ambiguous = dates(evidence, context=source)
    if country and region(country).order != "DMY" and re.search(r"\b[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}\b", normalize(evidence)):
        return "ambiguous"  # Dotted notation conflicts with the selected regional convention.
    if ambiguous:
        return "ambiguous"
    if not proposed:
        return "missing"
    return "verified" if compact(evidence) and compact(evidence) in compact(source) and found == {proposed} else "mismatch"


def check_amount(source: str, evidence: str, proposed: str | None) -> str:
    if not proposed:
        return "missing"
    return ("verified" if compact(evidence) and compact(evidence) in compact(source)
            and amount_matches(amounts(evidence), amounts(proposed)) else "mismatch")


_PII = re.compile(
    r"(?P<email>[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})"
    r"|(?P<iban>\b[A-Z]{2}[0-9]{2}(?:[ \u00a0]?[A-Z0-9]){11,30}\b)"
    r"|(?P<ni>\b[A-Z]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[A-D]\b)"
    r"|passport(?:[ \t]+(?:no\.?|number))?[ \t]*[:#][ \t]*(?P<passport>[A-Z0-9]{6,12})\b"
    r"|(?P<phone>(?<![\w+])\+(?:\([0-9]{1,4}\)|[0-9]{1,4})(?:[ ().-]?[0-9]){7,14}(?![0-9])"
    r"|(?<![0-9])\([0-9]{2,4}\)[ .-]?[0-9]{3,4}[ .-]?[0-9]{3,4}(?![0-9])"
    r"|(?<=[ :])0[0-9]{2,4}[ .-][0-9]{3,4}[ .-][0-9]{3,4}(?![0-9]))"
    r"|(?P<digits>(?<![\w])(?:[0-9][ -]?){8,}[0-9](?![\w]))",
    re.IGNORECASE,
)


_COUNTRY_PII = {
    "United Kingdom": r"(?P<id>\b[A-Z]{2}[ \t]?[0-9]{2}[ \t]?[0-9]{2}[ \t]?[0-9]{2}[ \t]?[A-D]\b)",
    "Japan": r"(?:My Number|個人番号|マイナンバー)[ \t:：]*(?P<id>[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4})\b",
    "Spain": r"\b(?P<id>(?:[0-9]{8}|[XYZ][0-9]{7})[ -]?[A-Z])\b",
}
_PHONE = {
    "United Kingdom": r"\b(?P<id>0[0-9]{4}[ \t][0-9]{6})\b",
    "Japan": r"\b(?P<id>0[0-9]{1,3}-[0-9]{2,4}-[0-9]{4})\b",
    "France": r"\b(?P<id>0[1-9](?:[ .-][0-9]{2}){4})\b",
}
_BANK = {
    "United Kingdom": r"sort[ -]code[ \t:#]*(?P<id>[0-9]{2}-[0-9]{2}-[0-9]{2})\b",
    "Japan": r"(?:口座番号|account number)[ \t:：]*(?P<id>[0-9]{7})\b",
}


def display_amount(text: str, country: str) -> str:
    """Localize separator style without converting or guessing the currency."""
    rules = region(country)
    matches = amounts(text)
    if not rules.decimal or len(matches) != 1:
        return text
    currency, amount = next(iter(matches))
    if currency != rules.currency:
        return text
    symbol = {"EUR": "€", "GBP": "£", "USD": "$", "JPY": "¥", "CNY": "¥", "KRW": "₩", "PLN": "zł"}.get(currency, currency + " ")
    digits = f"{amount:,.0f}" if currency in {"JPY", "KRW"} and amount == amount.to_integral_value() else f"{amount:,.2f}"
    if rules.decimal == ",":
        return digits.translate(str.maketrans({",": "\u202f", ".": ","})) + " " + symbol.strip()
    return symbol + digits


def redact(text: str, *, country: str = "") -> str:
    def mask(value: str) -> str:
        significant = [index for index, char in enumerate(value) if char.isalnum()]
        end = set(significant[-4:])
        return "".join(char if index in end or not char.isalnum() else "•" for index, char in enumerate(value))

    for patterns in (_COUNTRY_PII, _PHONE, _BANK):
        if pattern := patterns.get(country):
            normalized = text.translate(_FULLWIDTH)
            for match in reversed(list(re.finditer(pattern, normalized, re.IGNORECASE))):
                start, end = match.span("id")
                text = text[:start] + mask(normalized[start:end]) + text[end:]
    normalized = text.translate(_FULLWIDTH)
    replacements = list(_PII.finditer(normalized))
    for match in reversed(replacements):
        # Match normalized digits but preserve every unrelated source character.
        span = match.span("passport") if match["passport"] else match.span()
        text = text[:span[0]] + mask(normalized[span[0]:span[1]]) + text[span[1]:]
    return text


def roundtrip_status(reference: str, backward: str) -> str:
    """Conservative drift signal. Paraphrases can trigger review."""
    first_dates, first_ambiguous = dates(reference)
    last_dates, last_ambiguous = dates(backward)
    first_amounts, last_amounts = amounts(reference), amounts(backward)
    if first_ambiguous or last_ambiguous or first_dates != last_dates:
        return "review"
    if first_amounts != last_amounts and not amount_matches(first_amounts, last_amounts):
        return "review"
    first, last = (set(re.findall(r"[a-z0-9]+", value.casefold())) for value in (reference, backward))
    if not first or not last:
        return "unavailable"
    negation = {"not", "never", "no", "mustn't", "cannot", "don't"}
    if bool(first & negation) != bool(last & negation):
        return "review"
    return "passed" if len(first & last) / len(first | last) >= .42 else "review"
