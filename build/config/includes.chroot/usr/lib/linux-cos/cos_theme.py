"""Build the Linux-C.O.S GTK + window-manager themes (COS-Dual, COS-Red, COS-Blue).

Run at image build time by the 0065 hook (needs arc-theme and python3-pil,
both in the package lists).  The themes are derived from Arc-Dark -- a complete,
well-tested widget set -- by remapping its palette onto the COS palette
(palettes.json), then appending the COS layer: neon focus glow, transitions,
animated progress bars, rounded translucent panels and menus.

    python3 cos_theme.py [--themes-dir /usr/share/themes] [--arc /usr/share/themes/Arc-Dark]
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys

SHARE = os.environ.get("COS_SHARE", "/usr/share/linux-cos")


def h2r(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def r2h(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in c)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


class Remap:
    """Arc-Dark palette -> COS palette, by role then by lightness."""

    def __init__(self, p: dict):
        self.p = {k: h2r(v) for k, v in p.items() if isinstance(v, str) and v.startswith("#")}
        bg, s1, s2, bd = self.p["bg"], self.p["surface"], self.p["surface2"], self.p["border"]
        fg, dim = self.p["fg"], self.p["dim"]
        # lightness ramp for neutral colours: dark -> light
        self.ramp = [(0.10, mix(bg, (0, 0, 0), 0.25)), (0.17, bg), (0.22, s1), (0.27, s2),
                     (0.33, mix(s2, bd, 0.55)), (0.42, bd), (0.62, dim), (0.80, mix(dim, fg, 0.6)), (0.88, fg), (1.01, (255, 255, 255))]
        self.fixed = {
            "#5294e2": self.p["accent"], "#2b2e39": bg, "#383c4a": s1, "#404552": s2,
            "#2f343f": mix(bg, s1, 0.5), "#d3dae3": fg, "#bac3cf": mix(fg, dim, 0.35),
            "#f08437": self.p["warn"], "#f27835": self.p["warn"], "#fc4138": self.p["bad"],
            "#f04a50": self.p["bad"], "#ec1b22": self.p["bad"], "#f4797e": mix(self.p["bad"], fg, 0.3),
            "#4dadd4": self.p["accent2"], "#76c0de": mix(self.p["accent2"], fg, 0.3), "#2e96c0": self.p["accent2"],
            "#a9caf1": mix(self.p["accent"], fg, 0.5),
        }

    def color(self, rgb) -> tuple[float, float, float]:
        r, g, b = rgb
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s > 0.38 and 0.5 < h < 0.72:        # the Arc blue family -> accent
            return mix(self.p["bg"], self.p["accent"], min(1.0, 0.25 + v))
        if s > 0.45 and (h < 0.07 or h > 0.93):  # reds
            return mix(self.p["bg"], self.p["bad"], v)
        if s > 0.45 and 0.07 <= h < 0.2:        # oranges / yellows
            return mix(self.p["bg"], self.p["warn"], v)
        L = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        prev = self.ramp[0]
        for stop in self.ramp:
            if L <= stop[0]:
                span = max(1e-6, stop[0] - prev[0])
                return mix(prev[1], stop[1], max(0.0, min(1.0, (L - prev[0]) / span)))
            prev = stop
        return self.ramp[-1][1]

    def hexs(self, h: str) -> str:
        k = h.lower()
        if k in self.fixed:
            return r2h(self.fixed[k])
        return r2h(self.color(h2r(h)))

    def css(self, text: str) -> str:
        text = re.sub(r"#[0-9a-fA-F]{6}\b", lambda m: self.hexs(m.group(0)), text)
        text = re.sub(r"#[0-9a-fA-F]{3}\b", lambda m: self.hexs(m.group(0)) if len(m.group(0)) == 4 else m.group(0), text)

        def rgba(m):
            r, g, b = (int(float(x)) for x in m.group(1).split(",")[:3])
            nr, ng, nb = self.color((r, g, b))
            rest = m.group(1).split(",")[3:]
            fn = "rgba" if rest else "rgb"
            return f"{fn}({int(nr)}, {int(ng)}, {int(nb)}" + ("," + ",".join(rest) if rest else "") + ")"

        return re.sub(r"rgba?\(\s*([0-9.]+\s*,\s*[0-9.]+\s*,\s*[0-9.]+(?:\s*,\s*[0-9.]+)?)\s*\)", rgba, text)


def cos_layer(p: dict) -> str:
    """The Linux-C.O.S look on top of the remapped widget set."""
    a, a2, bg, s1, s2, bd = p["accent"], p["accent2"], p["bg"], p["surface"], p["surface2"], p["border"]
    return f"""
/* ====================== Linux-C.O.S layer ====================== */
@define-color cos_accent {a};
@define-color cos_accent2 {a2};
@define-color cos_bg {bg};
@define-color cos_surface {s1};
@define-color cos_border {bd};

* {{ -gtk-icon-style: symbolic; }}

