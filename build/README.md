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

- **Calamares never created a user.** The `exec` sequence had no `users`
  job (the `users` *page* only collects input), and also lacked
  `displaymanager`, `networkcfg`, `hwclock`, `initramfscfg`/`initramfs`.
  `scripts/lint.sh` now fails if `users` or `initramfs` go missing again.
- **Calamares aborted at the last step**: `packages.conf` did a plain
  `remove` of `calamares-settings-linux-cos`, a package that never existed
  (our settings are plain files). With the apt backend an unknown name in
  `remove` fails the whole install; it is `try_remove` now (lint-enforced).
- The installed system inherited the live session's lightdm autologin for
  `kali` (an account that doesn't exist there) and dead installer icons;
  `shellprocess.conf` removes them.
- `ufw --force enable` ran at first boot but `ufw.service` stayed disabled
  from the build hook, so the firewall was gone after the next reboot.
  `linux-cos-firstboot` now re-enables the unit.
- `linux-cos-firstboot` also ran in the live session (no marker survives a
  live boot) and started a multi-GB `docker pull` into the RAM overlay. It
  is live-aware now (firewall only), and the pull is its own unit
  (`linux-cos-blackarch-pull.service`, never in live) instead of a `&`
  child of a oneshot service.
- `docker compose` was never installed (only `docker.io`), so `cos-stacks`
  could not start anything -- `docker-compose` is in `base.list.chroot`.
- Stacks published their ports on `0.0.0.0` -- Docker-published ports
  bypass ufw entirely -- and shipped shared `change-me` passwords. Ports are
  `127.0.0.1` now and `cos-stacks` generates per-user random secrets
  (both lint-enforced).
- The live user wasn't in the `docker`/`wireshark` groups
  (`user-default-groups=` in `--bootappend-live`), and `splash` was missing
  from the kernel command line, so the Plymouth theme never showed.
- The Plymouth hook sed'ed background colors into a `.script` file that the
  `spinner` theme doesn't have (it is a two-step theme); colors now go in
  the `[two-step]` section of the `.plymouth` file.
- `unattended-upgrades` targeted Debian's `-security` origin, which a
  kali-rolling system never has; it silently did nothing.
- `0035-usrlocal-scripts.hook.chroot` duplicated every script by hand and
  had drifted (e.g. `linux-cos-live-password` only existed in the hook). It
  is generated now: `python3 scripts/sync-usrlocal-hook.py` (CI checks it).

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
  config/includes.binary/   -- files for the ISO itself (boot menu splash
                               images for GRUB and isolinux)
  branding/                 -- wallpapers/logo (placeholders -- see TODO)
  docs/
    BLACKARCH-INTEGRATION.md -- why BlackArch is a container, and the real
                                 size/time tradeoff on baking it into the ISO
  output/                   -- finished .iso lands here after a build
```

What the user gets, by location inside `config/includes.chroot/`:

```
usr/local/bin/cos-help            quick start (ES/EN) -- also "Quick Start" in the menu
usr/local/bin/cos-stacks          blue-team stacks: interactive menu, up/down/logs/creds
usr/local/bin/blackarch-shell     BlackArch container: shell, one-off commands, --status
usr/local/bin/cos-pause           keeps menu-launched terminals open until Enter
usr/local/bin/linux-cos-session-setup   per-user: wallpaper on every monitor, trusted installer icon
usr/local/sbin/linux-cos-firstboot      firewall (+ BlackArch image on installed systems)
usr/local/sbin/linux-cos-blackarch-pull one-time image download (its own systemd unit)
etc/xdg/menus/applications-merged/linux-cos.menu + usr/share/applications/linux-cos-*.desktop
                                  the "Linux-C.O.S" folder in the XFCE applications menu
usr/share/grub/themes/linux-cos/ + etc/default/grub.d/zz-linux-cos.cfg
                                  GRUB theme on installed systems
usr/share/doc/linux-cos/README.md the offline user guide ("User Guide" in the menu)
opt/linux-cos/blueteam-stacks/<stack>/{stack.meta,secrets.list,docker-compose.yml}
```

Edit the scripts under `usr/local/{bin,sbin}/` and then run
`python3 scripts/sync-usrlocal-hook.py` -- the 0035 hook is generated from
them. Boot artwork is rendered by `node scripts/render-boot-art.mjs`.

## Checking changes without building an ISO

```bash
scripts/lint.sh          # shellcheck, YAML, Calamares invariants, desktop files, drift
tests/cli/run.sh         # cos-stacks / blackarch-shell / cos-help against a fake docker
```

CI (`.github/workflows/ci.yml`) runs both plus the website tests on every push.

## Getting a downloadable ISO

Three ways, easiest first:

**1. GitHub Actions (no local setup).** The `Build ISO` workflow
(`.github/workflows/iso.yml`) builds the ISO on a GitHub runner -- which,
unlike a locked-down sandbox, can reach the Kali/Parrot mirrors and has the
disk the build needs. Actions tab -> **Build ISO** -> **Run workflow** ->
pick a profile. When it finishes, download the ISO from the run's
**Artifacts** section and verify it with the `SHA256SUMS` next to it. (The
workflow must be on the repo's **default branch** for the Run button to
appear.) Push a `v*` tag and the ISO is also attached to a GitHub Release.

**2. Locally with Docker.** Needs Docker able to run privileged containers,
tens of GB of free disk and bandwidth, and over an hour:

```bash
cd build
./build.sh                       # full profile (default)
COS_PROFILE=slim ./build.sh      # smaller, CI-friendly
nohup ./build.sh > build.out 2>&1 &   # or in the background
tail -f output/build.log
```

The ISO lands in `build/output/*.iso`.

### Build profiles (`COS_PROFILE`)

How much of Kali's tool set goes in. Everything else (hardening, the
blue-team stack, `cos-*`, `cos-ai`, the installer, branding) is the same.

| profile | Kali packages | rough ISO | fits a free CI runner? |
|---------|---------------|-----------|------------------------|
| `full` (default) | `kali-linux-everything` | ~14.6 GiB | no -- large/self-hosted runner |
| `slim` | `kali-linux-default` | a few GB | yes |
| `min` | `kali-linux-headless` | smallest | yes |

git always ships `full`; `slim`/`min` only rewrite the Kali metapackage list
in the build volume (`build-inside.sh`), so the committed config is untouched.

Decide on the BlackArch baked-in-vs-first-boot tradeoff **before** a full
build -- read `docs/BLACKARCH-INTEGRATION.md`, it changes final ISO size a lot.

## Running and installing the ISO

**Live session login: `kali` / `kali`** (autologin is on by default, so
you shouldn't even see the prompt -- see it above if autologin is ever off).
The ISO is **amd64 (x86_64)** and a hybrid image (boots from USB or as a
DVD/optical image). Secure Boot must be **off** (no signed bootloader yet).

### VirtualBox (Windows, Linux, Intel Mac)

Works natively because the host is x86_64.

1. New -> Type **Linux**, Version **Debian (64-bit)**.
2. Memory 4096 MB+; CPUs 2+.
3. To test the installer, add a 60+ GB virtual disk (the live session alone
   needs none).
4. Settings -> System -> enable **EFI** (Calamares installs a GRUB EFI
   loader). Settings -> Storage -> attach the `.iso` to the optical drive.
5. Start. For the install path, double-click **Install Linux-C.O.S** on the
   desktop.

On an **Apple Silicon** Mac VirtualBox can't run an x86_64 guest (it lists
the type but `VBoxManage startvm` fails with
`VBOX_E_PLATFORM_ARCH_NOT_SUPPORTED`) -- use UTM instead.

### UTM (Apple Silicon Mac)

1. Create a New Virtual Machine -> **Emulate** (not "Virtualize", which on
   Apple Silicon only does ARM64 guests and silently creates an
   incompatible VM).
2. Linux; Architecture **x86_64**.
3. Boot ISO image: the `.iso`.
4. Memory 4096 MB+; add a 60+ GB disk to test the installer.
5. Leave "Use Virtualization" / "Hardware OpenGL Acceleration" unchecked --
   neither applies when emulating a different architecture than the host.

This is pure software emulation (QEMU TCG) -- boot is genuinely slow,
several minutes from GRUB to desktop, not a sign anything is hung.

### A real computer

Write the ISO to a 32 GB+ USB stick (balenaEtcher, Rufus in **DD mode**, or
`dd ... conv=fsync`), turn Secure Boot off in the firmware, pick the USB
from the boot menu, and run the desktop installer. "Erase disk" wipes the
whole disk (Windows included) -- choose "Install alongside" or manual
partitioning to dual-boot, and back up first. Full-disk encryption (LUKS2)
is offered on the partitioning page.

## TODO (known gaps, in rough priority order)

- [ ] run the `Build ISO` workflow on the default branch and confirm the
      slim profile finishes within the runner's disk/time budget (the config
      is in place; it has not been run end-to-end yet)
- [ ] boot-test in VirtualBox/UTM (see "Running and installing the ISO"
      above) -- not done yet
- [ ] boot-test the Calamares install path specifically once the live
      session boots -- `unpackfs.conf`'s squashfs path
      (`/run/live/medium/live/filesystem.squashfs`) was written from
      live-boot's documented default, not verified against this actual
      ISO's layout yet
- [ ] decide BlackArch baked-in vs. first-boot (docs/BLACKARCH-INTEGRATION.md)
      -- currently first-boot (nothing baked in), so first real boot needs
      network to get `blackarch-shell` working
- [ ] boot-test the new boot menus: the installed-system GRUB theme
      (`usr/share/grub/themes/linux-cos/`) and the live ISO splash images in
      `config/includes.binary/` -- the latter rely on live-build placing its
      own `boot/grub/splash.png` / `isolinux/splash.png` at those paths, which
      is live-build's documented layout but not yet confirmed on this ISO
- [ ] boot-test the XFCE "Linux-C.O.S" menu folder and the session-setup
      autostart (wallpaper on every monitor, trusted installer launcher)
- [ ] Secure Boot is explicitly disabled (`--uefi-secure-boot disable`) --
      fine for VM testing, but this ISO will not boot on real hardware with
      Secure Boot on until that's revisited (needs Kali's own shim/signed
      grub, which the build doesn't have a path to yet)
- [ ] this ISO was built with `--debian-installer none` -- Calamares (the
      live-desktop installer) is the only install path; nothing here uses
      classic Debian-Installer
