"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; objects from data/site.json."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
C = SITE["cols"]
OBJ = [dict(zip(C, r)) for r in SITE["rows"]]
for o in OBJ:
    o["type"] = TN[o["t"]]; o["group"] = GN[o["g"]]; o["body_"] = o["body"]
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
TP = DISPB.copy(); TP.set_size(15)
TCOL = {"lander": NAVY, "rover": "#2E9A8C", "crash": HOT, "stage": "#8C8478", "item": "#E0A11B"}
W_IN = 12.0                                   # 12 in x 150 dpi = 1800 px for the blog


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def find(body, name):
    o = next(o for o in OBJ if o["body"] == body and o["name"] == name)
    return o["lon"], o["lat"]


# ---------- Moon map ----------
def body_map(body, labels, title, sub, zoom=None, zlabels=None, ztitle=""):
    """Whole-globe map with callouts on the paper either side; optionally a zoomed panel below (with its own callouts)."""
    mw = .56; gw = mw * W_IN; gh = gw / 2
    zh = gw * (zoom[3] - zoom[2]) / (zoom[1] - zoom[0]) if zoom else 0
    H = 1.6 + gh + .45 + (zh + .75 if zoom else 0) + .85
    fig = plt.figure(figsize=(W_IN, H), facecolor=BG)
    fy = lambda inch: inch / H                     # inches from the top to a figure fraction from the bottom
    y_top = 1 - fy(1.6)
    ax = fig.add_axes([(1 - mw) / 2, y_top - fy(gh), mw, fy(gh)])
    planet(ax, body)
    rows = [o for o in OBJ if o["body"] == body]
    gpts = draw_objects(ax, body, rows, scale=.9, k=4.5)
    fig.text(.012, 1 - fy(.25), title, fontproperties=DISPB, fontsize=20, color=FG, va="top")
    fig.text(.012, 1 - fy(.72), sub, fontsize=9.6, color=MUT, va="top", linespacing=1.45)
    if body == "moon":
        for x in (-90, 90): ax.axvline(x, color="#FFFFFF", lw=1.1, ls=(0, (4, 3)), zorder=2)
        for x, s_ in ((-135, "far side"), (0, "near side, facing Earth"), (135, "far side")):
            fig.text(ax.get_position().x0 + mw * (x + 180) / 360, y_top + fy(.07), s_, ha="center", va="bottom", fontsize=8.8, color=MUT)
    items = []
    for nm, txt in labels:
        p = next(q for q in gpts if q["name"] == nm)          # where the symbol was drawn (shared sites are spread on a ring)
        items.append((p["x"], max(p["y"], -89.2), txt, "l" if p["lon"] < 0 else "r"))
    callouts(fig, ax, items, fontsize=8.6, gap=fy(.215), ymin=y_top - fy(gh) + fy(.08), ymax=y_top - fy(.08))
    cap_y = y_top - fy(gh) - fy(.08)
    fig.text(.5, cap_y, f"Base map: {OPM_ATT}. Plain bands beyond 85 degrees north and south: no imagery.", ha="center", va="top", fontsize=7.6, color=MUT)
    if zoom:
        x0, x1, y0, y1 = zoom
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#FFFFFF", lw=1.3, zorder=8))
        zt = cap_y - fy(.5)
        fig.text(.5, zt + fy(.05), ztitle, ha="center", va="bottom", fontsize=11, color=FG, fontweight="medium")
        az = fig.add_axes([(1 - mw) / 2, zt - fy(zh), mw, fy(zh)])
        planet(az, body, ext=zoom, lw=1.3, frame="#FFFFFF")
        for sp in az.spines.values(): sp.set_edgecolor(FG)
        pts = draw_objects(az, body, [o for o in rows if o["lon"] is not None and x0 <= o["lon"] <= x1 and y0 <= o["lat"] <= y1], scale=1.25, k=1.2 * (x1 - x0) / 72)
        zi = []
        for nm, txt in zlabels:
            p = next(q for q in pts if q["name"] == nm)
            zi.append((p["x"], p["y"], txt, "l" if p["x"] < (x0 + x1) / 2 else "r"))
        callouts(fig, az, zi, fontsize=8.6, gap=fy(.215), ymin=zt - fy(zh) + fy(.08), ymax=zt - fy(.08))
    fig.legend(handles=legend_handles(item_label="Small items left by Apollo crews, one star per site" if body == "moon" else "Smaller pieces such as heat shields, one star per site"),
               loc="lower center", bbox_to_anchor=(.5, fy(.5)), ncol=5, frameon=False, fontsize=9, handletextpad=.3, columnspacing=1.3)
    groups = [g for g in GN if any(o["group"] == g for o in rows if o["type"] != "item")]
    fig.legend(handles=[Patch(color=GC[g], label="Soviet Union" if body == "mars" and g.startswith("Soviet") else g) for g in groups], loc="lower center", bbox_to_anchor=(.5, fy(.08)), ncol=len(groups), frameon=False, fontsize=9,
               handlelength=1, columnspacing=1.1, handletextpad=.4)
    return fig


