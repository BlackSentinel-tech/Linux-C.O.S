// Linux-C.O.S website -- end-to-end tests in a real browser (Chromium via
// Playwright), driven by node's built-in test runner:
//
//   node --test tests/website/
//
// Serves website/ itself on a random localhost port; no other setup.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); } catch {
  playwright = require(join(process.env.NPM_GLOBAL || '/opt/node22/lib/node_modules', 'playwright'));
}

const SITE = join(dirname(fileURLToPath(import.meta.url)), '../../website');
const PAGES = ['index', 'features', 'tools', 'download', 'docs', 'faq', '404'];
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };

let server, base, browser;

before(async () => {
  server = http.createServer(async (req, res) => {
    const path = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname)).replace(/^(\.\.[/\\])+/, '');
    let file = join(SITE, path === '/' ? 'index.html' : path);
    try {
      if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
      res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream' });
      res.end(await readFile(file));
    } catch {
      res.writeHead(404, { 'content-type': TYPES['.html'] });
      res.end(await readFile(join(SITE, '404.html')));
    }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await playwright.chromium.launch();
});
after(async () => { await browser?.close(); server?.close(); });

async function newPage(opts = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, locale: 'en-US', ...opts });
  const page = await ctx.newPage();
  page.errors = [];
  page.on('pageerror', e => page.errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') page.errors.push(m.text()); });
  return page;
}

test('every page loads cleanly: no JS/CSP errors, one h1, title, lang, landmarks', async () => {
  const page = await newPage();
  for (const p of PAGES) {
    await page.goto(`${base}/${p}.html`, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('h1').count(), 1, `${p}: exactly one h1`);
    assert.ok((await page.title()).includes('Linux-C.O.S'), `${p}: title`);
    assert.equal(await page.getAttribute('html', 'lang'), 'en');
    assert.equal(await page.locator('main#main').count(), 1, `${p}: main landmark`);
    assert.equal(await page.locator('nav[aria-label]').count(), 1, `${p}: labelled nav`);
  }
  assert.deepEqual(page.errors, []);
});

test('no horizontal scrolling on a phone, a tablet or a desktop', async () => {
  for (const width of [360, 390, 768, 1280]) {
    const page = await newPage({ viewport: { width, height: 800 } });
    for (const p of PAGES) {
      await page.goto(`${base}/${p}.html`, { waitUntil: 'networkidle' });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 0, `${p} @${width}px overflows by ${overflow}px`);
    }
  }
});

test('every internal link and #anchor resolves', async () => {
  const page = await newPage();
  const seen = new Set();
  for (const p of PAGES) {
    await page.goto(`${base}/${p}.html`, { waitUntil: 'networkidle' });
    const hrefs = await page.$$eval('a[href]', as => as.map(a => a.getAttribute('href')));
    for (const href of hrefs) {
      if (/^(https?:|mailto:)/.test(href) || seen.has(p + href)) continue;
      seen.add(p + href);
      const [file, hash] = href.split('#');
      const target = file || `${p}.html`;
      const res = await fetch(`${base}/${target}`);
      assert.equal(res.status, 200, `${p}: link ${href} -> ${res.status}`);
      if (hash) {
        const html = await res.text();
        assert.ok(html.includes(`id="${hash}"`), `${p}: anchor #${hash} missing in ${target}`);
      }
    }
  }
});

test('desktop nav marks the current page', async () => {
  const page = await newPage();
  for (const [p, label] of [['features', 'Features'], ['tools', 'Tools'], ['docs', 'Docs'], ['faq', 'FAQ'], ['download', 'Download']]) {
    await page.goto(`${base}/${p}.html`);
    const current = page.locator('#primary-nav a[aria-current="page"]');
    assert.equal(await current.count(), 1);
    assert.equal((await current.innerText()).trim(), label);
  }
});