button, entry, spinbutton, combobox, switch, scale trough, tab, headerbar, .titlebar {{
  transition: 140ms ease-out;
}}
button {{ border-radius: 7px; }}
button:hover {{ border-color: {a}; box-shadow: 0 0 10px alpha({a}, 0.45); }}
button:active, button:checked {{ box-shadow: inset 0 0 10px alpha({a}, 0.35), 0 0 12px alpha({a}, 0.5); }}
button.suggested-action {{ background-image: linear-gradient(to bottom, {a}, shade({a}, 0.72)); color: {bg}; border-color: {a}; }}
button.suggested-action:hover {{ box-shadow: 0 0 16px alpha({a}, 0.8); }}
button.destructive-action {{ background-image: linear-gradient(to bottom, {p["bad"]}, shade({p["bad"]}, 0.7)); border-color: {p["bad"]}; }}

entry, spinbutton, textview text {{ border-radius: 7px; }}
entry:focus, spinbutton:focus {{ border-color: {a}; box-shadow: 0 0 0 1px {a}, 0 0 14px alpha({a}, 0.35); }}

selection, *:selected, row:selected, .view:selected, menuitem:hover, treeview.view:selected {{
  background-color: alpha({a}, 0.28); color: {p["fg"]};
}}
row:selected, treeview.view:selected {{ box-shadow: inset 3px 0 0 {a}; }}

headerbar, .titlebar {{ background-image: linear-gradient(to bottom, {s2}, {s1}); border-bottom: 1px solid {bd}; box-shadow: inset 0 -1px 0 alpha({a}, 0.35); }}
notebook > header > tabs > tab:checked {{ box-shadow: inset 0 -2px 0 {a}; }}

scale trough {{ border-radius: 4px; }}
scale highlight, progressbar progress {{ background-image: linear-gradient(to right, {a2}, {a}); border-radius: 4px; box-shadow: 0 0 10px alpha({a}, 0.7); }}
progressbar trough {{ border-radius: 4px; background-color: {bg}; border: 1px solid {bd}; }}
levelbar block.filled {{ background-color: {a}; box-shadow: 0 0 6px alpha({a}, 0.6); }}
switch {{ border-radius: 14px; background-image: none; background-color: {bg}; border: 1px solid {bd}; }}
switch slider {{ border-radius: 14px; background-image: linear-gradient(to bottom, {p["dim"]}, shade({p["dim"]}, 0.7)); border: none; }}
switch:checked {{ background-color: alpha({a}, 0.32); border-color: {a}; box-shadow: 0 0 10px alpha({a}, 0.55); }}
switch:checked slider {{ background-image: linear-gradient(to bottom, {a}, shade({a}, 0.75)); box-shadow: 0 0 8px alpha({a}, 0.8); }}
checkbutton check:checked, radiobutton radio:checked {{ background-image: linear-gradient(to bottom, {a}, shade({a}, 0.75)); box-shadow: 0 0 8px alpha({a}, 0.55); }}

scrollbar slider {{ min-width: 6px; min-height: 6px; border-radius: 4px; background-color: alpha({a}, 0.45); }}
scrollbar slider:hover {{ background-color: {a}; box-shadow: 0 0 8px alpha({a}, 0.6); }}
scrollbar trough {{ background-color: transparent; }}

menu, .menu, .popup, popover.background, popover {{ background-color: alpha({s1}, 0.94); border: 1px solid {bd}; border-radius: 10px; box-shadow: 0 8px 28px rgba(0,0,0,0.6), 0 0 0 1px alpha({a}, 0.18); }}
menuitem {{ border-radius: 6px; margin: 1px 4px; }}
tooltip, tooltip.background {{ background-color: alpha({bg}, 0.96); border: 1px solid {a}; border-radius: 8px; box-shadow: 0 0 14px alpha({a}, 0.4); color: {p["fg"]}; }}

@keyframes cos-pulse {{ from {{ box-shadow: 0 0 4px alpha({a}, 0.2); }} to {{ box-shadow: 0 0 16px alpha({a}, 0.85); }} }}
spinner:checked {{ color: {a}; }}
.cos-pulse {{ animation: cos-pulse 1.6s ease-in-out infinite alternate; }}

/* ---------- XFCE panels, whisker menu, docklike ---------- */
.xfce4-panel.panel, #XfcePanelWindow, .xfce4-panel {{ background-color: alpha({bg}, 0.62); color: {p["fg"]}; }}
.xfce4-panel button {{ border-radius: 9px; border: 1px solid transparent; background: transparent; box-shadow: none; padding: 2px 6px; }}
.xfce4-panel button:hover {{ background-color: alpha({a}, 0.14); border-color: alpha({a}, 0.5); box-shadow: 0 0 10px alpha({a}, 0.35); }}
.xfce4-panel button:checked {{ background-color: alpha({a}, 0.22); border-color: {a}; box-shadow: inset 0 -2px 0 {a}, 0 0 10px alpha({a}, 0.4); }}
#XfcePanelWindow.dock-panel, .cos-dock {{ border-radius: 18px; border: 1px solid alpha({a}, 0.4); box-shadow: 0 0 22px alpha({a}, 0.25); }}
.xfce4-panel label {{ font-weight: 500; }}