M, A = R["moon"], R["mars"]
MOON_L = [("Luna 9 Automated Lunar Station (lander capsule and airbag)", "Luna 9 (first soft landing) 1966"),
          ("Luna 17 and Lunokhod 1", "Luna 17 and Lunokhod 1, 1970"), ("Chang'e 3 lander", "Chang'e 3 and Yutu, 2013"),
          ("Chang'e 5 descent stage", "Chang'e 5, 2020"), ("Chang'e 6 descent stage", "Chang'e 6, 2024"), ("Ranger 4", "Ranger 4, 1962"),
          ("LCROSS Centaur", "LCROSS, 2009"), ("Hakuto-R Mission 2 Resilience", "Hakuto-R Mission 2, 2025"), ("Lunar Orbiter 3", "Lunar Orbiter 3, 1966"),
          ("Blue Ghost M1", "Blue Ghost M1, 2025"), ("Luna 24 descent stage", "Luna 23 and 24, 1974 and 1976"),
          ("Chandrayaan-3 Vikram lander and Pragyan rover", "Chandrayaan-3, 2023"), ("Chang'e 4 lander", "Chang'e 4 and Yutu-2, 2019"),
          ("IM-2 Athena lander, with MAPP LV1, Micro-Nova, AstroAnt and Yaoki", "IM-1 and IM-2, 2024 and 2025"), ("Lunar Prospector", "Lunar Prospector, 1999"),
          ("Hakuto-R Mission 1", "Hakuto-R Mission 1, 2023"), ("Chang'e 1", "Chang'e 1, 2009")]
MOON_Z = [("Luna 2", "Luna 2 (first to arrive) 1959"), ("Apollo 15 LM-10 Falcon descent stage", "Apollo 15 (Fallen Astronaut) 1971"),
          ("Apollo 17 LM-12 Challenger descent stage", "Apollo 17 (last crew) 1972"), ("Apollo 11 LM-5 Eagle descent stage", "Apollo 11, 1969"),
          ("Apollo 16 LM-11 Orion descent stage", "Apollo 16, 1972"), ("SLIM", "SLIM, 2024"), ("Ranger 7", "Ranger 7, 1964"),
          ("Apollo 12 LM-6 Intrepid descent stage", "Apollo 12, 1969"), ("Surveyor 3 (separate from descent stage)", "Surveyor 3, 1967"),
          ("Apollo 14 LM-8 Antares descent stage", "Apollo 14 (golf balls) 1971"), ("Apollo 14 S-IVB (S-IVB-509)", "Apollo 14 S-IVB, 1971"),
          ("Apollo 15 S-IVB (S-IVB-510)", "Apollo 15 S-IVB, 1971"), ("Beresheet", "Beresheet, 2019"), ("Surveyor 6 (separate from descent stage)", "Surveyor 6, 1967")]
