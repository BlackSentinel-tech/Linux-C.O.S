# Linux-C.O.S -- how the system is put together

One operating system, not three toolkits in a trench coat.

```
            Kali (kali-rolling)  ── the base: kernel, apt, desktop
              ├─ Kali tools ......... native apt packages
              ├─ Parrot tools ....... native apt packages (Parrot repo, pinned low)
              └─ BlackArch tools .... Arch container, behind the SAME commands
                       │
              cos_core (catalog + resolver)  <- usr/share/linux-cos/{tools,categories}.tsv
       ┌───────┬───────┴────────┬─────────────┬───────────────┐
      cos    COS Hub     unified menu    shell hook     rofi launcher
   (CLI)  (GTK dashboard) (20 categories) (command-not-found)
```

## The unified layer (`usr/lib/linux-cos/`)

| File | Role |
|---|---|
| `cos_core.py` | Loads the catalog; `resolve(tool)` says native / container / installable; mode + fx state; palette. Standard library only. |
| `cos_cli.py` | The `cos` command (launcher: `usr/local/bin/cos`). |
| `cos_menu.py` | Regroups every tool under the 20 categories and creates launchers for tools that have none (hook 0070). |
| `cos_theme.py` | Derives the COS-Dual / COS-Red / COS-Blue GTK + xfwm4 themes from Arc-Dark (hook 0065). |
| `cos_session.py` | `cos session start|apply`: picom, conky HUD, wallpaper, rofi/terminal/prompt palette for the chosen mode + fx level. |
| `cos_wallpaperd.py` | Animated wallpaper (GTK + Cairo): rings, grid pulse, particles. |
| `cos_hub.py` | COS Hub. |
| `conky/hud.lua` | The desktop HUD. |

**One source of truth per concern.** Colours: `usr/share/linux-cos/palettes.json`
feeds the themes, HUD, wallpapers, boot art, prompt, terminal and Hub. Tools:
`scripts/build-cos-catalog.py` maps Kali's and Parrot's metapackages and
BlackArch's groups onto one taxonomy (`tools.tsv`, CI-checked for drift).

## Modes and effects

* `cos mode dual|red|blue` -- accent colours everywhere, instantly.
* `cos fx auto|high|low|off` -- `auto` = `low` in a VM (no GPU), `high` on bare
  metal. `high`: picom GLX (blur, rounded corners, shadows, animations) + animated
  wallpaper. `low`: picom xrender (shadows, fade, rounded corners) + static wallpaper.

## Boot chain

GRUB (BIOS isolinux / UEFI grub-efi) → Plymouth (animated ring, 72 frames) →
LightDM (COS theme) → XFCE session → `cos session start` (autostart).

## Performance choices

zstd squashfs + zstd initramfs (faster boot), zram swap, earlyoom, sysctl for
many sockets/watchers, per-device I/O scheduler, journald caps, short systemd
timeouts, guest tools for VirtualBox / VMware / QEMU-UTM / Hyper-V.

## Regenerating artwork

```
python3 scripts/render-cos-assets.py --fonts <dir>   # wallpapers, Plymouth frames, boot menus, fastfetch logo
python3 scripts/build-cos-catalog.py                 # tool catalog after changing data/*.json
```
Fonts: Oxanium + JetBrains Mono (both OFL; `apt install fonts-oxanium fonts-jetbrains-mono`).

## Testing the desktop without booting the ISO

```
docker build --platform linux/amd64 -t cos-desktop-test tests/desktop
tests/desktop/run.sh desktop /tmp/shots     # also: widgets, hub, menus
```
Renders the real desktop (panel, dock, picom, HUD, wallpaper, Hub, menus) on a
virtual X server in a Kali container and saves screenshots.
