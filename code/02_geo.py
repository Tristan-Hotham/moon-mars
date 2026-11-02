"""Base imagery for the static figures, the header and the collage: the OpenPlanetaryMap zoom 3 mosaics (web Mercator,
2048 x 2048 px, latitudes to +/-85.05 degrees) resampled to plate carree (equirectangular, 2048 x 1024 px, the whole
globe). Rows beyond +/-85.05 degrees have no imagery and are left transparent; the figures draw them as plain paper.
Also writes a graticule (every 30 degrees) for the page. Output: WORK/<body>_eq.png, data/graticule.json."""
import numpy as np
from PIL import Image
from common import *

LATMAX = np.degrees(np.arctan(np.sinh(np.pi)))      # 85.0511, the web Mercator limit
for body in ("moon", "mars"):
    src = np.asarray(Image.open(f"{RAW}/opm_{body}_z3_mercator.png").convert("RGB"))
    H, Wd = src.shape[:2]
    assert (H, Wd) == (2048, 2048)
    oh, ow = 1024, 2048
    lat = 90 - (np.arange(oh) + .5) * 180 / oh
    ok = np.abs(lat) < LATMAX
    y = (1 - np.log(np.tan(np.pi / 4 + np.radians(np.clip(lat, -LATMAX, LATMAX)) / 2)) / np.pi) / 2 * H
    yi = np.clip(np.floor(y).astype(int), 0, H - 1)
    out = np.zeros((oh, ow, 4), np.uint8)
    xi = np.clip(((np.arange(ow) + .5) * Wd / ow).astype(int), 0, Wd - 1)
    out[:, :, :3] = src[yi][:, xi]
    out[:, :, 3] = np.where(ok, 255, 0)[:, None]
    Image.fromarray(out, "RGBA").save(f"{WORK}/{body}_eq.png")
    print(body, "plate carree", out.shape, "rows without imagery:", int((~ok).sum()))

feats = []
for lon in range(-180, 181, 30):
    feats.append({"type": "Feature", "properties": {"k": "lon", "v": lon}, "geometry": {"type": "LineString", "coordinates": [[lon, la] for la in range(-85, 86, 5)]}})
for la in range(-60, 61, 30):
    feats.append({"type": "Feature", "properties": {"k": "lat", "v": la}, "geometry": {"type": "LineString", "coordinates": [[lo, la] for lo in range(-180, 181, 10)]}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/graticule.json")
print("graticule", len(feats))
