# Graph Report - build  (2026-11-04)

## Corpus Check
- 25 files · ~83,819 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 118 nodes · 212 edges · 29 communities (10 shown, 10 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1dd53314`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Linux-C.O.S
- cos-stacks script
- Why BlackArch is a container, not native packages
- cmd_down
- config
- build.sh
- build-inside.sh
- wazuh/README.md
- blackarch-shell
- linux-cos-firstboot
- Linux-C.O.S user guide
- cos-help
- linux-cos-session-setup
- cos-pause
- linux-cos-blackarch-pull
- linux-cos-live-password
- cos-stacks
- cos-ai
- require_stack
- docker_up

## God Nodes (most connected - your core abstractions)
1. `Linux-C.O.S user guide` - 8 edges
2. `Linux-C.O.S` - 7 edges
3. `Status` - 3 edges
4. `4. Defensive stack` - 2 edges
5. `Why BlackArch is a container, not native packages` - 2 edges
6. `build-inside.sh script` - 1 edges
7. `build.sh script` - 1 edges
8. `Real bugs found and fixed getting here (keep this list -- every one of` - 1 edges
9. `these will bite again if a fix gets reverted by accident)` - 1 edges
10. `Layout` - 1 edges

## Surprising Connections (you probably didn't know these)
- `cos-stacks script` --calls--> `cmd_down()`  [EXTRACTED]
  build/config/includes.chroot/usr/local/bin/cos-stacks → build/config/includes.chroot/usr/local/bin/cos-stacks  _Bridges community 1 → community 3_
- `cos-stacks script` --calls--> `cmd_up()`  [EXTRACTED]
  build/config/includes.chroot/usr/local/bin/cos-stacks → build/config/includes.chroot/usr/local/bin/cos-stacks  _Bridges community 1 → community 16_
- `wazuh_up()` --calls--> `die()`  [EXTRACTED]
  build/config/includes.chroot/usr/local/bin/cos-stacks → build/config/includes.chroot/usr/local/bin/cos-stacks  _Bridges community 3 → community 16_
- `compose()` --calls--> `docker_cmd()`  [EXTRACTED]
  build/config/includes.chroot/usr/local/bin/cos-stacks → build/config/includes.chroot/usr/local/bin/cos-stacks  _Bridges community 19 → community 3_
- `cmd_info()` --calls--> `docker_up()`  [EXTRACTED]
  build/config/includes.chroot/usr/local/bin/cos-stacks → build/config/includes.chroot/usr/local/bin/cos-stacks  _Bridges community 19 → community 1_

## Import Cycles
- None detected.

## Communities (29 total, 10 thin omitted)

### Community 0 - "Linux-C.O.S"
Cohesion: 0.20
Nodes (9): Building, Checking changes without building an ISO, Layout, Linux-C.O.S, Real bugs found and fixed getting here (keep this list -- every one of, Status, Testing the ISO, these will bite again if a fix gets reverted by accident) (+1 more)

### Community 1 - "cos-stacks script"
Cohesion: 0.52
Nodes (7): cos-stacks script, cmd_creds(), cmd_info(), cmd_list(), cols(), menu(), meta()

### Community 3 - "cmd_down"
Cohesion: 0.54
Nodes (8): cmd_down(), cmd_logs(), cmd_status(), compose(), die(), need_docker(), stack_compose(), wazuh_compose()

### Community 8 - "blackarch-shell"
Cohesion: 0.80
Nodes (4): blackarch-shell script, docker_cmd(), need_docker(), usage()

### Community 10 - "Linux-C.O.S user guide"
Cohesion: 0.20
Nodes (9): 1. Live session, 2. AI assistant (`cos-ai`), 3. Offensive tools, 4. Defensive stack, 5. Installing to disk, 6. Hardening reference, 7. Help & bugs, Heavy platforms: `cos-stacks` (+1 more)

### Community 11 - "cos-help"
Cohesion: 0.61
Nodes (7): cos-help script, ai(), defense(), install_topic(), line(), offense(), system()

### Community 16 - "cos-stacks"
Cohesion: 0.25
Nodes (10): cmd_up(), ensure_secrets(), env_file(), has_secrets(), info(), usage(), version_ge(), warn() (+2 more)

### Community 17 - "cos-ai"
Cohesion: 0.31
Nodes (17): cos-ai script, chat_call(), cmd_models(), cmd_setup(), cmd_status(), die(), have_ollama(), info() (+9 more)

### Community 18 - "require_stack"
Cohesion: 0.67
Nodes (3): require_stack(), stacks(), valid_stack()

### Community 19 - "docker_up"
Cohesion: 0.67
Nodes (4): docker_cmd(), docker_up(), running_count(), status_word()

## Knowledge Gaps
- **18 isolated node(s):** `build-inside.sh script`, `build.sh script`, `Real bugs found and fixed getting here (keep this list -- every one of`, `these will bite again if a fix gets reverted by accident)`, `Layout` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 46 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `build-inside.sh script`, `build.sh script`, `Real bugs found and fixed getting here (keep this list -- every one of` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._