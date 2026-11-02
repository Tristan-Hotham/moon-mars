"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, graticule.json) is embedded. Facts stated in words are checked
here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23872995 and https://blog.tristanhotham.com/2026/10/31/moon-mars/
stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
M, A, MA, LM, LA, B = R["moon"], R["mars"], R["mass"], R["land"]["moon"], R["land"]["mars"], R["boom"]

# facts stated in words (page, blog, paper, collage)
assert R["first"]["moon"] == "Luna 2" and R["first"]["moon_date"] == "13 September 1959" and R["first"]["mars_date"] == "27 November 1971"
assert MA["sivb_n"] == 5 and all(13000 < h["kg"] < 14500 and "S-IVB" in h["name"] for h in R["heaviest"][:5])      # "five ... each about 14 tonnes"
assert MA["sivb_kg"] > MA["apollo_kg"] / 2                                                                          # "most of that is five objects"
assert R["heaviest_mars"][0]["name"] == "Tianwen-1 (lander)"
assert 19 <= MA["moon_kg"] / MA["mars_kg"] <= 21                                                                   # "about 20 times"
assert B["moon_2020s_table"] > B["moon_2000s_table"] + B["moon_2010s_table"]                                        # "more than the 2000s and 2010s put together"
assert B["moon_1980s_table"] == 0 and B["gap_first_after"] == 1990
assert B["private_soft"] == 3 and sorted(p["name"].split()[0] for p in B["private"] if p["status"] == "landed") == ["Blue", "IM-1", "IM-2"]
assert B["private"][0]["name"] == "Beresheet" and B["private"][-1]["company"] == "SpaceX" and B["private"][-1]["year"] == 2026
assert M["working"] == 3 and all(n.startswith("Chang'e") for n in M["working_names"])                            # "all Chinese"
assert A["working"] == 2 and A["working_names"] == ["Curiosity (rover)", "Perseverance (rover)"]
assert LM["by"]["China"]["ok"] == LM["by"]["China"]["n"] == 4                                                       # "four for four"
assert LM["commercial"]["n"] == 6 and LM["commercial"]["ok"] == 3
assert "Luna 25" in LM["by"]["Soviet Union and Russia"]["missions"] and "Luna 25" not in LM["by"]["Soviet Union and Russia"]["ok_missions"]
assert LA["by"]["Europe (ESA)"]["ok"] == 0 and LA["by"]["China"]["n"] == LA["by"]["China"]["ok"] == 1
assert LA["by"]["Soviet Union and Russia"]["ok_missions"] == ["Mars 3 lander"]
assert len(M["far_soft"]) < M["far_table"] / 2 and {"Ranger 4", "Lunar Orbiter 1", "Lunar Orbiter 2", "Lunar Orbiter 3"} <= set(M["far_names"])  # "most crashed"
assert {"Luna 5", "IM-1 Odysseus lander and EagleCam", "Mars Polar Lander and Deep Space 2 probes"} <= {d["name"] for d in R["disagree"]}
assert B["n_countries"] == 7 and M["n_countries"] == 10
assert R["fun"]["flags"] == 6 and R["fun"]["flags_standing"] == 5
assert all(c["dec"] != 1980 or c["moon"] == 0 for c in R["decades"])


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23872995", "https://blog.tristanhotham.com/2026/10/31/moon-mars/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE)).replace("/*GRAT*/", open(f"{DATA}/graticule.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    for us in ("color ", "aluminum", "program ", "honor ", "meters"):
        assert us not in vis.replace("Color", ""), us
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
