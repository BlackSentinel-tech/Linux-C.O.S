#!/usr/bin/env python3
"""Animated Linux-C.O.S wallpaper (GTK3 + Cairo, no extra packages).

Paints the HUD-less base wallpaper for the active mode and animates the
emblem rings, a pulse travelling over the grid floor, drifting particles and
the emblem glow.  One desktop-type window per monitor, ~24 fps; `cos fx low`
replaces it with the static image.  Layout matches scripts/render-cos-assets.py
(2560x1440 design units).
"""
import math
import os
import random
import signal
import sys
import time

sys.path.insert(0, os.environ.get("COS_LIB", "/usr/lib/linux-cos"))
import cos_core as core  # noqa: E402

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
import cairo  # noqa: E402
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402

BG = os.environ.get("COS_BG", "/usr/share/backgrounds/linux-cos")
LOGO = os.environ.get("COS_LOGO", BG + "/logo.png")
FPS = int(os.environ.get("COS_WALLPAPER_FPS", "24"))
DESIGN_W, DESIGN_H = 2560.0, 1440.0
CX, CY = 1280.0, 0.37 * 1440.0
HORIZON = 0.60 * 1440.0


def rgb(hex_, a=1.0):
    h = hex_.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.k = h / DESIGN_H
        self.t0 = time.time()
        self.mode = None
        self.rnd = random.Random(11)
        self.motes = [[self.rnd.random(), self.rnd.random() * 0.58, self.rnd.uniform(0.6, 2.2),
                       self.rnd.uniform(0.02, 0.08), self.rnd.uniform(0, 6.28), self.rnd.choice((0, 0, 1))]
                      for _ in range(90)]
        self.base = None
        self.logo = None
        self.load("dual")

    def load(self, mode):
        self.mode = mode
        self.pal = core.palette(mode) or {}
        path = f"{BG}/{mode}-base.jpg"
        if not os.path.exists(path):
            path = f"{BG}/{mode}.jpg"
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file(path)
            # cover-fit
            s = max(self.w / pb.get_width(), self.h / pb.get_height())
            nw, nh = int(pb.get_width() * s) + 1, int(pb.get_height() * s) + 1
            pb = pb.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, self.w, self.h)
            c = cairo.Context(surf)
            Gdk.cairo_set_source_pixbuf(c, pb, (self.w - nw) / 2, (self.h - nh) / 2)
            c.paint()
            self.base = surf
        except Exception:
            self.base = None
        if self.logo is None:
            try:
                size = int(270 * self.k)
                self.logo = GdkPixbuf.Pixbuf.new_from_file_at_size(LOGO, size, size)
            except Exception:
                self.logo = None

    # --- drawing -----------------------------------------------------------------
    def draw(self, cr):
        t = time.time() - self.t0
        k = self.k
        p = self.pal
        a1, a2 = p.get("accent", "#00e5ff"), p.get("accent2", "#ff2e63")
        if self.base:
            cr.set_source_surface(self.base, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(*rgb(p.get("bg", "#060914"))[:3])
            cr.paint()

        self.grid_pulse(cr, t, a1)
        self.motes_draw(cr, t, a1, a2)
        self.rings(cr, t, a1, a2, p.get("dim", "#7f8db8"))
        self.emblem(cr, t, a1, p)

    def grid_pulse(self, cr, t, col):
        k = self.k
        period = 5.5
        ph = (t % period) / period
        if ph > 0.8:
            return
        f = ph / 0.8
        y = (HORIZON + (DESIGN_H - HORIZON) * (f ** 1.7)) * k
        band = (14 + 120 * f) * k
        g = cairo.LinearGradient(0, y - band, 0, y + band)
        a = 0.30 * math.sin(math.pi * min(1, f * 1.1))
        g.add_color_stop_rgba(0, *rgb(col, 0))
        g.add_color_stop_rgba(0.5, *rgb(col, max(0, a)))
        g.add_color_stop_rgba(1, *rgb(col, 0))
        cr.set_source(g)
        cr.rectangle(0, y - band, self.w, band * 2)
        cr.fill()

    def motes_draw(self, cr, t, a1, a2):
        for m in self.motes:
            x0, y0, r, sp, ph, which = m
            y = (y0 - (t * sp) * 0.15) % 0.6
            x = (x0 + math.sin(t * 0.2 + ph) * 0.01) % 1.0
            tw = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.7 + ph * 3))
            cr.set_source_rgba(*rgb(a2 if which else a1, 0.55 * tw))
            cr.arc(x * self.w, y * self.h, r * self.k * 1.4, 0, 6.2832)
            cr.fill()

    def rings(self, cr, t, a1, a2, dim):
        k = self.k
        cx, cy = self.w / 2, CY * k
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        # static thin circles
        for r, al in ((330, 0.28), (410, 0.20), (520, 0.11)):
            cr.set_line_width(2 * k)
            cr.set_source_rgba(*rgb(a1, al))
            cr.arc(cx, cy, r * k, 0, 6.2832)
            cr.stroke()

        def arc(r, start, sweep, width, col, al):
            for gw, ga in ((width * 3.2, al * 0.12), (width * 2.0, al * 0.22), (width, al)):
                cr.set_line_width(gw * k)
                cr.set_source_rgba(*rgb(col, ga))
                cr.arc(cx, cy, r * k, math.radians(start), math.radians(start + sweep))
                cr.stroke()

        arc(380, 200 + t * 12, 70, 5, a1, 0.95)
        arc(380, 20 + t * 12, 70, 5, a2, 0.95)
        arc(380, 110 + t * 12, 34, 3, a1, 0.5)
        # dashed counter-rotating ring
        cr.set_dash([14 * k, 11 * k])
        for start, col in ((300, a1), (100, a2)):
            cr.set_line_width(3 * k)
            cr.set_source_rgba(*rgb(col, 0.7))
            cr.arc(cx, cy, 460 * k, math.radians(start - t * 9), math.radians(start - t * 9 + 90))
            cr.stroke()
        cr.set_dash([])
        # tick ring with a sweeping highlight
        sweep = (t * 40) % 360
        cr.set_line_width(2 * k)
        for i in range(120):
            ang = i * 3.0
            d = min((ang - sweep) % 360, (sweep - ang) % 360)
            lit = max(0.0, 1 - d / 40.0)
            r0, r1 = 548 * k, (566 if i % 5 == 0 else 556) * k
            col = a2 if i % 10 == 0 else a1
            cr.set_source_rgba(*rgb(col, 0.22 + 0.7 * lit + (0.25 if i % 5 == 0 else 0)))
            ar = math.radians(ang)
            cr.move_to(cx + r0 * math.cos(ar), cy + r0 * math.sin(ar))
            cr.line_to(cx + r1 * math.cos(ar), cy + r1 * math.sin(ar))
            cr.stroke()

    def emblem(self, cr, t, a1, p):
        k = self.k
        cx, ey = self.w / 2, (CY - 90) * k
        breathe = 0.5 + 0.5 * math.sin(t * 1.4)
        g = cairo.RadialGradient(cx, ey, 10 * k, cx, ey, 200 * k)
        g.add_color_stop_rgba(0, *rgb(a1, 0.26 + 0.16 * breathe))
        g.add_color_stop_rgba(1, *rgb(a1, 0))
        cr.set_source(g)
        cr.arc(cx, ey, 200 * k, 0, 6.2832)
        cr.fill()
        if self.logo:
            Gdk.cairo_set_source_pixbuf(cr, self.logo, cx - self.logo.get_width() / 2, ey - self.logo.get_height() / 2)
            cr.paint()
        # title
        cr.select_font_face("Oxanium", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(66 * k)
        title, sp = "LINUX-C.O.S", 12 * k
        widths = [cr.text_extents(c).x_advance for c in title]
        total = sum(widths) + sp * (len(title) - 1)
        x, y = cx - total / 2, (CY + 90 + 52) * k
        for layer in (0, 1):
            xx = x
            for c, wd in zip(title, widths):
                cr.move_to(xx, y)
                cr.set_source_rgba(*(rgb(a1, 0.35) if layer == 0 else rgb(p.get("fg", "#e8eeff"))))
                if layer == 0:
                    cr.set_line_width(5 * k)
                    cr.text_path(c)
                    cr.stroke()
                else:
                    cr.show_text(c)
                xx += wd + sp
        cr.select_font_face("JetBrains Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(17 * k)
        sub = "CYBER OFFENSIVE & DEFENSIVE SECURITY"
        sw = [cr.text_extents(c).x_advance for c in sub]
        total = sum(sw) + 5 * k * (len(sub) - 1)
        xx, y = cx - total / 2, (CY + 90 + 100 + 14) * k
        cr.set_source_rgba(*rgb(p.get("dim", "#7f8db8")))
        for c, wd in zip(sub, sw):
            cr.move_to(xx, y)
            cr.show_text(c)
            xx += wd + 5 * k


class Wallpaper(Gtk.Window):
    def __init__(self, geom):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_wmclass("cos-wallpaperd", "cos-wallpaperd")
        self.set_title("Linux-C.O.S wallpaper")
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.stick()
        self.move(geom.x, geom.y)
        self.set_default_size(geom.width, geom.height)
        self.resize(geom.width, geom.height)
        self.scene = Scene(geom.width, geom.height)
        self.area = Gtk.DrawingArea()
        self.area.connect("draw", lambda w, cr: (self.scene.draw(cr), False)[1])
        self.add(self.area)
        self.show_all()
        GLib.timeout_add(int(1000 / FPS), lambda: (self.area.queue_draw(), True)[1])


def main():
    wins = []
    display = Gdk.Display.get_default()
    for i in range(display.get_n_monitors()):
        wins.append(Wallpaper(display.get_monitor(i).get_geometry()))

    def check_mode():
        m = core.get_mode()
        for w in wins:
            if w.scene.mode != m:
                w.scene.load(m)
        return True

    GLib.timeout_add_seconds(2, check_mode)
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    signal.signal(signal.SIGINT, lambda *_: Gtk.main_quit())
    Gtk.main()


if __name__ == "__main__":
    main()
