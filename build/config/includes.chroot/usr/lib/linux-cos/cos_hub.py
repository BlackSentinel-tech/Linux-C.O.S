#!/usr/bin/env python3
"""COS Hub -- the Linux-C.O.S control centre (GTK3).

One window for everything the distro unifies: red/blue/dual mode, effects,
the combined Kali + Parrot + BlackArch tool catalog, and quick actions for
the container, the blue-team stacks and the local AI assistant.
"""
import os
import shutil
import subprocess
import sys
import threading

sys.path.insert(0, os.environ.get("COS_LIB", "/usr/lib/linux-cos"))
import cos_core as core  # noqa: E402

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

ES = core.lang() == "es"


def tr(en, es):
    return es if ES else en


def css_for(p):
    a, a2, bg, s1, s2, bd = p["accent"], p["accent2"], p["bg"], p["surface"], p["surface2"], p["border"]
    return f"""
window.cos-hub {{ background-color: {bg}; }}
.cos-side {{ background-color: {s1}; border-right: 1px solid {bd}; padding: 18px 10px; }}
.cos-brand {{ font-family: "Oxanium"; font-weight: 700; font-size: 17px; letter-spacing: 3px; color: {a}; }}
.cos-sub {{ color: {p['dim']}; font-size: 11px; letter-spacing: 2px; }}
.cos-nav {{ background: transparent; border: 1px solid transparent; border-radius: 10px; padding: 10px 14px; color: {p['dim']}; font-weight: 600; }}
.cos-nav:hover {{ color: {p['fg']}; background-color: alpha({a}, 0.10); }}
.cos-nav.active {{ color: {p['fg']}; background-color: alpha({a}, 0.18); border-color: alpha({a}, 0.7); box-shadow: 0 0 14px alpha({a}, 0.35); }}
.cos-h1 {{ font-family: "Oxanium"; font-weight: 700; font-size: 26px; color: {p['fg']}; }}
.cos-h2 {{ font-family: "Oxanium"; font-weight: 600; font-size: 15px; color: {p['dim']}; letter-spacing: 2px; }}
.cos-card {{ background-color: alpha({s2}, 0.85); border: 1px solid {bd}; border-radius: 14px; padding: 16px; }}
.cos-card:hover {{ border-color: alpha({a}, 0.7); box-shadow: 0 0 16px alpha({a}, 0.25); }}
.cos-num {{ font-family: "Oxanium"; font-weight: 700; font-size: 34px; color: {p['fg']}; }}
.cos-red {{ color: {p['bad']}; }} .cos-cyan {{ color: {a}; }} .cos-blue {{ color: #3d8bff; }} .cos-ok {{ color: {p['ok']}; }}
.cos-dim {{ color: {p['dim']}; }}
.cos-num-sm {{ font-family: "Oxanium"; font-weight: 700; font-size: 20px; }}
.cos-mode {{ border-radius: 12px; padding: 12px 18px; font-weight: 700; }}
.cos-mode.sel {{ box-shadow: 0 0 18px alpha({a}, 0.7); border-color: {a}; }}
.cos-action {{ border-radius: 14px; padding: 16px 12px; }}
searchentry, entry {{ background-color: {s1}; }}
treeview.view {{ background-color: transparent; }}
"""


