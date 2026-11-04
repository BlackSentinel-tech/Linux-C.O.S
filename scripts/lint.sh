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
scripts="build/build.sh build/build-inside.sh build/auto/config scripts/lint.sh
  $(ls build/config/hooks/normal/00*.hook.chroot)
  $(ls $INC/usr/local/bin/* $INC/usr/local/sbin/*)"
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
[ "$fail" -eq "$gen_before" ] && ok "hook, tool data and website pages"

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

echo "python"
if python3 -m py_compile scripts/*.py; then ok "py_compile"; else bad "py_compile"; fi

echo
if [ "$fail" -ne 0 ]; then echo "lint: FAILED"; exit 1; fi
echo "lint: all checks passed"
