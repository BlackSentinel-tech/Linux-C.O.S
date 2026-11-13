#!/bin/sh
# Linux-C.O.S -- build orchestrator. Run from macOS, Linux or Windows
# (WSL2) with Docker available.
#
# usage: ./build.sh
#
# What it does:
#   1. builds the cos-builder Docker image (Debian + live-build toolchain)
#   2. runs it --privileged (live-build needs real chroot/mount) with this
#      directory bind-mounted in, and kicks off build-inside.sh
#   3. the finished ISO lands in build/output/*.iso
#
# This is a long-running, bandwidth-heavy operation (pulls the Debian base,
# Kali's kali-linux-everything, Parrot's exclusives, and every blue-team
# package -- realistically tens of GB and well over an hour). Run it in the
# background and tail build/output/build.log, don't block on it in a
# foreground shell.
set -e
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "[linux-cos] docker is not installed or not on PATH -- see build/README.md" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "[linux-cos] the Docker daemon is not reachable (is Docker Desktop / dockerd running?)" >&2
  exit 1
fi

# COS_BUILDER_PLATFORM=linux/amd64 runs the whole builder as amd64. On Apple
# Silicon with Docker Desktop's Rosetta this is near-native speed, and it is
# required there anyway: grub-pc-bin / grub-efi-amd64-bin (see Dockerfile)
# have no arm64 builds, so the default arm64 builder image cannot be built.
PLATFORM_ARGS=''
if [ -n "${COS_BUILDER_PLATFORM:-}" ]; then
  PLATFORM_ARGS="--platform $COS_BUILDER_PLATFORM"
  echo "[linux-cos] builder platform: $COS_BUILDER_PLATFORM"
fi

echo "[linux-cos] building the build environment image"
# shellcheck disable=SC2086
docker build $PLATFORM_ARGS -t cos-builder .

mkdir -p output cache

# This Mac is Apple Silicon (arm64); the ISO targets amd64 (real pentest
# laptops are overwhelmingly x86_64, and several Kali/BlackArch tools still
# lack arm64 builds). That means every package's post-install scripts run
# under emulation during the build -- registering binfmt handlers here is
# what makes that possible at all, but expect the build to run noticeably
# slower than on x86_64 hardware because of it.
# On an x86_64 host (Linux, Intel Mac, Windows/WSL2) there is nothing to
# emulate, so skip it there.
case "$(uname -m)" in
  x86_64|amd64)
    echo "[linux-cos] native amd64 host -- no QEMU emulation needed" ;;
  *) if [ "${COS_BUILDER_PLATFORM:-}" = linux/amd64 ]; then
    echo "[linux-cos] amd64 builder (Rosetta) -- skipping QEMU binfmt"
  else
    echo "[linux-cos] registering QEMU binfmt handlers for cross-arch (amd64 on $(uname -m) host)"
    docker run --rm --privileged tonistiigi/binfmt --install amd64
  fi ;;
esac

# live-build's chroot needs mknod (real device nodes for debootstrap).
# Docker Desktop's bind mount of this macOS directory is virtiofs/gRPC-fuse
# underneath -- neither supports mknod, so the actual chroot build has to
# happen on a real Linux filesystem: a named Docker volume, not this bind
# mount. The bind mounts (/src, and /website for the offline guide) are
# read-only input (config/hooks/branding);
# build-inside.sh rsyncs it into the volume, builds there, and copies the
# finished ISO back out to output/ on the host side.
docker volume create cos-workspace >/dev/null

# COS_PROFILE selects how much of Kali's tool set goes in (full|slim|min);
# default full. Pass it through to build-inside.sh. See build/README.md.
COS_PROFILE=${COS_PROFILE:-full}
echo "[linux-cos] starting the live-build run (profile: $COS_PROFILE)"
# shellcheck disable=SC2086
docker run --rm --privileged $PLATFORM_ARGS \
    -e "COS_PROFILE=$COS_PROFILE" \
    -v "$(pwd):/src:ro" \
    -v "$(pwd)/../website:/website:ro" \
    -v "cos-workspace:/build" \
    -v "$(pwd)/output:/src-output" \
    -v "$(pwd)/cache:/var/cache/apt/archives" \
    cos-builder /src/build-inside.sh
