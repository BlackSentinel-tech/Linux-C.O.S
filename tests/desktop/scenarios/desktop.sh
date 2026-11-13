# the full COS desktop: xfwm4 + panels + picom + HUD + wallpaper, then screenshots
set -u
export GTK_THEME=
xfsettingsd &
sleep 1
xfwm4 --compositor=off --replace >/tmp/xfwm4.log 2>&1 &
sleep 1
xfce4-panel >/tmp/panel.log 2>&1 &
sleep 2
COS_MODE_ARG=${COS_MODE:-dual}
cos mode "$COS_MODE_ARG" >/tmp/cos-mode.log 2>&1
cos fx "${COS_FX:-high}" >/tmp/cos-fx.log 2>&1
sleep 5
xfce4-terminal --geometry=100x28+120+160 -e "zsh -ic 'cos tools cats | head -8; echo; cos; exec zsh'" >/tmp/term.log 2>&1 &
sleep 4
xwd -root -silent | convert xwd:- png:/out/${COS_SHOT:-desktop}.png 2>/dev/null || import -window root /out/${COS_SHOT:-desktop}.png
ps aux | grep -E 'picom|conky|wallpaperd|xfce4-panel|xfwm4' | grep -v grep | awk '{print $11,$12,$13}' > /out/${COS_SHOT:-desktop}.ps
cp /tmp/*.log /out/ 2>/dev/null || true
cp ~/.cache/linux-cos/*.log /out/ 2>/dev/null || true
cp ~/.config/xfce4/panel/docklike.rc /out/docklike.rc 2>/dev/null || true