fig = body_map("moon", MOON_L, f"Everything on the Moon: {M['n']} objects",
               f"{M['n_table']} landers, impactors and stages from Wikipedia's list ({M['no_coords']} of them without a known place, not shown), plus {M['n_items']} small items\n"
               f"left by Apollo crews, placed at their landing sites. Colour: who left it. Symbol: what it is.",
               zoom=(-32, 40, -14, 35), zlabels=MOON_Z, ztitle="Zoom: the middle of the near side, where all six Apollo crews landed")
both(fig, "moon_map")

MARS_L = [("Viking 1 lander", "Viking 1, 1976"), ("Pathfinder (lander)", "Pathfinder and Sojourner, 1997"), ("Opportunity (rover)", "Opportunity, 2004"),
          ("Schiaparelli EDM (lander)", "Schiaparelli (crashed) 2016"), ("Mars 6 lander", "Mars 6 (crashed) 1974"), ("Phoenix (lander)", "Phoenix, 2008"),
          ("Mars 3 lander and PrOP-M rover", "Mars 3 (first soft landing) 1971"), ("Viking 2 lander", "Viking 2, 1976"), ("Spirit (rover)", "Spirit, 2004"),
          ("Curiosity (rover)", "Curiosity (working) 2012"), ("InSight (lander)", "InSight, 2018"), ("Perseverance (rover)", "Perseverance (working) 2021"),
          ("Zhurong (rover)", "Tianwen-1 and Zhurong, 2021"), ("Beagle 2 (lander)", "Beagle 2, 2003"), ("Mars 2 lander and PrOP-M rover", "Mars 2 (first to arrive) 1971"),
          ("Mars Polar Lander and Deep Space 2 probes", "Mars Polar Lander, 1999")]
fig = body_map("mars", MARS_L, f"Everything on Mars: {A['n']} objects",
               f"{A['n_table']} landers, rovers and crash sites from Wikipedia's list, plus {A['n_items']} smaller pieces the article names, placed at their landing sites.\n"
               f"The positions of Mars 2, 3 and 6 and Mars Polar Lander are estimates. Colour: who left it. Symbol: what it is.")
both(fig, "mars_map")

# ---------- mass by country ----------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 4.9), facecolor=BG, gridspec_kw={"width_ratios": [1.15, 1]})
fig.subplots_adjust(left=.2, right=.97, wspace=.85, top=.8, bottom=.06)
for ax, b, tot in ((axs[0], "moon", R["mass"]["moon_kg"]), (axs[1], "mars", R["mass"]["mars_kg"])):
    rows = sorted(R["mass"][f"{b}_groups"], key=lambda r: -r["kg"])[::-1]
    ax.set_facecolor(BG)
    v = [r["kg"] / 1000 for r in rows]
    ax.barh([SHORT[r["group"]] if b == "moon" or r["group"] != "Soviet Union and Russia" else "USSR" for r in rows], v, color=[GC[r["group"]] for r in rows], height=.66)
    for i, r in enumerate(rows):
        ax.text(v[i] + max(v) * .02, i, f"{r['kg'] / 1000:,.1f} t ({r['pct']:.0f}%)" if r["kg"] >= 1000 else f"{r['kg']:,.0f} kg", va="center", fontsize=9.5)
    ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
    ax.set_xlim(0, max(v) * 1.45)
    ax.set_title(f"{BODY[b]}: {tot / 1000:,.1f} tonnes", loc="left", color=FG, fontproperties=TP)
fig.text(.012, .955, "Who left the most mass, in tonnes", fontsize=12.5, color=FG, va="top", fontweight="medium")
fig.text(.012, .905, "Kilograms as listed by Wikipedia, each shared or repeated figure counted once. Small items have no mass and add nothing. Scales differ.", fontsize=9, color=MUT, va="top")
both(fig, "mass")

