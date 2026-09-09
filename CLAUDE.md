## graphify

This project has a knowledge graph with god nodes, community structure, and
cross-file relationships covering the actual OS build project. The real data
lives at `build/graphify-out/`; `graphify-out/` at the repo root is a symlink
to it, so every default-path graphify command (`graphify query`, `path`,
`explain`, no `--graph` needed) just works from the project root.

**Important path note**: graphify hardcodes `build` as a skipped directory name
(same bucket as `dist`/`target`/`out` -- generated-output heuristics), but this
project's real source tree is literally named `build/`. Re-extraction/rebuild
must target the `build` subfolder directly -- **`graphify update build`, never
`graphify update .`** -- or the whole tree gets silently skipped and you get a
0-node graph with no error (the symlink only fixes reads, not the scan root).
`tools/` (vendored external repos: graphify itself, claude-code-router,
repomix, aider, ccusage) and `data/*.json` (raw tool catalogs, not
architecture) are intentionally excluded -- see `.graphifyignore`.

Rules:
- For codebase questions, first run `graphify query "<question>"` when `graphify-out/graph.json` exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation instead of raw source browsing.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code under `build/`, run `graphify update build` to keep the graph current (AST-only, no API cost).
- An Obsidian vault mirroring this same graph lives at `obsidian-vault/` (visual browsing for a human, not for Claude -- query the JSON graph directly instead of walking the vault's markdown notes).
- A richer live visualization (more colors, glow, motion) lives at `build/graphify-out/graph-live.html` -- open it for a human-facing view; it's cosmetic only, not a data source.
