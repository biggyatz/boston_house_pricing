"""Parsing helpers for Nepali property and vehicle listings."""
import re

SQFT = {"ropani": 5476.0, "aana": 342.25, "paisa": 85.5625, "dam": 21.390625,
        "bigha": 72900.0, "kattha": 3645.0, "dhur": 182.25, "sqft": 1.0, "sqm": 10.7639}
UNIT_ALIASES = {"ropani": "ropani", "aana": "aana", "ana": "aana", "anna": "aana", "paisa": "paisa", "dam": "dam",
                "bigha": "bigha", "kattha": "kattha", "katha": "kattha", "kaththa": "kattha", "dhur": "dhur",
                "sq ft": "sqft", "sqft": "sqft", "sq. ft": "sqft", "square feet": "sqft", "sq m": "sqm", "sqm": "sqm"}
UNIT_RE = "|".join(sorted((re.escape(k) for k in UNIT_ALIASES), key=len, reverse=True))

def area_sqft(text):
    """'0-2-2-0' (ropani-aana-paisa-dam), '3 Aana', '45 dhur', '1 ropani 4 aana', '1-2-0' (bigha-kattha-dhur)."""
    if not text:
        return None
    t = text.lower().replace(",", "").strip(" :–-")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", t)
    if m:
        r, a, p, d = map(float, m.groups())
        return r * SQFT["ropani"] + a * SQFT["aana"] + p * SQFT["paisa"] + d * SQFT["dam"]
    total, found = 0.0, False
    for num, unit in re.findall(rf"(\d+(?:\.\d+)?)\s*({UNIT_RE})\b", t):
        total += float(num) * SQFT[UNIT_ALIASES[unit]]; found = True
    return total if found else None

def npr(text):
    """Parse a Nepali price string to (amount_in_NPR, per_unit or None).
    Handles '1 crore 50 lakh', 'Rs. 18 Lakh per aana', 'Rs 2,20,00,000', '1 lakh 45 thousand per dhur'."""
    if not text:
        return None, None
    t = text.lower().replace("\xa0", " ")
    t = re.sub(r"\(.*?\)", " ", t)
    per = None
    m = re.search(rf"(?:per|/|प्रति)\s*({UNIT_RE})", t)
    if m:
        per = UNIT_ALIASES[m.group(1)]
        t = t[:m.start()]
    words = {"crore": 1e7, "cr": 1e7, "karod": 1e7, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "thousand": 1e3, "hajar": 1e3, "k": 1e3}
    total, hit = 0.0, False
    for num, w in re.findall(r"(\d+(?:\.\d+)?)\s*(crore|cr|karod|lakhs|lakh|lacs|lac|thousand|hajar)\b", t.replace(",", "")):
        total += float(num) * words[w]; hit = True
    if hit:
        return total, per
    m = re.search(r"(\d[\d,]{3,}(?:\.\d+)?)", t)
    if m:
        return float(m.group(1).replace(",", "")), per
    return None, per

def first_float(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None

def ad_year(y, now=2026):
    """Listings sometimes use Bikram Sambat years (e.g. 2075). Convert BS to AD (BS - 57)."""
    if y is None:
        return None
    y = int(y)
    if now + 1 < y <= now + 60:  # BS year
        y -= 57
    return y if 1980 <= y <= now + 1 else None

PHONE_RE = re.compile(r"\s*[(\[]*(?:\+?977[-\s]?)?\b9[678]\d[-\s]?\d{3}[-\s]?\d{4}\b[)\]]*|\s*[(\[]*\[phone\][)\]]*")

def strip_phones(text):
    """Remove Nepali mobile numbers (and earlier '[phone]' masks) from free text."""
    return PHONE_RE.sub("", text or "").strip(" -,:|")
