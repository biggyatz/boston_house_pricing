"""Clean raw property listings (99aana + Hamrobazar) into one table: property.csv."""
import json, re
import pandas as pd
from nepal_units import area_sqft, npr, first_float, strip_phones, SQFT

AANA = SQFT["aana"]
DISTRICTS = {"kathmandu": "Kathmandu", "ktm": "Kathmandu", "lalitpur": "Lalitpur", "patan": "Lalitpur", "bhaktapur": "Bhaktapur",
             "kaski": "Kaski", "pokhara": "Kaski", "chitwan": "Chitwan", "bharatpur": "Chitwan", "rupandehi": "Rupandehi",
             "butwal": "Rupandehi", "bhairahawa": "Rupandehi", "morang": "Morang", "biratnagar": "Morang", "sunsari": "Sunsari",
             "dharan": "Sunsari", "itahari": "Sunsari", "kavre": "Kavrepalanchok", "kavrepalanchok": "Kavrepalanchok",
             "banepa": "Kavrepalanchok", "dhulikhel": "Kavrepalanchok", "makwanpur": "Makwanpur", "hetauda": "Makwanpur",
             "nuwakot": "Nuwakot", "jhapa": "Jhapa", "kailali": "Kailali", "dhangadhi": "Kailali", "banke": "Banke", "nepalgunj": "Banke"}

def norm_locality(s):
    s = re.sub(r"[-\s]*\d+\b", "", s or "").strip(" ,.-")
    s = re.sub(r"\b(municipality|nagarpalika|mahanagarpalika|metropolitan|city|ward|chowk|marga|road|tole)\b", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" ,.-").title() or None

def split_address(addr):
    """'VS Colony, Pepsicola, Kathmandu' -> ('Pepsicola', 'Kathmandu')."""
    parts = [p.strip() for p in re.split(r",", addr or "") if p.strip()]
    district = None
    for p in reversed(parts):
        key = re.sub(r"[^a-z]", "", p.lower().split("-")[0])
        if key in DISTRICTS:
            district = DISTRICTS[key]; parts.remove(p); break
    locality = norm_locality(parts[-1]) if parts else None
    return locality, district

def from_99aana(r):
    h = r.get("header") or []
    kv = {}
    hl = r.get("highlights") or []
    for i, l in enumerate(hl):
        key = l.rstrip(":").strip()
        if i + 1 < len(hl) and key in ("Type", "Price", "Address", "Total Land Area", "Area", "Land Area", "Road", "Floor", "Floors",
                                       "Total no. of rooms", "Total no. of Bathroom", "Built up Area", "Facing", "Road Type", "Built Year"):
            kv[key] = hl[i + 1].lstrip(":–- \xa0").strip()
    title = r.get("title") or ""
    typ = "Land" if title.lower().startswith("land") else "House"
    addr = h[3] if len(h) > 3 else kv.get("Address")
    price_text = h[4] if len(h) > 4 else kv.get("Price")
    area_text = kv.get("Total Land Area") or kv.get("Area") or kv.get("Land Area")
    if not area_text and "sq m" in h:
        k = h.index("sq m"); area_text = h[k + 1] if k + 1 < len(h) else None
    floors = first_float(kv.get("Floor") or kv.get("Floors"))
    road = first_float(kv.get("Road"))
    rooms = first_float(h[h.index("Rooms") + 1]) if "Rooms" in h and h.index("Rooms") + 1 < len(h) else first_float(kv.get("Total no. of rooms"))
    baths = first_float(h[h.index("Bathrooms") + 1]) if "Bathrooms" in h and h.index("Bathrooms") + 1 < len(h) else first_float(kv.get("Total no. of Bathroom"))
    loc, dist = split_address(addr)
    return dict(source="99aana.com", url=r["url"], title=title, type=typ, locality=loc, district=dist, address=addr,
                price_text=price_text, area_text=area_text, floors=floors, road_ft=road, rooms=rooms, bathrooms=baths,
                listed=(r.get("published") or "")[:10])

TERAI = {"Chitwan", "Rupandehi", "Morang", "Sunsari", "Jhapa", "Kailali", "Banke", "Makwanpur"}
SCRAPED = pd.Timestamp("2026-10-09")

