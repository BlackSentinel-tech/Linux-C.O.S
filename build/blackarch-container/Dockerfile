# Linux-C.O.S -- the full BlackArch tool layer, baked as a standalone image.
#
# Heads-up on scale: installing the *entire* `blackarch` package group is not
# a small download -- historically tens of GB and a multi-hour build even on
# a fast connection, because it's 2,858 packages including several sizeable
# wordlist/ML/SDR toolchains. This is the honest cost of "every BlackArch
# tool, preinstalled, zero download after boot" -- see docs/BLACKARCH-INTEGRATION.md
# for the size/time tradeoff and the leaner alternative (pull on first boot
# instead of baking into the ISO).
#
# Build standalone:   docker build -t linux-cos/blackarch:latest .
# Export for baking into the ISO:  docker save linux-cos/blackarch:latest -o blackarch-image.tar
#   then drop that tar at build/config/includes.chroot/opt/linux-cos/blackarch-image.tar
#   before running the main ISO build -- linux-cos-firstboot loads it with no
#   network needed if it's present.
FROM archlinux:base-devel

RUN pacman -Syu --noconfirm --needed git curl sudo zsh

# BlackArch's own strap script wires up their repo + keyring correctly
# (safer than hand-rolling pacman.conf edits that drift when they rotate keys).
# NOTE: no checksum pin here -- BlackArch doesn't publish one for strap.sh,
# so this is trust-on-first-use against blackarch.org over TLS. If you want
# stronger supply-chain assurance, vendor a copy of strap.sh you've reviewed
# into this directory and COPY it in instead of curling it at build time.
RUN curl -O https://blackarch.org/strap.sh \
    && chmod +x strap.sh \
    && ./strap.sh

# The full group. This is the "todo" the user actually asked for.
RUN pacman -Syu --noconfirm --needed blackarch

RUN useradd -m -s /usr/bin/zsh -G wheel operator \
    && echo '%wheel ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/wheel

WORKDIR /home/operator
CMD ["/usr/bin/zsh"]
