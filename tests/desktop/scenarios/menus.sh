# application menu (unified categories), rofi launcher, red mode + low effects
set -u
xfsettingsd & sleep 1
xfwm4 --compositor=off --replace >/dev/null 2>&1 & sleep 1
xfce4-panel >/tmp/panel.log 2>&1 & sleep 3
cos mode red >/dev/null 2>&1
cos fx low >/dev/null 2>&1
sleep 6
xdotool mousemove 17 17 click 1; sleep 2
import -window root /out/menu-whisker.png
xdotool key Escape; sleep 1
rofi -show drun >/tmp/rofi.log 2>&1 &
sleep 2; xdotool type --delay 60 "nmap"; sleep 1.5
import -window root /out/menu-rofi.png
xdotool key Escape; sleep 1
xfce4-terminal --geometry=110x30+160+120 -e "zsh -ic 'fastfetch; cos tools -s blackarch -c web | head -6; exec zsh'" >/dev/null 2>&1 &
sleep 5
import -window root /out/red-low.png
cp ~/.cache/linux-cos/*.log /out/ 2>/dev/null || true; cp /tmp/rofi.log /tmp/panel.log /out/ 2>/dev/null || true
