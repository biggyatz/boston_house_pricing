"use strict";
const el = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const TERAI = new Set(["Chitwan", "Rupandehi", "Morang", "Sunsari", "Jhapa", "Kailali", "Banke", "Makwanpur"]);
const SQFT = { ropani: 5476, aana: 342.25, paisa: 85.5625, dam: 21.390625, bigha: 72900, kattha: 3645, dhur: 182.25 };

// Nepali number style: crore / lakh.
function npr(v, digits = 2) {
  if (v >= 1e7) return `Rs ${(v / 1e7).toFixed(digits).replace(/\.?0+$/, "")} crore`;
  if (v >= 1e5) return `Rs ${(v / 1e5).toFixed(digits - 1 < 0 ? 0 : digits - 1).replace(/\.?0+$/, "")} lakh`;
  return "Rs " + Math.round(v).toLocaleString("en-IN");
}
const nprShort = v => v >= 1e7 ? (v / 1e7).toFixed(1).replace(/\.0$/, "") + " Cr" : (v / 1e5).toFixed(0) + " L";

const tip = el("tooltip");
function showTip(e, title, rows) {
  tip.innerHTML = `<b>${esc(title)}</b>` + rows.map(([k, v]) => `<div class="row"><span>${esc(k)}</span><span>${esc(v)}</span></div>`).join("");
  tip.hidden = false;
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX + 14, y = e.clientY + 14;
  if (x + w > innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > innerHeight - 8) y = e.clientY - h - 14;
  tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px";
}
function bindTips(svg, lookup) {
  svg.querySelectorAll("[data-tip]").forEach(n => {
    n.addEventListener("pointermove", e => { const t = lookup(n.dataset.tip); showTip(e, t.title, t.rows); });
    n.addEventListener("pointerleave", () => { tip.hidden = true; });
  });
}
function hbar(x, y, w, h, r = 4) {
  w = Math.max(w, 1); r = Math.min(r, w, h / 2);
  return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
}
const median = a => { const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

let M, L;
const state = { type: "House", district: "Kathmandu", locality: "", road_ft: 13, storeys: 2.5 };
Promise.all([fetch("model.json").then(r => r.json()), fetch("listings.json").then(r => r.json())]).then(([m, l]) => { M = m; L = l; init(); });

function init() {
  renderKPIs();
  chips("type", ["House", "Land"], state.type, v => { state.type = v; el("storey-field").hidden = v !== "House"; update(); renderMarket(); });
  const dcounts = {};
  L.forEach(r => { dcounts[r.district] = (dcounts[r.district] || 0) + 1; });
  const districts = M.districts.filter(d => d !== "Other" && (dcounts[d] || 0) >= 5).sort((a, b) => dcounts[b] - dcounts[a]);
  chips("district", districts, state.district, v => { state.district = v; fillLocalities(); toggleUnits(); update(); });
  fillLocalities(); toggleUnits();
  el("locality").addEventListener("change", e => { state.locality = e.target.value; update(); });
  document.querySelectorAll(".area-inputs input").forEach(i => i.addEventListener("input", update));
  el("road").addEventListener("input", e => { state.road_ft = +e.target.value; el("road-o").textContent = e.target.value + " ft"; update(); });
  el("storeys").addEventListener("input", e => { state.storeys = +e.target.value; el("st-o").textContent = e.target.value; update(); });
  chips("mkt-type", ["House", "Land"], "House", v => { mktType = v; renderMarket(); });
  document.querySelectorAll("[data-table-toggle]").forEach(btn => btn.addEventListener("click", () => {
    const t = el(btn.dataset.tableToggle + "-table"); t.hidden = !t.hidden; btn.textContent = t.hidden ? "Show table" : "Hide table";
  }));
  renderAbout();
  update(); renderMarket();
  let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { update(); renderMarket(); }, 120); });
}

function chips(id, values, current, onPick) {
  const box = el(id);
  box.innerHTML = values.map(v => `<button class="chip" role="radio" data-v="${esc(v)}" aria-checked="${v === current}">${esc(v)}</button>`).join("");
  box.addEventListener("click", e => {
    const b = e.target.closest(".chip"); if (!b) return;
    box.querySelectorAll(".chip").forEach(c => c.setAttribute("aria-checked", c === b));
    onPick(b.dataset.v);
  });
}
function fillLocalities() {
  const locs = M.localities.filter(l => l.district === state.district).sort((a, b) => a.name.localeCompare(b.name));
  el("locality").innerHTML = `<option value="">Anywhere in ${esc(state.district)}</option>` +
    locs.map(l => `<option value="${esc(l.name)}">${esc(l.name)} (${l.n} listings)</option>`).join("");
  state.locality = "";
}
function toggleUnits() {
  const terai = TERAI.has(state.district);
  el("area-rapd").hidden = terai; el("area-bkd").hidden = !terai;
}
function areaAana() {
  const n = id => Math.max(0, parseFloat(el(id).value) || 0);
  const sqft = TERAI.has(state.district)
    ? n("b-b") * SQFT.bigha + n("b-k") * SQFT.kattha + n("b-d") * SQFT.dhur
    : n("a-r") * SQFT.ropani + n("a-a") * SQFT.aana + n("a-p") * SQFT.paisa + n("a-d") * SQFT.dam;
  return sqft / SQFT.aana;
}

