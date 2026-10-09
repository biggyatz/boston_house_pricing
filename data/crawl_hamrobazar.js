// Polite Hamrobazar search crawler (robots.txt allows /search/product and /detail/).
// Usage: node crawl_hamrobazar.js <pathRegex> <out.jsonl> <query>...
// Saves only the listing URL and the card text; phone numbers are stripped and
// seller names are dropped at parse time.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [pathRe, outFile, ...queries] = process.argv.slice(2);
  const re = new RegExp(pathRe);
  const seen = new Set(fs.existsSync(outFile) ? fs.readFileSync(outFile, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l).url) : []);
  const out = fs.createWriteStream(outFile, { flags: 'a' });
  const b = await chromium.launch({ executablePath: process.env.EXE });
  const p = await b.newPage({ userAgent: 'Mozilla/5.0 (research crawler; contact via github.com/biggyatz)' });
  for (const q of queries) {
    try {
      await p.goto('https://hamrobazaar.com/search/product?q=' + encodeURIComponent(q), { waitUntil: 'networkidle', timeout: 60000 });
    } catch (e) { console.error('goto', q, e.message); continue; }
    await p.waitForTimeout(3000);
    let stale = 0, before = seen.size;
    for (let i = 0; i < 60 && stale < 3; i++) {
      const cards = await p.$$eval('a[href*="/detail/"]', as => {
        const res = [];
        for (const a of as) {
          let el = a; for (let k = 0; k < 6 && el.parentElement && el.innerText.length < 40; k++) el = el.parentElement;
          res.push({ url: a.href.split('?')[0], text: el.innerText });
        }
        return res;
      });
      let added = 0;
      for (const c of cards) {
        if (!re.test(c.url) || seen.has(c.url)) continue;
        seen.add(c.url); added++;
        const text = c.text.replace(/(\+?977[-\s]?)?9[678]\d[-\s]?\d{3}[-\s]?\d{4}/g, '[phone]').replace(/\b9[678]\d{8}\b/g, '[phone]');
        out.write(JSON.stringify({ source: 'hamrobazaar.com', query: q, url: c.url, text, scraped: new Date().toISOString() }) + '\n');
      }
      stale = added ? 0 : stale + 1;
      await p.mouse.wheel(0, 30000); await p.waitForTimeout(2500);
    }
    console.error(q, '+', seen.size - before, 'total', seen.size);
  }
  out.end(); await b.close();
})();
