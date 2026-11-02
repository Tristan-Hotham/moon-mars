"""Parse the Wikipedia articles in raw/wiki_pages.json into one table of human-made objects on the Moon and Mars.

Sources and what is taken from each (all English Wikipedia, CC BY-SA 4.0, revision ids recorded):
  * List_of_artificial_objects_on_the_Moon, table 'Table of objects': one row per object with country, year, mass in
    pounds and kilograms, status, location and notes. Rows are coloured by the article's legend: red = crashed
    (unintentionally), no colour = impactor or post-mission crash, cream = landed, green = operational. The last row
    is the article's total ('Total estimated dry mass'), kept only for comparison.
  * List_of_artificial_objects_on_Mars, table 'List of landers and vehicles': year, agency, mission, objects, mass (kg),
    status and location; rows coloured success (tan), operational (green) or failure (red).
  * List_of_landings_on_extraterrestrial_bodies, tables 'Mars' and "Earth's Moon": every landing or impact with its date,
    coordinates and notes, coloured by outcome (tan = soft landing with data return, yellow-green = sample return, blue =
    crewed). Used for the landing success rates and for full dates of arrival.
  * Moon_landing: the crewed landings table (landing site names) and the uncrewed soft landing tables (landing zones).
  * Fallen_Astronaut, Apollo_Lunar_Surface_Experiments_Package, Lunar_Roving_Vehicle and the introductions of the two
    lists: the small items left by Apollo crews (flags, plaques, golf balls, Fallen Astronaut, retroreflectors and so
    on) and on Mars (pennants, heat shields, shrouds). These are not rows in any table. Each is added by hand, with
    the phrase in the article that names it checked below, and is given the coordinates of its landing site.

Cleaning: tables are expanded cell by cell with rowspans and colspans, so a value that the article writes once for
two rows (Hakuto-R Mission 1 and the Emirates Lunar Mission share year, mass, status and place) is copied to both
rows for display but its mass is counted once. Footnote markers are removed. Coordinates come from the decimal
'geo' span of each location; longitudes are wrapped to -180..180 (the Mars table gives some as west longitudes
beyond 180, such as 313 W, or as east longitudes from 0 to 360, such as 354.47 E). Where the article has no
coordinates the object keeps none; nothing is invented."""
import re
from bs4 import BeautifulSoup
from common import *

W = jload(f"{RAW}/wiki_pages.json")
REV = {k: v.get("revid") for k, v in W.items()}
MISSING = sorted(k for k, v in W.items() if "html" not in v)
assert MISSING == ["Golf_on_the_Moon", "Lunar_flags_(Apollo)", "Lunar_laser_ranging_experiments"], MISSING
soup = lambda k: BeautifulSoup(W[k]["html"], "lxml")


