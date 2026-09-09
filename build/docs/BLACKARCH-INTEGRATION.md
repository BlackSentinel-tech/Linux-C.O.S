# Why BlackArch is a container, not native packages

Debian (what Linux-C.O.S, Kali, and Parrot are all built on) uses `.deb`
packages installed by `apt`. BlackArch is Arch Linux with `pacman` packages.
There is no `apt install` for a `pacman` package -- the formats, dependency
resolvers, and filesystem layout conventions are different projects that
don't interoperate. Getting BlackArch's 2,858 tools onto a Debian base
natively would mean manually repackaging each one as a `.deb`, tracking
their upstream updates forever, ourselves. That's not a weekend project --
it's what the actual BlackArch team already does full-time for their own
distro.

The practical answer every real hybrid pentest-OS project reaches for is:
run BlackArch *as itself*, in a container, on top of the Debian base. That's
`blackarch-shell` -- it's a real, unmodified Arch Linux userland with the
full `blackarch` package group installed, so every tool runs exactly like it
would on real BlackArch (same binaries, same behavior), sharing your home
directory so files aren't trapped inside the container.

## The one real tradeoff: size vs. "zero download after boot"

The full `blackarch` pacman group is not small: historically tens of GB and
a multi-hour install even on a fast line, because it includes several
sizeable wordlist, ML, and SDR toolchains. That cost doesn't disappear just
because we're baking it into a container -- it has to happen *somewhere*.
Two honest options:

**A. Bake it into the ISO at build time (`build/blackarch-container/`).**
   `docker build` there produces the full image; `docker save` it to
   `build/config/includes.chroot/opt/linux-cos/blackarch-image.tar` and the
   next `./build.sh` run copies that tarball straight into the ISO. Result:
   the ISO itself grows by however large that tarball is (expect it to
   dominate total ISO size), the build machine needs to download the whole
   BlackArch group once during the container build, but a machine booted
   from the finished ISO needs **zero** network to get `blackarch-shell`
   working. This is the literal "preinstalled from day one" the user asked
   for, and it's what `linux-cos-firstboot` looks for first.

**B. Pull it on first real boot instead (the fallback path already wired
   up in `linux-cos-firstboot`).** ISO stays small and fast to build; the
   *installed* machine downloads the BlackArch image once, in the
   background, the first time it has network. Nothing to do here -- it's
   already the fallback when no baked-in tarball is present.

Neither of these is "wrong" -- it's a build-size/build-time vs.
distribution-size tradeoff, and it's a call worth making deliberately
rather than discovering by surprise when a 40GB ISO won't fit on a USB
stick. Default right now is **B** (nothing baked in yet) until that's
confirmed; flip to **A** by running the steps above before `./build.sh`.