function renderKPIs() {
  const sources = Object.keys(M.sources).length;
  const years = Object.keys(M.years).map(Number);
  el("lead-n").textContent = M.n.toLocaleString("en-IN");
  const kv = [
    ["Listings analysed", M.n.toLocaleString("en-IN"), `from ${sources} listing sites`],
    ["Areas covered", M.localities.length, `across ${M.districts.filter(d => d !== "Other").length} districts`],
    ["Listing years", `${Math.min(...years)}–${Math.max(...years)}`, `estimates at ${M.latest_year} levels`],
    ["Typical error", `±${M.cv.median_abs_pct_err}%`, "median, on held-out listings"],
  ];
  el("kpis").innerHTML = kv.map(([l, v, n]) => `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");
  el("sources").innerHTML = "Data: public listings from " + Object.entries(M.sources).map(([s, n]) => `<a href="https://${esc(s)}">${esc(s)}</a> (${n.toLocaleString("en-IN")})`).join(" and ") + ". Collected October 2026 within each site's robots.txt rules; no personal data is stored.";
}

function update() {
  const aana = areaAana();
  el("area-hint").textContent = aana > 0 ? `${aana.toFixed(2)} aana · ${Math.round(aana * SQFT.aana).toLocaleString("en-IN")} sq ft` : "Enter the land area";
  if (!(aana > 0.25)) { el("price").textContent = "–"; el("meta").innerHTML = ""; el("range-chart").innerHTML = ""; el("comps").innerHTML = ""; return; }
  const x = { type: state.type, district: state.district, locality: state.locality, area_aana: aana, road_ft: state.road_ft, storeys: state.type === "House" ? state.storeys : null };
  const p = predictPrice(M, x);
  el("price").textContent = npr(p.price);
  el("meta").innerHTML = `<span>Likely range <strong>${nprShort(p.low)} – ${nprShort(p.high)}</strong></span><span><strong>${npr(p.price / aana)}</strong> per aana</span>`;
  renderRange(p);
  renderComps(x, p.price);
}

function renderRange(p) {
  const host = el("range-chart"), W = Math.max(300, host.clientWidth), H = 64, m = { l: 8, r: 8 };
  const lo = p.low * 0.85, hi = p.high * 1.1, x = v => m.l + ((v - lo) / (hi - lo)) * (W - m.l - m.r);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Likely price range">`;
  s += `<rect x="${x(p.low)}" y="18" width="${x(p.high) - x(p.low)}" height="14" rx="4" fill="var(--accent-wash)"/>`;
  s += `<rect x="${x(p.q1)}" y="18" width="${x(p.q3) - x(p.q1)}" height="14" rx="4" fill="var(--accent)" opacity=".35"/>`;
  s += `<circle cx="${x(p.price)}" cy="25" r="7" fill="var(--accent)" class="dot"/>`;
  s += `<text class="tick" x="${x(p.low)}" y="50" text-anchor="middle">${nprShort(p.low)}</text><text class="tick" x="${x(p.high)}" y="50" text-anchor="middle">${nprShort(p.high)}</text>`;
  s += `<text class="tick" x="${x(p.low)}" y="12">Likely range (80%); darker band = middle 50%</text></svg>`;
  host.innerHTML = s;
}

function renderComps(x, est) {
  const score = r => (r.type === x.type ? 0 : 3) + (r.locality && r.locality === x.locality ? 0 : r.district === x.district ? 1 : 3) + Math.abs(Math.log(r.area / x.area_aana)) * 2 + (M.latest_year - r.year) * 0.15;
  const comps = L.filter(r => r.district === x.district).sort((a, b) => score(a) - score(b)).slice(0, 5);
  el("comps").innerHTML = comps.map(r => `
    <a class="comp" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">
      <span class="t">${esc(r.title)}</span><span class="p">${nprShort(r.price)}</span>
      <span class="m">${esc(r.type)} · ${r.area.toFixed(1)} aana · ${esc([r.locality, r.district].filter(Boolean).join(", "))}<span class="badge">${esc(r.source.replace(/\.com.*/, ""))} ${r.year}</span></span>
      <span class="m r">${nprShort(r.price / r.area)}/aana</span>
    </a>`).join("") || `<p class="sub">No listings in this district yet.</p>`;
}

let mktType = "House";
function renderMarket() {
  const groups = {};
  L.filter(r => r.type === mktType && r.locality).forEach(r => { const k = r.locality + " | " + r.district; (groups[k] = groups[k] || []).push(r.price / r.area); });
  const rows = Object.entries(groups).filter(([, v]) => v.length >= 4)
    .map(([k, v]) => ({ loc: k.split(" | ")[0], dist: k.split(" | ")[1], med: median(v), n: v.length }))
    .sort((a, b) => b.med - a.med).slice(0, 20);
  const host = el("mkt-chart");
  if (!rows.length) { host.innerHTML = `<p class="sub">Not enough ${mktType.toLowerCase()} listings per area yet.</p>`; el("mkt-table").innerHTML = ""; return; }
  const W = Math.max(300, host.clientWidth), labelW = Math.min(190, W * 0.4), rowH = 26, barH = 14, H = rows.length * rowH + 24;
  const max = Math.max(...rows.map(r => r.med)) * 1.12, x = v => labelW + (v / max) * (W - labelW - 60);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Median price per aana by area">`;
  const narrow = W < 520;
  const step = [1e6, 2e6, 5e6, 1e7, 2e7, 5e7].find(st => max / st <= (narrow ? 3 : 6));
  for (let t = 0; t <= max; t += step) s += `<line class="gridline" x1="${x(t)}" x2="${x(t)}" y1="0" y2="${H - 20}"/><text class="tick" x="${x(t)}" y="${H - 6}" text-anchor="middle">${t ? nprShort(t) : "0"}</text>`;
  rows.forEach((r, i) => {
    const y = i * rowH + 5;
    s += `<text class="lbl" x="${labelW - 8}" y="${y + barH / 2 + 4}" text-anchor="end">${esc(narrow ? r.loc : r.loc + ", " + r.dist)}</text>`;
    s += `<path d="${hbar(labelW, y, x(r.med) - labelW, barH)}" fill="var(--accent)"/>`;
    s += `<text class="val" x="${x(r.med) + 6}" y="${y + barH / 2 + 4}">${nprShort(r.med)}</text>`;
    s += `<rect class="hit" data-tip="${i}" x="0" y="${y - 6}" width="${W}" height="${rowH}"/>`;
  });
  s += `<line class="baseline" x1="${labelW}" x2="${labelW}" y1="0" y2="${H - 20}"/></svg>`;
  host.innerHTML = s;
  bindTips(host.querySelector("svg"), i => ({ title: `${rows[i].loc}, ${rows[i].dist}`, rows: [["Median per aana", npr(rows[i].med)], ["Listings", rows[i].n]] }));
  el("mkt-table").innerHTML = `<table><thead><tr><th>Area</th><th>District</th><th class="n">Median per aana</th><th class="n">Listings</th></tr></thead><tbody>` +
    rows.map(r => `<tr><td>${esc(r.loc)}</td><td>${esc(r.dist)}</td><td class="n">${npr(r.med)}</td><td class="n">${r.n}</td></tr>`).join("") + "</tbody></table>";
}

function renderAbout() {
  el("about-text").innerHTML = `A hedonic regression on the log of asking price, the standard approach for property valuation. It uses property type, land area, district, locality (shrunk toward its district when listings are few), road width, storeys and listing year, and estimates are given at ${M.latest_year} price levels. In 5-fold cross-validation it explains ${Math.round(M.cv.r2_log * 100)}% of the variation in log price (gradient boosting: ${Math.round(M.cv_gboost.r2_log * 100)}%, median error ${M.cv_gboost.median_abs_pct_err}%), so the simpler, explainable model was kept.`;
  const c = M.cv, g = M.cv_gboost;
  const tiles = [
    ["Median error", `${c.median_abs_pct_err}%`, "on held-out listings (5-fold CV)"],
    ["Within ±25%", `${c.within_25pct}%`, "of held-out listings"],
    ["R² (log price)", c.r2_log.toFixed(2), `gradient boosting: ${g.r2_log.toFixed(2)}`],
    ["Training listings", M.n.toLocaleString("en-IN"), "after cleaning and outlier removal"],
  ];
  el("model-stats").innerHTML = tiles.map(([l, v, n]) => `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");
}
