# picom fallback: a broken GLX profile must still leave a compositor running
set -u
xfsettingsd & sleep 1
python3 - <<'PY'
import sys
sys.path.insert(0, "/usr/lib/linux-cos")
import cos_session
cos_session.PICOM_HIGH = 'this is not valid libconfig;\n'   # makes the "high" config unparsable
import cos_core
cos_core.set_fx("high")
cos_session.apply()
PY
sleep 3
{ echo "picom running: $(pgrep -x picom | wc -l)"; echo "config now:"; head -3 ~/.config/linux-cos/picom.conf; } > /out/fallback.txt
