#!/bin/bash
# runs inside cos-desktop-test: overlay the ISO files, run the build-time
# generators, start a virtual X desktop as an unprivileged user, run a scenario.
set -eu
scenario=$1
cp -a /inc/. /
mkdir -p /usr/local/bin
for hook in 0065-theme 0070-menu; do
  [ -f /hooks/$hook.hook.chroot ] && sh /hooks/$hook.hook.chroot
done
id tester >/dev/null 2>&1 || useradd -m -s /bin/zsh tester
cp -a /etc/skel/. /home/tester/ 2>/dev/null || true
chown -R tester:tester /home/tester
export DISPLAY=:99
Xvfb :99 -screen 0 ${COS_RES:-1920x1080x24} +extension GLX +extension RANDR +render -noreset >/tmp/xvfb.log 2>&1 &
for i in $(seq 1 50); do xdpyinfo -display :99 >/dev/null 2>&1 && break; sleep 0.2; done
exec su tester -c "export DISPLAY=:99 HOME=/home/tester XDG_RUNTIME_DIR=/tmp/xdg-tester COS_SHARE=/usr/share/linux-cos; mkdir -p -m700 \$XDG_RUNTIME_DIR; exec dbus-run-session -- bash /t/scenarios/$scenario.sh"
