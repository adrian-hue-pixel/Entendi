"""Picker coverage and optional regional context for letters."""

from dataclasses import dataclass
from datetime import date

EUROPE = """Albania|Andorra|Armenia|Austria|Azerbaijan|Belarus|Belgium|Bosnia and Herzegovina|Bulgaria|Croatia|Cyprus|Czechia|Denmark|Estonia|Finland|France|Georgia|Germany|Greece|Hungary|Iceland|Ireland|Italy|Kosovo|Latvia|Liechtenstein|Lithuania|Luxembourg|Malta|Moldova|Monaco|Montenegro|Netherlands|North Macedonia|Norway|Poland|Portugal|Romania|Russia|San Marino|Serbia|Slovakia|Slovenia|Spain|Sweden|Switzerland|Turkey|Ukraine|United Kingdom|Vatican City"""
ASIA = """Afghanistan|Bahrain|Bangladesh|Bhutan|Brunei|Cambodia|China|Hong Kong|India|Indonesia|Iran|Iraq|Israel|Japan|Jordan|Kazakhstan|Kuwait|Kyrgyzstan|Laos|Lebanon|Macau|Malaysia|Maldives|Mongolia|Myanmar|Nepal|North Korea|Oman|Pakistan|Palestine|Philippines|Qatar|Saudi Arabia|Singapore|South Korea|Sri Lanka|Syria|Taiwan|Tajikistan|Thailand|Timor-Leste|Turkmenistan|United Arab Emirates|Uzbekistan|Vietnam|Yemen"""
OTHER = """Angola|Argentina|Australia|Bolivia|Brazil|Cameroon|Canada|Cape Verde|Chile|Colombia|Costa Rica|Cuba|DR Congo|Dominican Republic|Ecuador|El Salvador|Equatorial Guinea|Guatemala|Guinea-Bissau|Haiti|Honduras|Ivory Coast|Madagascar|Mexico|New Zealand|Nicaragua|Panama|Paraguay|Peru|São Tomé and Príncipe|Senegal|Suriname|United States|Uruguay|Venezuela"""
COUNTRIES = tuple(sorted(set((EUROPE + "|" + ASIA + "|" + OTHER).split("|")), key=str.casefold)) + ("Other",)

_BY_LANGUAGE = {
    "English": "United Kingdom|Ireland|Malta|Singapore|Philippines|Hong Kong|United States|Canada|Australia|New Zealand|India",
    "Spanish": "Spain|Mexico|Colombia|Argentina|Peru|Chile|Venezuela|Ecuador|Guatemala|Cuba|Bolivia|Dominican Republic|Honduras|Paraguay|El Salvador|Nicaragua|Costa Rica|Panama|Uruguay|Equatorial Guinea",
    "French": "France|Belgium|Switzerland|Luxembourg|Monaco|Canada|Haiti|DR Congo|Senegal|Ivory Coast|Cameroon|Madagascar",
    "German": "Germany|Austria|Switzerland|Liechtenstein|Luxembourg|Belgium",
    "Portuguese": "Portugal|Timor-Leste|Brazil|Angola|Mozambique|Cape Verde|Guinea-Bissau|São Tomé and Príncipe",
    "Italian": "Italy|San Marino|Vatican City|Switzerland",
    "Russian": "Russia|Belarus|Kazakhstan|Kyrgyzstan", "Polish": "Poland",
    "Dutch": "Netherlands|Belgium|Suriname", "Turkish": "Turkey|Cyprus",
    "Chinese (Simplified)": "China|Singapore", "Japanese": "Japan", "Korean": "South Korea",
    "Vietnamese": "Vietnam", "Indonesian": "Indonesia", "Thai": "Thailand", "Hindi": "India",
}
COUNTRIES = tuple(sorted(set(COUNTRIES[:-1]) | {"Mozambique"}, key=str.casefold)) + ("Other",)


def local_languages(country: str) -> tuple[str, ...]:
    return tuple(language for language, locations in _BY_LANGUAGE.items() if country in locations.split("|")) or ("English",)


@dataclass(frozen=True)
class Region:
    order: str
    decimal: str
    currency: str
    examples: str


_DEFAULT = Region("DMY", "", "", "")
_REGIONS = {
    "United Kingdom": Region("DMY", ".", "GBP", "council tax statement, NHS appointment letter, HMRC notice"),
    "United States": Region("MDY", ".", "USD", "county tax notice, municipal utility bill"),
    "Canada": Region("YMD", ".", "CAD", "provincial notice, municipal utility bill"),
    "Switzerland": Region("DMY", ".", "CHF", "commune notice, cantonal tax letter"),
    "Germany": Region("DMY", ",", "EUR", "municipal fee notice, Finanzamt letter"),
    "France": Region("DMY", ",", "EUR", "mairie notice, tax notice"),
    "Spain": Region("DMY", ",", "EUR", "ayuntamiento notice, tax letter"),
    "Japan": Region("YMD", ".", "JPY", "city hall notice, municipal tax notice"),
    "China": Region("YMD", ".", "CNY", "municipal notice, utility payment letter"),
    "Singapore": Region("DMY", ".", "SGD", "town council letter, utility bill"),
    "South Korea": Region("YMD", ".", "KRW", "district office notice, municipal tax notice"),
    "Poland": Region("DMY", ",", "PLN", "municipal notice"),
    "Thailand": Region("DMY", ".", "THB", "district office notice"),
}
_EURO = set("Austria|Belgium|Croatia|Cyprus|Estonia|Finland|Greece|Ireland|Italy|Latvia|Lithuania|Luxembourg|Malta|Netherlands|Portugal|Slovakia|Slovenia".split("|"))


def region(country: str) -> Region:
    return _REGIONS.get(country, Region("DMY", ",", "EUR", "") if country in _EURO else _DEFAULT)


def formatted_date(day: date, country: str) -> str:
    fmt = {"MDY": "%m/%d/%Y", "YMD": "%Y-%m-%d", "DMY": "%d/%m/%Y"}[region(country).order]
    return day.strftime(fmt)


def benefits_location(country: str, nation: str = "") -> str | None:
    return "England (United Kingdom)" if country == "United Kingdom" and nation == "England" else None
