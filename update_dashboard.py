#!/usr/bin/env python3
"""
Auto-update D2D Adoption Dashboard.
Reads the latest RM_QUERY_*.csv in the repo, fetches fresh walldecor shares,
recomputes the RAW array, and writes it back into D2D_Adoption_Dashboard.html.
"""

import csv, json, re, os, glob
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import urllib.request

IST = timezone(timedelta(hours=5, minutes=30))

# Always process through yesterday (today's data is incomplete)
MAX_DATE = (datetime.now(IST) - timedelta(days=1)).strftime('%Y-%m-%d')
print(f"MAX_DATE: {MAX_DATE}")

# ── Find CSV ──────────────────────────────────────────────────────────────────
csv_files = sorted(glob.glob('RM_QUERY_*.csv') + glob.glob('data/RM_QUERY_*.csv'))
if not csv_files:
    raise FileNotFoundError("No RM_QUERY_*.csv found. Commit the CSV first.")
csv_path = csv_files[-1]  # alphabetically last = most recent date
print(f"CSV: {csv_path}")

# ── Fetch walldecor shares ────────────────────────────────────────────────────
WALLDECOR = "https://walldecor-prod-backend-455448097070.asia-south2.run.app"
all_shares = []
page = 1
while True:
    url = f"{WALLDECOR}/admin/shares?page={page}&limit=50"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    batch = data.get("shares", [])
    if not batch:
        break
    all_shares.extend(batch)
    if page % 10 == 0:
        print(f"  walldecor page {page}: {len(all_shares)} shares", flush=True)
    if len(batch) < 50:
        break
    page += 1
print(f"Total walldecor shares: {len(all_shares)}")

# ── Index shares ──────────────────────────────────────────────────────────────
shares_by_req = defaultdict(list)
d2d_links_by_date = defaultdict(int)

for share in all_shares:
    req_id = (share.get("surveyRequestId") or "").strip()
    created_raw = share.get("createdAt", "")
    if not created_raw:
        continue
    try:
        dt_utc = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        dt_ist = dt_utc.astimezone(IST)
    except Exception:
        continue
    ist_date = dt_ist.strftime("%Y-%m-%d")
    if ist_date >= "2026-06-01":
        d2d_links_by_date[ist_date] += 1
    if req_id:
        shares_by_req[req_id].append(dt_ist.replace(tzinfo=None))

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_date(s):
    if not s or not s.strip():
        return None
    try:
        parts = s.strip().split("/")
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        return f"20{y:02d}-{m:02d}-{d:02d}"
    except Exception:
        return None

def parse_dt(s):
    if not s or not s.strip():
        return None
    for fmt in ("%d/%m/%y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M:%S.%f"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            pass
    return None

# ── Aggregate CSV ─────────────────────────────────────────────────────────────
data = defaultdict(lambda: {
    "gr": 0, "sv": 0, "qt": 0, "hi": 0,
    "d2d": 0,
    "qt_d2d_b": 0, "qt_d2d_a": 0, "qt_no_d2d": 0,
    "hi_d2d_b": 0, "hi_d2d_a": 0, "hi_no_d2d": 0,
})

with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        survey_date = parse_date(row.get("SURVEY_DATE", ""))
        if not survey_date or not ("2026-06-01" <= survey_date <= MAX_DATE):
            continue

        d = data[survey_date]
        d["gr"] += 1

        if row.get("SURVEY_DELIVERED", "0").strip() == "1":
            d["sv"] += 1

        quote_shared = row.get("QUOTE_SHARED", "").strip().upper() == "TRUE"
        if quote_shared:
            d["qt"] += 1

        order_id = row.get("ORDER_ID", "").strip()
        has_hiring = order_id not in ("", "NULL", "null")
        if has_hiring:
            hiring_date = parse_date(row.get("HIRING_DATE", ""))
            if hiring_date and "2026-06-01" <= hiring_date <= MAX_DATE:
                data[hiring_date]["hi"] += 1

        req_id = row.get("SURVEY_REQUEST_ID", "").strip()
        survey_start = parse_dt(row.get("SURVEY_START", "").strip())
        req_shares = sorted(shares_by_req.get(req_id, []))

        if req_shares:
            d["d2d"] += 1

        timing = "none"
        if req_shares and survey_start:
            cutoff = survey_start + timedelta(hours=3)
            if any(survey_start <= s <= cutoff for s in req_shares):
                timing = "b"
            elif any(s > cutoff for s in req_shares):
                timing = "a"
        elif req_shares:
            timing = "a"

        if quote_shared:
            if timing == "b":
                d["qt_d2d_b"] += 1
            elif timing == "a":
                d["qt_d2d_a"] += 1
            else:
                d["qt_no_d2d"] += 1

        if has_hiring:
            hiring_date = parse_date(row.get("HIRING_DATE", ""))
            if hiring_date and "2026-06-01" <= hiring_date <= MAX_DATE:
                if timing == "b":
                    data[hiring_date]["hi_d2d_b"] += 1
                elif timing == "a":
                    data[hiring_date]["hi_d2d_a"] += 1
                else:
                    data[hiring_date]["hi_no_d2d"] += 1

# ── Build RAW array string ────────────────────────────────────────────────────
all_dates = sorted(d for d in set(list(data.keys()) + list(d2d_links_by_date.keys()))
                   if "2026-06-01" <= d <= MAX_DATE)

lines = ["const RAW = ["]
for date in all_dates:
    d = data[date]
    links = d2d_links_by_date.get(date, 0)
    lines.append(
        f'  {{date:"{date}",gr:{d["gr"]},sv:{d["sv"]},qt:{d["qt"]},'
        f'd2d:{d["d2d"]},qt_d2d_b:{d["qt_d2d_b"]},qt_d2d_a:{d["qt_d2d_a"]},'
        f'qt_no_d2d:{d["qt_no_d2d"]},hi:{d["hi"]},hi_d2d_b:{d["hi_d2d_b"]},'
        f'hi_d2d_a:{d["hi_d2d_a"]},hi_no_d2d:{d["hi_no_d2d"]},d2d_links:{links}}},'
    )
lines.append("];")
new_raw = "\n".join(lines)

# ── Patch HTML ────────────────────────────────────────────────────────────────
html_path = "D2D_Adoption_Dashboard.html"
with open(html_path, encoding="utf-8") as f:
    html = f.read()

patched = re.sub(r"const RAW = \[[\s\S]*?\];", new_raw, html)
if patched == html:
    print("WARNING: RAW array pattern not found in HTML — no changes made.")
else:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(patched)
    print(f"Updated {html_path} with {len(all_dates)} dates through {MAX_DATE}")
