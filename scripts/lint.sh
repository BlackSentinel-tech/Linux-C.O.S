#!/bin/sh
# Linux-C.O.S -- static checks for everything that can be verified without
# building a 15 GB ISO. Run from anywhere: scripts/lint.sh
# Needs: shellcheck, yamllint, desktop-file-validate (desktop-file-utils),
# xmllint (libxml2-utils), python3. Missing tools are reported, not ignored.
set -u
cd "$(dirname "$0")/.." || exit 1

fail=0
ok()   { printf '  \033[32mok\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=1; }
need() { command -v "$1" >/dev/null 2>&1 || { bad "missing tool: $1"; return 1; }; }

INC=build/config/includes.chroot

echo "shell scripts"
# usr/local/bin/cos is Python (checked by py_compile below), everything else there is shell
shell_bins=""
for f in "$INC"/usr/local/bin/* "$INC"/usr/local/sbin/*; do
  case "$f" in */bin/cos) ;; *) shell_bins="$shell_bins $f" ;; esac
done
scripts="build/build.sh build/build-inside.sh build/auto/config scripts/lint.sh
  $(ls build/config/hooks/normal/00*.hook.chroot)
  $shell_bins"
if need shellcheck; then
  # shellcheck disable=SC2086
  if shellcheck -s sh $scripts; then ok "shellcheck ($(echo $scripts | wc -w) files)"; else bad "shellcheck"; fi
fi
for f in $scripts; do sh -n "$f" || bad "sh -n $f"; done
ok "sh -n syntax"
for f in "$INC"/usr/local/bin/* "$INC"/usr/local/sbin/* build/config/hooks/normal/00*.hook.chroot; do
  [ -x "$f" ] || bad "not executable: $f"
done
ok "scripts are executable"

echo "generated files are in sync with their sources"
gen_before=$fail
python3 scripts/sync-usrlocal-hook.py --check >/dev/null || bad "0035 hook is stale: python3 scripts/sync-usrlocal-hook.py"
python3 scripts/build-website-data.py --check >/dev/null || bad "tools.json is stale: python3 scripts/build-website-data.py"
python3 scripts/build-website.py --check >/dev/null || bad "website pages are stale: python3 scripts/build-website.py"
python3 scripts/build-cos-catalog.py --check >/dev/null || bad "tool catalog is stale: python3 scripts/build-cos-catalog.py"
[ "$fail" -eq "$gen_before" ] && ok "hook, tool data, website pages and the unified catalog"

echo "YAML (Calamares, compose)"
if need yamllint; then
  yaml="$(ls $INC/etc/calamares/settings.conf $INC/etc/calamares/modules/*.conf \
         $INC/etc/calamares/branding/linux-cos/branding.desc \
         $INC/opt/linux-cos/blueteam-stacks/*/docker-compose.yml .github/workflows/*.yml 2>/dev/null)"
  # shellcheck disable=SC2086
  if yamllint -d '{extends: relaxed, rules: {line-length: disable, colons: disable, indentation: disable}}' $yaml; then
    ok "yamllint"
  else
    bad "yamllint"
  fi
fi
cal_before=$fail
python3 - <<'EOF' || fail=1
import sys, yaml, pathlib
inc = pathlib.Path("build/config/includes.chroot/etc/calamares")
settings = yaml.safe_load((inc / "settings.conf").read_text())
exec_mods = [m for step in settings["sequence"] for k, v in step.items() if k == "exec" for m in v]
show_mods = [m for step in settings["sequence"] for k, v in step.items() if k == "show" for m in v]
errors = []
# regressions this project already hit once
if "users" not in exec_mods:
    errors.append("calamares: 'users' missing from the exec sequence (no account would be created)")
for need in ("mount", "unpackfs", "fstab", "bootloader", "umount", "initramfs", "displaymanager"):
    if need not in exec_mods:
        errors.append(f"calamares: '{need}' missing from the exec sequence")
if {"initramfs", "bootloader"} <= set(exec_mods) and exec_mods.index("initramfs") > exec_mods.index("bootloader"):
    errors.append("calamares: initramfs must run before bootloader")
pk = yaml.safe_load((inc / "modules/packages.conf").read_text())
for op in pk["operations"]:
    if "remove" in op:
        errors.append("calamares packages.conf: use try_remove -- a plain remove of an unknown package aborts the install")
if "welcome" not in show_mods or "finished" not in show_mods:
    errors.append("calamares: welcome/finished pages missing")
for e in errors:
    print("  FAIL " + e)
sys.exit(1 if errors else 0)
EOF
[ "$fail" -eq "$cal_before" ] && ok "Calamares sequence invariants"

echo "compose stacks"
stacks_before=$fail
for d in "$INC"/opt/linux-cos/blueteam-stacks/*/; do
  [ -f "${d}stack.meta" ] || bad "missing stack.meta in $d"
  if [ -f "${d}docker-compose.yml" ]; then
    # every published port must be bound to localhost (Docker bypasses ufw)
    if grep -E '^\s*ports:' "${d}docker-compose.yml" | grep -vE '"127\.0\.0\.1:' >/dev/null; then
      bad "$d: a port is published on all interfaces"
    fi
    if grep -nE '^\s*[A-Z_]*(PASSWORD|PASSPHRASE)[A-Z_]*: *[^$ ]' "${d}docker-compose.yml"; then
      bad "$d: hard-coded password in docker-compose.yml"
    fi
  fi