class Hub(Gtk.Window):
    def __init__(self):
        super().__init__(title="COS Hub")
        self.set_wmclass("cos-hub", "cos-hub")
        self.get_style_context().add_class("cos-hub")
        self.set_default_size(1100, 700)
        self.set_size_request(900, 560)
        try:
            self.set_icon_name("linux-cos")
        except Exception:
            pass
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.apply_css()

        root = Gtk.Box()
        self.add(root)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        side.get_style_context().add_class("cos-side")
        side.set_size_request(220, -1)
        root.pack_start(side, False, False, 0)
        brand = Gtk.Label(label="LINUX-C.O.S", xalign=0)
        brand.get_style_context().add_class("cos-brand")
        sub = Gtk.Label(label="COS HUB", xalign=0)
        sub.get_style_context().add_class("cos-sub")
        side.pack_start(brand, False, False, 0)
        side.pack_start(sub, False, False, 14)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=180)
        root.pack_start(self.stack, True, True, 0)
        self.nav = {}
        for key, label in (("dash", tr("Dashboard", "Panel")), ("tools", tr("Tools", "Herramientas")),
                           ("look", tr("Appearance", "Apariencia"))):
            b = Gtk.Button(label=label, relief=Gtk.ReliefStyle.NONE)
            b.get_child().set_xalign(0)
            b.get_style_context().add_class("cos-nav")
            b.connect("clicked", lambda _b, k=key: self.show_page(k))
            side.pack_start(b, False, False, 0)
            self.nav[key] = b
        side.pack_end(Gtk.Label(label=f"cos {core.get_mode()} · fx {core.effective_fx()}", xalign=0, name="foot"), False, False, 0)

        self.stack.add_named(self.page_dash(), "dash")
        self.stack.add_named(self.page_tools(), "tools")
        self.stack.add_named(self.page_look(), "look")
        self.show_page("dash")
        self.show_all()
        threading.Thread(target=self.probe_container, daemon=True).start()

    # --- helpers ----------------------------------------------------------------------
    def apply_css(self):
        self.provider.load_from_data(css_for(core.palette()).encode())

    def show_page(self, key):
        self.stack.set_visible_child_name(key)
        for k, b in self.nav.items():
            ctx = b.get_style_context()
            (ctx.add_class if k == key else ctx.remove_class)("active")

    def page(self, title, subtitle=""):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, margin=28)
        h = Gtk.Label(label=title, xalign=0)
        h.get_style_context().add_class("cos-h1")
        box.pack_start(h, False, False, 0)
        if subtitle:
            s = Gtk.Label(label=subtitle, xalign=0)
            s.get_style_context().add_class("cos-dim")
            box.pack_start(s, False, False, 0)
        return box

    def card(self, big, small, css="cos-cyan"):
        c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        c.get_style_context().add_class("cos-card")
        n = Gtk.Label(label=str(big), xalign=0)
        n.get_style_context().add_class("cos-num")
        n.get_style_context().add_class(css)
        t = Gtk.Label(label=small, xalign=0)
        t.get_style_context().add_class("cos-dim")
        c.pack_start(n, False, False, 0)
        c.pack_start(t, False, False, 0)
        return c, n

    @staticmethod
    def term(*argv, title="Linux-C.O.S"):
        cmd = ["xfce4-terminal", "-T", title, "-x", "cos-pause", *argv]
        if not shutil.which("xfce4-terminal"):
            cmd = ["x-terminal-emulator", "-e", " ".join(argv)]
        try:
            subprocess.Popen(cmd, start_new_session=True)
        except OSError:
            pass

    # --- pages ------------------------------------------------------------------------------
    def page_dash(self):
        box = self.page(tr("Dashboard", "Panel"), tr("Kali, Parrot and BlackArch as one system.", "Kali, Parrot y BlackArch como un solo sistema."))
        ts = core.tools().values()
        n = {s: sum(1 for t in ts if t.source == s) for s in ("kali", "parrot", "blackarch")}
        grid = Gtk.Grid(column_spacing=14, row_spacing=14, column_homogeneous=True)
        for i, (num, label, css) in enumerate((
                (len(core.tools()), tr("tools in one catalog", "herramientas en un catálogo"), "cos-cyan"),
                (n["kali"], "Kali", "cos-blue"), (n["parrot"], "Parrot", "cos-cyan"), (n["blackarch"], "BlackArch", "cos-red"))):
            c, _ = self.card(num, label, css)
            grid.attach(c, i, 0, 1, 1)
        box.pack_start(grid, False, False, 4)

        self.container_card, self.container_lbl = self.card("…", tr("BlackArch container", "Contenedor BlackArch"), "cos-dim")
        self.container_lbl.get_style_context().remove_class("cos-num")
        self.container_lbl.get_style_context().add_class("cos-num-sm")
        self.container_lbl.set_margin_top(10)
        self.container_lbl.set_margin_bottom(6)
        grid.attach(self.container_card, 4, 0, 1, 1)

        h = Gtk.Label(label=tr("QUICK ACTIONS", "ACCIONES RÁPIDAS"), xalign=0)
        h.get_style_context().add_class("cos-h2")
        box.pack_start(h, False, False, 10)
        acts = Gtk.Grid(column_spacing=14, row_spacing=14, column_homogeneous=True)
        items = (
            (tr("Terminal", "Terminal"), lambda *_: subprocess.Popen(["xfce4-terminal"], start_new_session=True)),
            (tr("BlackArch shell", "Shell BlackArch"), lambda *_: self.term("blackarch-shell", title="BlackArch")),
            (tr("AI assistant", "Asistente IA"), lambda *_: self.term("cos-ai", title="cos-ai")),
            (tr("Blue-team stacks", "Stacks blue team"), lambda *_: self.term("cos-stacks", title="cos-stacks")),
            (tr("System health", "Salud del sistema"), lambda *_: self.term("cos", "doctor", title="cos doctor")),
            (tr("Quick start", "Inicio rápido"), lambda *_: self.term("cos-help", title="cos-help")),
        )
        for i, (label, cb) in enumerate(items):
            b = Gtk.Button(label=label)
            b.get_style_context().add_class("cos-action")
            b.connect("clicked", cb)
            acts.attach(b, i % 3, i // 3, 1, 1)
        box.pack_start(acts, False, False, 0)
        return box

    def probe_container(self):
        ok = core.docker_has_image()
        GLib.idle_add(self.set_container, ok)

    def set_container(self, ok):
        self.container_lbl.set_text(tr("Ready", "Listo") if ok else tr("Not downloaded", "Sin descargar"))
        ctx = self.container_lbl.get_style_context()
        ctx.remove_class("cos-dim")
        ctx.add_class("cos-ok" if ok else "cos-red")

    def page_tools(self):
        box = self.page(tr("Tools", "Herramientas"), tr("Double-click a tool to run it. BlackArch tools run from the container.", "Doble clic para ejecutar. Las de BlackArch corren desde el contenedor."))
        bar = Gtk.Box(spacing=10)
        self.search = Gtk.SearchEntry(placeholder_text=tr("Search 3,000+ tools…", "Buscar entre más de 3.000 herramientas…"))
        self.search.set_hexpand(True)
        self.cat = Gtk.ComboBoxText()
        self.cat.append("", tr("All categories", "Todas las categorías"))
        for c in sorted(core.categories().values(), key=lambda c: c.order):
            self.cat.append(c.id, c.name)
        self.cat.set_active(0)
        self.src = Gtk.ComboBoxText()
        for k, v in (("", tr("All sources", "Todos los orígenes")), ("kali", "Kali"), ("parrot", "Parrot"), ("blackarch", "BlackArch")):
            self.src.append(k, v)
        self.src.set_active(0)
        for w in (self.search, self.cat, self.src):
            bar.pack_start(w, w is self.search, True, 0)
        box.pack_start(bar, False, False, 0)

        installed = core._dpkg_installed()
        self.model = Gtk.ListStore(str, str, str, str, str)  # dot, name, category, source, source-id
        cats = core.categories()
        for t in sorted(core.tools().values(), key=lambda t: t.name):
            if t.source == "cos":
                continue
            native = t.name in installed or shutil.which(t.name)
            dot = "●" if native else ("◆" if t.source == "blackarch" else "○")
            self.model.append([dot, t.name, cats[t.cat].name if t.cat in cats else t.cat, core.SOURCE_LABEL.get(t.source, t.source), t.source])
        self.filter = self.model.filter_new()
        self.filter.set_visible_func(self.visible)
        self.sorted = Gtk.TreeModelSort(model=self.filter)
        view = Gtk.TreeView(model=self.sorted)
        for i, (title, w) in enumerate((("", 30), (tr("Tool", "Herramienta"), 280), (tr("Category", "Categoría"), 240), (tr("Source", "Origen"), 100))):
            r = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, r, text=i)
            col.set_min_width(w)
            col.set_sort_column_id(i)
            view.append_column(col)
        view.connect("row-activated", self.on_run)
        self.view = view
        sw = Gtk.ScrolledWindow()
        sw.add(view)
        box.pack_start(sw, True, True, 0)
        foot = Gtk.Label(label="●  " + tr("installed here", "instalada aquí") + "     ◆  " + tr("BlackArch container", "contenedor BlackArch") + "     ○  " + tr("installable", "instalable"), xalign=0)
        foot.get_style_context().add_class("cos-dim")
        box.pack_start(foot, False, False, 0)
        for w in (self.search,):
            w.connect("search-changed", lambda *_: self.filter.refilter())
        for w in (self.cat, self.src):
            w.connect("changed", lambda *_: self.filter.refilter())
        return box

    def visible(self, model, it, _):
        q = self.search.get_text().lower().strip()
        name, cat, src = model[it][1], model[it][2], model[it][4]
        cid = self.cat.get_active_id()
        if cid:
            t = core.tools().get(name)
            if not t or t.cat != cid:
                return False
        sid = self.src.get_active_id()
        if sid and src != sid:
            return False
        return not q or q in name.lower()

    def on_run(self, view, path, _col):
        name = view.get_model()[path][1]
        r = core.resolve(name)
        if r.kind == "installable":
            self.term("cos", "install", name, title=f"install {name}")
        else:
            self.term("cos", "run", name, title=name)

    def page_look(self):
        box = self.page(tr("Appearance", "Apariencia"), tr("Colour mode and effects apply instantly.", "El modo de color y los efectos se aplican al instante."))
        h = Gtk.Label(label=tr("MODE", "MODO"), xalign=0)
        h.get_style_context().add_class("cos-h2")
        box.pack_start(h, False, False, 4)
        row = Gtk.Box(spacing=12)
        self.mode_btns = {}
        for m, label in (("dual", "DUAL"), ("red", "RED TEAM"), ("blue", "BLUE TEAM")):
            b = Gtk.Button(label=label)
            b.get_style_context().add_class("cos-mode")
            b.connect("clicked", lambda _b, mm=m: self.set_mode(mm))
            row.pack_start(b, False, False, 0)
            self.mode_btns[m] = b
        box.pack_start(row, False, False, 0)
        h2 = Gtk.Label(label=tr("EFFECTS", "EFECTOS"), xalign=0)
        h2.get_style_context().add_class("cos-h2")
        box.pack_start(h2, False, False, 10)
        row2 = Gtk.Box(spacing=12)
        self.fx_btns = {}
        for fx, label in (("auto", "AUTO"), ("high", tr("HIGH", "ALTO")), ("low", tr("LOW", "BAJO")), ("off", "OFF")):
            b = Gtk.Button(label=label)
            b.get_style_context().add_class("cos-mode")
            b.connect("clicked", lambda _b, f=fx: self.set_fx(f))
            row2.pack_start(b, False, False, 0)
            self.fx_btns[fx] = b
        box.pack_start(row2, False, False, 0)
        self.fx_note = Gtk.Label(xalign=0, wrap=True)
        self.fx_note.get_style_context().add_class("cos-dim")
        box.pack_start(self.fx_note, False, False, 6)
        self.refresh_look()
        return box

    def refresh_look(self):
        for m, b in self.mode_btns.items():
            (b.get_style_context().add_class if m == core.get_mode() else b.get_style_context().remove_class)("sel")
        for f, b in self.fx_btns.items():
            (b.get_style_context().add_class if f == core.get_fx() else b.get_style_context().remove_class)("sel")
        self.fx_note.set_text(tr(f"Effective level: {core.effective_fx()}  (virtualisation: {core.virt()}). "
                                 "High = blur, animations and live wallpaper; Low = light effects for VMs and old hardware.",
                                 f"Nivel efectivo: {core.effective_fx()}  (virtualización: {core.virt()}). "
                                 "Alto = desenfoque, animaciones y fondo vivo; Bajo = efectos ligeros para VMs y equipos antiguos."))

    def set_mode(self, m):
        core.set_mode(m)
        self.refresh_look()
        self.apply_css()
        self.run_apply()

    def set_fx(self, f):
        core.set_fx(f)
        self.refresh_look()
        self.run_apply()

    def run_apply(self):
        def work():
            try:
                import cos_session
                cos_session.apply()
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()


def main():
    Hub().connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