/* ---------- login greeter ---------- */
#login_window, #panel_window {{ background-color: alpha({bg}, 0.72); border: 1px solid alpha({a}, 0.5); border-radius: 14px; box-shadow: 0 0 40px alpha({a}, 0.25); }}
#login_window entry {{ background-color: alpha({bg}, 0.9); }}
#login_window button {{ border-radius: 10px; }}
"""


def build_gtk(arc: str, out: str, p: dict, name: str) -> None:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio

    rm = Remap(p)
    for ver in ("gtk-3.0", "gtk-4.0"):
        src = os.path.join(arc, ver)
        res_path = os.path.join(src, "gtk.gresource")
        if not os.path.exists(res_path):
            continue
        dst = os.path.join(out, ver)
        os.makedirs(dst, exist_ok=True)
        res = Gio.Resource.load(res_path)
        prefix = "/org/gnome/arc-theme"
        names = [n for n in res.enumerate_children(prefix, 0) if n.endswith(".css") and "dark" in n]
        if not names:
            continue
        css = res.lookup_data(f"{prefix}/{names[0]}", 0).get_data().decode()
        # the dark main sheet pulls extra sheets/assets from the resource: inline what it imports
        for imp in re.findall(r'@import url\("resource://([^"]+)"\);', css):
            try:
                inner = res.lookup_data(imp, 0).get_data().decode()
            except Exception:
                inner = ""
            css = css.replace(f'@import url("resource://{imp}");', inner)
        css = re.sub(r'url\("resource://[^"]+/assets/([^"]+)"\)', r'url("assets/\1")', css)
        # assets (check/radio/switch artwork) are separate files in the resource
        adir = os.path.join(dst, "assets")
        try:
            os.makedirs(adir, exist_ok=True)
            for n in res.enumerate_children(prefix + "/assets", 0):
                data = res.lookup_data(f"{prefix}/assets/{n}", 0).get_data()
                with open(os.path.join(adir, n), "wb") as f:
                    f.write(data)
        except Exception:
            pass
        with open(os.path.join(dst, "gtk.css"), "w", encoding="utf-8") as f:
            f.write(rm.css(css) + cos_layer(p))
        with open(os.path.join(dst, "gtk-dark.css"), "w", encoding="utf-8") as f:
            f.write('@import url("gtk.css");\n')


def build_xfwm(arc: str, out: str, p: dict) -> None:
    from PIL import Image

    src = os.path.join(arc, "xfwm4")
    if not os.path.isdir(src):
        return
    dst = os.path.join(out, "xfwm4")
    os.makedirs(dst, exist_ok=True)
    rm = Remap(p)
    cache: dict[tuple, tuple] = {}
    for fn in os.listdir(src):
        path = os.path.join(src, fn)
        if fn.endswith(".png"):
            im = Image.open(path).convert("RGBA")
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a == 0:
                        continue
                    k = (r, g, b)
                    if k not in cache:
                        cache[k] = tuple(int(round(v)) for v in rm.color(k))
                    px[x, y] = (*cache[k], a)
            im.save(os.path.join(dst, fn))
        elif fn == "themerc":
            t = open(path, encoding="utf-8").read()
            t = rm.css(t)
            t = re.sub(r"^active_text_color=.*$", f"active_text_color={p['fg']}", t, flags=re.M)
            t = re.sub(r"^inactive_text_color=.*$", f"inactive_text_color={p['dim']}", t, flags=re.M)
            with open(os.path.join(dst, fn), "w", encoding="utf-8") as f:
                f.write(t)
        else:
            with open(path, "rb") as fi, open(os.path.join(dst, fn), "wb") as fo:
                fo.write(fi.read())


def build(themes_dir: str, arc: str) -> list[str]:
    with open(os.path.join(SHARE, "palettes.json"), encoding="utf-8") as f:
        pals = json.load(f)
    made = []
    for mode, p in pals.items():
        name = "COS-" + mode.capitalize()
        out = os.path.join(themes_dir, name)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "index.theme"), "w", encoding="utf-8") as f:
            f.write(f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={name}\nComment=Linux-C.O.S {p['name']} theme\n"
                    "Encoding=UTF-8\n\n[X-GNOME-Metatheme]\nGtkTheme=" + name + "\nMetacityTheme=" + name + "\nIconTheme=Papirus-Dark\n")
        build_gtk(arc, out, p, name)
        build_xfwm(arc, out, p)
        made.append(name)
    return made


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--themes-dir", default="/usr/share/themes")
    ap.add_argument("--arc", default="/usr/share/themes/Arc-Dark")
    a = ap.parse_args()
    if not os.path.isdir(a.arc):
        print(f"cos_theme: {a.arc} not found (install arc-theme)", file=sys.stderr)
        return 1
    print("themes:", ", ".join(build(a.themes_dir, a.arc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
