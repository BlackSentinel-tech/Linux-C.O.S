#!/usr/bin/env python3
"""Regenerate build/config/hooks/normal/0035-usrlocal-scripts.hook.chroot.

live-build has repeatedly failed to copy config/includes.chroot/usr/local/
{bin,sbin} into the image (see the hook's header), so the hook writes those
scripts itself with heredocs. Hand-maintaining two copies of every script is
how they drift apart -- so the files under includes.chroot are the single
source of truth and this script writes the hook from them.

    python3 scripts/sync-usrlocal-hook.py          # rewrite the hook
    python3 scripts/sync-usrlocal-hook.py --check  # exit 1 if it is stale (CI)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "build/config/includes.chroot"
HOOK = ROOT / "build/config/hooks/normal/0035-usrlocal-scripts.hook.chroot"

HEADER = """#!/bin/sh
# Linux-C.O.S build hook -- writes our /usr/local/bin and /usr/local/sbin
# scripts directly instead of relying on includes.chroot for them.
#
# GENERATED FILE -- do not edit by hand. The source of truth is
# config/includes.chroot/usr/local/{bin,sbin}/; regenerate this hook with
#     python3 scripts/sync-usrlocal-hook.py
# (CI runs it with --check and fails if this file is stale).
#
# Every real build attempt so far has shown config/includes.chroot copying
# correctly into every other location (etc/, usr/share/, etc/systemd/) --
# except /usr/local/bin and /usr/local/sbin specifically end up empty every
# time, on both a session-interrupted run and a fully clean uninterrupted
# one. Root cause not pinned down (something in live-build's
# Chroot_copy_dir / rsync -K handling of those two paths specifically, on a
# still-forming FHS tree). Heredocs here, using the exact mechanism every
# other hook in this project already relies on successfully, are more
# reliable than chasing that mystery further.
set -e

echo "[linux-cos] writing /usr/local/bin and /usr/local/sbin scripts"

mkdir -p /usr/local/bin /usr/local/sbin
"""


def scripts() -> list[Path]:
    out: list[Path] = []
    for sub in ("usr/local/bin", "usr/local/sbin"):
        out += sorted(p for p in (INC / sub).iterdir() if p.is_file())
    return out


def render() -> str:
    parts = [HEADER]
    targets = []
    for p in scripts():
        body = p.read_text()
        if not body.endswith("\n"):
            body += "\n"
        if "\nLINUX_COS_EOF\n" in "\n" + body:
            raise SystemExit(f"{p}: contains the heredoc terminator")
        target = "/" + str(p.relative_to(INC))
        targets.append(target)
        parts.append(f"\ncat > {target} <<'LINUX_COS_EOF'\n{body}LINUX_COS_EOF\n")
    parts.append("\nchmod 0755 " + " ".join(targets) + "\n")
    return "".join(parts)


def main() -> int:
    want = render()
    if "--check" in sys.argv[1:]:
        have = HOOK.read_text() if HOOK.exists() else ""
        if have != want:
            print(f"{HOOK.relative_to(ROOT)} is stale -- run: python3 scripts/sync-usrlocal-hook.py")
            return 1
        print("usrlocal hook is in sync")
        return 0
    HOOK.write_text(want)
    HOOK.chmod(0o755)
    print(f"wrote {HOOK.relative_to(ROOT)} ({len(scripts())} scripts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
