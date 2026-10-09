// Visit each Hamrobazar car listing (robots.txt allows /detail/) and keep only
// structured fields: title, price, condition, body type, make year, plus km /
// fuel / transmission extracted from the description. No seller names, phone
// numbers or free text are stored.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [inFile, outFile] = process.argv.slice(2);
  const urls = [...new Set(fs.readFileSync(inFile, 'utf8').trim().split('\n').map(l => JSON.parse(l).url))];
  const done = new Set(fs.existsSync(outFile) ? fs.readFileSync(outFile, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l).url) : []);
  const out = fs.createWriteStream(outFile, { flags: 'a' });
  const b = await chromium.launch({ executablePath: process.env.EXE });
  const p = await b.newPage({ userAgent: 'Mozilla/5.0 (research crawler; contact via github.com/biggyatz)' });
  let n = 0;
  for (const url of urls) {
    if (done.has(url)) continue;
    try {
      await p.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
      await p.waitForTimeout(1200);
      const t = await p.evaluate(() => document.body.innerText);
      const L = t.split('\n').map(s => s.trim()).filter(Boolean);
      const at = k => { const i = L.indexOf(k); return i >= 0 ? L[i + 1] : null; };
      // The title is the line just before the listing id ("HB-81485B").
      const hi = L.findIndex(x => /^HB-[0-9A-F]+$/i.test(x));
      const title = hi > 0 ? L[hi - 1] : null;
      const si0 = L.indexOf('Specifications'), vi = L.indexOf('View all', si0);
      const specs = {};
      if (si0 >= 0) for (let k = si0 + 1; k + 1 < (vi > si0 ? vi : si0 + 21); k += 2) specs[L[k]] = L[k + 1];
      const cond = L.find(s => /^(Brand new|Like new|Used|Not working)$/i.test(s)) || null;
      const posted = L.find(s => /^Posted /.test(s)) || null;
      const ai = L.indexOf('About this listing'), si = L.indexOf('Specifications');
      const desc = ai >= 0 ? L.slice(ai + 1, si > ai ? si : ai + 6).join(' ') : '';
      const blob = (title || '') + ' ' + desc;
      const road = (blob.match(/(\d{1,2})\s*(?:ft|feet|fit|foot)\b[^.]{0,20}?(?:road|bato|access|wide|width)/i) || blob.match(/(?:road|bato)[^.\d]{0,20}(\d{1,2})\s*(?:ft|feet|fit)/i) || [])[1] || null;
      const storey = (blob.match(/(\d(?:\.\d)?)\s*(?:storey|story|storeyed|floors?|tale|tala)\b/i) || [])[1] || null;
      const area = (blob.match(/(\d+(?:\.\d+)?\s*(?:ropani|aana|ana|anna|dhur|kattha|katha|bigha)(?:\s*\d+(?:\.\d+)?\s*(?:aana|ana|paisa|dhur|kattha))*)/i) || [])[1] || null;
      const km = (blob.match(/(\d{1,3}(?:[,.]\d{3})+|\d{3,6}|\d{1,3}(?:\.\d)?\s*k)\s*(?:km|kms|kilomet)/i) || [])[1] || null;
      const fuel = (blob.match(/\b(petrol|diesel|electric|EV|hybrid)\b/i) || [])[1] || null;
      const trans = (blob.match(/\b(automatic|manual|AT|MT|CVT|AMT)\b/) || blob.match(/\b(automatic|manual)\b/i) || [])[1] || null;
      const phone = /(\+?977[-\s]?)?\b9[678]\d[-\s]?\d{3}[-\s]?\d{4}\b/g;
      out.write(JSON.stringify({ source: 'hamrobazaar.com', url, title: title && title.replace(phone, '[phone]'), price: at('Price'), condition: cond, posted,
        body_type: at('Types'), make_year: at('Make Year'), km_text: km, fuel, transmission: trans,
        specs, road_ft: road, storeys: storey, area_text: area, scraped: new Date().toISOString() }) + '\n');
    } catch (e) { console.error('ERR', url, e.message); }
    if (++n % 50 === 0) console.error(n);
    await p.waitForTimeout(1500);
  }
  out.end(); await b.close();
})();
