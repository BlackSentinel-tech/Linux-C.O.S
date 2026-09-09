#!/bin/sh
# Linux-C.O.S -- build orchestrator, run from macOS.
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

echo "[linux-cos] building the build environment image"
docker build -t cos-builder .

mkdir -p output cache

# This Mac is Apple Silicon (arm64); the ISO targets amd64 (real pentest
# laptops are overwhelmingly x86_64, and several Kali/BlackArch tools still
# lack arm64 builds). That means every package's post-install scripts run
# under emulation during the build -- registering binfmt handlers here is
# what makes that possible at all, but expect the build to run noticeably
# slower than on x86_64 hardware because of it.
echo "[linux-cos] registering QEMU binfmt handlers for cross-arch (amd64 on arm64 host)"
docker run --rm --privileged tonistiigi/binfmt --install amd64

# live-build's chroot needs mknod (real device nodes for debootstrap).
# Docker Desktop's bind mount of this macOS directory is virtiofs/gRPC-fuse
# underneath -- neither supports mknod, so the actual chroot build has to
# happen on a real Linux filesystem: a named Docker volume, not this bind
# mount. The bind mount (/src) is read-only input (config/hooks/branding);
# build-inside.sh rsyncs it into the volume, builds there, and copies the
# finished ISO back out to output/ on the host side.
docker volume create cos-workspace >/dev/null

echo "[linux-cos] starting the live-build run"
docker run --rm --privileged \
    -v "$(pwd):/src:ro" \
    -v "cos-workspace:/build" \
    -v "$(pwd)/output:/src-output" \
    -v "$(pwd)/cache:/var/cache/apt/archives" \
    cos-builder /src/build-inside.sh
