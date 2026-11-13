# the COS Hub on the COS theme (dashboard, tools, appearance pages)
set -u
xfsettingsd & sleep 1
xfwm4 --compositor=off --replace >/dev/null 2>&1 & sleep 1
xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s "COS-Dual"
cos session prompt
python3 /usr/lib/linux-cos/cos_hub.py >/tmp/hub.log 2>&1 &
sleep 4
xdotool search --name "COS Hub" windowmove 150 60 2>/dev/null
sleep 1
import -window root /out/hub-dash.png
xdotool mousemove 240 281 click 1; sleep 1
xdotool mousemove 700 200 click 1; xdotool type --delay 40 "sql"; sleep 1.5
import -window root /out/hub-tools.png
xdotool mousemove 240 331 click 1; sleep 1
import -window root /out/hub-look.png
cp /tmp/hub.log /out/hub.log
