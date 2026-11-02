"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, symbols by type, and the planetary base maps (OpenPlanetaryMap mosaics resampled to
plate carree by 02_geo.py), framed on light paper. Labels go on the paper around a map, never over the imagery;
leader lines are checked so that none crosses another label or leader."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
from PIL import Image
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, RULE, PAPER2 = "#F6F4EF", "#1D2128", "#636A72", "#DDD8CC", "#ECE8DF"
HOT, COOL, NAVY, RUST = "#C8322B", "#2F5FA7", "#1F2F4D", "#B4532A"
GC = dict(GROUPS)
MK = {"lander": "o", "rover": "s", "crash": "X", "stage": "D", "item": "*"}
MS = {"lander": 70, "rover": 62, "crash": 74, "stage": 52, "item": 120}
BODY = {"moon": "Moon", "mars": "Mars"}


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


_EQ = {}


def eq(body):
    if body not in _EQ:
        _EQ[body] = np.asarray(Image.open(f"{WORK}/{body}_eq.png"))
    return _EQ[body]


def planet(ax, body, ext=(-180, 180, -90, 90), grat=True, frame=FG, lw=1.0, nodata=PAPER2):
    """Plate carree base map. Rows beyond the Mercator limit (85.05 degrees) have no imagery and show as paper."""
    ax.set_facecolor(nodata)
    ax.imshow(eq(body), extent=(-180, 180, -90, 90), origin="upper", interpolation="lanczos", zorder=0)
    if grat:
        for x in range(-150, 180, 30): ax.axvline(x, color="#FFFFFF", lw=.45, alpha=.35, zorder=1)
        for y in range(-60, 90, 30): ax.axhline(y, color="#FFFFFF", lw=.45, alpha=.35, zorder=1)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_edgecolor(frame); s.set_linewidth(lw)


def layout(rows, k=1.0):
    """Spread objects that share a position on a small ring so each symbol shows; k is about one symbol's width in
    degrees on the axes being drawn. Items: one star per site."""
    out, groups = [], {}
    for r in rows:
        if r["lat"] is None: continue
        key = (round(r["lat"], 1), round(r["lon"], 1), r["type"] == "item")
        groups.setdefault(key, []).append(r)
    for (la, lo, it), g in groups.items():
        if it:   # one star per site, nudged up and right of the site so it does not hide the lander
            out.append(dict(g[0], n_items=len(g), x=g[0]["lon"] + .8 * k, y=g[0]["lat"] + .8 * k)); continue
        n = len(g)
        for i, r in enumerate(sorted(g, key=lambda r: TN.index(r["type"]))):
            if n == 1: out.append(dict(r, x=r["lon"], y=r["lat"])); continue
            a = np.pi / 2 + 2 * np.pi * i / n; rad = k * (.75 + .18 * n)
            out.append(dict(r, x=r["lon"] + rad * np.cos(a), y=r["lat"] + rad * np.sin(a)))
    return out


def draw_objects(ax, body, rows, scale=1.0, ec="#FFFFFF", z=5, k=0.0):
    pts = layout([r for r in rows if r["body"] == body], k)
    for t in TN:
        q = [p for p in pts if p["type"] == t]
        if not q: continue
        if t == "item":
            ax.scatter([p["x"] for p in q], [p["y"] for p in q], s=[scale * (MS[t] + 18 * min(p["n_items"], 12)) for p in q], marker="*",
                       c="#FFFFFF", edgecolors=FG, linewidths=.8, zorder=z + 1)
        else:
            ax.scatter([p["x"] for p in q], [p["y"] for p in q], s=scale * MS[t], marker=MK[t], c=[GC[p["group"]] for p in q], edgecolors=ec,
                       linewidths=.9 * scale ** .5, zorder=z + (0 if t == "crash" else .5))
    return pts


def legend_handles(groups=None, types=True, item_label="Small items left by crews, one star per site"):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h = []
    if types:
        for t in TN:
            if t == "item":
                h.append(Line2D([], [], ls="", marker="*", ms=13, mfc="#FFFFFF", mec=FG, label=item_label))
            else:
                h.append(Line2D([], [], ls="", marker=MK[t], ms=8.5, mfc="#8C8478", mec="#FFFFFF", label=TYPE_NAME[t]))
    for g in (groups or []):
        h.append(Patch(color=GC[g], label=g))
    return h


def callouts(fig, ax, items, pad=.008, fontsize=9.5, gap=.032, ymin=.06, ymax=.94, color=FG, weight="medium"):
    """Label points from the paper margins left and right of the map axes. items: (x, y, text, side) in data units;
    side 'l' or 'r'. Labels sit right-aligned (left side) or left-aligned (right side) against the map frame, spread
    vertically; leaders run straight from the frame to the point. Slots are swapped until no two leaders cross, and
    the result is checked: no label overlaps another label, no leader crosses another leader or label."""
    from shapely.geometry import LineString, box
    fig.canvas.draw(); R = fig.canvas.get_renderer()
    axb = ax.get_position()
    placed = []
    for side in ("l", "r"):
        q = [it for it in items if it[3] == side]
        if not q: continue
        pts = [tuple(fig.transFigure.inverted().transform(ax.transData.transform((x, y)))) for x, y, _, _ in q]
        X = axb.x0 - pad if side == "l" else axb.x1 + pad
        order = list(np.argsort([-p[1] for p in pts]))
        ys, last = [], None
        for i in order:
            y = min(max(pts[i][1], ymin), ymax)
            if last is not None and last - y < gap: y = last - gap
            ys.append(y); last = y
        over = ymin - min(ys)
        if over > 0: ys = [y + over for y in ys]
        slot = {i: ys[j] for j, i in enumerate(order)}
        seg = lambda i: LineString([(X, slot[i]), pts[i]])
        for _ in range(200):
            swapped = False
            for a in range(len(q)):
                for b in range(a + 1, len(q)):
                    if seg(a).crosses(seg(b)):
                        slot[a], slot[b] = slot[b], slot[a]; swapped = True
            if not swapped: break
        for i, (x, y, s, _) in enumerate(q):
            t = fig.text(X - .004 if side == "l" else X + .004, slot[i], s, ha="right" if side == "l" else "left", va="center", fontsize=fontsize, color=color,
                         fontweight=weight, linespacing=1.15)
            bb = t.get_window_extent(R).transformed(fig.transFigure.inverted())
            fig.add_artist(plt.Line2D([X, pts[i][0]], [slot[i], pts[i][1]], transform=fig.transFigure, color=color, lw=.7, zorder=20))
            fig.add_artist(plt.Line2D([X, pts[i][0]], [slot[i], pts[i][1]], transform=fig.transFigure, color="#FFFFFF", lw=2.2, alpha=.55, zorder=19))
            placed.append((s, box(bb.x0, bb.y0, bb.x1, bb.y1), seg(i)))
    for a, ba, la in placed:
        x0, y0, x1, y1 = ba.bounds
        assert x1 <= axb.x0 + 1e-6 or x0 >= axb.x1 - 1e-6, ("label over the map", a)
        assert x0 >= 0 and x1 <= 1, ("label off the page", a)
        for b, bb_, lb in placed:
            if a == b: continue
            assert not ba.intersects(bb_), ("labels overlap", a, b)
            assert not la.crosses(lb) and not la.intersects(bb_), ("leader crosses", a, b)
    return placed