# ---------- objects per decade ----------
D = R["decades"]
fig = plt.figure(figsize=(W_IN, 5.0), facecolor=BG); ax = fig.add_axes([.07, .2, .9, .6]); ax.set_facecolor(BG)
xs = np.arange(len(D)); w = .38
for k, b in enumerate(("moon", "mars")):
    base = np.zeros(len(D))
    for t in TN:
        v = np.array([d[f"{b}_{t}"] for d in D], float)
        ax.bar(xs + (k - .5) * w * 1.05, v, w, bottom=base, color=TCOL[t], edgecolor=BG, lw=.6, hatch=None if b == "moon" else "////")
        base += v
    for i, d in enumerate(D):
        if d[b]: ax.text(xs[i] + (k - .5) * w * 1.05, d[b] + .8, f"{d[b]}", ha="center", fontsize=9, color=FG)
ax.set_xticks(xs); ax.set_xticklabels([f"{d['dec']}s" for d in D]); spines(ax); ax.set_ylabel("objects arriving")
ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.set_ylim(0, max(max(d["moon"], d["mars"]) for d in D) * 1.15)
ax.text(xs[3], 4, "nothing\narrives\n1977 to 1989", ha="center", fontsize=9, color=MUT)
fig.text(.012, .955, "Objects arriving per decade: Moon (solid) and Mars (hatched)", fontsize=12.5, color=FG, va="top", fontweight="medium")
fig.text(.012, .905, f"Year as listed (for some orbiters, the launch year). The 2020s are not over yet. One object without a year (SELENE's Ouna) is left out.", fontsize=9, color=MUT, va="top")
fig.legend(handles=[Patch(color=TCOL[t], label=TYPE_NAME[t]) for t in TN], loc="lower center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(.5, -.005))
both(fig, "decades")

# ---------- landing success by country ----------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 4.6), facecolor=BG, gridspec_kw={"width_ratios": [1, 1]})
fig.subplots_adjust(left=.17, right=.97, wspace=.7, top=.78, bottom=.08)
for ax, b in ((axs[0], "moon"), (axs[1], "mars")):
    L = R["land"][b]; rows = sorted(L["rows"], key=lambda r: (r["n"], r["ok"]))
    ax.set_facecolor(BG)
    for i, r in enumerate(rows):
        ax.barh(i, r["n"], color=GC[r["group"]], alpha=.25, height=.62)
        ax.barh(i, r["ok"], color=GC[r["group"]], height=.62)
        ax.text(r["n"] + .25, i, f"{r['ok']} of {r['n']} ({r['pct']:.0f}%)", va="center", fontsize=9.5)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(["Soviet Union" if (b == "mars" and r["group"].startswith("Soviet")) else SHORT[r["group"]].replace("Others", "Israel") for r in rows])
    ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
    ax.set_xlim(0, max(r["n"] for r in rows) * 1.6)
    ax.set_title(f"{BODY[b]}: {L['ok']} of {L['n']} ({L['pct']:.0f}%)", loc="left", fontproperties=TP, color=FG)
fig.text(.012, .955, "Soft landing attempts that worked, by country", fontsize=12.5, color=FG, va="top", fontweight="medium")
fig.text(.012, .905, "Solid: landed and sent data back. Pale: attempts that crashed or fell silent. Deliberate impacts are not attempts. Source: Wikipedia, list of landings.", fontsize=9, color=MUT, va="top")
both(fig, "landing")

# ---------- heaviest objects ----------
Hv = R["heaviest"][:12][::-1]
fig = plt.figure(figsize=(W_IN, 5.6), facecolor=BG); ax = fig.add_axes([.36, .07, .6, .76]); ax.set_facecolor(BG)
ax.barh(range(len(Hv)), [h["kg"] / 1000 for h in Hv], color=[GC[h["group"]] for h in Hv], height=.66)
ax.set_yticks(range(len(Hv))); ax.set_yticklabels([f"{h['name'].replace(' rocket third stage (Vostok)', ' third stage')} ({h['year']})" for h in Hv], fontsize=9.5)
for i, h in enumerate(Hv):
    ax.text(h["kg"] / 1000 + .15, i, f"{h['kg'] / 1000:,.1f} t", va="center", fontsize=9.5)
spines(ax); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0); ax.set_xlim(0, 16.5)
fig.text(.012, .955, "The heaviest things humans have left on another world", fontsize=12.5, color=FG, va="top", fontweight="medium")
fig.text(.012, .905, "All on the Moon. The top five are the spent third stages of Saturn V rockets, crashed on purpose for seismic research.", fontsize=9, color=MUT, va="top")
fig.legend(handles=[Patch(color=GC[g], label=g) for g in ("United States", "Soviet Union and Russia")], loc="lower right", frameon=False, fontsize=9.5, bbox_to_anchor=(.97, .1))
both(fig, "heaviest")

