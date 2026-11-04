/* Linux-C.O.S website -- shared behaviour for every page.
   No dependencies, no third-party requests. Everything degrades: without JS
   the pages still render in English with a working (always visible on
   desktop, stacked on mobile) navigation. */
(function () {
  'use strict';

  var root = document.documentElement;
  // the full Spanish menu needs ~1080px next to the logo and the 44px buttons
  var MOBILE_MAX = 1100;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { /* private mode / blocked storage: just don't remember */ }
    return null;
  }

  // ---------- strings used by scripts (page text lives in the HTML) ------
  var STRINGS = {
    en: {
      menuOpen: 'Open menu', menuClose: 'Close menu',
      themeToDark: 'Switch to dark theme', themeToLight: 'Switch to light theme',
      langSwitch: 'Cambiar a español', copy: 'Copy', copied: 'Copied', copyFail: 'Press Ctrl+C',
      copyLabel: 'Copy command to clipboard', toTop: 'Back to top', anchor: 'Link to this section',
      faqNone: 'No question matches. Try another word or ask on GitHub.',
    },
    es: {
      menuOpen: 'Abrir menú', menuClose: 'Cerrar menú',
      themeToDark: 'Cambiar a tema oscuro', themeToLight: 'Cambiar a tema claro',
      langSwitch: 'Switch to English', copy: 'Copiar', copied: 'Copiado', copyFail: 'Pulsa Ctrl+C',
      copyLabel: 'Copiar el comando al portapapeles', toTop: 'Volver arriba', anchor: 'Enlace a esta sección',
      faqNone: 'Ninguna pregunta coincide. Prueba otra palabra o pregunta en GitHub.',
    },
  };
  function lang() { return root.getAttribute('data-lang') === 'es' ? 'es' : 'en'; }
  function t(key) { return (STRINGS[lang()] || STRINGS.en)[key] || STRINGS.en[key] || key; }

  window.COS = window.COS || {};
  window.COS.t = t;
  window.COS.lang = lang;
  window.COS.addStrings = function (more) {
    Object.keys(more).forEach(function (l) {
      STRINGS[l] = STRINGS[l] || {};
      Object.keys(more[l]).forEach(function (k) { STRINGS[l][k] = more[l][k]; });
    });
  };

  // ---------- language ---------------------------------------------------
  function applyLang(l, persist) {
    root.setAttribute('data-lang', l);
    root.lang = l;
    if (persist) store('cos-lang', l);
    var title = root.getAttribute('data-title-' + l);
    if (title) document.title = title;
    var desc = document.querySelector('meta[name="description"]');
    var d = root.getAttribute('data-desc-' + l);
    if (desc && d) desc.setAttribute('content', d);
    document.querySelectorAll('[data-ph-' + l + ']').forEach(function (el) {
      el.setAttribute('placeholder', el.getAttribute('data-ph-' + l));
    });
    document.querySelectorAll('[data-aria-' + l + ']').forEach(function (el) {
      el.setAttribute('aria-label', el.getAttribute('data-aria-' + l));
    });
    document.querySelectorAll('[data-title-' + l + ']:not(html)').forEach(function (el) {
      el.setAttribute('title', el.getAttribute('data-title-' + l));
    });
    var lb = document.getElementById('lang-toggle');
    if (lb) lb.setAttribute('title', t('langSwitch'));
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', currentTheme() === 'light' ? '#f5f7fc' : '#070a14');
    syncThemeButton();
    syncMenuButton();
    document.querySelectorAll('.copy-btn').forEach(function (b) {
      if (!b.classList.contains('copied')) { b.textContent = t('copy'); b.setAttribute('aria-label', t('copyLabel')); }
    });
    var top = document.querySelector('.to-top');
    if (top) top.setAttribute('aria-label', t('toTop'));
    document.dispatchEvent(new CustomEvent('cos:langchange', { detail: { lang: l } }));
  }

  // ---------- theme ------------------------------------------------------
  function currentTheme() {
    var explicit = root.getAttribute('data-theme');
    if (explicit) return explicit;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  function syncThemeButton() {
    var b = document.getElementById('theme-toggle');
    if (!b) return;
    var th = currentTheme();
    b.setAttribute('title', th === 'dark' ? t('themeToLight') : t('themeToDark'));
    b.setAttribute('aria-pressed', th === 'light' ? 'true' : 'false');
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', th === 'light' ? '#f5f7fc' : '#070a14');
  }

  // ---------- mobile menu ------------------------------------------------
  var menuBtn, navList;
  function isMobile() { return window.innerWidth <= MOBILE_MAX; }
  function menuOpen() { return document.body.classList.contains('menu-open'); }
  function syncMenuButton() {
    if (!menuBtn) return;
    var open = menuOpen();
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuBtn.setAttribute('aria-label', open ? t('menuClose') : t('menuOpen'));
  }
  function setMenu(open, opts) {
    opts = opts || {};
    document.body.classList.toggle('menu-open', open);
    if (navList) {
      // hidden from AT and tab order while collapsed on mobile
      if (isMobile() && !open) navList.setAttribute('inert', '');
      else navList.removeAttribute('inert');
    }
    syncMenuButton();
    if (open) {
      var first = navList && navList.querySelector('a');
      if (first) first.focus({ preventScroll: true });
    } else if (opts.returnFocus && menuBtn) {
      menuBtn.focus({ preventScroll: true });
    }
  }

  function initMenu() {
    menuBtn = document.getElementById('menu-toggle');
    navList = document.getElementById('primary-nav');
    if (!menuBtn || !navList) return;
    setMenu(false);
    menuBtn.addEventListener('click', function () { setMenu(!menuOpen()); });
    navList.addEventListener('click', function (e) {
      if (e.target.closest('a') && isMobile()) setMenu(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menuOpen()) { setMenu(false, { returnFocus: true }); return; }
      if (e.key === 'Tab' && menuOpen() && isMobile()) {
        // keep focus inside the header while the menu covers the page: cycle
        // through its visible controls (logo, links, ES/EN, theme, toggle)
        var header = menuBtn.closest('.site-header');
        var items = Array.prototype.slice.call(header.querySelectorAll('a[href], button'))
          .filter(function (x) { return x.offsetParent !== null && !x.closest('[inert]'); });
        if (!items.length) return;
        e.preventDefault();
        var i = items.indexOf(document.activeElement);
        var next = e.shiftKey ? (i <= 0 ? items.length - 1 : i - 1) : (i === -1 || i === items.length - 1 ? 0 : i + 1);
        items[next].focus({ preventScroll: true });
      }
    });
    document.addEventListener('click', function (e) {
      // anything in the header (ES/EN, theme) keeps the menu open
      if (menuOpen() && !e.target.closest('.site-header')) setMenu(false);
    });
    var wasMobile = isMobile();
    window.addEventListener('resize', function () {
      var m = isMobile();
      if (m !== wasMobile) { wasMobile = m; setMenu(false); }
    });
  }

  // ---------- copy buttons -----------------------------------------------
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy') ? resolve() : reject(new Error('copy failed')); }
      catch (err) { reject(err); }
      finally { document.body.removeChild(ta); }
    });
  }
  // any box that scrolls sideways (home terminal, wide tables) must be
  // reachable by keyboard; code blocks are handled in initCopy
  function initScrollRegions() {
    var boxes = Array.prototype.slice.call(document.querySelectorAll('.terminal pre, .table-wrap'));
    function sync() {
      boxes.forEach(function (box) {
        if (box.scrollWidth > box.clientWidth + 1) {
          box.setAttribute('tabindex', '0');
          box.setAttribute('role', 'region');
          box.setAttribute('aria-label', lang() === 'es' ? 'Contenido desplazable' : 'Scrollable content');
        } else {
          box.removeAttribute('tabindex'); box.removeAttribute('role'); box.removeAttribute('aria-label');
        }
      });
    }
    sync();
    window.addEventListener('resize', sync);
    document.addEventListener('cos:langchange', sync);
  }

  function initCopy() {
    document.querySelectorAll('.code').forEach(function (block) {
      var pre = block.querySelector('pre');
      if (!pre) return;
      // a block whose lines scroll horizontally must be reachable by
      // keyboard -- but only then (no pointless tab stops)
      var syncScrollable = function () {
        if (pre.scrollWidth > pre.clientWidth + 1) {
          pre.setAttribute('tabindex', '0');
          pre.setAttribute('role', 'region');
          pre.setAttribute('aria-label', lang() === 'es' ? 'Código (desplazable)' : 'Code (scrollable)');
        } else {
          pre.removeAttribute('tabindex'); pre.removeAttribute('role'); pre.removeAttribute('aria-label');
        }
      };
      syncScrollable();
      window.addEventListener('resize', syncScrollable);
      document.addEventListener('cos:langchange', syncScrollable);
      // reference listings (several independent commands) get no copy
      // button: pasted at once they would all run, one after the other
      if (block.classList.contains('ref') || block.querySelector('.copy-btn')) return;
      block.classList.add('has-copy');
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'copy-btn'; b.textContent = t('copy');
      b.setAttribute('aria-label', t('copyLabel'));
      b.addEventListener('click', function () {
        // copy only the commands: drop "# comment" lines and a leading "$ "
        var text = pre.innerText.split('\n')
          .filter(function (line) { return !/^\s*#/.test(line); })
          .map(function (line) { return line.replace(/^\$ /, ''); })
          .join('\n').trim();
        copyText(text).then(function () {
          b.textContent = t('copied'); b.classList.add('copied');
          b.setAttribute('aria-label', t('copied'));
        }, function () {
          b.textContent = t('copyFail'); b.setAttribute('aria-label', t('copyFail'));
        }).then(function () {
          setTimeout(function () {
            b.textContent = t('copy'); b.classList.remove('copied'); b.setAttribute('aria-label', t('copyLabel'));
          }, 1800);
        });
      });
      block.appendChild(b);
    });
  }

  // ---------- docs: heading anchors + table of contents scrollspy --------
  function initAnchors() {
    document.querySelectorAll('.prose h2[id], .prose h3[id]').forEach(function (h) {
      if (h.querySelector('.anchor')) return;
      var a = document.createElement('a');
      a.className = 'anchor'; a.href = '#' + h.id; a.textContent = '#';
      a.setAttribute('aria-label', t('anchor'));
      h.appendChild(a);
    });
  }
  // the docs TOC turns into a sidebar at 980px (its own CSS breakpoint)
  function tocCollapsed() { return window.innerWidth < 980; }
  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.toc a[href^="#"]'));
    if (!links.length) return;
    var sections = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var current = null;
    function update() {
      // the section being read = the last one whose heading is above a line
      // just under the sticky header (works the same scrolling up or down)
      var line = 120, idx = 0;
      sections.forEach(function (sec, i) { if (sec && sec.getBoundingClientRect().top <= line) idx = i; });
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) idx = sections.length - 1;
      if (links[idx] === current) return;
      if (current) { current.classList.remove('active'); current.removeAttribute('aria-current'); }
      current = links[idx];
      current.classList.add('active');
      current.setAttribute('aria-current', 'location');
    }
    var queued = false;
    window.addEventListener('scroll', function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; update(); });
    }, { passive: true });
    update();
    // on mobile the TOC is a <details>: close it after picking a section
    links.forEach(function (a) {
      a.addEventListener('click', function () {
        var d = a.closest('details');
        if (d && tocCollapsed()) d.open = false;
      });
    });
    var d = document.querySelector('.toc details');
    if (d && !tocCollapsed()) d.open = true;
  }

  // ---------- FAQ search + deep links -------------------------------------
  function initFaq() {
    var input = document.getElementById('faq-filter');
    var items = Array.prototype.slice.call(document.querySelectorAll('.faq details'));
    if (!items.length) return;
    function openFromHash() {
      var id = decodeURIComponent(location.hash.slice(1));
      var target = id && document.getElementById(id);
      if (target && target.tagName === 'DETAILS') { target.open = true; }
    }
    openFromHash();
    window.addEventListener('hashchange', openFromHash);
    if (!input) return;
    var none = document.getElementById('faq-empty');
    var before = null; // which answers were open before the user started filtering
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      if (q && !before) before = items.map(function (d) { return d.open; });
      var shown = 0;
      items.forEach(function (d, i) {
        // search only the visible language
        var text = Array.prototype.slice.call(d.querySelectorAll('[data-l="' + lang() + '"]'))
          .map(function (x) { return x.textContent; }).join(' ').toLowerCase() || d.textContent.toLowerCase();
        var hit = !q || text.indexOf(q) !== -1;
        d.hidden = !hit;
        if (hit) shown++;
        if (q) d.open = hit;
        else if (before) d.open = before[i];
      });
      if (!q) before = null;
      if (none) { none.hidden = shown !== 0; none.textContent = t('faqNone'); }
    });
  }

  // ---------- back to top ------------------------------------------------
  function initToTop() {
    var b = document.querySelector('.to-top');
    if (!b) return;
    var onScroll = function () { b.classList.toggle('show', window.scrollY > 900); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    b.addEventListener('click', function () {
      window.scrollTo({ top: 0 });
      var skip = document.getElementById('main');
      if (skip) skip.focus({ preventScroll: true });
    });
  }

  // ---------- boot -------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    initMenu();
    initCopy();
    initScrollRegions();
    initAnchors();
    initToc();
    initFaq();
    initToTop();

    var lb = document.getElementById('lang-toggle');
    if (lb) lb.addEventListener('click', function () { applyLang(lang() === 'es' ? 'en' : 'es', true); });
    var tb = document.getElementById('theme-toggle');
    if (tb) tb.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store('cos-theme', next);
      syncThemeButton();
    });
    var y = document.getElementById('year');
    if (y) y.textContent = String(new Date().getFullYear());

    applyLang(lang(), false);
  });
})();
