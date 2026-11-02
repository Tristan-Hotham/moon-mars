"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json, data/sites.json).

Definitions:
  * object: a row of the Moon or Mars table in Wikipedia's lists of artificial objects, plus the small items the
    articles name (flags, plaques, golf balls, retroreflectors and so on; see 01_parse.py). A row can hold more than
    one thing (Luna 17 and Lunokhod 1); I keep the article's rows as they are.
  * mass: the table's kilograms. Where a value is shared by two rows (rowspan) or repeated for a rover (Yutu, Yutu-2)
    it is counted once. Upper and lower bounds ('<5,727', '>700') are taken at face value. Small items have no mass.
  * soft-landed: the Moon table's 'landed' or 'operational' rows; on Mars the success and operational rows plus Mars 3
    and Beagle 2, which reached the surface intact but failed. Crashed: everything else (failed landings, deliberate
    impacts, spent orbiters, rocket stages).
  * still working: rows the tables colour as operational. Retroreflectors still used for laser ranging are counted
    separately.
  * landing success: from the 'List of landings on extraterrestrial bodies': a soft landing attempt succeeds when the
    article colours it as a soft landing with data return (or sample return, or a crewed landing). Deliberate impacts
    are not attempts. Landers that never reached their target (lost at launch or on the way) are not in that list.
  * far side of the Moon: longitude more than 90 degrees east or west, as the Moon list defines it."""
import numpy as np, pandas as pd
from common import *

P = jload(f"{WORK}/parsed.json")
O = pd.DataFrame(P["objects"])
L = pd.DataFrame(P["landings"])
REV = P["rev"]
pc = lambda a, b: round(100 * a / b, 1) if b else None
R = {}

# ---------- source ----------
O["table"] = (~O.raw_name.isin([r["raw_name"] for r in P["objects"] if r.get("quote")])).astype(int)
R["source"] = {"rev": REV, "missing": P["missing"], "moon_rows": int(((O.body == "moon") & (O.table == 1)).sum()), "mars_rows": int(((O.body == "mars") & (O.table == 1)).sum()),
               "items_moon": int(((O.body == "moon") & (O.table == 0)).sum()), "items_mars": int(((O.body == "mars") & (O.table == 0)).sum()),
               "landing_rows": len(L), "year": 2026}
s = R["source"]
assert s["moon_rows"] == 104 and s["mars_rows"] == 20, s

# ---------- counts per body ----------
def body_stats(b):
    a = O[O.body == b]; t = a[a.table == 1]
    d = {"n": len(a), "n_table": len(t), "n_items": len(a) - len(t),
         "types": {k: int((a.type == k).sum()) for k in TN}, "status": {k: int((a.status == k).sum()) for k in dict(STATUS)},
         "soft": int((t.touchdown == "soft").sum()), "hard": int((t.touchdown == "hard").sum()),
         "working": int(((t.status == "working")).sum()), "no_coords": int(a.lat.isna().sum()),
         "no_coords_names": a[a.lat.isna()].name.tolist(), "approx": int((a.approx == 1).sum()),
         "countries": sorted(t.country.unique().tolist()), "n_groups": int(t.group.nunique()),
         "first_year": int(t.year.min()), "rovers": [v for vs in a.rovers for v in vs], "uncertain": int(t.uncertain.sum())}
    d["n_rovers"] = len(d["rovers"]); d["n_countries"] = len(d["countries"])
    d["soft_pct"] = pc(d["soft"], d["n_table"]); d["hard_pct"] = pc(d["hard"], d["n_table"])
    d["working_names"] = t[t.status == "working"].name.tolist()
    return d


R["moon"], R["mars"] = body_stats("moon"), body_stats("mars")
M, A = R["moon"], R["mars"]
M["far"] = int(O[(O.body == "moon")].far.sum()); M["far_table"] = int(O[(O.body == "moon") & (O.table == 1)].far.sum())
withc = O[(O.body == "moon") & O.lat.notna() & (O.table == 1)]
M["near_table"] = len(withc) - M["far_table"]; M["with_coords_table"] = len(withc)
M["far_pct"] = pc(M["far_table"], len(withc))
M["far_names"] = O[(O.body == "moon") & (O.far == 1)].name.tolist()
M["far_soft"] = O[(O.body == "moon") & (O.far == 1) & (O.touchdown == "soft") & (O.table == 1)].name.tolist()
assert M["far_soft"] == ["Chang'e 4 lander", "Chang'e 4 Yutu-2 rover", "Chang'e 6 descent stage", "Jinchan rover"], M["far_soft"]
# the Moon article: "40 major objects landed softly"
M["table_soft_text"] = P["facts"]["table_soft_text"]
R["reflectors"] = {"apollo": ["Apollo 11", "Apollo 14", "Apollo 15"], "others": ["Lunokhod 1", "Lunokhod 2", "Chandrayaan-3"], "n": 6}

# ---------- mass ----------
def mass_by(b):
    a = O[(O.body == b)]
    tot = float(a.mass_count.sum())
    g = a.groupby("group").mass_count.sum()
    rows = [{"group": k, "kg": round(float(g.get(k, 0)), 1), "pct": pc(float(g.get(k, 0)), tot), "n": int((a.group == k).sum())} for k in GN if (a.group == k).any()]
    return tot, rows


mt, mrows = mass_by("moon"); at, arows = mass_by("mars")
R["mass"] = {"moon_kg": round(mt), "mars_kg": round(at), "moon_t": round(mt / 1000, 1), "mars_t": round(at / 1000, 1), "moon_groups": mrows, "mars_groups": arows,
             "moon_vs_mars_x": round(mt / at), "wiki_intro_kg": P["facts"]["wiki_moon_kg"], "wiki_table_kg": P["facts"]["table_total_kg"],
             "no_mass_moon": int(((O.body == "moon") & (O.table == 1) & O.mass_kg.isna()).sum())}
MG = {r["group"]: r for r in mrows}; AG = {r["group"]: r for r in arows}
R["mass"]["moon_by"] = MG; R["mass"]["mars_by"] = AG
R["mass"]["us_moon_pct"] = MG["United States"]["pct"]; R["mass"]["su_moon_pct"] = MG["Soviet Union and Russia"]["pct"]
R["mass"]["us_mars_pct"] = AG["United States"]["pct"]
sivb = O[O.raw_name.str.contains("S-IVB")]
R["mass"]["sivb_n"] = len(sivb); R["mass"]["sivb_kg"] = round(float(sivb.mass_count.sum())); R["mass"]["sivb_pct"] = pc(float(sivb.mass_count.sum()), mt)
R["mass"]["diff_vs_table"] = round(R["mass"]["wiki_table_kg"] - mt)
# apollo: everything with an Apollo mission
ap = O[(O.body == "moon") & O.mission.str.match(r"^Apollo \d+$")]
R["mass"]["apollo_kg"] = round(float(ap.mass_count.sum())); R["mass"]["apollo_pct"] = pc(float(ap.mass_count.sum()), mt); R["mass"]["apollo_n"] = len(ap)
assert len(sivb) == 5

# ---------- heaviest, first, timeline ----------
H = O[O.mass_count > 0].sort_values("mass_count", ascending=False)
R["heaviest"] = [{"name": r.name, "body": r.body, "kg": round(r.mass_count), "year": int(r.year), "type": r.type, "group": r.group} for r in H.head(15).itertuples()]
assert all("S-IVB" in r["name"] for r in R["heaviest"][:5])                     # "the five S-IVB stages are the heaviest"
R["heaviest_mars"] = [{"name": r.name, "kg": round(r.mass_count), "year": int(r.year)} for r in H[H.body == "mars"].head(5).itertuples()]
R["heaviest_soft"] = [{"name": r.name, "kg": round(r.mass_count), "year": int(r.year)} for r in H[(H.body == "moon") & (H.touchdown == "soft") & (H.type != "item")].head(5).itertuples()]
first = O[(O.body == "moon") & (O.table == 1)].sort_values("year").iloc[0]
R["first"] = {"moon": first["name"], "moon_date": first["date"], "moon_year": int(first["year"]),
              "mars": "Mars 2 lander and PrOP-M rover", "mars_date": O[O.raw_name == "Mars 2 lander and PrOP-M rover"].iloc[0]["date"]}
assert R["first"]["moon"] == "Luna 2" and R["first"]["moon_date"] == "13 September 1959" and R["first"]["mars_date"] == "27 November 1971"
f2 = O[O.raw_name == "Luna 2 Third stage of Vostok rocket"].iloc[0]
R["first"]["luna2_stage_kg"] = round(f2.mass_count); R["first"]["luna2_kg"] = round(O[O.raw_name == "Luna 2"].iloc[0].mass_count)

dec = []
for d in range(1950, 2030, 10):
    row = {"dec": d}
    for b in ("moon", "mars"):
        a = O[(O.body == b) & (O.year >= d) & (O.year < d + 10)]
        row[b] = len(a); row[b + "_table"] = int(a.table.sum())
        for t in TN: row[f"{b}_{t}"] = int((a.type == t).sum())
    dec.append(row)
R["decades"] = dec
D = {r["dec"]: r for r in dec}
R["boom"] = {"moon_2020s": D[2020]["moon"], "moon_2020s_table": D[2020]["moon_table"], "moon_2010s_table": D[2010]["moon_table"], "moon_2000s_table": D[2000]["moon_table"],
             "moon_1960s_table": D[1960]["moon_table"], "moon_1970s_table": D[1970]["moon_table"], "moon_1980s_table": D[1980]["moon_table"], "moon_1990s_table": D[1990]["moon_table"]}
b20 = O[(O.body == "moon") & (O.year >= 2020) & (O.table == 1)]
R["boom"]["groups"] = {g: int((b20.group == g).sum()) for g in GN if (b20.group == g).any()}
R["boom"]["countries"] = sorted(b20.country.unique().tolist()); R["boom"]["n_countries"] = len(R["boom"]["countries"])
priv = O[(O.private != "") & (O.body == "moon")]
R["boom"]["private_n"] = len(priv); R["boom"]["private"] = [{"name": r.name, "company": r.private, "year": int(r.year), "status": r.status} for r in priv.itertuples()]
R["boom"]["private_soft"] = int((priv.touchdown == "soft").sum())
R["boom"]["names"] = b20.name.tolist()
R["boom"]["since2019_table"] = int(((O.body == "moon") & (O.year >= 2019) & (O.table == 1)).sum())
R["boom"]["quiet_years"] = "1977 to 1989"
gap = O[(O.body == "moon") & (O.year > 1976) & (O.year < 1990)]
assert len(gap) == 0 and D[1980]["moon"] == 0                                        # no object arrived 1977 to 1989
R["boom"]["gap_first_after"] = int(O[(O.body == "moon") & (O.year > 1976)].year.min())
mars_dec = {r["dec"]: r["mars_table"] for r in dec}
R["mars_by_decade"] = mars_dec

# ---------- landing success (landings list) ----------
def landing(b):
    a = L[(L.body == b) & (L.attempt == 1)]
    rows = []
    for g in GN:
        q = a[a.group == g]
        if len(q): rows.append({"group": g, "n": len(q), "ok": int(q.success.sum()), "fail": int(len(q) - q.success.sum()), "pct": pc(q.success.sum(), len(q)),
                                "first": int(q.date.str[-4:].astype(int).min()), "missions": q.mission.tolist(), "ok_missions": q[q.success == 1].mission.tolist()})
    return {"n": len(a), "ok": int(a.success.sum()), "pct": pc(a.success.sum(), len(a)), "by": {r["group"]: r for r in rows}, "rows": rows}


R["land"] = {"moon": landing("moon"), "mars": landing("mars")}
LM_, LA_ = R["land"]["moon"], R["land"]["mars"]
assert LA_["n"] == 16 and LA_["ok"] == 11, (LA_["n"], LA_["ok"])
assert LA_["by"]["United States"]["n"] == 10 and LA_["by"]["United States"]["ok"] == 9 and LA_["by"]["China"]["ok"] == 1 and LA_["by"]["Europe (ESA)"]["ok"] == 0
assert LA_["by"]["Soviet Union and Russia"]["ok"] == 1 and LA_["by"]["Soviet Union and Russia"]["n"] == 3
lm = L[(L.body == "moon") & (L.attempt == 1)].copy(); lm["y"] = lm.date.str[-4:].astype(int)
R["land"]["moon"]["since2019"] = {"n": int((lm.y >= 2019).sum()), "ok": int(lm[lm.y >= 2019].success.sum())}
R["land"]["moon"]["since2019"]["pct"] = pc(R["land"]["moon"]["since2019"]["ok"], R["land"]["moon"]["since2019"]["n"])
R["land"]["moon"]["crewed"] = int(L.crewed.sum()); R["land"]["moon"]["sample"] = int(L[(L.body == "moon")]["sample"].sum())
lmc = lm[lm.mission.str.contains("IM-1|IM-2|Blue Ghost|Hakuto|Beresheet")]
R["land"]["moon"]["commercial"] = {"n": len(lmc), "ok": int(lmc.success.sum()), "missions": lmc.mission.tolist()}
assert R["land"]["moon"]["commercial"]["n"] == 6 and R["land"]["moon"]["commercial"]["ok"] == 3
R["land"]["moon"]["first_soft"] = "Luna 9, 3 February 1966"
assert lm[lm.success == 1].iloc[0].mission == "Luna 9" and lm[lm.success == 1].iloc[0].date == "3 February 1966"

# ---------- coordinates: the two lists disagree for a few objects ----------
def sep(la1, lo1, la2, lo2):
    p1, p2, l1, l2 = map(np.radians, (la1, la2, lo1, lo2))
    return float(np.degrees(2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))))


dis = []
for r in P["objects"]:
    if r.get("alt_lat") is not None and r["lat"] is not None:
        d = sep(r["lat"], r["lon"], r["alt_lat"], r["alt_lon"])
        if d > 1: dis.append({"name": r["name"], "body": r["body"], "lat": r["lat"], "lon": r["lon"], "alt_lat": r["alt_lat"], "alt_lon": r["alt_lon"], "deg": round(d, 1)})
R["disagree"] = dis; R["n_disagree"] = len(dis)
R["n_compared"] = sum(1 for r in P["objects"] if r.get("alt_lat") is not None and r["lat"] is not None)

# ---------- the fun list ----------
it = O[O.table == 0]
R["items"] = [{"name": r.name, "body": r.body, "mission": r.mission, "year": int(r.year), "note": r.status_raw, "src": r.src} for r in it.itertuples()]
R["fun"] = {"flags": int(it.name.str.contains("United States flag").sum()), "flags_standing": 5, "plaques": int(it.name.str.contains("ladder").sum()),
            "alsep": int(it.name.str.contains(r"\(ALSEP\)").sum()), "lrrr": int(it.name.str.contains("Retroreflector").sum()), "lrv": 3,
            "fallen_names": 14, "fallen_us": 8, "fallen_su": 6, "fallen_cm": 8.9, "alsep_end": "30 September 1977"}
assert R["fun"]["flags"] == 6 and R["fun"]["plaques"] == 6 and R["fun"]["alsep"] == 5 and R["fun"]["lrrr"] == 3
R["wiki"] = {"intro_kg": "187,400", "intro_lb": "413,100"}
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "att": OPM_ATT}

# ---------- data tables ----------
cols = ["id", "body", "name", "mission", "country", "group", "year", "date", "type", "status", "touchdown", "mass_kg", "mass_count", "mass_note", "lat", "lon",
        "approx", "coord_from", "far", "site", "rovers", "private", "uncertain", "status_raw", "wiki", "src"]
X = O.copy()
X["coord_from"] = X.coord_from.fillna("table")
X["rovers"] = X.rovers.map(lambda v: "; ".join(v))
X["src_revid"] = X.src.map(REV)
X["type"] = X.type.map(TYPE_NAME); X["status"] = X.status.map(STATUS_NAME)
X[cols + ["src_revid"]].rename(columns={"group": "country_group", "mass_kg": "mass_kg_as_listed", "mass_count": "mass_kg_counted", "far": "far_side",
                                        "status_raw": "status_as_listed", "wiki": "wikipedia_url", "src": "source_article", "approx": "approximate_position",
                                        "coord_from": "coordinates_from"}).to_csv(f"{DATA}/objects.csv", index=False)
Lx = L[["body", "mission", "country_raw", "group", "date", "lat", "lon", "attempt", "success", "crewed", "sample", "notes"]]
Lx.rename(columns={"country_raw": "country_as_listed", "group": "country_group", "attempt": "soft_landing_attempt", "success": "soft_landing_success", "notes": "notes_as_listed"}).to_csv(f"{DATA}/landings.csv", index=False)
pd.DataFrame([{"body": b, **r} for b, rows in (("moon", mrows), ("mars", arows)) for r in rows]).rename(columns={"group": "country_group", "kg": "mass_kg", "pct": "share_pct", "n": "objects"}).to_csv(f"{DATA}/mass_by_country.csv", index=False)
pd.DataFrame(dec).rename(columns={"dec": "decade"}).to_csv(f"{DATA}/objects_by_decade.csv", index=False)
pd.DataFrame([{"body": b, **{k: v for k, v in r.items() if k not in ("missions", "ok_missions")}, "successes": "; ".join(r["ok_missions"])} for b in ("moon", "mars") for r in R["land"][b]["rows"]]) \
    .rename(columns={"group": "country_group", "n": "attempts", "ok": "succeeded", "fail": "failed", "pct": "success_pct", "first": "first_attempt_year"}).to_csv(f"{DATA}/landing_success.csv", index=False)

# ---------- page data ----------
TI = {t: i for i, t in enumerate(TN)}; SI = {k: i for i, (k, _) in enumerate(STATUS)}; GI = {g: i for i, g in enumerate(GN)}
rows = []
for r in P["objects"]:
    rows.append([r["id"], r["body"], r["name"], r["mission"], r["country"], GI[r["group"]], r["year"], r["date"], TI[r["type"]], SI[r["status"]],
                 r["mass_kg"], r["mass_note"] if (r["mass_note"] or r["mass_shared"] or r["mass_dup"]) else "", r["lat"], r["lon"], int(r.get("approx", 0)),
                 r.get("approx_note", "") or ("estimated position" if r.get("approx") else ""), r["wiki"], r["status_raw"], r["far"], r["private"], r.get("site", ""),
                 r["touchdown"], int(r["type"] != "item" or not r.get("quote"))])
SITE = {"cols": ["id", "body", "name", "mission", "country", "g", "year", "date", "t", "s", "kg", "kgnote", "lat", "lon", "approx", "approxnote", "wiki", "status", "far", "private", "site", "touch", "table"],
        "rows": rows, "groups": GROUPS, "types": TYPES, "status": STATUS, "tiles": TILES, "att": OPM_ATT}
# landing-site names: the Moon from the Moon landing article's tables, Mars from the location column
sites = []
for b in ("moon", "mars"):
    seen = set()
    for r in P["objects"]:
        if r["body"] != b or r["lat"] is None or r["type"] in ("item", "stage") or not r.get("site"): continue
        k = r["site"]
        if k in seen: continue
        seen.add(k); sites.append({"body": b, "name": k, "lat": r["lat"], "lon": r["lon"], "mission": r["mission"]})
# mission labels: one per mission and place
labs = []
for b in ("moon", "mars"):
    seen = set()
    for r in sorted(P["objects"], key=lambda r: (r["type"] not in ("lander", "rover"), r["type"] == "item")):
        if r["body"] != b or r["lat"] is None: continue
        m = r["mission"].replace(" (on Hakuto-R Mission 1)", "").replace(" (on the Chang'e 5-T1 launch)", "")
        m = re.sub(r"^Mars Exploration Rover \((\w+)\)", r"\1", m)
        key = (m, round(r["lat"]), round(r["lon"]))
        if key in seen or r["type"] == "item": continue
        seen.add(key); labs.append({"body": b, "name": m if r["type"] != "stage" else r["name"], "lat": r["lat"], "lon": r["lon"], "major": int(r["type"] in ("lander", "rover"))})
SITE["sites"] = sites; SITE["labels"] = labs
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("moon", {k: M[k] for k in ("n", "n_table", "n_items", "types", "status", "soft", "hard", "working", "no_coords", "far_table", "near_table", "n_rovers", "n_countries")})
print("mars", {k: A[k] for k in ("n", "n_table", "n_items", "types", "status", "soft", "hard", "working", "n_rovers", "n_countries")})
print("mass", {k: v for k, v in R["mass"].items() if k not in ("moon_by", "mars_by")})
print("heaviest", R["heaviest"][:8]); print("heaviest soft", R["heaviest_soft"])
print("decades", dec); print("boom", R["boom"])
print("land moon", {k: v for k, v in LM_.items() if k != "rows"}); print("land mars", {k: (v if k != "by" else {g: (x["ok"], x["n"]) for g, x in v.items()}) for k, v in LA_.items() if k != "rows"})
print("disagree", dis); print("sites", len(sites), "labels", len(labs))
