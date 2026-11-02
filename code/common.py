"""Shared paths, groupings and helpers for the moon-mars project ("Junk on the Moon and Mars").

Raw inputs (read in place, never modified), in raw/ beside this folder:
  raw/wiki_pages.json   English Wikipedia articles as parsed HTML, each with its revision id ('revid'), CC BY-SA 4.0:
                        List_of_artificial_objects_on_the_Moon, List_of_artificial_objects_on_Mars,
                        List_of_missions_to_the_Moon, List_of_missions_to_Mars, Moon_landing,
                        List_of_landings_on_extraterrestrial_bodies, Fallen_Astronaut,
                        List_of_artificial_objects_on_extra-terrestrial_surfaces (a redirect page only),
                        Apollo_Lunar_Surface_Experiments_Package, Lunar_Roving_Vehicle.
                        Three more titles were requested but do not exist on Wikipedia under those names
                        (Golf_on_the_Moon, Lunar_flags_(Apollo), Lunar_laser_ranging_experiments); the file
                        holds the API's 'missingtitle' error for them and they are not used.
  raw/opm_moon_z3_mercator.png, raw/opm_mars_z3_mercator.png
                        2048 x 2048 web Mercator mosaics at zoom 3 of the OpenPlanetaryMap basemaps
                        opm-moon-basemap-v0-1 (feature labels baked in) and opm-mars-basemap-v0-2.
                        "OpenPlanetaryMap basemaps (OpenPlanetary), from NASA and USGS data".
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("MM_RAW", os.path.join(ROOT, "raw"))
FONTS = os.environ.get("MM_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("MMTMP", "/dev/shm/moonmars"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "moon-mars"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23872995"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/moon-mars/"          # filled in by the publisher
WIKI = "https://en.wikipedia.org/wiki/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
OPM_ATT = "OpenPlanetaryMap basemaps (OpenPlanetary), from NASA and USGS data"
TILES = {"moon": "https://cartocdn-gusc.global.ssl.fastly.net/opmbuilder/api/v1/map/named/opm-moon-basemap-v0-1/all/{z}/{x}/{y}.png",
         "mars": "https://cartocdn-gusc.global.ssl.fastly.net/opmbuilder/api/v1/map/named/opm-mars-basemap-v0-2/all/{z}/{x}/{y}.png"}
ARTICLES = ["List_of_artificial_objects_on_the_Moon", "List_of_artificial_objects_on_Mars", "List_of_landings_on_extraterrestrial_bodies",
            "Moon_landing", "Fallen_Astronaut", "Apollo_Lunar_Surface_Experiments_Package", "Lunar_Roving_Vehicle",
            "List_of_missions_to_the_Moon", "List_of_missions_to_Mars", "List_of_artificial_objects_on_extra-terrestrial_surfaces"]

# Who left it: the country or agency column, grouped. Order = legend and stack order.
GROUPS = [("United States", "#2F5FA7"), ("Soviet Union and Russia", "#C8322B"), ("China", "#E0A11B"), ("Japan", "#D46A8C"),
          ("India", "#7B57A8"), ("Europe (ESA)", "#2E9A8C"), ("Others (Israel, Luxembourg, UAE)", "#7E776C")]
GCOL = dict(GROUPS); GN = [g for g, _ in GROUPS]
COUNTRY_GROUP = {"United States": "United States", "NASA": "United States", "USSR": "Soviet Union and Russia", "Russia": "Soviet Union and Russia",
                 "China": "China", "CNSA": "China", "Japan": "Japan", "India": "India", "European Space Agency": "Europe (ESA)",
                 "ESA (UK)": "Europe (ESA)", "ESA Roscosmos": "Europe (ESA)", "Israel": "Others (Israel, Luxembourg, UAE)",
                 "Luxembourg": "Others (Israel, Luxembourg, UAE)", "United Arab Emirates": "Others (Israel, Luxembourg, UAE)"}
COUNTRY_NAME = {"USSR": "Soviet Union", "NASA": "United States (NASA)", "CNSA": "China (CNSA)", "European Space Agency": "European Space Agency",
                "ESA (UK)": "European Space Agency (United Kingdom)", "ESA Roscosmos": "European Space Agency with Roscosmos"}
SHORT = {"United States": "US", "Soviet Union and Russia": "USSR and Russia", "China": "China", "Japan": "Japan", "India": "India",
         "Europe (ESA)": "Europe", "Others (Israel, Luxembourg, UAE)": "Others"}

# What it is (my classification from the object's name and status; see 01_parse.py). Order = legend order.
TYPES = [("lander", "Lander"), ("rover", "Rover or helicopter"), ("crash", "Impact or crash"), ("stage", "Rocket or ascent stage"),
         ("item", "Small item left behind")]
TYPE_NAME = dict(TYPES); TN = [t for t, _ in TYPES]

# Status classes. The Moon table colours its rows (legend: crashed unintentionally, impactor or post-mission crash,
# landed, operational); the Mars table colours rows success, operational or failure.
STATUS = [("working", "Still working"), ("landed", "Landed, no longer working"), ("failed", "Crashed or failed on landing"),
          ("impact", "Deliberate impact or end-of-mission crash"), ("left", "Left by astronauts")]
STATUS_NAME = dict(STATUS)

# Commercial landers and payloads (Wikipedia, Moon_landing: 'Commercial landings', and the mission lists).
PRIVATE = {"Beresheet": "SpaceIL", "Manfred Memorial Moon Mission": "LuxSpace", "Hakuto-R Mission 1": "ispace", "Hakuto-R Mission 2 Resilience": "ispace",
           "Tenacious rover": "ispace Europe", "IM-1 Odysseus EagleCam": "Intuitive Machines", "IM-2 Athena MAPP LV1 Micro-Nova AstroAnt Yaoki": "Intuitive Machines",
           "Blue Ghost M1": "Firefly Aerospace", "Falcon 9-425 upper stage (2025-010D)": "SpaceX"}
FAR_LON = 90                   # the Moon list: "objects at greater than 90 degrees east or west are on the far side"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "t": return f"{float(v) / 1000:,.1f}"          # kilograms as tonnes
    if f == "t0": return f"{round(float(v) / 1000):,}"
    if f == "word": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Word": return (WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}").capitalize()
    raise ValueError(f)


def fill(text, R, fmtf=fmt, keep=("DOI", "BLOG_URL", "DOI_URL")):
    """Replace {{path|format}} tokens with values from results.json; leave the publisher's placeholders alone."""
    def rep(m):
        if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE_"):
            return m.group(0)
        return fmtf(get(R, m.group(1)), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def wrap_lon(lon):
    """Planetocentric longitudes given east-positive from 0 to 360, or west longitudes beyond 180, to -180..180."""
    v = ((float(lon) + 180.0) % 360.0) - 180.0
    return 180.0 if v == -180.0 and float(lon) > 0 else v
