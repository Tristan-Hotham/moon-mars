# Junk on the Moon and Mars: every human-made object on two worlds

A map and analysis of every human-made object on the Moon and Mars, built from English Wikipedia's lists: 133 objects on the Moon (104 table rows plus 29 small items left by Apollo crews) and 27 on Mars (20 rows plus 7 smaller pieces). Where each one is, who left it, when, how heavy it is and whether it still works.

Interactive page: https://maps.tristanhotham.com/moon-mars/
Paper: https://doi.org/10.5281/zenodo.23872995
Blog post: https://blog.tristanhotham.com/2026/10/31/moon-mars/

## Headline results

- Mass: 203,228 kg on the Moon and 10,380 kg on Mars, counting each listed figure once. The United States left 58% of the lunar mass, the Soviet Union and Russia 31%, China 7%. The five Apollo S-IVB third stages (about 14 t each) are the heaviest objects and 34% of the total. Wikipedia's own totals: 222,729 kg (table) and "over 187,400 kilograms" (introduction).
- Timeline: Luna 2 hit the Moon on 13 September 1959; Mars 2 reached Mars on 27 November 1971. 34 table objects reached the Moon in the 1960s and 28 in the 1970s, none from 1977 to 1989, and 20 so far in the 2020s from 7 countries; 9 objects in the table came from companies, 3 of which landed softly.
- Landing: 28 of 40 soft landing attempts on the Moon worked (70%); 11 of 16 on Mars (69%), 9 of 10 for the United States, 1 of 3 for the Soviet Union, 0 of 2 for Europe and 1 of 1 for China.
- Status: of the 104 Moon rows, 36 arrived softly and 68 hard; 3 are listed as operating (all Chinese). On Mars 2 still work (Curiosity, Perseverance). Six lunar retroreflectors are still used for laser ranging.
- Far side: 15 of the 87 located Moon table objects (17%) lie on the far side; only China has landed there.

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

- Tables parsed cell by cell with BeautifulSoup, expanding row and column spans; footnote markers removed; coordinates from each cell's decimal geo span; longitudes wrapped to -180..180 (the Mars table uses west longitudes beyond 180 and east longitudes 0 to 360 for some rows). No coordinates are invented: 17 Moon objects have none.
- Mass: the tables' kilograms; a value shared by two rows, or repeated for a rover (Yutu, Yutu-2), is counted once. Bounds and launch masses are taken as given.
- Small items: each named in a source sentence that the build checks, and placed at its landing site's coordinates (the Fallen Astronaut and its plaque have their own).
- Type: my classification from the name (lander, rover or helicopter, impact or crash, rocket or ascent stage, small item). Status: the row colours. Far side: longitude beyond 90 degrees, as the Moon list defines it.
- Landing success: the landings list's colours (soft landing with data return, sample return, crewed) against attempts that crashed or lost contact; deliberate impacts excluded.
- The object tables and the landings list disagree by more than one degree on 8 of 86 shared positions; the object tables are used and the alternatives kept.

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

- Wikipedia contributors, CC BY-SA 4.0: "List of artificial objects on the Moon" (revision 1370338372), "List of artificial objects on Mars" (1373656289), "List of landings on extraterrestrial bodies" (1372275847), "Moon landing" (1380159374), "Fallen Astronaut" (1359569457), "Apollo Lunar Surface Experiments Package" (1354555151), "Lunar Roving Vehicle" (1380980067), "List of missions to the Moon" (1380188613), "List of missions to Mars" (1383270651).
- Base maps: OpenPlanetaryMap basemaps (OpenPlanetary), from NASA and USGS data.

Licences: code MIT; text, figures and derived data CC BY 4.0, except `data/objects.csv` and `data/landings.csv`, which are adapted from Wikipedia tables and are shared under CC BY-SA 4.0. See `LICENSE`.

## Citation

Hotham, T. (2026) Junk on the Moon and Mars: an inventory of every human-made object on two worlds. Zenodo. https://doi.org/10.5281/zenodo.23872995

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
