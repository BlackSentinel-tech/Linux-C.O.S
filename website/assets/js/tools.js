/* Linux-C.O.S website -- tool catalog explorer (tools.html).
   Data: assets/data/tools-data.js (window.COS_TOOLS; works from file://, as
   in the offline copy inside the ISO) with assets/data/tools.json as the
   fetch fallback -- both built by scripts/build-website-data.py.
   State lives in the URL (?q=&src=&cat=) so a filtered view can be shared
   and the back button works. */
(function () {
  'use strict';

  var BITS = { kali: 1, parrot: 2, blackarch: 4 };
  var LABEL = { kali: 'Kali', parrot: 'Parrot', blackarch: 'BlackArch' };
  var PAGE = 60;
  function own(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }

  window.COS.addStrings({
    en: {
      loading: 'Loading the catalog…', loadFail: 'The catalog could not be loaded.', retry: 'Try again',
      results1: '1 tool', results: '{n} tools', resultsOf: 'Showing {shown} of {n} tools', loadMore: 'Show {k} more',
      allCats: 'All categories', openPage: 'Open the tool page for {name}',
      chartSub: 'Top {k} categories for the current source · a tool can be in several · select a bar to filter',
      chartTable: 'Show as table', chartBars: 'Show as chart', category: 'Category', count: 'Tools',
      bar: '{cat}: {n} tools', run: 'Run:', runIn: 'Run in blackarch-shell:', anySource: 'Search all sources',
      emptySrc: 'Nothing in {src} — other sources may have it.',
    },
    es: {
      loading: 'Cargando el catálogo…', loadFail: 'No se pudo cargar el catálogo.', retry: 'Reintentar',
      results1: '1 herramienta', results: '{n} herramientas', resultsOf: 'Mostrando {shown} de {n} herramientas', loadMore: 'Ver {k} más',
      allCats: 'Todas las categorías', openPage: 'Abrir la página de {name}',
      chartSub: 'Las {k} categorías principales del origen actual · una herramienta puede estar en varias · elige una barra para filtrar',
      chartTable: 'Ver como tabla', chartBars: 'Ver como gráfico', category: 'Categoría', count: 'Herramientas',
      bar: '{cat}: {n} herramientas', run: 'Ejecutar:', runIn: 'Ejecutar en blackarch-shell:', anySource: 'Buscar en todos los orígenes',
      emptySrc: 'Nada en {src} — puede estar en otros orígenes.',
    },
  });
  var t = window.COS.t;
  function es() { return window.COS.lang() === 'es'; }
  function fmt(s, vars) { return s.replace(/\{(\w+)\}/g, function (_, k) { return vars[k]; }); }
  function nf(n) {
    // es-ES leaves 4-digit numbers ungrouped by default; group them anyway so
    // "3.351" here matches "2.858" elsewhere on the site
    try { return n.toLocaleString(es() ? 'es-ES' : 'en-US', { useGrouping: 'always' }); }
    catch (e) { return n.toLocaleString(es() ? 'es-ES' : 'en-US'); }
  }

  // category names come from the data in English; Spanish labels for display
  var CAT_ES = {
    'AI': 'IA', 'Automation': 'Automatización', 'Automotive': 'Automoción', 'Bluetooth': 'Bluetooth',
    'Checker': 'Verificadores', 'Cloud': 'Nube', 'Code Audit': 'Auditoría de código',
    'Crypto & Stego': 'Cripto y estego', 'Database Assessment': 'Evaluación de bases de datos',
    'Defense: Detect': 'Defensa: detectar', 'Defense: Identify': 'Defensa: identificar',
    'Defense: Protect': 'Defensa: proteger', 'Defense: Respond': 'Defensa: responder',
    'Defense: Recover': 'Defensa: recuperar', 'Denial of Service': 'Denegación de servicio',
    'Exploitation': 'Explotación', 'Forensics': 'Forense', 'Fuzzing': 'Fuzzing', 'Other': 'Otras',
    'Hardware & GPU': 'Hardware y GPU', 'Information Gathering': 'Recopilación de información',
    'Malware Analysis': 'Análisis de malware', 'Mobile': 'Móvil', 'Networking': 'Redes',
    'Password Attacks': 'Ataques a contraseñas', 'Post Exploitation': 'Post-explotación',
    'RFID & NFC': 'RFID y NFC', 'Reporting': 'Informes', 'Reverse Engineering': 'Ingeniería inversa',
    'Sniffing & Spoofing': 'Sniffing y spoofing', 'Social Engineering': 'Ingeniería social',
    'Software Defined Radio': 'Radio definida por software', 'VoIP': 'VoIP',
    'Vulnerability Analysis': 'Análisis de vulnerabilidades', 'Web Applications': 'Aplicaciones web',
    'Windows & Active Directory': 'Windows y Active Directory', 'Wireless': 'Inalámbricas',
  };
  function catLabel(c) { return es() && CAT_ES[c] ? CAT_ES[c] : c; }

  var el = {
    q: document.getElementById('tool-q'),
    cat: document.getElementById('tool-cat'),
    chips: document.getElementById('src-chips'),
    list: document.getElementById('tool-list'),
    count: document.getElementById('tool-count'),
    more: document.getElementById('load-more'),
    clear: document.getElementById('clear-filters'),
    status: document.getElementById('tool-status'),
    empty: document.getElementById('tool-empty'),
    emptySrc: document.getElementById('empty-src'),
    chart: document.getElementById('cat-chart'),
    chartTable: document.getElementById('cat-table'),
    chartToggle: document.getElementById('chart-toggle'),
    chartSub: document.getElementById('chart-sub'),
  };
  if (!el.list) return;

  var data = null;
  var state = { q: '', src: 'all', cat: '' };
  var shown = PAGE;
  var filtered = [];
  var tableMode = false;

  function toolUrl(row) {
    if (row[3]) return row[3];
    if (row[1] & BITS.kali) return 'https://www.kali.org/tools/' + encodeURIComponent(row[0]) + '/';
    if (row[1] & BITS.blackarch) return 'https://github.com/BlackArch/blackarch/tree/master/packages/' + encodeURIComponent(row[0]);
    return '';
  }
  function commands(row) { return (data.commands && own(data.commands, row[0])) ? data.commands[row[0]] : null; }
  function cats(row) { return row[2]; }

  // ---------- URL state --------------------------------------------------
  function readUrl() {
    var p = new URLSearchParams(location.search);
    state.q = (p.get('q') || '').slice(0, 200);
    var s = (p.get('src') || '').toLowerCase();
    state.src = own(BITS, s) ? s : 'all';
    // category: match case-insensitively, drop unknown ones
    var c = (p.get('cat') || '').toLowerCase();
    state.cat = '';
    if (c) data.categories.forEach(function (name) { if (name.toLowerCase() === c) state.cat = name; });
    writeUrl(false); // normalise what we could not use out of the address bar
  }
  function writeUrl(push) {
    var p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.src !== 'all') p.set('src', state.src);
    if (state.cat) p.set('cat', state.cat);
    var qs = p.toString();
    var url = location.pathname + (qs ? '?' + qs : '') + location.hash;
    if (url === location.pathname + location.search + location.hash) return;
    history[push ? 'pushState' : 'replaceState'](null, '', url);
  }

  // ---------- filtering --------------------------------------------------
  function haystack(row) {
    var parts = [row[0]];
    var cmd = commands(row);
    if (cmd) parts = parts.concat(cmd);
    cats(row).forEach(function (i) {
      var c = data.categories[i];
      parts.push(c);
      if (es() && CAT_ES[c]) parts.push(CAT_ES[c]); // Spanish names only match in Spanish
    });
    return parts.join(' ').toLowerCase();
  }
  function tokens() { return state.q.trim().toLowerCase().split(/\s+/).filter(Boolean); }
  function textMatch(row, terms) {
    if (!terms.length) return true;
    var h = haystack(row);
    // every word must match ("metasploit framework" finds metasploit-framework)
    return terms.every(function (w) { return h.indexOf(w) !== -1; });
  }
  function matchesSrc(row) { return state.src === 'all' || (row[1] & BITS[state.src]); }
  function nameRank(row, q) {
    var names = [row[0].toLowerCase()].concat((commands(row) || []).map(function (c) { return c.toLowerCase(); }));
    if (names.indexOf(q) !== -1) return 0;
    if (names.some(function (n) { return n.indexOf(q) === 0; })) return 1;
    return 2;
  }
  function apply() {
    var terms = tokens();
    var q = terms.join(' ');
    var catIdx = state.cat ? data.categories.indexOf(state.cat) : -1;
    filtered = data.tools.filter(function (row) {
      if (!matchesSrc(row)) return false;
      if (catIdx !== -1 && cats(row).indexOf(catIdx) === -1) return false;
      return textMatch(row, terms);
    });
    if (q) {
      filtered.sort(function (a, b) {
        var an = a[0].toLowerCase(), bn = b[0].toLowerCase();
        return nameRank(a, q) - nameRank(b, q) || (an < bn ? -1 : an > bn ? 1 : 0);
      });
    }
    shown = PAGE;
    render();
    renderChart();
    syncControls();
  }

  // ---------- rendering --------------------------------------------------
  function badge(src) {
    var s = document.createElement('span');
    s.className = 'src ' + src;
    s.textContent = LABEL[src];
    return s;
  }
  function render() {
    el.list.textContent = '';
    var frag = document.createDocumentFragment();
    filtered.slice(0, shown).forEach(function (row) {
      var li = document.createElement('li');
      li.className = 'tool';
      var name = document.createElement('div');
      name.className = 'tool-name';
      var url = toolUrl(row);
      if (url) {
        var a = document.createElement('a');
        a.href = url; a.textContent = row[0];
        a.target = '_blank'; a.rel = 'noopener noreferrer';
        a.setAttribute('aria-label', fmt(t('openPage'), { name: row[0] }));
        name.appendChild(a);
      } else {
        name.textContent = row[0];
      }
      var meta = document.createElement('div');
      meta.className = 'tool-meta';
      ['kali', 'parrot', 'blackarch'].forEach(function (src) { if (row[1] & BITS[src]) meta.appendChild(badge(src)); });
      var cat = document.createElement('span');
      cat.textContent = cats(row).map(function (i) { return catLabel(data.categories[i]); }).join(' · ');
      meta.appendChild(cat);
      // how to run it: native tools by name, BlackArch-only ones in the container
      var run = document.createElement('div');
      run.className = 'tool-run';
      var native = row[1] & (BITS.kali | BITS.parrot);
      var cmd = (commands(row) || [row[0]])[0];
      var lab = document.createElement('span');
      lab.textContent = native ? t('run') : t('runIn');
      var code = document.createElement('code');
      code.textContent = native ? cmd : 'blackarch-shell ' + cmd;
      run.appendChild(lab); run.appendChild(document.createTextNode(' ')); run.appendChild(code);
      li.appendChild(name); li.appendChild(meta); li.appendChild(run);
      frag.appendChild(li);
    });
    el.list.appendChild(frag);

    var n = filtered.length;
    el.count.textContent = n > shown ? fmt(t('resultsOf'), { shown: nf(shown), n: nf(n) })
      : n === 1 ? t('results1') : fmt(t('results'), { n: nf(n) });
    el.more.hidden = n <= shown;
    el.more.querySelector('button').textContent = fmt(t('loadMore'), { k: nf(Math.min(PAGE, n - shown)) });

    el.empty.hidden = n !== 0;
    var srcHint = n === 0 && state.src !== 'all';
    el.emptySrc.hidden = !srcHint;
    if (srcHint) el.emptySrc.querySelector('span').textContent = fmt(t('emptySrc'), { src: LABEL[state.src] });
    el.clear.hidden = !(state.q || state.src !== 'all' || state.cat);
  }

  function syncControls() {
    if (el.q.value !== state.q) el.q.value = state.q;
    el.chips.querySelectorAll('.chip').forEach(function (c) {
      c.setAttribute('aria-pressed', c.getAttribute('data-src') === state.src ? 'true' : 'false');
    });
    // category options: counts for the current source/search
    var terms = tokens();
    var counts = new Array(data.categories.length).fill(0);
    data.tools.forEach(function (row) {
      if (!matchesSrc(row) || !textMatch(row, terms)) return;
      cats(row).forEach(function (i) { counts[i]++; });
    });
    el.cat.textContent = '';
    var all = document.createElement('option');
    all.value = ''; all.textContent = t('allCats');
    el.cat.appendChild(all);
    data.categories
      .map(function (c, i) { return { c: c, i: i, label: catLabel(c) }; })
      .sort(function (a, b) { return a.label.localeCompare(b.label, es() ? 'es' : 'en'); })
      .forEach(function (o) {
        if (!counts[o.i] && o.c !== state.cat) return;
        var opt = document.createElement('option');
        opt.value = o.c; opt.textContent = o.label + ' (' + nf(counts[o.i]) + ')';
        el.cat.appendChild(opt);
      });
    el.cat.value = state.cat;
  }

  // ---------- chart (single series -> no legend; tooltip + table view) ---
  var tip = null;
  function showTip(text, x, y) {
    if (!tip) { tip = document.createElement('div'); tip.className = 'chart-tip'; tip.setAttribute('aria-hidden', 'true'); document.body.appendChild(tip); }
    tip.textContent = text;
    tip.hidden = false;
    var w = tip.offsetWidth;
    tip.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, x + 12)) + 'px';
    tip.style.top = Math.max(8, y - 36) + 'px';
  }
  function hideTip() { if (tip) tip.hidden = true; }

  function renderChart(focusCat) {
    if (!el.chart) return;
    var counts = {};
    data.tools.forEach(function (row) {
      if (!matchesSrc(row)) return;
      cats(row).forEach(function (i) {
        var c = data.categories[i];
        if (c === data.other) return; // "uncategorised" says nothing as a bar
        counts[c] = (counts[c] || 0) + 1;
      });
    });
    var rows = Object.keys(counts).map(function (c) { return [c, counts[c]]; })
      .sort(function (a, b) { return b[1] - a[1] || (a[0] < b[0] ? -1 : 1); }).slice(0, 12);
    var max = rows.length ? rows[0][1] : 1;
    el.chartSub.textContent = fmt(t('chartSub'), { k: rows.length });

    el.chart.textContent = '';
    rows.forEach(function (r) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'bar-row';
      b.setAttribute('data-cat', r[0]);
      b.setAttribute('aria-pressed', state.cat === r[0] ? 'true' : 'false');
      var lab = document.createElement('span'); lab.className = 'bar-label'; lab.textContent = catLabel(r[0]);
      var track = document.createElement('span'); track.className = 'bar-track'; track.setAttribute('aria-hidden', 'true');
      var fill = document.createElement('span'); fill.className = 'bar-fill';
      // reserve 48px at the end of the track for the value label
      var frac = (r[1] / max).toFixed(4);
      fill.style.width = 'calc((100% - 48px) * ' + frac + ')';
      var val = document.createElement('span'); val.className = 'bar-val'; val.textContent = nf(r[1]);
      val.style.left = 'calc((100% - 48px) * ' + frac + ')';
      var sr = document.createElement('span'); sr.className = 'visually-hidden'; sr.textContent = ' ' + nf(r[1]);
      track.appendChild(fill); track.appendChild(val);
      b.appendChild(lab); b.appendChild(sr); b.appendChild(track);
      b.addEventListener('mousemove', function (e) { showTip(fmt(t('bar'), { cat: catLabel(r[0]), n: nf(r[1]) }), e.clientX, e.clientY); });
      b.addEventListener('mouseleave', hideTip);
      b.addEventListener('click', function (e) {
        state.cat = state.cat === r[0] ? '' : r[0];
        writeUrl(true); apply();
        // keep the keyboard user on the bar they pressed (bars are rebuilt)
        var again = el.chart.querySelector('[data-cat="' + r[0].replace(/"/g, '\\"') + '"]');
        if (again && e.detail === 0) again.focus();
        else document.getElementById('results-heading').scrollIntoView({ block: 'start' });
      });
      el.chart.appendChild(b);
    });

    // table view: same data, for screen readers, print and colour-blind users
    var tbody = el.chartTable.querySelector('tbody');
    tbody.textContent = '';
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      var a = document.createElement('td'); a.textContent = catLabel(r[0]);
      var b = document.createElement('td'); b.textContent = nf(r[1]);
      tr.appendChild(a); tr.appendChild(b); tbody.appendChild(tr);
    });
    el.chartTable.querySelector('[data-col="cat"]').textContent = t('category');
    el.chartTable.querySelector('[data-col="n"]').textContent = t('count');
    el.chartToggle.textContent = tableMode ? t('chartBars') : t('chartTable');
  }

  // ---------- wiring -----------------------------------------------------
  // (no inline onsubmit: the site's CSP forbids inline handlers)
  var debounce;
  var form = el.q.form;
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearTimeout(debounce);
    state.q = el.q.value; writeUrl(false); apply();
  });
  el.q.addEventListener('input', function () {
    clearTimeout(debounce);
    debounce = setTimeout(function () { state.q = el.q.value.slice(0, 200); writeUrl(false); apply(); }, 120);
  });
  el.q.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && el.q.value) { e.preventDefault(); el.q.value = ''; state.q = ''; writeUrl(false); apply(); }
  });
  // replaceState: arrowing through the options must not add history entries
  el.cat.addEventListener('change', function () { state.cat = el.cat.value; writeUrl(false); apply(); });
  el.chips.addEventListener('click', function (e) {
    var c = e.target.closest('.chip');
    if (!c) return;
    state.src = c.getAttribute('data-src');
    state.cat = '';
    writeUrl(true); apply();
  });
  el.more.querySelector('button').addEventListener('click', function () {
    var firstNew = shown;
    shown += PAGE;
    render();
    var item = el.list.children[firstNew];
    var link = item && item.querySelector('a');
    if (link) link.focus({ preventScroll: true });
  });
  function clearAll() { state = { q: '', src: 'all', cat: '' }; writeUrl(true); apply(); el.q.focus(); }
  el.clear.addEventListener('click', clearAll);
  document.getElementById('empty-clear').addEventListener('click', clearAll);
  el.emptySrc.querySelector('button').addEventListener('click', function () {
    state.src = 'all'; writeUrl(true); apply(); el.q.focus();
  });
  el.chartToggle.addEventListener('click', function () {
    tableMode = !tableMode;
    el.chart.hidden = tableMode;
    el.chartTable.hidden = !tableMode;
    el.chartToggle.textContent = tableMode ? t('chartBars') : t('chartTable');
  });
  window.addEventListener('popstate', function () { if (data) { readUrl(); apply(); } });
  document.addEventListener('cos:langchange', function () {
    if (data) { apply(); setCounts(); } else { el.status.textContent = t('loading'); }
  });
  window.addEventListener('scroll', hideTip, { passive: true });

  function setCounts() {
    el.chips.querySelectorAll('.chip').forEach(function (c) {
      var s = c.getAttribute('data-src');
      var n = s === 'all' ? data.counts.total : data.counts[s];
      var span = c.querySelector('.n');
      if (span) span.textContent = nf(n);
    });
  }

  function ready(d) {
    data = d;
    el.status.hidden = true;
    document.getElementById('explorer').removeAttribute('aria-busy');
    readUrl();
    setCounts();
    apply();
  }
  function load() {
    if (window.COS_TOOLS) { ready(window.COS_TOOLS); return; }
    el.status.hidden = false;
    el.status.textContent = t('loading');
    fetch('assets/data/tools.json', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(ready)
      .catch(function () {
        el.status.textContent = t('loadFail') + ' ';
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'btn btn-ghost btn-sm'; b.textContent = t('retry');
        b.addEventListener('click', load);
        el.status.appendChild(b);
      });
  }
  load();
})();
