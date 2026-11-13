#!/bin/sh
# Linux-C.O.S -- render the desktop in a container and save screenshots.
#   tests/desktop/run.sh <scenario> [outdir]
# Scenarios live in tests/desktop/scenarios/<name>.sh and run inside the
# cos-desktop-test image (build it: docker build -t cos-desktop-test tests/desktop)
# with the ISO's includes.chroot overlaid on / exactly as live-build would.
set -eu
cd "$(dirname "$0")/../.."
scenario=${1:?usage: run.sh <scenario> [outdir]}
out=${2:-${TMPDIR:-/tmp}/cos-desktop-shots}
mkdir -p "$out"
exec docker run --rm --platform linux/amd64 --shm-size=1g \
  -e COS_MODE -e COS_FX -e COS_SHOT -e COS_RES \
  -v "$PWD/build/config/includes.chroot:/inc:ro" \
  -v "$PWD/build/config/hooks/normal:/hooks:ro" \
  -v "$PWD/build/branding:/branding:ro" \
  -v "$PWD/tests/desktop:/t:ro" \
  -v "$out:/out" \
  cos-desktop-test /t/inside.sh "$scenario"