test('mobile menu: opens, traps focus, closes on Escape/link/outside click', async () => {
  const page = await newPage({ viewport: { width: 390, height: 844 }, hasTouch: true });
  await page.goto(`${base}/index.html`);
  const toggle = page.locator('#menu-toggle');
  const firstLink = page.locator('#primary-nav a').first();
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(await firstLink.isVisible(), false, 'menu hidden at start');

  await toggle.click();
  assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(await toggle.getAttribute('aria-label'), 'Close menu');
  await page.waitForTimeout(250);
  assert.ok(await firstLink.isVisible(), 'menu visible when open');
  assert.equal(await page.evaluate(() => document.activeElement.innerText.trim()), 'Features', 'focus moves into the menu');
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).overflow), 'hidden', 'page scroll locked');

  // focus trap: Shift+Tab from the toggle goes to the last link
  await toggle.focus();
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.evaluate(() => document.activeElement.innerText.trim()), 'GitHub');

  await page.keyboard.press('Escape');
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'menu-toggle', 'focus returns to the toggle');

  await toggle.click();
  await page.mouse.click(200, 800); // outside (on the backdrop)
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false', 'outside click closes');

  await toggle.click();
  await page.waitForTimeout(250);
  await page.locator('#primary-nav a', { hasText: 'Docs' }).click();
  await page.waitForURL(/docs\.html/);
  assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'), 'false');
  assert.equal(await page.locator('#primary-nav a').first().isVisible(), false, 'menu closed after navigating');
  assert.deepEqual(page.errors, []);
});

test('closed mobile menu is not reachable by keyboard', async () => {
  const page = await newPage({ viewport: { width: 390, height: 844 } });
  await page.goto(`${base}/index.html`);
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press('Tab');
    const inNav = await page.evaluate(() => !!document.activeElement.closest('#primary-nav'));
    assert.equal(inNav, false, `tab stop ${i} landed inside the hidden menu`);
  }
});

test('skip link jumps to the main content', async () => {
  const page = await newPage();
  await page.goto(`${base}/features.html`);
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.className), 'skip-link');
  await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'main');
});

test('language: auto-detects Spanish, toggles, persists across pages', async () => {
  const page = await newPage({ locale: 'es-ES' });
  await page.goto(`${base}/index.html`);
  assert.equal(await page.getAttribute('html', 'lang'), 'es');
  assert.match(await page.locator('h1').innerText(), /Defiende/);
  assert.match(await page.title(), /Seguridad ofensiva/);
  await page.click('#lang-toggle');
  assert.equal(await page.getAttribute('html', 'lang'), 'en');
  assert.match(await page.locator('h1').innerText(), /Defend the box/);
  await page.goto(`${base}/docs.html`);
  assert.equal(await page.getAttribute('html', 'lang'), 'en', 'choice persists');
  assert.equal(await page.locator('#menu-toggle').getAttribute('aria-label'), 'Open menu');
});

test('theme: toggle switches and persists without flashing', async () => {
  const page = await newPage({ colorScheme: 'dark' });
  await page.goto(`${base}/index.html`);
  const bg = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  const dark = await bg();
  await page.click('#theme-toggle');
  assert.equal(await page.getAttribute('html', 'data-theme'), 'light');
  assert.notEqual(await bg(), dark);
  await page.goto(`${base}/faq.html`);
  assert.equal(await page.getAttribute('html', 'data-theme'), 'light', 'set before first paint on the next page');
});

