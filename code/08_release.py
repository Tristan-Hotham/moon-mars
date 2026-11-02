"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23872995, https://doi.org/10.5281/zenodo.23872995 and https://blog.tristanhotham.com/2026/10/31/moon-mars/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Junk_on_the_Moon_and_Mars"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
MB, AB = R["mass"]["moon_by"], R["mass"]["mars_by"]
assert [round(MB[g]["kg"] / 1000, 1) for g in ("United States", "Soviet Union and Russia", "China", "India", "Japan")] == [117.9, 63.5, 15.1, 3.3, 3.0]
assert [round(AB[g]["kg"] / 1000, 1) for g in ("United States", "Soviet Union and Russia", "China")] == [5.2, 3.1, 1.5] and round(AB["Europe (ESA)"]["kg"]) == 610
D = {d["dec"]: d for d in R["decades"]}
assert (D[1960]["moon"], D[1970]["moon"], D[1980]["moon"], D[2020]["moon"]) == (44, 46, 0, 20)
assert D[1980]["mars"] == 0 and all(3 <= D[d]["mars"] <= 8 for d in (1970, 1990, 2000, 2010, 2020))
L = R["land"]
assert [(L["moon"]["by"][g]["ok"], L["moon"]["by"][g]["n"]) for g in ("United States", "Soviet Union and Russia", "China", "Japan", "India", "Others (Israel, Luxembourg, UAE)")] == [(14, 16), (8, 14), (4, 4), (1, 3), (1, 2), (0, 1)]
assert [(L["mars"]["by"][g]["ok"], L["mars"]["by"][g]["n"]) for g in ("United States", "Soviet Union and Russia", "Europe (ESA)", "China")] == [(9, 10), (1, 3), (0, 2), (1, 1)]
assert (L["moon"]["ok"], L["moon"]["n"], L["mars"]["ok"], L["mars"]["n"]) == (28, 40, 11, 16)
H = R["heaviest"]
assert 13.4 < H[4]["kg"] / 1000 < 14.1 and round(H[5]["kg"] / 1000, 1) == 9.1 and all(4000 <= h["kg"] < 6000 and h["name"].startswith("Luna") for h in H[6:12])
assert abs(R["mass"]["sivb_pct"] - 100 / 3) < 3                                                          # "a third"
assert 18 < R["mass"]["moon_kg"] / R["mass"]["mars_kg"] < 22 and round(R["mass"]["us_mars_pct"]) == 50   # "about a twentieth", "half of it American"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    from PIL import Image
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23872995"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
M, A, MA = R["moon"], R["mars"], R["mass"]
meta = {"title": "Junk on the Moon and Mars: every human-made object on two worlds, mapped",
        "slug": "moon-mars",
        "excerpt": f"I mapped every human-made object on the Moon and Mars from Wikipedia's lists: {M['n']} on the Moon and {A['n']} on Mars, {MA['moon_t']:.0f} tonnes and {MA['mars_t']:.1f} tonnes. A third of the Moon's junk is five Saturn V rocket stages, and almost all of it is dead.",
        "seo_description": f"A map of all {M['n'] + A['n']} human-made objects on the Moon and Mars: landers, rovers, crashes, rocket stages, flags and golf balls.",
        "tags": ["Moon", "Mars", "space exploration", "maps", "data visualisation", "Apollo", "lunar landings", "Wikipedia"],
        "header_alt": f"Title card reading 'Junk on the Moon and Mars' in red, black and rust on pale paper, beside two framed maps: a grey Moon scattered with coloured symbols for {M['n']} objects, crowded in the middle of the near side, and an orange Mars with {A['n']}."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/moon-mars_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"moon-mars/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"moon-mars/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "moon-mars/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Junk on the Moon and Mars: An Inventory of Every Human-Made Object on Two Worlds",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Data adapted from English Wikipedia (CC BY-SA 4.0); the derived object and landing tables are shared under CC BY-SA 4.0. Base maps: {OPM_ATT}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Moon", "Mars", "space exploration", "spacecraft", "lunar landings", "Mars landings", "space heritage", "Apollo", "Wikipedia", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "The files data/objects.csv and data/landings.csv inside the zip are adapted from Wikipedia and licensed CC BY-SA 4.0; everything else is CC BY 4.0 (text, figures, other data) or MIT (code).",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": WIKI + "List_of_artificial_objects_on_the_Moon", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": WIKI + "List_of_artificial_objects_on_Mars", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": WIKI + "List_of_landings_on_extraterrestrial_bodies", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj and "DSIT" not in sj and "DCMS" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
