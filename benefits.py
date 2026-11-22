"""Fixed, preliminary checks for three central government schemes in India."""

from dataclasses import dataclass

STATES = (
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh",
    "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry",
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal",
)


@dataclass(frozen=True)
class Scheme:
    name: str
    likely: bool
    criteria: str
    documents: tuple[str, ...]
    office: str
    url: str


def check(profile: dict[str, str]) -> list[Scheme]:
    age = int(profile["age"])
    state = profile["state"]
    bpl = profile["bpl"] == "Yes"
    local_office = f"Ask your Gram Panchayat or municipal social welfare office in {state}."
    pension_documents = ("Proof of age", "Proof of below-poverty-line status", "Bank account details")
    applications = [
        Scheme("Indira Gandhi National Old Age Pension Scheme", age >= 60 and bpl,
               "Age 60 or older and belongs to a household on the official below-poverty-line list.",
               pension_documents, local_office, "https://nsap.nic.in/"),
        Scheme("Indira Gandhi National Widow Pension Scheme",
               age >= 40 and bpl and profile["gender"] == "Woman" and profile["widowed"] == "Yes",
               "For widows aged 40 or older who belong to a household on the official below-poverty-line list.",
               pension_documents + ("Spouse’s death certificate",), local_office, "https://nsap.nic.in/"),
        Scheme("Pradhan Mantri Shram Yogi Maan-dhan",
               18 <= age <= 40 and profile["occupation"] == "Unorganised worker"
               and profile["monthly_income"] == "₹15,000 or less" and profile["pension_exclusion"] == "No",
               "Age 18–40, unorganised worker, monthly income up to ₹15,000, and no NPS, ESIC, EPFO coverage or income tax.",
               ("Aadhaar card", "Savings or Jan Dhan bank account documents"),
               "Visit a Common Service Centre (CSC).",
               "https://www.labour.gov.in/offerings/schemes-and-services/details/pm-sym-QTOzATMtQWa"),
    ]
    return sorted(applications, key=lambda scheme: not scheme.likely)