# ---------- crashed or landed (paper and blog) ----------
SC = [("working", "#2E9A8C", "still working"), ("landed", NAVY, "landed, no longer working"), ("failed", HOT, "crashed or failed on landing"),
      ("impact", "#8C8478", "deliberate impact, end-of-mission crash or stage")]
fig = plt.figure(figsize=(W_IN, 3.3), facecolor=BG); ax = fig.add_axes([.08, .3, .9, .48]); ax.set_facecolor(BG)
for i, b in enumerate(("moon", "mars")):
    rows = [o for o in OBJ if o["body"] == b and o["table"] == 1]
    n = len(rows); x = 0
    for k, c, lab in SC:
        v = sum(1 for o in rows if STATUS[o["s"]][0] == k)
        if not v: continue
        ax.barh(1 - i, v / n * 100, left=x, color=c, height=.6, edgecolor=BG)
        if v / n > .04: ax.text(x + v / n * 50, 1 - i, str(v), ha="center", va="center", color="#FFFFFF", fontsize=10.5, fontweight="medium")
        x += v / n * 100
ax.set_yticks([1, 0]); ax.set_yticklabels([f"Moon ({M['n_table']})", f"Mars ({A['n_table']})"]); ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
spines(ax); ax.tick_params(axis="y", length=0, labelsize=10.5)
fig.text(.012, .95, "What happened to them: the rows of Wikipedia's tables, by status", fontsize=12.5, color=FG, va="top", fontweight="medium")
fig.legend(handles=[Patch(color=c, label=l) for _, c, l in SC], loc="lower center", ncol=4, frameon=False, fontsize=9.5, bbox_to_anchor=(.5, -.01))
both(fig, "status")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
MWF = .42; MHF = MWF * 12 / 2 / 6.3
for k, (b, y0) in enumerate((("moon", .955 - .04 - MHF), ("mars", .04))):
    ax = fig.add_axes([.55, y0, MWF, MHF]); planet(ax, b, grat=False, lw=.8)
    draw_objects(ax, b, [o for o in OBJ if o["body"] == b], scale=.5, k=4.5)
    t = f"{BODY[b]}: {R[b]['n']} objects, {R['mass'][b + '_kg'] / 1000:,.{0 if b == 'moon' else 1}f} tonnes"
    fig.text(.55, y0 + MHF + .012, t, fontsize=10.5, color=FG, va="bottom", fontweight="medium")
fig.text(.04, .86, "Junk", fontproperties=DISP, fontsize=60, color=HOT, va="top")
fig.text(.04, .70, "on the Moon", fontproperties=DISP, fontsize=34, color=FG, va="top")
fig.text(.04, .60, "and Mars", fontproperties=DISP, fontsize=34, color=RUST, va="top")
fig.text(.04, .44, f"Every human-made object on the\nMoon and Mars: landers, rovers,\ncrashed probes, rocket stages, flags\nand golf balls. Who left it, when,\nand whether it still works.", fontproperties=SERP, fontsize=13.5, color=FG, va="top", linespacing=1.35)
fig.text(.04, .04, "maps.tristanhotham.com/moon-mars", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
