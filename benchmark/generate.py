"""Generate reproducible, fictional notices and independently assigned labels."""

import json
from pathlib import Path
import random

OUT = Path(__file__).resolve().parent / "data" / "notices.jsonl"
FIRST = ("en", "es", "fr", "de", "zh", "ja")
EXTRA = ("hi", "ta", "th")
LANG = {
    "en": ("Water Office", "School Office", "Community Centre", "Notice {n}", "Issued: {issue}.", "Payment deadline: {value}.", "Amount due: {value}.", "No deadline is stated.", "No payment is due.", "Office reference: SYN-{n}."),
    "es": ("Oficina del Agua", "Secretaría Escolar", "Centro Comunitario", "Aviso {n}", "Emisión: {issue}.", "Fecha límite de pago: {value}.", "Importe a pagar: {value}.", "No se indica la fecha límite.", "No se solicita ningún pago.", "Referencia de la oficina: SYN-{n}."),
    "fr": ("Service des Eaux", "Bureau Scolaire", "Centre Municipal", "Avis {n}", "Émis le : {issue}.", "Date limite de paiement : {value}.", "Montant dû : {value}.", "Aucune échéance indiquée.", "Aucun paiement demandé.", "Référence du service : SYN-{n}."),
    "de": ("Wasseramt", "Schulbüro", "Gemeindezentrum", "Bescheid {n}", "Ausgestellt am: {issue}.", "Zahlungsfrist: {value}.", "Zahlbetrag: {value}.", "Keine Frist angegeben.", "Keine Zahlung erforderlich.", "Aktenzeichen: SYN-{n}."),
    "zh": ("供水服务处", "学校办公室", "社区服务中心", "通知 {n}", "签发日期：{issue}。", "缴费截止日期：{value}。", "应缴金额：{value}。", "未注明截止日期。", "无需支付。", "通知编号：SYN-{n}。"),
    "ja": ("水道サービス窓口", "学校事務室", "地域サービスセンター", "通知 {n}", "発行日：{issue}。", "お支払期限：{value}。", "お支払金額：{value}。", "期限の記載はありません。", "お支払いは不要です。", "通知番号：SYN-{n}。"),
    "hi": ("जल सेवा कार्यालय", "विद्यालय कार्यालय", "सामुदायिक केंद्र", "सूचना {n}", "जारी करने की तारीख: {issue}।", "भुगतान की अंतिम तारीख: {value}।", "देय राशि: {value}।", "अंतिम तारीख नहीं दी गई है।", "भुगतान की आवश्यकता नहीं है।", "कार्यालय संदर्भ: SYN-{n}।"),
    "ta": ("குடிநீர் சேவை அலுவலகம்", "பள்ளி அலுவலகம்", "சமூக மையம்", "அறிவிப்பு {n}", "வெளியிட்ட நாள்: {issue}.", "கட்டணம் செலுத்த வேண்டிய நாள்: {value}.", "செலுத்த வேண்டிய தொகை: {value}.", "கடைசித் தேதி குறிப்பிடப்படவில்லை.", "கட்டணம் செலுத்தத் தேவையில்லை.", "அலுவலகக் குறிப்பு: SYN-{n}."),
    "th": ("สำนักงานประปา", "สำนักงานโรงเรียน", "ศูนย์บริการชุมชน", "ประกาศ {n}", "วันที่ออกเอกสาร: {issue}", "กำหนดชำระ: {value}", "ยอดที่ต้องชำระ: {value}", "ไม่ได้ระบุวันครบกำหนด", "ไม่ต้องชำระ", "รหัสเอกสาร SYN-{n}"),
}
MONTHS = {
    "en": ("March", "April", "June", "October"), "es": ("marzo", "abril", "junio", "octubre"),
    "fr": ("mars", "avril", "juin", "octobre"), "de": ("März", "April", "Juni", "Oktober"),
}
CURRENCIES = {"en": ("GBP", "£"), "es": ("EUR", "€"), "fr": ("EUR", "€"), "de": ("EUR", "€"),
              "zh": ("CNY", "元"), "ja": ("JPY", "円"), "hi": ("GBP", "£"),
              "ta": ("GBP", "£"), "th": ("GBP", "£")}
WIDTH = str.maketrans("0123456789/.,", "０１２３４５６７８９／．，")


def written_date(lang, i, y, m, d):
    if i % 6 == 5:
        return f"{y}-{m:02}-{d:02}"
    if lang in {"zh", "ja"}:
        text = f"{y}年{m}月{d}日"
        return text.translate(WIDTH) if i % 2 else text
    if lang in MONTHS and i % 2 == 0:
        month = MONTHS[lang][(3, 4, 6, 10).index(m)]
        if lang == "es":
            return f"{d} de {month} de {y}"
        return f"{d}{'.' if lang == 'de' else ''} {month} {y}"
    if lang == "de":
        return f"{d:02}.{m:02}.{y}"
    if d > 12:
        return f"{d:02}/{m:02}/{y}"
    return f"{y}-{m:02}-{d:02}"


def written_amount(lang, units, cents, style):
    code, symbol = CURRENCIES[lang]
    if code in {"CNY", "JPY"}:
        text = f"{units:,}{symbol}"
        return text.translate(WIDTH) if style % 2 else text
    if lang in {"fr", "es", "de"}:
        separator = "\u202f" if lang == "fr" else "."
        return f"{units:,}".replace(",", separator) + f",{cents:02} {symbol}"
    return f"{symbol}{units:,}.{cents:02}"


def fixtures():
    rng = random.Random(44017)
    for lang in (*FIRST, *EXTRA):
        words = LANG[lang]
        count = 24 if lang in FIRST else 12
        for index in range(count):
            cid = f"{lang}-{index+1:03}"
            y, m, d = 2026, rng.choice((3, 4, 6, 10)), rng.randint(2, 27)
            units, cents = rng.choice((38, 116, 480, 1120, 1250, 2215)), rng.choice((0, 25, 50, 56, 75))
            code, _ = CURRENCIES[lang]
            if code in {"JPY", "CNY"}:
                cents = 0
            deadline, scenario = f"{y}-{m:02}-{d:02}", "clear"
            printed_date = written_date(lang, index, y, m, d)
            printed_amount = written_amount(lang, units, cents, index)
            if index in {17, 18, 19}:
                printed_date, deadline, scenario = "03/04/2026", None, "ambiguous_date"
            elif index in {20, 21}:
                printed_date, deadline, scenario = "", None, "no_deadline"
            elif index == 22:
                scenario, printed_date = "deadline_year_first_slash", f"{y}/{m:02}/{d:02}"
            if index == 23:
                scenario, printed_amount = "no_amount", ""
            date_quote = words[5].format(value=printed_date) if printed_date else ""
            amount_quote = words[6].format(value=printed_amount) if printed_amount else ""
            issue = f"2026-01-{(index % 26) + 1:02}"
            lines = [words[index % 3], words[3].format(n=index + 1), words[4].format(issue=issue),
                     date_quote or words[7], amount_quote or words[8], words[9].format(n=index + 1)]
            yield {"id": cid, "split": "benchmark" if lang in FIRST else "exploratory", "language": lang,
                   "scenario": scenario, "text": "\n".join(lines), "deadline": deadline,
                   "currency": code if printed_amount else None, "amount": f"{units}.{cents:02}" if printed_amount else None,
                   "deadline_source": date_quote, "amount_source": amount_quote, "issue_date": issue}


def main():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in fixtures()), encoding="utf-8")


if __name__ == "__main__":
    main()