def clean(s):
    s = s.replace("﻿", "").replace("\xa0", " ").replace("​", "")
    s = re.sub(r"\[\s*(?:[a-z]|\d+|citation needed|note \d+)\s*\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def ctext(c, sep=" "):
    c = BeautifulSoup(str(c), "lxml")
    for x in c.find_all(["sup", "style"]):
        x.decompose()
    for x in c.select('span[style*="display:none"]'):
        x.decompose()
    return clean(c.get_text(sep))


def expand(table):
    """Rows of (cell, shared) with rowspan and colspan expanded; shared = copied from a cell above."""
    out, pend = [], {}
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"], recursive=False)
        row, col, it = [], 0, iter(cells)
        while True:
            if col in pend:
                c, left = pend[col]
                row.append((c, True)); pend[col] = (c, left - 1)
                if left - 1 <= 0: del pend[col]
                col += 1; continue
            c = next(it, None)
            if c is None:
                if any(k > col for k in pend): col += 1; continue
                break
            rs, cs = int(c.get("rowspan", 1) or 1), int(c.get("colspan", 1) or 1)
            for k in range(cs):
                row.append((c, False))
                if rs > 1: pend[col] = (c, rs - 1)
                col += 1
        out.append((tr, row))
    return out


def colour(tr, cells):
    st = (tr.get("style") or "") + " " + " ".join((c.get("style") or "") for c, _ in cells)
    m = re.search(r"#([0-9a-fA-F]{6})", st)
    return m.group(1).lower() if m else ""


def geo(c):
    g = c.find("span", class_="geo")
    if not g:
        return None, None
    a, b = [float(x) for x in g.get_text().replace("﻿", "").split(";")]
    return round(a, 5), round(wrap_lon(b), 5)


def mass(s):
    """'1,984', '<5,727', '>700', '1552 (launch mass)', '1285' -> (kg, note)."""
    s = clean(s); note = ""
    if not s or s in ("?", "Unknown"): return None, "no mass given"
    if "(" in s: note = s[s.index("(") + 1:s.rindex(")")] if ")" in s else ""
    if s.startswith("<"): note = (note + "; " if note else "") + "upper bound"
    if s.startswith(">"): note = (note + "; " if note else "") + "lower bound"
    m = re.search(r"\d[\d,]*(?:\.\d+)?", s)
    return float(m.group(0).replace(",", "")), note


def parts(c):
    """Name cell split on line breaks, footnotes removed."""
    c = BeautifulSoup(str(c), "lxml")
    for x in c.find_all("sup"): x.decompose()
    h = re.sub(r"<br\s*/?>", "\n", str(c))
    return [clean(BeautifulSoup(p, "lxml").get_text(" ")) for p in h.split("\n") if clean(BeautifulSoup(p, "lxml").get_text(" "))]


def links(c):
    return [a["href"] for a in c.find_all("a", href=True) if a["href"].startswith("/wiki/") and ":" not in a["href"][6:]]


ROVERS = ["Lunokhod 1", "Lunokhod 2", "Yutu-2", "Yutu", "Pragyan", "Lunar Roving Vehicle", "Jinchan", "Tenacious", "LEV-1", "LEV-2", "MAPP LV1",
          "AstroAnt", "Yaoki", "PrOP-M", "Sojourner", "Spirit", "Opportunity", "Curiosity", "Perseverance", "Ingenuity", "Zhurong"]
MISSION_RE = re.compile(r"^(Apollo \d+|Luna \d+|Chang'e \d(?:-T1)?|Surveyor \d|Ranger \d|Lunar Orbiter \d|Explorer \d+|Chandrayaan-\d|LCROSS|"
                        r"Hakuto-R Mission \d|IM-\d|Hiten|Lunar Prospector|SMART-1|GRAIL|LADEE|Beresheet|Longjiang-2|Blue Ghost M1|SLIM|Luna 25)")
MISSION_FIX = {"Hagoromo Hiten": "Hiten", "Moon Impact Probe (MIP) Chandrayaan-1": "Chandrayaan-1", "SELENE Rstar (Okina)": "SELENE (Kaguya)",
               "SELENE Vstar (Ouna)": "SELENE (Kaguya)", "SELENE (Kaguya) main orbiter": "SELENE (Kaguya)", "Jinchan rover": "Chang'e 6",
               "Tenacious rover": "Hakuto-R Mission 2", "LEV-1": "SLIM", "LEV-2": "SLIM", "Emirates Lunar Mission": "Emirates Lunar Mission (on Hakuto-R Mission 1)",
               "Manfred Memorial Moon Mission": "Manfred Memorial Moon Mission (on the Chang'e 5-T1 launch)",
               "Falcon 9-425 upper stage (2025-010D)": "SpaceX Falcon 9 launch 2025-010"}


def mission_of(name):
    if name in MISSION_FIX: return MISSION_FIX[name]
    m = MISSION_RE.match(name)
    return m.group(1) if m else name


DISPLAY = {"Luna 2 Third stage of Vostok rocket": "Luna 2 rocket third stage (Vostok)", "Moon Impact Probe (MIP) Chandrayaan-1": "Chandrayaan-1 Moon Impact Probe",
           "Hagoromo Hiten": "Hagoromo (released by Hiten)", "Chandrayaan-2 Vikram lander Pragyan rover": "Chandrayaan-2 Vikram lander and Pragyan rover",
           "Chandrayaan-3 Vikram lander Pragyan rover": "Chandrayaan-3 Vikram lander and Pragyan rover", "IM-1 Odysseus EagleCam": "IM-1 Odysseus lander and EagleCam",
           "IM-2 Athena MAPP LV1 Micro-Nova AstroAnt Yaoki": "IM-2 Athena lander, with MAPP LV1, Micro-Nova, AstroAnt and Yaoki",
           "Mars Polar Lander and Deep Space 2 (probes)": "Mars Polar Lander and Deep Space 2 probes", "Explorer 49 ( RAE-B )": "Explorer 49 (RAE-B)",
           "Luna 9 Automated Lunar Station (ALS) airbag and lander capsule": "Luna 9 Automated Lunar Station (lander capsule and airbag)"}


def disp(ps):
    raw = " ".join(ps)
    if raw in DISPLAY: return DISPLAY[raw]
    assert len(ps) <= 2, raw
    return raw


# ---------------- Moon objects table ----------------
S = soup("List_of_artificial_objects_on_the_Moon")
tabs = S.find_all("table", class_="wikitable")
assert "Crashed (unintentionally)" in tabs[0].get_text() and "Operational" in tabs[0].get_text()
MOON_COL = {"ffb7b7": "failed", "": "impact", "fcf2cf": "landed", "ddf2d8": "working"}
G = expand(tabs[1])
hdr = [ctext(c) for c, _ in G[0][1]]
assert hdr == ["Artificial object", "Image", "Country", "Year", "Mass ( lb )", "Mass ( kg )", "Status", "Location", "Notes"], hdr
moon, total_row = [], None
for tr, row in G[1:]:
    if row[0][0].name == "th":
        total_row = [ctext(c) for c, _ in row]; continue
    cell = {h: row[i] for i, h in enumerate(hdr) if i < len(row)}
    nm_parts = parts(cell["Artificial object"][0]); raw_name = " ".join(nm_parts)
    kg, mnote = mass(ctext(cell["Mass ( kg )"][0]))
    lat, lon = geo(cell["Location"][0])
    loc_txt = ctext(cell["Location"][0])
    yr = ctext(cell["Year"][0])
    moon.append({"body": "moon", "raw_name": raw_name, "name": disp(nm_parts), "parts": nm_parts, "country_raw": ctext(cell["Country"][0]),
                 "year": int(yr) if yr.isdigit() else None, "year_raw": yr, "mass_kg": kg, "mass_note": mnote, "mass_shared": cell["Mass ( kg )"][1],
                 "status_raw": ctext(cell["Status"][0]), "colour": colour(tr, row), "lat": lat, "lon": lon,
                 "loc_raw": loc_txt if lat is None else "", "coord_shared": cell["Location"][1] and lat is not None,
                 "links": links(cell["Artificial object"][0]), "src": "List_of_artificial_objects_on_the_Moon"})
assert total_row and total_row[0] == "Total estimated dry mass", total_row
TOTAL = {"lb": float(total_row[4].replace(",", "")), "kg": float(total_row[5].replace(",", "")), "soft_text": total_row[6]}
assert TOTAL["kg"] == 222729 and "40 major objects landed softly" in TOTAL["soft_text"]
for r in moon:
    assert r["colour"] in MOON_COL, (r["name"], r["colour"])
    r["status"] = MOON_COL[r["colour"]]
# the Jinchan row has no year of its own in some revisions; here it does
assert all(r["year"] for r in moon if r["raw_name"] != "SELENE Vstar (Ouna)"), [r["name"] for r in moon if not r["year"]]

# ---------------- Mars objects table ----------------
S = soup("List_of_artificial_objects_on_Mars")
tabs = S.find_all("table", class_="wikitable")
MARS_COL = {"ffbbbb": "failed", "efe7b8": "landed", "ccffd9": "working"}
G = expand(tabs[1])
hdr = [ctext(c) for c, _ in G[0][1]]
assert hdr == ["Year", "Agency", "Mission", "Object(s)", "Image", "Mass (kg)", "Status", "Location"], hdr
mars = []
for tr, row in G[1:]:
    cell = {h: row[i] for i, h in enumerate(hdr)}
    nm_parts = parts(cell["Object(s)"][0])
    kg, mnote = mass(ctext(cell["Mass (kg)"][0]))
    lat, lon = geo(cell["Location"][0])
    loc = ctext(cell["Location"][0])
    site = clean(re.split(r"\d", loc.replace("Estimated at", ""), maxsplit=1)[0]).strip(" ,")
    mars.append({"body": "mars", "raw_name": " ".join(nm_parts), "name": disp(nm_parts), "parts": nm_parts, "country_raw": ctext(cell["Agency"][0]).replace("( UK )", "(UK)"),
                 "year": int(ctext(cell["Year"][0])), "year_raw": ctext(cell["Year"][0]), "mass_kg": kg, "mass_note": mnote, "mass_shared": cell["Mass (kg)"][1],
                 "status_raw": ctext(cell["Status"][0]), "colour": colour(tr, row), "lat": lat, "lon": lon, "approx": int("Estimated" in loc),
                 "site": site, "mission_col": ctext(cell["Mission"][0]), "coord_shared": cell["Location"][1], "loc_raw": "",
                 "links": links(cell["Object(s)"][0]), "src": "List_of_artificial_objects_on_Mars"})
for r in mars:
    assert r["colour"] in MARS_COL, (r["name"], r["colour"])
    r["status"] = MARS_COL[r["colour"]]
    assert r["lat"] is not None, r["name"]
assert len(mars) == 20 and not any(r["mass_shared"] for r in mars)

# ---------------- classification ----------------
SOFT_FAIL = ("after soft landing", "Landed safely")       # Mars 3 and Beagle 2 reached the surface intact but failed
for r in moon + mars:
    n, st = r["raw_name"], r["status_raw"]
    r["rovers"] = [v for v in ROVERS if re.search(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", n) and not (v == "Yutu" and "Yutu-2" in n)]
    if r["raw_name"] == "Emirates Lunar Mission": r["rovers"] = ["Rashid"]
    if r["body"] == "moon":
        r["touchdown"] = "soft" if r["status"] in ("landed", "working") else "hard"
    else:
        r["touchdown"] = "soft" if r["status"] in ("landed", "working") or any(k in st for k in SOFT_FAIL) else "hard"
    stage = re.search(r"\bstage\b|S-IVB|Centaur", n) is not None and r["touchdown"] == "hard"
    rover_only = r["rovers"] and not re.search(r"lander|\band\b|Luna \d|Athena|Mars \d|Pathfinder", n, re.I)
    if stage: r["type"] = "stage"
    elif r["raw_name"] == "Tianwen-1 Remote camera": r["type"] = "item"
    elif rover_only: r["type"] = "rover"
    elif r["touchdown"] == "hard": r["type"] = "crash"
    else: r["type"] = "lander"
    r["uncertain"] = int(bool(re.search(r"Likely|or in orbit|not confirmed", st)))
    r["mission"] = mission_of(r["raw_name"]) if r["body"] == "moon" else r["mission_col"]
    r["group"] = COUNTRY_GROUP[r["country_raw"]]
    r["country"] = COUNTRY_NAME.get(r["country_raw"], r["country_raw"])
    r["private"] = PRIVATE.get(r["raw_name"], "")
    hrefs = r["links"]
    pick = hrefs[-1] if (r["type"] == "rover" and len(hrefs) > 1) else (hrefs[0] if hrefs else "")
    r["wiki"] = ("https://en.wikipedia.org" + pick) if pick else WIKI + r["src"]
# Mars rover rows also name the mission in the mission column
for r in mars:
    if r["mission"] == "Mars Exploration Rover": r["mission"] = f"Mars Exploration Rover ({r['parts'][0].split()[0]})"
# rover rows that repeat the lander's mass exactly (Chang'e 3 and Yutu, Chang'e 4 and Yutu-2): count the mass once
dup = []
for a, b in zip(moon, moon[1:]):
    if b["type"] == "rover" and b["mission"] == a["mission"] and b["mass_kg"] == a["mass_kg"] and (b["lat"], b["lon"]) == (a["lat"], a["lon"]):
        b["mass_note"] = f"the table repeats the {a['name']} figure ({a['mass_kg']:,.0f} kg); counted once, with the lander"; b["mass_dup"] = 1; dup.append(b["name"])
assert dup == ["Chang'e 3 Yutu rover", "Chang'e 4 Yutu-2 rover"], dup
for r in moon + mars:
    r.setdefault("mass_dup", 0)
    if r["mass_shared"]:
        r["mass_note"] = "shares one mass figure with the row above in the table; counted once"
    r["mass_count"] = 0 if (r["mass_shared"] or r["mass_dup"] or r["mass_kg"] is None) else r["mass_kg"]

# ---------------- landings list: dates, outcomes, coordinates ----------------
S = soup("List_of_landings_on_extraterrestrial_bodies")
LAND = []
for t in S.find_all("table", class_="wikitable"):
    h3 = t.find_previous("h3").get_text(strip=True).replace("[edit]", "")
    body = "mars" if h3.startswith("Mars") else "moon" if "Moon" in h3 and "Saturn" not in h3 else None
    if not body: continue
    G = expand(t)
    hdr = [ctext(c) for c, _ in G[0][1]]
    assert hdr[:5] == ["Mission", "Country/Agency", "Date of landing/impact", "Coordinates", "Notes"], hdr
    for tr, row in G[1:]:
        c = {h: row[i][0] for i, h in enumerate(hdr) if i < len(row)}
        date = ctext(c["Date of landing/impact"])
        if "NET" in date: continue                       # future mission row
        lat, lon = geo(c["Coordinates"])
        LAND.append({"body": body, "mission": ctext(c["Mission"]), "country_raw": ctext(c["Country/Agency"]), "date": date, "lat": lat, "lon": lon,
                     "notes": ctext(c["Notes"]), "colour": colour(tr, [(tr, 0)]) or colour(tr, row), "shared": row[0][1]})
LCOUNTRY = {"USSR": "Soviet Union and Russia", "Russia": "Soviet Union and Russia", "USA": "United States", "China": "China", "Japan": "Japan",
            "India": "India", "ESA": "Europe (ESA)", "UK / ESA": "Europe (ESA)", "ESA RFSA": "Europe (ESA)", "Israel": "Others (Israel, Luxembourg, UAE)"}
FAIL_RE = re.compile(r"unsuccessful|failed attempt|contact lost|crash|first attempt to land|no contact|transmission ended", re.I)
NOT_ATTEMPT = re.compile(r"intentional|S-IVB|impactor", re.I)     # deliberate impacts ('Unintentional' covers Ranger 4, an impactor)
for e in LAND:
    e["group"] = LCOUNTRY[e["country_raw"]]
    e["success"] = int(bool(e["colour"]))
    if e["success"]: e["attempt"] = 1
    elif e["body"] == "mars": e["attempt"] = 1               # every Mars row is a landing attempt
    else: e["attempt"] = int(bool(FAIL_RE.search(e["notes"])) and not NOT_ATTEMPT.search(e["notes"]))
    e["crewed"] = int(e["colour"] == "c0e0e0"); e["sample"] = int(e["colour"] == "dfe771")

# ---------------- Moon_landing: site names ----------------
S = soup("Moon_landing")
SITES = {}
for t in S.find_all("table", class_="wikitable"):
    G = expand(t); hdr = [ctext(c) for c, _ in G[0][1]]
    key = "Lunar landing site" if "Lunar landing site" in hdr else "Landing zone" if "Landing zone" in hdr else None
    if not key: continue
    mcol = hdr[0]
    for tr, row in G[1:]:
        c = {h: row[i][0] for i, h in enumerate(hdr) if i < len(row)}
        nm, zone = ctext(c[mcol]), ctext(c[key])
        if zone and nm: SITES[mission_of(nm)] = zone

# ---------------- dates and cross-checks ----------------
def ekey(e):
    m = e["mission"]
    for a, b in (("Kaguya", "SELENE (Kaguya) main orbiter"), ("SELENE Rstar (Okina)", "SELENE Rstar (Okina)"), ("Chandrayaan-1 Moon Impact Probe", "Moon Impact Probe (MIP) Chandrayaan-1"),
                 ("Smart Lander for Investigating Moon (SLIM)", "SLIM"), ("LCROSS (Centaur)", "LCROSS Centaur"), ("LCROSS (Shepherding Spacecraft)", "LCROSS Shepherding Spacecraft")):
        if m == a: return b
    return mission_of(m)


EV = {}
for e in LAND:
    k = ekey(e)
    if e["shared"] and "ascent stage" in e["notes"]: k = k + " ascent stage"
    if e["body"] == "moon" and k == "Apollo 13": k = "Apollo 13 S-IVB"
    EV.setdefault((e["body"], k), e)
    EV.setdefault((e["body"], e["mission"]), e)
MARS_EV = {"Mars 2 lander and PrOP-M rover": "Mars 2 lander", "Mars 3 lander and PrOP-M rover": "Mars 3 lander", "Mars 6 lander": "Mars 6 lander",
           "Viking 1 lander": "Viking 1 lander", "Viking 2 lander": "Viking 2 lander", "Pathfinder (lander)": "Mars Pathfinder and Sojourner rover",
           "Sojourner (rover)": "Mars Pathfinder and Sojourner rover", "Mars Polar Lander and Deep Space 2 (probes)": "Mars Polar Lander and two penetrators Deep Space 2",
           "Beagle 2 (lander)": "Beagle 2", "Spirit (rover)": "MER-A Spirit", "Opportunity (rover)": "MER-B Opportunity", "Phoenix (lander)": "Phoenix",
           "Curiosity (rover)": "Mars Science Laboratory ( Curiosity )", "Schiaparelli EDM (lander)": "ExoMars Schiaparelli EDM lander", "InSight (lander)": "InSight",
           "Perseverance (rover)": "Mars 2020 Perseverance rover and Ingenuity helicopter", "Ingenuity (helicopter)": "Mars 2020 Perseverance rover and Ingenuity helicopter",
           "Tianwen-1 (lander)": "Tianwen-1 lander and Zhurong rover", "Zhurong (rover)": "Tianwen-1 lander and Zhurong rover", "Tianwen-1 Remote camera": "Tianwen-1 lander and Zhurong rover"}
evm = {(e["body"], e["mission"]): e for e in LAND}
unmatched = []
for r in moon + mars:
    e = None
    if r["body"] == "mars":
        e = evm.get(("mars", MARS_EV[r["raw_name"]]))
    else:
        for k in (r["raw_name"], r["mission"] + (" ascent stage" if "ascent stage" in r["raw_name"] else ""), r["mission"]):
            if ("moon", k) in EV: e = EV[("moon", k)]; break
        if r["type"] == "stage" and e is not None and not (("ascent stage" in r["raw_name"] and "ascent" in e["notes"]) or r["raw_name"].startswith(("LCROSS Centaur", "Apollo 13 S-IVB"))):
            e = None                                   # a stage's impact is not the lander's landing date
        if r["raw_name"].startswith("Apollo") and "ascent stage" in r["raw_name"]: e = None
        if r["raw_name"] in ("Hagoromo Hiten", "Emirates Lunar Mission", "Manfred Memorial Moon Mission", "Apollo 10 LM-4 Snoopy descent stage", "Luna 2 Third stage of Vostok rocket", "Apollo 15 subsatellite", "Apollo 16 subsatellite"): e = None
    if e is None:
        r["date"] = ""; unmatched.append(r["raw_name"]); continue
    yr = int(re.search(r"\d{4}", e["date"]).group(0))
    if abs(yr - r["year"]) > 1 or r["raw_name"] == "Hagoromo Hiten":
        r["date"] = ""; unmatched.append(r["raw_name"] + f" (year {r['year']} vs {e['date']})"); continue
    r["date"] = e["date"]; r["landing_mission"] = e["mission"]
    r["alt_lat"], r["alt_lon"] = e["lat"], e["lon"]
    if r["lat"] is not None and e["lat"] is not None:
        d = max(abs(r["lat"] - e["lat"]), abs(wrap_lon(r["lon"] - e["lon"])))
        r["coord_diff_deg"] = round(d, 2)
for r in moon + mars:
    r.setdefault("coord_diff_deg", None)
    if r["body"] == "moon":
        r["site"] = SITES.get(r["mission"], "")
        r.setdefault("approx", 0)

# ---------------- small items named in the articles ----------------
TX = {}
for k in ("List_of_artificial_objects_on_the_Moon", "List_of_artificial_objects_on_Mars", "Moon_landing", "Fallen_Astronaut", "Apollo_Lunar_Surface_Experiments_Package", "Lunar_Roving_Vehicle"):
    s = soup(k)
    for x in s.find_all(["sup", "style"]): x.decompose()
    TX[k] = clean(s.get_text(" "))
LM = {r["mission"]: r for r in moon if "descent stage" in r["raw_name"] and r["mission"].startswith("Apollo") and r["status"] == "landed"}
assert sorted(LM) == ["Apollo 11", "Apollo 12", "Apollo 14", "Apollo 15", "Apollo 16", "Apollo 17"], sorted(LM)
MOONLIST, ML, FA, AL = "List_of_artificial_objects_on_the_Moon", "Moon_landing", "Fallen_Astronaut", "Apollo_Lunar_Surface_Experiments_Package"
ITEMS = []


def item(body, name, at, src, quote, note="", status="left", lat=None, lon=None, mass_kg=None, mass_note="no mass given", year=None, country="United States", mission=None, approx_note=None):
    assert quote in TX[src], (name, quote)
    base = at if isinstance(at, dict) else None
    ITEMS.append({"body": body, "raw_name": name, "name": name, "parts": [name], "country_raw": country, "country": COUNTRY_NAME.get(country, country),
                  "group": COUNTRY_GROUP[country], "year": year or base["year"], "year_raw": str(year or base["year"]), "mass_kg": mass_kg, "mass_note": mass_note,
                  "mass_shared": False, "mass_dup": 0, "mass_count": mass_kg or 0, "status_raw": note, "colour": "", "status": status,
                  "lat": lat if lat is not None else base["lat"], "lon": lon if lon is not None else base["lon"],
                  "coord_from": "own" if lat is not None else f"landing site of {base['name']}", "approx": 1 if lat is None else 0,
                  "approx_note": approx_note or ("" if lat is not None else "placed at the landing site coordinates"),
                  "touchdown": "soft", "type": "item", "uncertain": 0, "rovers": [], "mission": mission or base["mission"], "private": "",
                  "wiki": WIKI + src, "src": src, "quote": quote, "date": "", "coord_diff_deg": None, "site": (base or {}).get("site", ""), "loc_raw": "", "coord_shared": False})


for m, r in LM.items():
    st = "Blown over by the ascent engine's exhaust, as Buzz Aldrin reported" if m == "Apollo 11" else "Still standing and casting a shadow in LROC images"
    item("moon", f"{m} United States flag", r, ML, "five of the six American flags are still standing and casting shadows at all of the sites, except Apollo 11", st)
for m, r in LM.items():
    item("moon", f"{m} commemorative plaque on the Lunar Module ladder", r, MOONLIST, "the commemorative plaques attached to the ladders of the six Apollo Lunar Modules",
         "On the ladder of the descent stage")
item("moon", "Apollo 11 goodwill messages disc", LM["Apollo 11"], MOONLIST, "the Apollo 11 goodwill messages disc", "Left by the Apollo 11 crew")
item("moon", "Silver astronaut pin left by Alan Bean for Clifton C. Williams", LM["Apollo 12"], MOONLIST,
     "the silver astronaut pin left by Alan Bean in honor of Clifton C. Williams whom he replaced", "Left by Alan Bean in honour of the astronaut he replaced")
item("moon", "Golf balls hit by Alan Shepard", LM["Apollo 14"], MOONLIST, "the golf balls Alan Shepard hit during an Apollo 14 moonwalk",
     "Hit by Alan Shepard during a moonwalk; the article does not say how many", approx_note="placed at the landing site coordinates; the balls flew some distance")
item("moon", "Bible left by David Scott", LM["Apollo 15"], MOONLIST, "the Bible left by David Scott", "Left by David Scott")
item("moon", "Fallen Astronaut statuette", LM["Apollo 15"], FA, "Fallen Astronaut is a 3.5-inch (8.9 cm) aluminum sculpture",
     "An 8.9 cm aluminium figure by Paul Van Hoeydonck, placed by David Scott on 2 August 1971 (UTC) at Hadley Rille", lat=26.13222, lon=3.63386)
item("moon", "Fallen Astronaut memorial plaque (14 names)", LM["Apollo 15"], FA, "a plaque bearing the names of eight American astronauts and six Soviet cosmonauts",
     "Names eight American astronauts and six Soviet cosmonauts who had died", lat=26.13222, lon=3.63386)
for m in ("Apollo 11", "Apollo 14", "Apollo 15"):
    item("moon", f"{m} Laser Ranging Retroreflector", LM[m], MOONLIST, "the only artificial objects on the Moon that are still in use are the retroreflectors for the Lunar Laser Ranging experiments left there by the Apollo 11 , 14, and 15 astronauts",
         "Still in use: laser pulses from Earth are timed off it to measure the distance to the Moon", status="working")
item("moon", "Apollo 11 Early Apollo Scientific Experiments Package (EASEP)", LM["Apollo 11"], AL, "Apollo 11 left a smaller package called the Early Apollo Scientific Experiments Package , or EASEP",
     "A smaller science package deployed on the only Apollo 11 moonwalk")
for m in ("Apollo 12", "Apollo 14", "Apollo 15", "Apollo 16", "Apollo 17"):
    item("moon", f"{m} Apollo Lunar Surface Experiments Package (ALSEP)", LM[m], AL, "The stations ran from deployment until the support operations were terminated on 30 September 1977",
         "Science station; support operations ended on 30 September 1977")
item("moon", "Apollo 12 ALSEP fuel transfer tool (discarded)", LM["Apollo 12"], AL, "He then inserted it into the RTG and discarded the FTT",
     "Discarded by Alan Bean after loading the nuclear power source")
LP = next(r for r in moon if r["raw_name"] == "Lunar Prospector")
item("moon", "Ashes of Eugene Shoemaker (on Lunar Prospector)", LP, ML, "a small vial of ashes from the body of pioneer lunar scientist Eugene Shoemaker was delivered by the Lunar Prospector to the crater named in his honor",
     "A small vial carried by Lunar Prospector into Shoemaker crater; the only human remains on the Moon", approx_note="at the impact point of Lunar Prospector",
     year=int(LP["date"][-4:]))
MS = {r["raw_name"]: r for r in mars}
MARSL = "List_of_artificial_objects_on_Mars"
for k in ("Mars 2 lander and PrOP-M rover", "Mars 3 lander and PrOP-M rover"):
    item("mars", f"Soviet pennant on the {k.split(' lander')[0]} lander", MS[k], MARSL, "Pennants of Soviet Union on Mars 2 and Mars 3 landers (1971)",
         "A pennant carried on the lander", country="USSR", approx_note="at the lander's estimated position")
item("mars", "Viking 2 surface sampler shroud", MS["Viking 2 lander"], MARSL, "the metal shroud ejected by the Viking 2 lander",
     "A metal cover thrown off by the lander and seen in its own pictures", country="NASA", approx_note="a few metres from the lander")
item("mars", "Opportunity heat shield", MS["Opportunity (rover)"], MARSL, "MER-B Opportunity ' s heat shield", "Photographed by the rover", country="NASA",
     approx_note="placed at the landing site coordinates; heat shields fall some distance away")
item("mars", "Curiosity (MSL) counterweights ejected during descent", MS["Curiosity (rover)"], MARSL, "the counterweights ejected by MSL during its descent",
     "Dropped during descent", country="NASA", approx_note="placed at the landing site coordinates; they fell kilometres away")
item("mars", "Schiaparelli heat shields and parachute", MS["Schiaparelli EDM (lander)"], MARSL, "there may be a lower heat shield, and at another location, a parachute and upper heat shield",
     "Separate pieces of the entry system", country="ESA Roscosmos", approx_note="placed at the lander's coordinates; the pieces lie at other spots nearby")
item("mars", "Three Forks Sample Depot (Perseverance sample tubes)", MS["Perseverance (rover)"], MARSL,
     "Three Forks Sample Depot , backup sample Depot of Perseverance cached samples for return to Earth by NASA-ESA Mars Sample Return Mission (2022)",
     "Backup depot of sealed sample tubes laid down by Perseverance for a later return to Earth", year=2022, country="NASA",
     approx_note="placed at the landing site coordinates; the depot is a few kilometres away")

# text facts checked here and used in the write-up
FACTS = {}
t = TX[MOONLIST]
for s in ("Five S-IVB third stages of Saturn V rockets from the Apollo program crashed into the Moon, and are the heaviest human-made objects on the lunar surface",
          "Humans have left over 187,400 kilograms (413,100 lb) of material on the Moon", "Besides the 2019 Chang'e 4 and SLIM missions",
          "Objects at greater than 90 degrees east or west are on the far side of the Moon", "a hammer and other tools", "Lunokhod 1 and Lunokhod 2"):
    assert s in t, s
assert "These three LRVs remain on the Moon" in TX["Lunar_Roving_Vehicle"]
assert "The LRRRs are the only experiments still in use" in TX[AL]
assert "Spacecraft that have not been precisely located include Mars 2 , Mars 3 , Mars 6 , Mars Polar Lander, and the two Deep Space 2 probes" in TX[MARSL]
assert "The table does not include smaller objects, such as springs, fragments, parachutes and heat shields" in TX[MARSL]
assert "the only human remains on the Moon" in TX[ML]
FACTS = {"wiki_moon_kg": 187400, "wiki_moon_lb": 413100, "table_total_kg": TOTAL["kg"], "table_total_lb": TOTAL["lb"], "table_soft_text": TOTAL["soft_text"]}

OBJ = moon + mars + ITEMS
for i, r in enumerate(OBJ):
    r["id"] = f"{r['body'][:2]}{i:03d}"
    r["far"] = int(r["body"] == "moon" and r["lon"] is not None and abs(r["lon"]) > FAR_LON)
jsave({"objects": OBJ, "landings": LAND, "sites": SITES, "rev": REV, "missing": MISSING, "facts": FACTS, "unmatched_dates": unmatched}, f"{WORK}/parsed.json", indent=1)
print("moon rows", len(moon), "mars rows", len(mars), "items", len(ITEMS), "landing rows", len(LAND), "sites", len(SITES))
print("unmatched dates:", unmatched)
for r in OBJ:
    print(f"{r['id']} {r['type']:6} {r['status']:7} {r['touchdown']:4} {r['group'][:12]:12} {str(r['year']):5} {r['mass_count']:>9} {str(r['lat']):>9} {str(r['lon']):>10} {r.get('date',''):18} {r['mission'][:28]:28} | {r['name'][:60]} {r['rovers'] or ''} {'diff=' + str(r['coord_diff_deg']) if r['coord_diff_deg'] and r['coord_diff_deg'] > 1 else ''}")
for e in LAND:
    print(e["body"], e["group"][:10], e["success"], e["attempt"], e["date"], e["mission"][:40], "|", e["notes"][:60])
