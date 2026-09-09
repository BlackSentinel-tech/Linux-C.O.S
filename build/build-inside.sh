#!/bin/sh
# Runs INSIDE the cos-builder container (see build.sh). Not meant to be run
# directly on macOS -- there's no debootstrap/chroot there.
#
# /src is this project, bind-mounted read-only from macOS (virtiofs/gRPC-fuse
# -- no mknod support, so live-build's chroot can't live here). /build is a
# real Docker volume (actual Linux filesystem underneath) where the chroot
# actually gets built. Sync config in, build, sync the finished ISO back out
# to /src-output (which macOS sees as build/output/).
set -e

echo "[linux-cos] syncing config into the build volume"
# THE ONE BUG THAT CAUSED EVERY "includes.chroot file went missing on
# resume" mystery in this project's history: --delete makes rsync remove
# anything in /build that isn't in /src -- and /src (this git-tracked
# project) never has a chroot/ directory, because live-build generates it
# fresh inside the volume. Every earlier version of this exclude list
# protected .build/local/cache/output but not chroot itself, so every
# resumed build silently rsync --delete'd parts of the already-built chroot
# before lb build even started, and which specific files survived depended
# on rsync's traversal order versus which subdirs had proc/sys/dev still
# mounted from the last run (mounted dirs can't be deleted through) --
# hence it looking "random" rather than a clean total wipe. If you add
# another live-build-generated top-level path here in the future (check
# `ls /build` inside the volume against this list), add it below too.
rsync -a --delete \
    --exclude='.build' --exclude='local' --exclude='cache' --exclude='chroot' \
    --exclude='chroot.packages.install' --exclude='chroot.packages.live' \
    --exclude='output' --exclude='build.out' \
    /src/ /build/

cd /build

echo "[linux-cos] lb config"
lb config

echo "[linux-cos] lb build (this is the long part: expect 30-90+ min for the"
echo "            Debian+Kali+Parrot layer alone, on top of whatever the"
echo "            BlackArch image step adds -- see docs/BLACKARCH-INTEGRATION.md)"
mkdir -p /src-output
lb build 2>&1 | tee /src-output/build.log

mv -f /build/*.iso /src-output/ 2>/dev/null || echo "[linux-cos] no ISO produced -- check output/build.log"
echo "[linux-cos] done -- see build/output/"
