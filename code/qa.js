// QA: open index.html at desktop and phone widths, log console errors, exercise the map, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8798; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here,
// so the page must work without its base map.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [], checks = [];
  const ok = (c, m) => { checks.push((c ? "ok   " : "FAIL ") + m); };
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/cartocdn|fastly|googleapis|gstatic/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError|tiles?/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8798) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(500); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map_moon");
    const nMoon = await p.locator(".mk").count(); ok(nMoon > 80, `${nm}: ${nMoon} Moon markers`);
    ok(await p.locator("#mapnote").innerText().then(t => /did not load/.test(t)), `${nm}: tile failure note shown`);
    // popup
    await p.evaluate(() => { const o = OBJ.find(o => o.name === "Apollo 11 LM-5 Eagle descent stage"); pick(o.id, true); });
    await p.waitForTimeout(1300);
    ok(await p.locator(".maplibregl-popup").count() === 1, `${nm}: popup opens`);
    ok(await p.locator(".maplibregl-popup a[href*='wikipedia']").count() === 1, `${nm}: popup has Wikipedia link`);
    await shot("#atlas", "popup_apollo11");
    // click a marker directly
    await p.evaluate(() => { home(); });
    await p.waitForTimeout(600);
    await p.locator(".mk").nth(5).click({ force: true }); await p.waitForTimeout(500);
    ok(await p.locator(".maplibregl-popup").count() === 1, `${nm}: clicking a marker opens its popup`);
    // slider and decade filter
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 1972; r.dispatchEvent(new Event("input")); });
    await p.waitForTimeout(500);
    const n72 = await p.evaluate(() => OBJ.filter(visible).length);
    ok(n72 > 50 && n72 < 120, `${nm}: up to 1972 shows ${n72}`);
    await shot("#atlas", "map_1972");
    await p.click('#modeRow [data-m="dec"]'); await p.waitForTimeout(400);
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 2024; r.dispatchEvent(new Event("input")); });
    await p.waitForTimeout(500);
    const n20 = await p.evaluate(() => OBJ.filter(visible).length);
    ok(n20 === await p.evaluate(() => R.decades.find(d => d.dec === 2020).moon), `${nm}: 2020s decade shows ${n20}`);
    await shot("#atlas", "map_2020s");
    await p.click('#modeRow [data-m="upto"]'); await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 2026; r.dispatchEvent(new Event("input")); });
    // type filter
    await p.locator("#typeRow .btn").nth(4).click(); await p.waitForTimeout(300);
    ok(await p.evaluate(() => OBJ.filter(visible).every(o => o.t !== 4)), `${nm}: type filter hides small items`);
    await p.locator("#typeRow .btn").nth(4).click();
    // layers panel
    await p.locator("#atlas").scrollIntoViewIfNeeded();
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.locator('.lyrPanel [data-k="sites"]').check(); await p.waitForTimeout(400);
    ok(await p.locator(".mlab.site").count() > 0, `${nm}: landing-site names layer`);
    await p.locator('.lyrPanel [data-k="grat"]').uncheck(); await p.waitForTimeout(300);
    ok(await p.evaluate(() => map.getLayoutProperty("grat", "visibility") === "none"), `${nm}: graticule toggles off`);
    await shot("#map", "layers_panel");
    await p.locator('.lyrPanel [data-k="grat"]').check(); await p.locator('.lyrPanel [data-k="sites"]').uncheck();
    await p.click(".lyrBtn");
    // Mars
    await p.click('#bodyRow [data-b="mars"]'); await p.waitForTimeout(800);
    const nMars = await p.evaluate(() => OBJ.filter(visible).length);
    ok(nMars === await p.evaluate(() => R.mars.n), `${nm}: Mars shows ${nMars}`);
    await shot("#atlas", "map_mars");
    await p.evaluate(() => { const o = OBJ.find(o => o.name === "Perseverance (rover)"); pick(o.id, true); });
    await p.waitForTimeout(1300); await shot("#atlas", "popup_perseverance");
    await p.click('#bodyRow [data-b="moon"]'); await p.waitForTimeout(500);
    for (const c of ["massChart", "decChart", "landChart", "statusChart", "poleChart", "heavyTable", "boomTable", "cards", "objTable"]) await shot("#" + c, c);
    // full screen
    await p.locator("#atlas").scrollIntoViewIfNeeded();
    ok(await p.locator(".mfs-btn").count() === 1, `${nm}: full-screen button present`);
    await p.click(".mfs-btn"); await p.waitForTimeout(1200);
    const fs = await p.evaluate(() => { const e = document.getElementById("map"); return !!document.fullscreenElement || e.classList.contains("mfs-fake"); });
    ok(fs, `${nm}: full screen on`);
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.click(".mfs-btn"); await p.waitForTimeout(600);
    if (nm === "phone") { await p.click("#theme"); await p.waitForTimeout(800); await shot("#atlas", "dark_map"); await shot("#massChart", "dark_mass"); }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(ov <= 0, `${nm}: horizontal overflow ${ov}px`);
    await p.close();
  }
  console.log(checks.join("\n"));
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
