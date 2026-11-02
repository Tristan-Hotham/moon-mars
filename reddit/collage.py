"""r/dataisbeautiful collage for moon-mars: 2400 x 3200 px, light paper background with the two planetary maps framed
on it. Numbers from data/results.json. Labels sit on the paper beside each map, never over the imagery; leaders are
checked so none crosses another label or leader (figstyle.callouts)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.patches import Patch

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
OBJ = [dict(zip(SITE["cols"], r)) for r in SITE["rows"]]
for o in OBJ:
    o["type"] = TN[o["t"]]; o["group"] = GN[o["g"]]
M, A, MA = R["moon"], R["mars"], R["mass"]
BGc = "#F7F5F0"
WI, HI = 12, 16
fig = plt.figure(figsize=(WI, HI), dpi=200, facecolor=BGc)
fy = lambda inch: 1 - inch / HI                           # inches from the top -> figure fraction

fig.text(.045, fy(.35), "Everything humans have left on the Moon and Mars", fontproperties=DISP, fontsize=33, color=FG, va="top")
fig.text(.045, fy(1.05), f"{M['n']} objects on the Moon and {A['n']} on Mars, from Luna 2 in 1959 to the private landers of the 2020s: landers, rovers, crashed\n"
         f"probes, spent rocket stages, six flags and some golf balls. {MA['moon_t']:.0f} tonnes on the Moon, {MA['mars_t']:.1f} on Mars. Almost all of it is dead.",
         fontproperties=SERP, fontsize=13.2, color=FG, va="top", linespacing=1.45)

MW = .56; GW = MW * WI; GH = GW / 2


def panel(body, top_in, labels, title):
    ax = fig.add_axes([(1 - MW) / 2, fy(top_in + GH), MW, GH / HI])
    planet(ax, body)
    rows = [o for o in OBJ if o["body"] == body]
    pts = draw_objects(ax, body, rows, scale=1.0, k=4.5)
    fig.text((1 - MW) / 2, fy(top_in - .08), title, fontsize=13, color=FG, va="bottom", fontweight="medium")
    if body == "moon":
        for x in (-90, 90): ax.axvline(x, color="#FFFFFF", lw=1.1, ls=(0, (4, 3)), zorder=2)
        for x, s in ((-135, "far side"), (0, "near side"), (135, "far side")):
            fig.text((1 - MW) / 2 + MW * (x + 180) / 360, fy(top_in + GH + .06), s, ha="center", va="top", fontsize=9.5, color=MUT)
    items = []
    for nm, txt in labels:
        p = next(q for q in pts if q["name"] == nm)
        items.append((p["x"], max(p["y"], -89.2), txt, "l" if p["lon"] < 0 else "r"))
    callouts(fig, ax, items, fontsize=9.3, gap=.21 / HI, ymin=fy(top_in + GH - .06), ymax=fy(top_in + .06))
    return ax


MOON_L = [("Luna 9 Automated Lunar Station (lander capsule and airbag)", "Luna 9, first soft landing"), ("Luna 17 and Lunokhod 1", "Lunokhod 1 rover, 1970"),
          ("Chang'e 3 lander", "Chang'e 3, still working"), ("Chang'e 6 descent stage", "Chang'e 6, far side, 2024"), ("Ranger 4", "Ranger 4, crashed 1962"),
          ("LCROSS Centaur", "LCROSS impact, 2009"), ("Apollo 14 LM-8 Antares descent stage", "Apollo 14: golf balls"), ("Apollo 12 LM-6 Intrepid descent stage", "Apollo 12, 1969"),
          ("Hakuto-R Mission 2 Resilience", "ispace, crashed 2025"),
          ("Luna 2", "Luna 2, first to arrive, 1959"), ("Apollo 15 LM-10 Falcon descent stage", "Apollo 15: Fallen Astronaut"),
          ("Apollo 11 LM-5 Eagle descent stage", "Apollo 11, 1969"), ("Apollo 17 LM-12 Challenger descent stage", "Apollo 17, last crew, 1972"),
          ("Blue Ghost M1", "Firefly Blue Ghost, 2025"), ("Chang'e 4 lander", "Chang'e 4, far side, working"),
          ("Chandrayaan-3 Vikram lander and Pragyan rover", "Chandrayaan-3, 2023"), ("IM-2 Athena lander, with MAPP LV1, Micro-Nova, AstroAnt and Yaoki", "Intuitive Machines IM-1, IM-2")]
MARS_L = [("Viking 1 lander", "Viking 1, 1976"), ("Pathfinder (lander)", "Pathfinder and Sojourner"), ("Opportunity (rover)", "Opportunity, 2004"),
          ("Schiaparelli EDM (lander)", "Schiaparelli, crashed 2016"), ("Mars 6 lander", "Mars 6, crashed 1974"), ("Phoenix (lander)", "Phoenix, 2008"),
          ("Mars 3 lander and PrOP-M rover", "Mars 3, first soft landing"), ("Viking 2 lander", "Viking 2, 1976"), ("Spirit (rover)", "Spirit, 2004"),
          ("Curiosity (rover)", "Curiosity, still working"), ("InSight (lander)", "InSight, 2018"), ("Perseverance (rover)", "Perseverance, still working"),
          ("Zhurong (rover)", "China's Zhurong, 2021"), ("Beagle 2 (lander)", "Beagle 2, 2003"), ("Mars 2 lander and PrOP-M rover", "Mars 2, crashed 1971"),
          ("Mars Polar Lander and Deep Space 2 probes", "Mars Polar Lander, 1999")]
panel("moon", 2.05, MOON_L, "")
fig.text(.045, fy(1.95), f"THE MOON  ·  {M['n']} objects, {MA['moon_t']:.0f} tonnes", fontsize=13, color=FG, va="bottom", fontweight="medium")
panel("mars", 2.05 + GH + .85, MARS_L, "")
fig.text(.045, fy(2.05 + GH + .75), f"MARS  ·  {A['n']} objects, {MA['mars_t']:.1f} tonnes", fontsize=13, color=FG, va="bottom", fontweight="medium")
y_leg = 2.05 + 2 * GH + .85 + .25
fig.text(.5, fy(y_leg), f"Base maps: {OPM_ATT}. Plain bands beyond 85 degrees: no imagery. Small items are placed at their landing sites.", ha="center", va="top", fontsize=8.6, color=MUT)

# ---- full legend under the maps
LP = SERP.copy(); LP.set_size(11.5)
fig.legend(handles=legend_handles(item_label="Small items (flags, plaques, heat shields...), one star per site"), loc="upper center", bbox_to_anchor=(.5, fy(y_leg + .3)), ncol=5,
           frameon=False, prop=LP, handletextpad=.35, columnspacing=1.2)
fig.legend(handles=[Patch(color=GC[g], label=g) for g in GN], loc="upper center", bbox_to_anchor=(.5, fy(y_leg + .72)), ncol=4, frameon=False, prop=LP,
           handlelength=1.1, columnspacing=1.3, handletextpad=.45)

# ---- numbers row
yn = y_leg + 1.65
nums = [(f"{MA['moon_t']:.0f} t", HOT, f"of hardware on the Moon,\n{MA['us_moon_pct']:.0f}% of it American"),
        (f"{MA['sivb_pct']:.0f}%", "#8C8478", f"of that is just five spent\nSaturn V rocket stages"),
        (f"{M['working'] + A['working']}", "#2E9A8C", f"objects still working: {M['working']} on\nthe Moon, {A['working']} on Mars"),
        (f"{R['land']['mars']['ok']}/{R['land']['mars']['n']}", RUST, f"attempts to land on Mars\nthat worked ({R['land']['mars']['pct']:.0f}%)")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, fy(yn), big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(xx, fy(yn + .62), small, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)

# ---- small panels: arrivals per decade and Mars landings
yp = yn + 1.55
D = R["decades"]
a = fig.add_axes([.075, fy(yp + 1.75), .42, 1.45 / HI]); a.set_facecolor(BGc)
xs = np.arange(len(D))
a.bar(xs - .2, [d["moon"] for d in D], .38, color="#6E6E6A", label="Moon")
a.bar(xs + .2, [d["mars"] for d in D], .38, color=RUST, label="Mars")
for i, d in enumerate(D):
    for k, b in ((-.2, "moon"), (.2, "mars")):
        if d[b]: a.text(i + k, d[b] + 1, str(d[b]), ha="center", fontsize=8.5, color=FG)
a.set_xticks(xs); a.set_xticklabels([f"{d['dec']}s"[2:] if False else f"'{str(d['dec'])[2:]}s" for d in D], fontsize=9.5); spines(a); a.set_yticks([]); a.spines["left"].set_visible(False)
a.set_ylim(0, 55); a.legend(frameon=False, fontsize=9.5, loc="upper right")
a.set_title("Objects arriving per decade: the space race, then a second rush", family=MONO, fontsize=10.5, color=FG, loc="left", pad=8)
b2 = fig.add_axes([.62, fy(yp + 1.75), .34, 1.45 / HI]); b2.set_facecolor(BGc); b2.axis("off")
b2.set_title("Soft landings that worked", family=MONO, fontsize=10.5, color=FG, loc="left", pad=8)
rows = [("Moon, all", R["land"]["moon"]["ok"], R["land"]["moon"]["n"], "#6E6E6A"), ("Mars, all", R["land"]["mars"]["ok"], R["land"]["mars"]["n"], RUST)]
LB = R["land"]["mars"]["by"]
rows += [("Mars, US", LB["United States"]["ok"], LB["United States"]["n"], GC["United States"]), ("Mars, USSR", LB["Soviet Union and Russia"]["ok"], LB["Soviet Union and Russia"]["n"], GC["Soviet Union and Russia"]),
         ("Mars, Europe", LB["Europe (ESA)"]["ok"], LB["Europe (ESA)"]["n"], GC["Europe (ESA)"]), ("Mars, China", LB["China"]["ok"], LB["China"]["n"], GC["China"])]
for i, (nm, ok, n, c) in enumerate(rows):
    yy = .9 - i * .165
    b2.text(0, yy, nm, fontsize=9.5, color=FG, va="center", transform=b2.transAxes)
    b2.barh([yy], [.45 * n / 40], left=.36, height=.11, color=c, alpha=.28, transform=b2.transAxes)
    b2.barh([yy], [.45 * ok / 40], left=.36, height=.11, color=c, transform=b2.transAxes)
    b2.text(.38 + .45 * n / 40, yy, f"{ok} of {n}", fontsize=9.5, va="center", transform=b2.transAxes)

fig.text(.045, .006, f"Source: Wikipedia, 'List of artificial objects on the Moon', '... on Mars', 'List of landings on extraterrestrial bodies' and related articles (CC BY-SA 4.0).\n"
         f"Mass: kilograms as listed, each figure counted once. Base maps: {OPM_ATT}.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/moon-mars", family=MONO, fontsize=8.3, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "junk_on_the_moon_and_mars.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
