"""Polite crawler for 99aana.com property listings (robots.txt: allow all).
Stores only property attributes + source URL; no seller names or phone numbers."""
import html, json, re, sys, time, urllib.request

FIELDS = {"Type": "type", "Price": "price_raw", "Address": "address", "Total Land Area": "land_area_rapd",
          "Total no. of rooms": "rooms", "Total no. of Bedroom": "bedrooms", "Total no. of Bathroom": "bathrooms",
          "Floor": "floors", "Road": "road", "Built Year": "built_year", "Facing": "facing", "Road Type": "road_type",
          "Built up Area": "built_up_area"}

def text_of(page):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", "\n", s))
    return [l.strip() for l in s.split("\n") if l.strip()]

def parse(url, page):
    """Keep the raw text of the listing header and the highlights block; parsed offline.
    Phone numbers are masked."""
    lines = [re.sub(r"\b9[678]\d{8}\b", "[phone]", l) for l in text_of(page)]
    rec = {"source": "99aana.com", "url": url}
    m = re.search(r'"datePublished":"([^"]+)"', page); rec["published"] = m.group(1) if m else None
    m = re.search(r'"dateModified":"([^"]+)"', page); rec["modified"] = m.group(1) if m else None
    m = re.search(r"<title>(.*?)</title>", page, re.S); title = html.unescape(m.group(1)).split(" - 99Aana")[0].strip() if m else ""
    rec["title"] = title
    # Header: the second occurrence of the title (first is the <title>-like heading) up to "Description".
    idx = [k for k, l in enumerate(lines) if l == title]
    if idx:
        k = idx[1] if len(idx) > 1 else idx[0]
        end = next((e for e in range(k, min(k + 40, len(lines))) if lines[e] in ("Description", "Overview")), k + 15)
        rec["header"] = lines[k:end]
    h = next((k for k, l in enumerate(lines) if l.endswith("Highlights")), None)
    if h is not None:
        end = next((e for e in range(h, min(h + 80, len(lines))) if lines[e].startswith(("Similar Properties", "Contact", "Facebook", "Nearby"))), h + 60)
        rec["highlights"] = lines[h + 1:end]
    return rec

done = set()
try:
    for l in open("raw_99aana_v2.jsonl"):
        r = json.loads(l)
        if "header" in r:
            done.add(r["url"])
except FileNotFoundError:
    pass
out = open("raw_99aana_v2.jsonl", "a")
import threading
from concurrent.futures import ThreadPoolExecutor
lock = threading.Lock()
todo = [u.strip() for u in open("urls_99aana.txt") if u.strip() and u.strip() not in done]

def work(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research crawler; contact via github.com/biggyatz)"})
        page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
        rec = parse(url, page)
        with lock:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
    except Exception as e:
        print("ERR", url, e, file=sys.stderr, flush=True)
    time.sleep(2.0)  # per worker; 3 workers stay under ~1 request/second overall

print("todo", len(todo), file=sys.stderr, flush=True)
with ThreadPoolExecutor(3) as ex:
    for n, _ in enumerate(ex.map(work, todo)):
        if n % 100 == 0:
            print(n, time.strftime("%H:%M:%S"), file=sys.stderr, flush=True)
