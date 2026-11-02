"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
M, A, MA, LM, LA, B, s = R["moon"], R["mars"], R["mass"], R["land"]["moon"], R["land"]["mars"], R["boom"], R["source"]
N = lambda v: f"{round(v):,}"
rev = s["rev"]
readme = f"""# Junk on the Moon and Mars: every human-made object on two worlds

A map and analysis of every human-made object on the Moon and Mars, built from English Wikipedia's lists: {M['n']} objects on the Moon ({M['n_table']} table rows plus {M['n_items']} small items left by Apollo crews) and {A['n']} on Mars ({A['n_table']} rows plus {A['n_items']} smaller pieces). Where each one is, who left it, when, how heavy it is and whether it still works.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Mass: {N(MA['moon_kg'])} kg on the Moon and {N(MA['mars_kg'])} kg on Mars, counting each listed figure once. The United States left {MA['us_moon_pct']:.0f}% of the lunar mass, the Soviet Union and Russia {MA['su_moon_pct']:.0f}%, China {MA['moon_by']['China']['pct']:.0f}%. The five Apollo S-IVB third stages (about 14 t each) are the heaviest objects and {MA['sivb_pct']:.0f}% of the total. Wikipedia's own totals: {N(MA['wiki_table_kg'])} kg (table) and "over 187,400 kilograms" (introduction).
- Timeline: Luna 2 hit the Moon on {R['first']['moon_date']}; Mars 2 reached Mars on {R['first']['mars_date']}. {B['moon_1960s_table']} table objects reached the Moon in the 1960s and {B['moon_1970s_table']} in the 1970s, none from 1977 to 1989, and {B['moon_2020s_table']} so far in the 2020s from {B['n_countries']} countries; {B['private_n']} objects in the table came from companies, {B['private_soft']} of which landed softly.
- Landing: {LM['ok']} of {LM['n']} soft landing attempts on the Moon worked ({LM['pct']:.0f}%); {LA['ok']} of {LA['n']} on Mars ({LA['pct']:.0f}%), {LA['by']['United States']['ok']} of {LA['by']['United States']['n']} for the United States, {LA['by']['Soviet Union and Russia']['ok']} of {LA['by']['Soviet Union and Russia']['n']} for the Soviet Union, 0 of 2 for Europe and 1 of 1 for China.
- Status: of the {M['n_table']} Moon rows, {M['soft']} arrived softly and {M['hard']} hard; {M['working']} are listed as operating (all Chinese). On Mars {A['working']} still work (Curiosity, Perseverance). Six lunar retroreflectors are still used for laser ranging.
- Far side: {M['far_table']} of the {M['with_coords_table']} located Moon table objects ({M['far_pct']:.0f}%) lie on the far side; only China has landed there.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). MapLibre with OpenPlanetaryMap raster tiles. |
| `header.png` | Social card, 1200 x 630. |
| `data/objects.csv` | **CC BY-SA 4.0.** Every object: body, name, mission, country, group, year, date, type, status, mass as listed and as counted, coordinates (and where they came from), far side flag, site, rovers carried, company, status text, Wikipedia link, source article and revision. |
| `data/landings.csv` | **CC BY-SA 4.0.** Landings and impacts on the Moon and Mars from the landings list, with soft landing attempt and success flags. |
| `data/mass_by_country.csv` | Mass and object counts by country or agency and body. |
| `data/objects_by_decade.csv` | Objects arriving per decade by body and type. |
| `data/landing_success.csv` | Soft landing attempts and successes by country and body. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/graticule.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Tables parsed cell by cell with BeautifulSoup, expanding row and column spans; footnote markers removed; coordinates from each cell's decimal geo span; longitudes wrapped to -180..180 (the Mars table uses west longitudes beyond 180 and east longitudes 0 to 360 for some rows). No coordinates are invented: {M['no_coords']} Moon objects have none.
- Mass: the tables' kilograms; a value shared by two rows, or repeated for a rover (Yutu, Yutu-2), is counted once. Bounds and launch masses are taken as given.
- Small items: each named in a source sentence that the build checks, and placed at its landing site's coordinates (the Fallen Astronaut and its plaque have their own).
- Type: my classification from the name (lander, rover or helicopter, impact or crash, rocket or ascent stage, small item). Status: the row colours. Far side: longitude beyond 90 degrees, as the Moon list defines it.
- Landing success: the landings list's colours (soft landing with data return, sample return, crewed) against attempts that crashed or lost contact; deliberate impacts excluded.
- The object tables and the landings list disagree by more than one degree on {R['n_disagree']} of {R['n_compared']} shared positions; the object tables are used and the alternatives kept.

## How to rerun

Needs Python 3 with beautifulsoup4, lxml, numpy, pandas, matplotlib, Pillow, shapely and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are in `raw/` (not in the repository's data release: `wiki_pages.json` and the two OpenPlanetaryMap mosaics). Intermediate files go to `/dev/shm/moonmars/work` (set `MMTMP` to change).

```
python3 code/01_parse.py        # parse the Wikipedia tables and texts, add small items, dates and checks
python3 code/02_geo.py          # base maps to plate carree, graticule
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Wikipedia contributors, CC BY-SA 4.0: "List of artificial objects on the Moon" (revision {rev['List_of_artificial_objects_on_the_Moon']}), "List of artificial objects on Mars" ({rev['List_of_artificial_objects_on_Mars']}), "List of landings on extraterrestrial bodies" ({rev['List_of_landings_on_extraterrestrial_bodies']}), "Moon landing" ({rev['Moon_landing']}), "Fallen Astronaut" ({rev['Fallen_Astronaut']}), "Apollo Lunar Surface Experiments Package" ({rev['Apollo_Lunar_Surface_Experiments_Package']}), "Lunar Roving Vehicle" ({rev['Lunar_Roving_Vehicle']}), "List of missions to the Moon" ({rev['List_of_missions_to_the_Moon']}), "List of missions to Mars" ({rev['List_of_missions_to_Mars']}).
- Base maps: {OPM_ATT}.

Licences: code MIT; text, figures and derived data CC BY 4.0, except `data/objects.csv` and `data/landings.csv`, which are adapted from Wikipedia tables and are shared under CC BY-SA 4.0. See `LICENSE`.

## Citation

Hotham, T. (2026) Junk on the Moon and Mars: an inventory of every human-made object on two worlds. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/meteorite-falls/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.

The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0 (Creative Commons Attribution 4.0),
with this exception:

  data/objects.csv and data/landings.csv are adapted from tables and text in
  English Wikipedia articles ("List of artificial objects on the Moon", "List of
  artificial objects on Mars", "List of landings on extraterrestrial bodies" and
  others; revision numbers in README.md) and are therefore shared under
  CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0). Credit
  "Wikipedia contributors" and Tristan Hotham, and share adaptations alike.

Base map imagery: OpenPlanetaryMap basemaps (OpenPlanetary), from NASA and USGS
data; it is not redistributed here except as rendered in the figures.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Everything humans have left on the Moon and Mars: {M['n']} objects and {MA['moon_t']:.0f} tonnes on the Moon, {A['n']} objects and {MA['mars_t']:.0f} tonnes on Mars. A third of the Moon's junk is five Saturn V rocket stages

## Body

I mapped every human-made object on the Moon and Mars from Wikipedia's lists, plus the small things the tables skip (six flags, the ladder plaques, Alan Shepard's golf balls, the Fallen Astronaut, the laser mirrors). The first arrival was Luna 2 in 1959. The Moon's junk came in two waves: {B['moon_1960s_table']} objects in the 1960s, {B['moon_1970s_table']} in the 1970s, nothing at all from 1977 to 1989, and already {B['moon_2020s_table']} in the 2020s, many from private companies. Almost all of it is dead: only {M['working']} lunar objects are listed as still operating, all Chinese, plus Curiosity and Perseverance on Mars. Landing is still hard: {LM['ok']} of {LM['n']} soft landing attempts on the Moon worked and {LA['ok']} of {LA['n']} on Mars. Caveats: masses are as listed (some launch masses), small items are placed at their landing sites, and two Wikipedia lists disagree on a few positions. Interactive map with a Moon/Mars switch and a year slider: {PAGE}

## Source comment

Source: English Wikipedia (CC BY-SA 4.0): "List of artificial objects on the Moon", "List of artificial objects on Mars", "List of landings on extraterrestrial bodies", plus "Moon landing", "Fallen Astronaut", "Apollo Lunar Surface Experiments Package" and "Lunar Roving Vehicle" for the small items. Base maps: OpenPlanetaryMap basemaps (OpenPlanetary), from NASA and USGS data.

Tools: Python (BeautifulSoup, pandas, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post, lic):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