def posted_date(text):
    m = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)", text or "")
    if not m:
        return SCRAPED
    n, u = int(m.group(1)), m.group(2)
    days = {"minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}[u] * n
    return SCRAPED - pd.Timedelta(days=days)

def locality_from_title(title):
    t = re.sub(r"[^\w\s,.-]", " ", title or "")
    dist = None
    for w in re.findall(r"[A-Za-z]+", t):
        if w.lower() in DISTRICTS:
            dist = DISTRICTS[w.lower()]
    m = re.search(r"\b(?:at|in|@|near)\s+([A-Za-z][A-Za-z .-]{2,30}?)(?:,|\s+-|-?\s*\d|$|\s+(?:kathmandu|lalitpur|bhaktapur|ktm|pokhara|chitwan))", t, re.I)
    loc = norm_locality(m.group(1)) if m else None
    if loc and loc.lower() in DISTRICTS:
        loc = None
    return loc, dist

def from_hamrobazar(r):
    title = r.get("title") or ""
    typ = "Land" if "/for-sale-land/" in r["url"] else "House"
    loc, dist = locality_from_title(title)
    spec = (r.get("specs") or {}).get("Land Size (Aana/Dhur)")
    area_text = r.get("area_text")
    if not area_text and spec:
        unit = "dhur" if dist in TERAI else "aana"
        area_text = f"{spec} {unit}"
    return dict(source="hamrobazaar.com", url=r["url"], title=title, type=typ, locality=loc, district=dist, address=None,
                price_text=r.get("price"), area_text=area_text, floors=first_float(r.get("storeys")), road_ft=first_float(r.get("road_ft")),
                rooms=None, bathrooms=None, listed=str(posted_date(r.get("posted")).date()))

def merge_spellings(rows, cutoff=0.9):
    """Map near-identical locality spellings within a district onto the most common one
    (e.g. 'Bhiasepati' -> 'Bhaisepati', 'Budanilkantha' -> 'Budhanilkantha')."""
    import difflib
    from collections import Counter
    by_d = {}
    for x in rows:
        if x["locality"]:
            by_d.setdefault(x["district"], Counter())[x["locality"]] += 1
    # Different places whose names happen to be spelled alike.
    distinct = {frozenset({"Narayanthan", "Narayantar"}), frozenset({"Dhaneshwor", "Baneshwor"})}
    canon = {}
    for d, cnt in by_d.items():
        names = [n for n, _ in cnt.most_common()]
        kept = []
        for n in names:
            key = n.lower().replace(" ", "").replace("h", "")
            match = next((k for k in kept if frozenset({n, k}) not in distinct and difflib.SequenceMatcher(None, key, k.lower().replace(" ", "").replace("h", "")).ratio() >= cutoff), None)
            canon[(d, n)] = match or n
            if not match:
                kept.append(n)
    for x in rows:
        if x["locality"]:
            x["locality"] = canon.get((x["district"], x["locality"]), x["locality"])
    return {k: v for k, v in canon.items() if k[1] != v}

def finalize(rows):
    # Fill a missing district from other listings of the same locality.
    loc_dist = {}
    for x in rows:
        if x["locality"] and x["district"]:
            loc_dist.setdefault(x["locality"], []).append(x["district"])
    for x in rows:
        if x["locality"] and not x["district"] and x["locality"] in loc_dist:
            x["district"] = max(set(loc_dist[x["locality"]]), key=loc_dist[x["locality"]].count)
    merged = merge_spellings(rows)
    print("merged spellings:", len(merged), list(merged.items()))
    out = []
    for x in rows:
        sqft = area_sqft(x["area_text"])
        price, per = npr(x["price_text"])
        if price and price < 10000:          # shorthand in lakh: "270" -> 270 lakh
            price *= 1e5
        if price and per:
            if not sqft: continue
            price = price * sqft / SQFT[per]
        if not (price and sqft):
            continue
        aana = sqft / AANA
        x.update(price_npr=round(price), area_aana=round(aana, 3), price_per_aana=round(price / aana), title=strip_phones(x["title"]))
        out.append(x)
    return pd.DataFrame(out)

if __name__ == "__main__":
    import os
    raw = [json.loads(l) for l in open("raw_99aana_v2.jsonl")]
    rows = [from_99aana(r) for r in raw]
    if os.path.exists("raw_hamrobazar_re_details.jsonl"):
        hb = [json.loads(l) for l in open("raw_hamrobazar_re_details.jsonl")]
        rows += [from_hamrobazar(r) for r in hb if r.get("title")]
        raw += hb
    df = finalize(rows)
    print(len(raw), "raw ->", len(df), "usable")
    print(df.district.value_counts(dropna=False).head(12))
    print(df[["type", "locality", "district", "price_npr", "area_aana", "price_per_aana", "floors", "road_ft", "listed"]].sample(12, random_state=1).to_string())
    print(df.groupby(["district", "type"]).price_per_aana.median().round(-3).head(20))
    df = df.drop_duplicates(subset=["url"])
    df.to_csv("property.csv", index=False)
    print("wrote property.csv", len(df))
