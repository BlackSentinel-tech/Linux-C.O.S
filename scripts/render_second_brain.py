#!/usr/bin/env python3
"""Linux-C.O.S -- renders a richer, more "alive" visualization of graphify's
knowledge graph than graphify's own stock `graph.html` (muted 10-color
Tableau palette, static nodes). This is a separate file for a reason:
`graphify update`/`graphify export html` regenerate graph.html from
graphify's own template every time and would clobber any hand-edit to that
file -- this script instead reads the same graph.json graphify already
produces and writes its own output (graph-live.html), so re-running it after
`graphify update build` never gets overwritten by graphify itself.

Usage:
    python3 scripts/render_second_brain.py [--graph build/graphify-out/graph.json]
                                            [--out build/graphify-out/graph-live.html]

Purely cosmetic (see CLAUDE.md's graphify section) -- Claude should query
graph.json directly (graphify query/path/explain), never scrape this HTML.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VIVID_PALETTE = [
    "#00e5ff",  # electric cyan
    "#ff2e9a",  # hot magenta
    "#7c4dff",  # violet
    "#00ff9c",  # neon green
    "#ffd600",  # gold
    "#ff6d00",  # neon orange
    "#ff1744",  # red
    "#18ffff",  # turquoise
    "#d500f9",  # magenta-purple
    "#c6ff00",  # lime
    "#40c4ff",  # sky blue
    "#ff80ab",  # pink
]


def build_html(graph: dict, labels: dict[str, str], title: str) -> str:
    nodes = graph.get("nodes", [])
    links = graph.get("links", graph.get("edges", []))

    # degree (for sizing + "hub glow")
    degree: dict[str, int] = {}
    for e in links:
        s, t = str(e.get("source")), str(e.get("target"))
        degree[s] = degree.get(s, 0) + 1
        degree[t] = degree.get(t, 0) + 1

    communities = sorted({n.get("community", 0) for n in nodes})
    palette = {
        cid: VIVID_PALETTE[i % len(VIVID_PALETTE)] for i, cid in enumerate(communities)
    }

    out_nodes = []
    for n in nodes:
        nid = n["id"]
        cid = n.get("community", 0)
        out_nodes.append(
            {
                "id": nid,
                "label": n.get("label", nid),
                "community": cid,
                "color": palette.get(cid, "#8888ff"),
                "degree": degree.get(nid, 0),
                "file_type": n.get("file_type", ""),
                "source_file": n.get("source_file", ""),
                "kind": n.get("node_kind", ""),
            }
        )

    out_links = []
    for e in links:
        out_links.append(
            {
                "source": str(e.get("source")),
                "target": str(e.get("target")),
                "relation": e.get("relation", ""),
            }
        )

    legend = [
        {
            "cid": cid,
            "color": palette[cid],
            "label": labels.get(str(cid), f"Community {cid}"),
            "count": sum(1 for n in nodes if n.get("community", 0) == cid),
        }
        for cid in communities
    ]

    payload = json.dumps({"nodes": out_nodes, "links": out_links, "legend": legend})

    return _TEMPLATE.replace("__PAYLOAD__", payload).replace("__TITLE__", title)


_TEMPLATE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: #05050f; overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  #stars { position: fixed; inset: 0; z-index: 0; }
  #graph-wrap { position: fixed; inset: 0; z-index: 1; }
  svg { width: 100%; height: 100%; cursor: grab; }
  svg:active { cursor: grabbing; }

  #header { position: fixed; top: 0; left: 0; right: 0; z-index: 5;
    padding: 18px 24px 10px; pointer-events: none;
    background: linear-gradient(to bottom, rgba(5,5,15,0.9), transparent); }
  #header h1 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.02em;
    background: linear-gradient(90deg, #00e5ff, #ff2e9a, #7c4dff, #00ff9c);
    background-size: 300% 100%;
    -webkit-background-clip: text; background-clip: text; color: transparent;
    animation: hue 8s linear infinite; }
  #header p { margin: 4px 0 0; font-size: 12px; color: #8a8aa8; }
  @keyframes hue { 0% { background-position: 0% 50%; } 100% { background-position: 300% 50%; } }

  #search-wrap { position: fixed; top: 18px; right: 24px; z-index: 6; width: 260px; }
  #search { width: 100%; background: rgba(20,20,40,0.85); backdrop-filter: blur(6px);
    border: 1px solid #33335a; color: #e8e8ff; padding: 9px 12px; border-radius: 10px;
    font-size: 13px; outline: none; box-shadow: 0 0 0 0 rgba(0,229,255,0); transition: box-shadow .2s; }
  #search:focus { border-color: #00e5ff; box-shadow: 0 0 16px rgba(0,229,255,0.4); }

  #legend { position: fixed; bottom: 20px; left: 20px; z-index: 6; max-width: 260px;
    background: rgba(15,15,30,0.85); backdrop-filter: blur(6px); border: 1px solid #2a2a4e;
    border-radius: 12px; padding: 14px 16px; max-height: 46vh; overflow-y: auto; }
  #legend h3 { margin: 0 0 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
    color: #8a8aa8; }
  .leg-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12.5px;
    color: #d8d8f0; cursor: pointer; user-select: none; }
  .leg-row:hover { color: #fff; }
  .leg-dot { width: 11px; height: 11px; border-radius: 50%; flex: none; box-shadow: 0 0 8px 1px currentColor; }
  .leg-count { margin-left: auto; color: #666; font-size: 11px; }
  .leg-row.dim { opacity: 0.35; }

  #info { position: fixed; bottom: 20px; right: 24px; z-index: 6; width: 300px;
    background: rgba(15,15,30,0.9); backdrop-filter: blur(6px); border: 1px solid #2a2a4e;
    border-radius: 12px; padding: 16px; display: none; }
  #info.show { display: block; }
  #info h3 { margin: 0 0 10px; font-size: 14px; color: #fff; }
  #info .row { font-size: 12px; color: #aab; margin-bottom: 6px; }
  #info .row b { color: #e8e8ff; }
  #info-close { position: absolute; top: 10px; right: 12px; cursor: pointer; color: #667; font-size: 14px; }
  #info-close:hover { color: #fff; }

  #stats { position: fixed; top: 62px; right: 24px; z-index: 6;
    font-size: 11px; color: #667; letter-spacing: 0.04em; text-align: right; }

  .node-label { fill: #eef; font-size: 10px; pointer-events: none;
    text-shadow: 0 0 4px #000, 0 0 8px #000; }
  .link { stroke-opacity: 0.55; }
</style>
</head>
<body>
<canvas id="stars"></canvas>
<div id="header">
  <h1>Linux-C.O.S -- Segundo Cerebro</h1>
  <p>Grafo de conocimiento en vivo -- generado por graphify, renderizado a mano</p>
</div>
<div id="search-wrap"><input id="search" placeholder="Buscar nodo..." autocomplete="off"></div>
<div id="legend"><h3>Comunidades</h3><div id="legend-list"></div></div>
<div id="info">
  <span id="info-close">&#10005;</span>
  <h3 id="info-title"></h3>
  <div id="info-body"></div>
</div>
<div id="stats"></div>
<div id="graph-wrap"><svg></svg></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const DATA = __PAYLOAD__;

// ---------- starfield background ----------
(function stars(){
  const c = document.getElementById('stars');
  const ctx = c.getContext('2d');
  let w, h, pts;
  function resize(){
    w = c.width = window.innerWidth; h = c.height = window.innerHeight;
    pts = Array.from({length: Math.floor((w*h)/9000)}, () => ({
      x: Math.random()*w, y: Math.random()*h, r: Math.random()*1.3+0.2,
      s: Math.random()*0.4+0.05, p: Math.random()*Math.PI*2
    }));
  }
  window.addEventListener('resize', resize); resize();
  function tick(t){
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle = '#0a0a1a';
    for (const pt of pts){
      const tw = 0.5 + 0.5*Math.sin(t*0.001*pt.s + pt.p);
      ctx.globalAlpha = 0.15 + tw*0.55;
      ctx.beginPath(); ctx.arc(pt.x, pt.y, pt.r, 0, Math.PI*2);
      ctx.fillStyle = '#bcd'; ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();

// ---------- graph ----------
const svg = d3.select('svg');
const g = svg.append('g');
svg.call(d3.zoom().scaleExtent([0.15, 6]).on('zoom', (ev) => g.attr('transform', ev.transform)));

const defs = svg.append('defs');
DATA.legend.forEach(l => {
  const f = defs.append('filter').attr('id', 'glow'+l.cid).attr('x','-150%').attr('y','-150%').attr('width','400%').attr('height','400%');
  f.append('feGaussianBlur').attr('stdDeviation', 4).attr('result', 'blur');
  const merge = f.append('feMerge');
  merge.append('feMergeNode').attr('in', 'blur');
  merge.append('feMergeNode').attr('in', 'SourceGraphic');
});

const maxDeg = Math.max(1, ...DATA.nodes.map(n => n.degree));
const radius = d3.scaleSqrt().domain([0, maxDeg]).range([7, 26]);

const sim = d3.forceSimulation(DATA.nodes)
  .force('link', d3.forceLink(DATA.links).id(d => d.id).distance(90).strength(0.35))
  .force('charge', d3.forceManyBody().strength(-260))
  .force('center', d3.forceCenter(0, 0))
  .force('collide', d3.forceCollide(d => radius(d.degree) + 14));

const link = g.append('g').selectAll('line')
  .data(DATA.links).join('line')
  .attr('class', 'link')
  .attr('stroke', d => {
    const s = DATA.nodes.find(n => n.id === d.source.id || n.id === d.source);
    return s ? s.color : '#556';
  })
  .attr('stroke-width', 1.4);

const nodeG = g.append('g').selectAll('g')
  .data(DATA.nodes).join('g')
  .attr('class', 'nodeg')
  .style('cursor', 'pointer')
  .call(d3.drag()
    .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; })
    .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
    .on('end', (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));

nodeG.append('circle')
  .attr('r', d => radius(d.degree))
  .attr('fill', d => d.color)
  .attr('filter', d => `url(#glow${d.community})`)
  .attr('opacity', 0.92);

nodeG.append('circle')
  .attr('r', d => Math.max(3, radius(d.degree) * 0.35))
  .attr('fill', '#fff')
  .attr('opacity', 0.85);

nodeG.append('text')
  .attr('class', 'node-label')
  .attr('dy', d => radius(d.degree) + 13)
  .attr('text-anchor', 'middle')
  .text(d => d.label.length > 28 ? d.label.slice(0, 26) + '...' : d.label);

// gentle breathing pulse on hub nodes (degree above median)
const med = d3.median(DATA.nodes, d => d.degree) || 0;
nodeG.filter(d => d.degree > med).select('circle')
  .each(function(d){
    d3.select(this).transition().duration(1400 + Math.random()*800)
      .ease(d3.easeSinInOut)
      .attr('r', radius(d.degree) * 1.18)
      .transition().duration(1400 + Math.random()*800)
      .ease(d3.easeSinInOut)
      .attr('r', radius(d.degree))
      .on('end', function repeat(){
        d3.select(this).transition().duration(1400 + Math.random()*800).ease(d3.easeSinInOut)
          .attr('r', radius(d.degree) * 1.18)
          .transition().duration(1400 + Math.random()*800).ease(d3.easeSinInOut)
          .attr('r', radius(d.degree))
          .on('end', repeat);
      });
  });

sim.on('tick', () => {
  link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  nodeG.attr('transform', d => `translate(${d.x},${d.y})`);
});

// center the view once the sim settles a bit
setTimeout(() => {
  const bounds = g.node().getBBox();
  const w = window.innerWidth, h = window.innerHeight;
  const scale = Math.min(2, 0.85 / Math.max(bounds.width / w, bounds.height / h, 0.001));
  const tx = w/2 - scale*(bounds.x + bounds.width/2);
  const ty = h/2 - scale*(bounds.y + bounds.height/2);
  svg.transition().duration(700).call(
    d3.zoom().scaleExtent([0.15, 6]).on('zoom', (ev) => g.attr('transform', ev.transform)).transform,
    d3.zoomIdentity.translate(tx, ty).scale(scale)
  );
}, 900);

// ---------- interaction ----------
const neighborsOf = id => {
  const s = new Set([id]);
  DATA.links.forEach(l => {
    const a = l.source.id || l.source, b = l.target.id || l.target;
    if (a === id) s.add(b);
    if (b === id) s.add(a);
  });
  return s;
};

function focusNode(d){
  const nbs = neighborsOf(d.id);
  nodeG.style('opacity', n => nbs.has(n.id) ? 1 : 0.12);
  link.style('opacity', l => (nbs.has(l.source.id||l.source) && nbs.has(l.target.id||l.target)) ? 0.9 : 0.04);
  document.getElementById('info').classList.add('show');
  document.getElementById('info-title').textContent = d.label;
  const conns = DATA.links.filter(l => (l.source.id||l.source)===d.id || (l.target.id||l.target)===d.id);
  document.getElementById('info-body').innerHTML = `
    <div class="row"><b>Comunidad:</b> ${DATA.legend.find(l=>l.cid===d.community)?.label ?? d.community}</div>
    <div class="row"><b>Archivo:</b> ${d.source_file || '-'}</div>
    <div class="row"><b>Tipo:</b> ${d.file_type || d.kind || '-'}</div>
    <div class="row"><b>Conexiones:</b> ${conns.length}</div>
  `;
}
function clearFocus(){
  nodeG.style('opacity', 1);
  link.style('opacity', 0.55);
  document.getElementById('info').classList.remove('show');
}
nodeG.on('click', (ev, d) => { ev.stopPropagation(); focusNode(d); });
svg.on('click', clearFocus);
document.getElementById('info-close').onclick = clearFocus;

// legend
const legendList = document.getElementById('legend-list');
const hidden = new Set();
DATA.legend.forEach(l => {
  const row = document.createElement('div');
  row.className = 'leg-row';
  row.style.color = l.color;
  row.innerHTML = `<span class="leg-dot" style="background:${l.color}"></span><span style="color:#d8d8f0">${l.label}</span><span class="leg-count">${l.count}</span>`;
  row.onclick = () => {
    if (hidden.has(l.cid)) { hidden.delete(l.cid); row.classList.remove('dim'); }
    else { hidden.add(l.cid); row.classList.add('dim'); }
    nodeG.style('display', n => hidden.has(n.community) ? 'none' : null);
    link.style('display', ln => {
      const sn = DATA.nodes.find(n => n.id === (ln.source.id||ln.source));
      const tn = DATA.nodes.find(n => n.id === (ln.target.id||ln.target));
      return (sn && hidden.has(sn.community)) || (tn && hidden.has(tn.community)) ? 'none' : null;
    });
  };
  legendList.appendChild(row);
});

// search
document.getElementById('search').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  if (!q) { clearFocus(); return; }
  const hit = DATA.nodes.find(n => n.label.toLowerCase().includes(q));
  if (hit) focusNode(hit);
});

document.getElementById('stats').textContent =
  `${DATA.nodes.length} nodos · ${DATA.links.length} conexiones · ${DATA.legend.length} comunidades`;
</script>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default="build/graphify-out/graph.json")
    ap.add_argument("--labels", default=None)
    ap.add_argument("--out", default="build/graphify-out/graph-live.html")
    ap.add_argument("--title", default="Linux-C.O.S -- Segundo Cerebro")
    args = ap.parse_args()

    graph_path = Path(args.graph)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))

    labels_path = Path(args.labels) if args.labels else graph_path.parent / ".graphify_labels.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8")) if labels_path.is_file() else {}

    html = build_html(graph, labels, args.title)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path} ({len(DATA_nodes := graph.get('nodes', []))} nodes)")


if __name__ == "__main__":
    main()