done
[ "$fail" -eq "$stacks_before" ] && ok "stacks: localhost-only ports, no hard-coded passwords"

echo "apt repositories reach the installed system"
# *.chroot archives only exist during the build; the final image needs the
# *.binary twin or the repo (and Parrot's priority-1 pin) silently vanish
for f in build/config/archives/*.chroot; do
  b="${f%.chroot}.binary"
  if [ ! -f "$b" ]; then bad "missing $b (copy of $f for the installed system)"
  elif ! cmp -s "$f" "$b"; then bad "$b differs from $f"; fi
done
ok "every archives/*.chroot has an identical *.binary"

echo "Wazuh override keeps UIs/APIs on localhost"
wo="$INC/opt/linux-cos/blueteam-stacks/wazuh/docker-compose.linux-cos.yml"
if grep -E '^\s*- "[0-9]+:' "$wo" | grep -vE '"(1514|1515):' >/dev/null; then
  bad "$wo publishes something other than the agent ports on all interfaces"
else
  ok "only 1514/1515 are network-facing"
fi

echo "desktop entries + XML"
if need desktop-file-validate; then
  for f in "$INC"/usr/share/applications/*.desktop "$INC"/etc/skel/Desktop/*.desktop \
           "$INC"/etc/xdg/autostart/*.desktop "$INC"/usr/share/desktop-directories/*.directory; do
    out=$(desktop-file-validate "$f" 2>&1 | grep -v ': hint: ') || true
    [ -z "$out" ] || bad "$out"
  done
  ok "desktop-file-validate"
fi
if need xmllint; then
  if xmllint --noout "$INC"/etc/xdg/menus/applications-merged/*.menu \
      "$INC"/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/*.xml build/branding/logo/*.svg; then
    ok "xmllint"
  else
    bad "xmllint"
  fi
fi

echo "systemd units"
for u in "$INC"/etc/systemd/system/*.service; do
  grep -q '^ExecStart=' "$u" || bad "$u: no ExecStart"
  exe=$(sed -n 's/^ExecStart=//p' "$u" | cut -d' ' -f1)
  [ -f "$INC$exe" ] || bad "$u: ExecStart target $exe is not shipped in includes.chroot"
done
ok "units point at shipped scripts"

echo "bootloader inputs (BIOS + UEFI hybrid)"
if grep -q 'grub-efi' build/auto/config; then
  grep -q '\bmtools\b' build/Dockerfile || bad "auto/config requests grub-efi but build/Dockerfile lacks mtools (the UEFI FAT image needs it)"
  grep -q 'grub-efi-amd64-bin' build/config/package-lists/bootloaders.list.chroot || bad "grub-efi requested but grub-efi-amd64-bin missing from bootloaders.list.chroot (Calamares UEFI install)"
  grep -q 'syslinux' build/auto/config || bad "grub-efi set without syslinux -- the ISO would lose legacy BIOS boot"
  [ "$fail" -eq 0 ] && ok "grub-efi hybrid inputs present (syslinux + mtools + grub-efi-amd64-bin)"
fi

echo "python"
if python3 -m py_compile scripts/*.py "$INC"/usr/lib/linux-cos/*.py "$INC"/usr/local/bin/cos; then ok "py_compile"; else bad "py_compile"; fi
find "$INC/usr/lib/linux-cos" "$INC/usr/local/bin" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null

echo "desktop consistency"
desk_before=$fail
python3 - <<'PY' || fail=1
import json, pathlib, re, sys
inc = pathlib.Path("build/config/includes.chroot")
errors = []
pal = json.loads((inc / "usr/share/linux-cos/palettes.json").read_text())
need = {"bg", "surface", "surface2", "border", "fg", "dim", "accent", "accent2", "ok", "warn", "bad"}
for mode, p in pal.items():
    miss = need - set(p)
    if miss:
        errors.append(f"palettes.json: {mode} lacks {sorted(miss)}")
    for k, v in p.items():
        if k != "name" and not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            errors.append(f"palettes.json: {mode}.{k} is not #rrggbb")
bg = inc / "usr/share/backgrounds/linux-cos"
for mode in pal:
    for suffix in (".jpg", "-base.jpg"):
        if not (bg / f"{mode}{suffix}").exists():
            errors.append(f"missing wallpaper {mode}{suffix} (python3 scripts/render-cos-assets.py)")
ply = inc / "usr/share/linux-cos/plymouth"
if not (ply / "watermark.png").exists() or len(list(ply.glob("throbber-*.png"))) < 24:
    errors.append("plymouth artwork missing (python3 scripts/render-cos-assets.py --only plymouth)")
# every wallpaper / icon / theme named in a config must exist or be generated
greeter = (inc / "etc/lightdm/lightdm-gtk-greeter.conf").read_text()
m = re.search(r"^background\s*=\s*(\S+)", greeter, re.M)
if m and not (inc / m.group(1).lstrip("/")).exists():
    errors.append(f"greeter background {m.group(1)} is not shipped")
for xml in (inc / "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml").glob("*.xml"):
    for path in re.findall(r'value="(/usr/share/[^"]+\.(?:jpg|png))"', xml.read_text()):
        if not (inc / path.lstrip("/")).exists():
            errors.append(f"{xml.name}: {path} is not shipped")
for theme in ("COS-Dual", "COS-Red", "COS-Blue"):
    if theme.split("-")[1].lower() not in pal:
        errors.append(f"theme {theme} has no palette")
# the hooks that generate the themes and the menu must exist and be ordered after packages/includes
hooks = sorted(p.name for p in pathlib.Path("build/config/hooks/normal").glob("00*.hook.chroot"))
for h in ("0035-usrlocal-scripts", "0040-branding", "0045-plymouth-theme", "0055-performance", "0065-theme", "0070-menu"):
    if h + ".hook.chroot" not in hooks:
        errors.append(f"hook {h} missing")
for pk in ("picom", "rofi", "conky-all", "python3-pil", "python3-gi", "arc-theme", "papirus-icon-theme", "fonts-oxanium", "starship"):
    found = any(pk in f.read_text().split() for f in pathlib.Path("build/config/package-lists").glob("*.list.chroot"))
    if not found:
        errors.append(f"package {pk} is not in any package list (the COS desktop needs it)")
for e in errors:
    print("  FAIL " + e)
sys.exit(1 if errors else 0)
PY
[ "$fail" -eq "$desk_before" ] && ok "palettes, wallpapers, boot art, hooks and desktop packages line up"

echo
if [ "$fail" -ne 0 ]; then echo "lint: FAILED"; exit 1; fi
echo "lint: all checks passed"
