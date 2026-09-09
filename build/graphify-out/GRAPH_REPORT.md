# Graph Report - build  (2026-09-09)

## Corpus Check
- 9 files · ~21,663 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 27 nodes · 19 edges · 10 communities (2 shown, 8 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Linux-C.O.S
- cos-stacks
- Why BlackArch is a container, not native packages
- Status
- config
- build.sh
- build-inside.sh
- wazuh/README.md
- blackarch-shell
- linux-cos-firstboot

## God Nodes (most connected - your core abstractions)
1. `Linux-C.O.S` - 6 edges
2. `Status` - 3 edges
3. `Why BlackArch is a container, not native packages` - 2 edges
4. `build-inside.sh script` - 1 edges
5. `build.sh script` - 1 edges
6. `Real bugs found and fixed getting here (keep this list -- every one of` - 1 edges
7. `these will bite again if a fix gets reverted by accident)` - 1 edges
8. `Layout` - 1 edges
9. `Building` - 1 edges
10. `Testing the ISO` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (10 total, 8 thin omitted)

### Community 0 - "Linux-C.O.S"
Cohesion: 0.33
Nodes (5): Building, Layout, Linux-C.O.S, Testing the ISO, TODO (known gaps, in rough priority order)

### Community 3 - "Status"
Cohesion: 0.67
Nodes (3): Real bugs found and fixed getting here (keep this list -- every one of, Status, these will bite again if a fix gets reverted by accident)

## Knowledge Gaps
- **10 isolated node(s):** `build-inside.sh script`, `build.sh script`, `Real bugs found and fixed getting here (keep this list -- every one of`, `these will bite again if a fix gets reverted by accident)`, `Layout` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 21 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Linux-C.O.S` connect `Linux-C.O.S` to `Status`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Status` connect `Status` to `Linux-C.O.S`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `build-inside.sh script`, `build.sh script`, `Real bugs found and fixed getting here (keep this list -- every one of` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._