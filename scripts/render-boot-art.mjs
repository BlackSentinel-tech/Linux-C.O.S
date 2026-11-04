#!/usr/bin/env node
// Linux-C.O.S -- renders the boot-menu artwork from the brand SVG, so the
// PNGs are reproducible instead of hand-exported:
//
//   build/config/includes.chroot/usr/share/grub/themes/linux-cos/
//       background.png (1920x1080) + select_*.png   installed-system GRUB theme
//   build/config/includes.binary/boot/grub/splash.png   live ISO GRUB background
//   build/config/includes.binary/isolinux/splash.png    live ISO BIOS menu (640x480)
//
// usage: node scripts/render-boot-art.mjs   (needs Playwright + Chromium)
import { readFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require('playwright');
} catch {
  playwright = require(join(process.env.NPM_GLOBAL || '/opt/node22/lib/node_modules', 'playwright'));
}

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const logo = readFileSync(join(ROOT, 'build/branding/logo/linux-cos-logo.svg'), 'utf8');
const logoUri = 'data:image/svg+xml;base64,' + Buffer.from(logo).toString('base64');

const page = (w, h, { logoSize, titleSize, subtitle = true, logoTop }) => `<!doctype html>
<html><head><style>
  html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden}
  body{background:radial-gradient(ellipse at 50% 35%,#101a45 0%,#0a0f24 45%,#05070d 100%);
       font-family:"DejaVu Sans Mono","Liberation Mono",monospace;color:#eef2ff;position:relative}
  .grid{position:absolute;inset:0;opacity:.18;
        background-image:linear-gradient(#1c3faa 1px,transparent 1px),linear-gradient(90deg,#1c3faa 1px,transparent 1px);
        background-size:${Math.round(w / 24)}px ${Math.round(w / 24)}px;
        mask-image:radial-gradient(ellipse at 50% 40%,#000 0%,transparent 70%)}
  .brand{position:absolute;left:0;right:0;top:${logoTop}px;text-align:center}
  img{width:${logoSize}px;height:${logoSize}px;display:block;margin:0 auto}
  h1{font-size:${titleSize}px;letter-spacing:.18em;margin:.35em 0 0;font-weight:700}
  p{font-size:${Math.round(titleSize * 0.36)}px;letter-spacing:.3em;color:#8d97c4;margin:.5em 0 0}
</style></head><body><div class="grid"></div>
<div class="brand"><img src="${logoUri}"><h1>LINUX-C.O.S</h1>
${subtitle ? '<p>CYBER OFFENSIVE &amp; DEFENSIVE SECURITY</p>' : ''}</div></body></html>`;

const targets = [
  { out: 'build/config/includes.chroot/usr/share/grub/themes/linux-cos/background.png',
    w: 1920, h: 1080, opts: { logoSize: 150, titleSize: 54, logoTop: 90 } },
  { out: 'build/config/includes.binary/boot/grub/splash.png',
    w: 1920, h: 1080, opts: { logoSize: 150, titleSize: 54, logoTop: 90 } },
  { out: 'build/config/includes.binary/isolinux/splash.png',
    w: 640, h: 480, opts: { logoSize: 64, titleSize: 22, logoTop: 26, subtitle: false } },
];

const browser = await playwright.chromium.launch();
const ctx = await browser.newContext({ deviceScaleFactor: 1 });
const tab = await ctx.newPage();
for (const t of targets) {
  await tab.setViewportSize({ width: t.w, height: t.h });
  await tab.setContent(page(t.w, t.h, t.opts), { waitUntil: 'load' });
  const out = join(ROOT, t.out);
  mkdirSync(dirname(out), { recursive: true });
  await tab.screenshot({ path: out, omitBackground: false });
  console.log('wrote', t.out);
}

// GRUB's styled highlight box is drawn from 9 slices (select_nw.png ...
// select_c.png). Solid translucent blue with a red left edge.
const themeDir = join(ROOT, 'build/config/includes.chroot/usr/share/grub/themes/linux-cos');
const slices = { nw: '#d6273c', w: '#d6273c', sw: '#d6273c',
                 n: '#1c3faacc', c: '#1c3faacc', s: '#1c3faacc',
                 ne: '#1c3faacc', e: '#1c3faacc', se: '#1c3faacc' };
for (const [name, color] of Object.entries(slices)) {
  const wide = name.endsWith('w') ? 4 : 1;
  await tab.setViewportSize({ width: wide, height: 1 });
  await tab.setContent(`<body style="margin:0;background:transparent"><div style="width:${wide}px;height:1px;background:${color}"></div></body>`);
  await tab.screenshot({ path: join(themeDir, `select_${name}.png`), omitBackground: true,
                         clip: { x: 0, y: 0, width: wide, height: 1 } });
}
console.log('wrote 9 select_*.png slices');
await browser.close();
