# Linux-C.O.S

**C**yber **O**ffensive & defensive **S**ecurity. One Debian-based Linux
distribution: Kali's and Parrot's tools installed natively, BlackArch's
2,858 tools available through a bundled container, a real blue-team stack
(Suricata, Zeek, YARA, ClamAV, Wazuh, osquery, Falco, AIDE, Lynis...)
alongside the offensive side, and the OS itself hardened by default
(AppArmor enforcing, sysctl hardening, default-deny firewall, auditd rules).
XFCE desktop.

It's a real distro in the same sense Kali or Parrot are "their own distro":
own name, own branding, own defaults, own installer output -- built on top
of Debian rather than reinvented from the kernel up, because that's how
every serious security distro (Kali, Parrot, Tails, Qubes' dom0) actually
does it too.

## Status

**First real ISO built successfully** -- `output/live-image-amd64.hybrid.iso`,
~14.6 GiB, `file` confirms `ISO 9660 CD-ROM filesystem data (DOS/MBR boot
sector) 'LINUX-C.O.S' (bootable)`. Not boot-tested in a VM yet -- that's the
next step.

Base ended up being Kali's own `kali-rolling`, not Debian bookworm --
bookworm-as-base hit an unfixable "Frankendebian" ABI mismatch (kali-tools-*
needs newer glibc/libstdc++ than bookworm ships); Kali's repo is a complete,
internally-consistent base on its own. See the comment block at the top of
`auto/config` for the full story, and `docs/BLACKARCH-INTEGRATION.md` for
the BlackArch-as-container tradeoff.

- [x] live-build config + package manifests (pulled straight from Kali's
      and Parrot's real metapackage definitions -- see `../data/`)
- [x] hardening hooks (sysctl, AppArmor, ufw -- applied at first boot, not
      build time, see below -- auditd, ssh)
- [x] BlackArch container mechanism + the size/time tradeoff documented
- [x] branding: logo (`branding/logo/`), wallpaper (`branding/wallpapers/`),
      wired into XFCE desktop, lightdm greeter, and a Plymouth boot theme
- [x] Calamares installer config (partition incl. LUKS full-disk encryption,
      users, bootloader, post-install package cleanup, branded slideshow)
- [x] build environment Docker image built and confirmed working
- [x] first full `./build.sh` run to a real, valid, bootable ISO

### Real bugs found and fixed getting here (keep this list -- every one of
### these will bite again if a fix gets reverted by accident)

- `--distribution` alone only sets the bootstrap distro; chroot and binary
  passes need `--distribution-chroot`/`--distribution-binary` too, or they
  silently default to bookworm even on a Kali-rolling build.
- Kali-rolling has no `-security`/`-updates` suites (`--security false
  --updates false`) and needs `--debootstrap-options` to pass an explicit
  `--keyring=` (the archive key has to be trusted before debootstrap can
  even fetch Kali's own Release file).
- `falco`/`sysdig` compile a DKMS/eBPF kernel driver in their postinst,
  against whatever kernel is running -- inside a chroot that's the build
  container's kernel, not the target's, so it hard-fails the build. Not
  installed by default; see `blueteam-native.list.chroot`. Install them
  post-boot instead, where DKMS can build against the real kernel.
- `ufw` cannot run *any* subcommand at build time either (`ufw default deny
  incoming` alone fails) -- it shells out to iptables to check its version,
  and there's no real netfilter stack inside a chroot. All ufw setup moved
  to `linux-cos-firstboot`.
- `/etc/os-release` is already a symlink to `/usr/lib/os-release` on
  Kali/Debian -- don't `cp` one onto the other, that's `cp` erroring
  "same file".
- `--debian-installer live` (live-build's own installer integration) is
  redundant with our Calamares setup *and* unconditionally requires
  `grub-efi-amd64-signed`/`shim-signed`, which Kali's repo doesn't carry.
  Set `--debian-installer none`.
- **The big one**: `build-inside.sh`'s `rsync --delete` didn't exclude
  `chroot`/`chroot.packages.*` (live-build-generated paths that never exist
  in this project's own source tree) -- every *resumed* build silently
  `rsync --delete`'d parts of the already-built chroot before `lb build`
  even started, and which files survived depended on rsync's traversal
  order versus what still had proc/sys/dev mounted from the last run. This
  is what made "resuming after a small fix" look increasingly broken across
  several attempts, when the underlying chroot/hook/package config was
  actually fine the whole time. **Corollary learned the hard way: once
  something fails inside the `binary_*` phase specifically, redo the whole
  binary phase from a clean volume rather than clearing one stage marker
  at a time** -- `binary_rootfs` does its own temporary renames of
  `chroot/boot`, `chroot/chroot`, etc., and an isolated stage-marker fix
  leaves those in an inconsistent state that only shows up several stages
  later (e.g. `chroot/boot` ends up genuinely empty, not just mis-flagged).
- `username=<name>` on the live cmdline gets `live-config` to create that
  account fresh on every live boot, but with **no usable password** -- and
  lightdm's PAM stack rejects a blank one at the graphical greeter (a text
  console login accepts it fine, which is what made this confusing to spot
  from a screenshot). Two things were needed, not one: an explicit
  `autologin-user=` in `lightdm.conf.d/` (lightdm doesn't get autologin for
  free from `username=` the way gdm3/sddm do), *and* a service
  (`linux-cos-live-password.service`, `After=live-config.service`) that
  sets a real password every boot, since the account itself is recreated
  from scratch each time -- there's no persistent state to set it once.
  Live user is `kali`/`kali`, same convention as Kali's own live images.
- an early experiment (before switching to the Docker-volume workspace)
  ran `lb config`/`lb build` directly against this bind-mounted host
  directory -- `chroot/` and a pile of live-build-generated `config/*`
  files ended up committed-adjacent on the host and had to be cleaned out
  by hand. If you ever see a real `build/chroot/` directory sitting next
  to this README, or empty dirs like `config/apt`, `config/packages.chroot`
  etc. alongside the real `config/{archives,hooks,includes.chroot,
  package-lists}`, that's this happening again -- it means something ran
  `lb config` outside the container/volume; delete the stray output, don't
  try to keep it in sync with anything.

## Layout

```
build/
  Dockerfile              -- the build environment (Debian + live-build)
  build.sh                -- run this from macOS to build the ISO
  build-inside.sh          -- runs inside the container; do not run directly
  auto/config              -- live-build settings (lb config)
  config/
    package-lists/         -- what gets installed; see each file's header
    hooks/normal/           -- build-time chroot hooks, numbered = order
    includes.chroot/        -- files copied verbatim into the ISO's filesystem
  blackarch-container/      -- Dockerfile for the full BlackArch tool image
  branding/                 -- wallpapers/logo (placeholders -- see TODO)
  docs/
    BLACKARCH-INTEGRATION.md -- why BlackArch is a container, and the real
                                 size/time tradeoff on baking it into the ISO
  output/                   -- finished .iso lands here after a build
```

## Building

Requires Docker (already installed and confirmed working on this machine).

```bash
cd build
./build.sh
```

This is long (expect over an hour) and bandwidth-heavy (Debian base + all
of Kali + the blue-team layer, tens of GB). Run it in the background:

```bash
nohup ./build.sh > build.out 2>&1 &
tail -f output/build.log
```

Decide on the BlackArch baked-in-vs-first-boot tradeoff **before** your
first real build -- read `docs/BLACKARCH-INTEGRATION.md`, it changes final
ISO size a lot.

## Testing the ISO

**Live session login: `kali` / `kali`** (autologin is on by default, so
you shouldn't even see the prompt -- see it above if autologin is ever off).

Once `output/*.iso` exists, boot it in **UTM** -- this Mac is Apple Silicon,
and VirtualBox on ARM only runs ARM guests (it *lists* x86_64 guest OS
types, but `VBoxManage startvm` fails outright with
`VBOX_E_PLATFORM_ARCH_NOT_SUPPORTED`; don't bother with the VBoxManage
route on this machine). In UTM:

1. Create a New Virtual Machine
2. **Emulate** -- not "Virtualize", which on Apple Silicon only supports
   ARM64 guests and will silently create an incompatible VM (UTM does warn
   about this, but only at the very end of the wizard)
3. Linux
4. Architecture: **x86_64**
5. Boot ISO image: `build/output/live-image-amd64.hybrid.iso`
6. Memory: 4096 MB or more
7. Storage: skip it to just test the live session; add a 20+ GB disk if
   you also want to test the Calamares install path
8. Leave "Use Virtualization" / "Hardware OpenGL Acceleration" unchecked --
   neither applies when emulating a different architecture than the host

This is pure software emulation (QEMU TCG, no hardware acceleration across
architectures) -- expect boot to be genuinely slow, several minutes from
GRUB to desktop, not a sign anything is hung.

## TODO (known gaps, in rough priority order)

- [ ] boot-test in UTM/VirtualBox (see "Testing the ISO" above) -- not done
      yet, this is the very next step
- [ ] boot-test the Calamares install path specifically once the live
      session boots -- `unpackfs.conf`'s squashfs path
      (`/run/live/medium/live/filesystem.squashfs`) was written from
      live-boot's documented default, not verified against this actual
      ISO's layout yet
- [ ] decide BlackArch baked-in vs. first-boot (docs/BLACKARCH-INTEGRATION.md)
      -- currently first-boot (nothing baked in), so first real boot needs
      network to get `blackarch-shell` working
- [ ] GRUB theme/background isn't done yet (boots to a plain text GRUB menu
      before Plymouth takes over) -- cosmetic only, not blocking
- [ ] Secure Boot is explicitly disabled (`--uefi-secure-boot disable`) --
      fine for VM testing, but this ISO will not boot on real hardware with
      Secure Boot on until that's revisited (needs Kali's own shim/signed
      grub, which the build doesn't have a path to yet)
- [ ] this ISO was built with `--debian-installer none` -- Calamares (the
      live-desktop installer) is the only install path; nothing here uses
      classic Debian-Installer