test('tools: search, source filter, category, URL state, load more, empty state', async () => {
  const page = await newPage();
  await page.goto(`${base}/tools.html`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tool-list .tool');
  assert.equal(await page.locator('#tool-list .tool').count(), 60, 'first page of results');
  assert.match(await page.locator('#tool-count').innerText(), /Showing 60 of 3,\d{3} tools/);
  assert.equal(await page.locator('#clear-filters').isVisible(), false, 'no clear button without filters');

  await page.fill('#tool-q', 'nmap');
  await page.waitForFunction(() => /^\d+ tools$/.test(document.getElementById('tool-count').textContent));
  assert.equal((await page.locator('#tool-list .tool-name').first().innerText()).trim(), 'nmap', 'exact match first');
  assert.match(page.url(), /\?q=nmap/);
  assert.ok(await page.locator('#clear-filters').isVisible());

  await page.click('.chip[data-src="blackarch"]');
  assert.equal(await page.locator('.chip[data-src="blackarch"]').getAttribute('aria-pressed'), 'true');
  assert.match(page.url(), /src=blackarch/);
  const names = await page.locator('#tool-list .tool').evaluateAll(els => els.map(e => e.textContent));
  assert.ok(names.every(n => n.includes('BlackArch')), 'only BlackArch tools');

  await page.goBack();
  assert.equal(await page.locator('.chip[data-src="all"]').getAttribute('aria-pressed'), 'true', 'back button restores filters');

  await page.fill('#tool-q', 'zzzz-no-such-tool');
  await page.waitForSelector('#tool-empty:not([hidden])');
  await page.click('#empty-clear');
  assert.equal(await page.inputValue('#tool-q'), '');
  assert.equal(await page.locator('#tool-list .tool').count(), 60);

  await page.click('#load-more button');
  assert.equal(await page.locator('#tool-list .tool').count(), 120);

  await page.selectOption('#tool-cat', 'Forensics');
  const cats = await page.locator('#tool-list .tool-meta').evaluateAll(els => els.map(e => e.textContent));
  assert.ok(cats.length > 0 && cats.every(c => c.includes('Forensics')));
  assert.match(page.url(), /cat=Forensics/);
  assert.deepEqual(page.errors, []);
});

test('tools: deep link, chart filter, table view', async () => {
  const page = await newPage();
  await page.goto(`${base}/tools.html?src=kali&q=burp`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tool-list .tool');
  assert.equal(await page.inputValue('#tool-q'), 'burp');
  assert.equal(await page.locator('.chip[data-src="kali"]').getAttribute('aria-pressed'), 'true');

  await page.goto(`${base}/tools.html`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#cat-chart .bar-row');
  const bar = page.locator('#cat-chart .bar-row').nth(1);
  const label = (await bar.locator('.bar-label').innerText()).trim();
  await bar.click();
  assert.equal(await page.inputValue('#tool-cat'), label, 'clicking a bar filters by its category');

  await page.click('#chart-toggle');
  assert.ok(await page.locator('#cat-table').isVisible());
  assert.equal(await page.locator('#cat-chart').isVisible(), false);
  assert.ok((await page.locator('#cat-table tbody tr').count()) >= 10);
});

test('tools in Spanish: categories translated, counts localized', async () => {
  const page = await newPage({ locale: 'es-ES' });
  await page.goto(`${base}/tools.html`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tool-list .tool');
  assert.match(await page.locator('#tool-count').innerText(), /Mostrando 60 de 3[.\s\u00a0]?\d{3} herramientas/ /* es-ES does not group 4-digit numbers */);
  const labels = await page.locator('#cat-chart .bar-label').allInnerTexts();
  assert.ok(labels.includes('Aplicaciones web'), labels.join(','));
});

test('docs: table of contents tracks the section; copy buttons copy commands', async () => {
  const page = await newPage({ permissions: ['clipboard-read', 'clipboard-write'] });
  await page.goto(`${base}/docs.html`);
  assert.equal(await page.locator('.toc details').getAttribute('open'), '', 'TOC expanded on desktop');
  await page.click('.toc a[href="#stacks"]');
  await page.waitForFunction(() => document.querySelector('.toc a.active')?.getAttribute('href') === '#stacks');
  const btn = page.locator('#stacks ~ .code .copy-btn').first();
  await btn.click();
  await page.waitForFunction(el => el.classList.contains('copied'), await btn.elementHandle());
  assert.equal((await btn.innerText()).trim(), 'Copied');
  const clip = await page.evaluate(() => navigator.clipboard.readText());
  assert.ok(clip.startsWith('cos-stacks'), clip);
});

test('faq: filter narrows the list, deep link opens the answer', async () => {
  const page = await newPage();
  await page.goto(`${base}/faq.html#secure-boot`);
  assert.equal(await page.locator('#secure-boot').getAttribute('open'), '');
  await page.fill('#faq-filter', 'password');
  const visible = await page.locator('.faq details:not([hidden])').count();
  assert.ok(visible >= 1 && visible < 6, `visible=${visible}`);
  await page.fill('#faq-filter', 'qwertyuiop');
  assert.ok(await page.locator('#faq-empty').isVisible());
});

test('security posture: strict CSP, no third-party requests', async () => {
  const page = await newPage();
  const external = [];
  page.on('request', r => { if (!r.url().startsWith(base) && !r.url().startsWith('data:')) external.push(r.url()); });
  for (const p of PAGES) {
    await page.goto(`${base}/${p}.html`, { waitUntil: 'networkidle' });
    const csp = await page.getAttribute('meta[http-equiv="Content-Security-Policy"]', 'content');
    assert.match(csp, /default-src 'self'/);
    assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval/);
  }
  assert.deepEqual(external, []);
});
