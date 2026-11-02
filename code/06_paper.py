"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23872995 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
OBJ = [dict(zip(SITE["cols"], r)) for r in SITE["rows"]]
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Junk_on_the_Moon_and_Mars"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
D = {d["dec"]: d for d in R["decades"]}
hard = lambda a, b: sum(1 for o in OBJ if o["body"] == "moon" and o["table"] == 1 and o["year"] and a <= o["year"] < b and o["touch"] == "hard")
assert hard(2000, 2010) > D[2000]["moon_table"] / 2 and hard(2010, 2020) > D[2010]["moon_table"] / 2      # "mostly hard impacts"
assert R["heaviest"][5]["name"].startswith("Luna 2")                                                        # "followed by the Luna 2 stage"
assert R["moon"]["far_soft"] == ["Chang'e 4 lander", "Chang'e 4 Yutu-2 rover", "Chang'e 6 descent stage", "Jinchan rover"]
assert R["mass"]["sivb_pct"] > 30 and R["mass"]["sivb_pct"] < 36                                             # "a third of it is five rocket stages"
mp = {d["name"]: d for d in R["disagree"]}
assert mp["Mars Polar Lander and Deep Space 2 probes"]["lat"] * mp["Mars Polar Lander and Deep Space 2 probes"]["alt_lat"] < 0   # different hemispheres
assert {"Surveyor 2", "IM-2 Athena lander, with MAPP LV1, Micro-Nova, AstroAnt and Yaoki", "Mars 2 lander and PrOP-M rover"} <= set(mp)


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f in ("t", "t0", "word", "Word"): return fmt(v, f)
    return tex(str(v))


GN_ = [g for g, _ in GROUPS]
rows = ""
for g in GN_:
    m, a = R["mass"]["moon_by"].get(g), R["mass"]["mars_by"].get(g)
    cell = lambda r: (f"{r['n']} & {r['kg']:,.0f} & {r['pct']:.1f}\\%" if r else "& &")
    rows += f"{tex(g)} & {cell(m)} & {cell(a)}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Objects and mass by country or agency. Mass in kilograms as listed, each figure counted once; small items have no mass.}\\label{tab:mass}"
      "\\begin{tabular}{lrrrrrr}\\toprule & \\multicolumn{3}{c}{Moon} & \\multicolumn{3}{c}{Mars}\\\\ Who & Objects & kg & Share & Objects & kg & Share\\\\\\midrule\n" + rows +
      f"\\midrule All & {R['moon']['n']} & {R['mass']['moon_kg']:,} & 100\\% & {R['mars']['n']} & {R['mass']['mars_kg']:,} & 100\\%\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(h['name'])} & {'Moon' if h['body'] == 'moon' else 'Mars'} & {h['year']} & {h['kg']:,}\\\\\n" for h in R["heaviest"][:10])
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten heaviest objects, kilograms as listed.}\\label{tab:heavy}"
      "\\begin{tabular}{llrr}\\toprule Object & Body & Year & kg\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for b in ("moon", "mars"):
    for r in sorted(R["land"][b]["rows"], key=lambda r: -r["n"]):
        nm = "Soviet Union" if b == "mars" and r["group"].startswith("Soviet") else r["group"].replace("Others (Israel, Luxembourg, UAE)", "Israel")
        rows += f"{'Moon' if b == 'moon' else 'Mars'} & {tex(nm)} & {r['n']} & {r['ok']} & {r['pct']:.0f}\\% & {r['first']}\\\\\n"
    rows += f"\\midrule {'Moon' if b == 'moon' else 'Mars'} & All & {R['land'][b]['n']} & {R['land'][b]['ok']} & {R['land'][b]['pct']:.0f}\\% & \\\\\n" + ("\\midrule\n" if b == "moon" else "")
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Soft landing attempts and successes by country (List of landings on extraterrestrial bodies).}\\label{tab:land}"
      "\\begin{tabular}{llrrrr}\\toprule Body & Who & Attempts & Succeeded & Rate & First attempt\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(i['name'])} & {'Moon' if i['body'] == 'moon' else 'Mars'} & {tex(i['mission'].replace('Mars Exploration Rover (Opportunity)', 'MER-B'))} & {i['year']}\\\\\n" for i in R["items"])
TI = ("\\begin{footnotesize}\\begin{longtable}{p{8.2cm}lp{3.4cm}r}\\caption{Small items added from the articles' text, placed at their landing sites.}\\label{tab:items}\\\\\\toprule Item & Body & Mission & Year\\\\\\midrule\\endhead\n"
      + rows + "\\bottomrule\\end{longtable}\\end{footnotesize}")
fmtc = lambda la, lo: f"{abs(la):.2f}{'S' if la < 0 else 'N'} {abs(lo):.2f}{'W' if lo < 0 else 'E'}"
rows = "".join(f"{tex(d['name'])} & {fmtc(d['lat'], d['lon'])} & {fmtc(d['alt_lat'], d['alt_lon'])} & {d['deg']:.1f}\\\\\n" for d in R["disagree"])
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{Objects whose positions in the object tables and in the landings list differ by more than one degree of arc.}\\label{tab:disagree}"
      "\\begin{tabular}{p{6.2cm}llr}\\toprule Object & Object table & Landings list & Degrees\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("MASS", TM), ("HEAVY", TH), ("LAND", TL), ("ITEMS", TI), ("DISAGREE", TD)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
