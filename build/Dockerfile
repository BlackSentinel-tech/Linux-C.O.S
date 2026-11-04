# Linux-C.O.S -- build environment. live-build needs debootstrap/chroot/
# mksquashfs, all of which want a real Linux kernel underneath -- this image
# runs inside Docker Desktop's Linux VM on macOS, with the container started
# --privileged (see build.sh) so chroot/mount work.
# mtools + dosfstools + grub-*-bin: build the UEFI (grub-efi) half of the
# BIOS+UEFI hybrid ISO -- see ../auto/config's --bootloaders.
FROM debian:bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    live-build \
    debootstrap \
    qemu-user-static \
    binfmt-support \
    rsync \
    cpio \
    xorriso \
    isolinux \
    syslinux-common \
    squashfs-tools \
    dosfstools \
    mtools \
    grub-common \
    grub-pc-bin \
    grub-efi-amd64-bin \
    git \
    curl \
    gnupg2 \
    ca-certificates \
    zstd \
    && rm -rf /var/lib/apt/lists/*

COPY kali-archive-keyring.gpg /usr/share/keyrings/kali-archive-keyring.gpg

WORKDIR /build
