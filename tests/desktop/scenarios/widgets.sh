# a window full of GTK widgets under the COS theme
set -u
xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s "COS-${COS_MODE:-Dual}" 2>/dev/null || true
export GTK_THEME="COS-${COS_MODE:-Dual}"
cat > /tmp/w.py <<'PY'
import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk, GLib
w=Gtk.Window(title="COS widgets"); w.set_default_size(720,520)
hb=Gtk.HeaderBar(show_close_button=True,title="Linux-C.O.S"); w.set_titlebar(hb)
b=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=16); w.add(b)
b.add(Gtk.Label(label="Linux-C.O.S theme test"))
e=Gtk.Entry(text="focused entry"); b.add(e)
r=Gtk.Box(spacing=8); b.add(r)
r.add(Gtk.Button(label="Button")); sb=Gtk.Button(label="Suggested"); sb.get_style_context().add_class("suggested-action"); r.add(sb)
db=Gtk.Button(label="Destructive"); db.get_style_context().add_class("destructive-action"); r.add(db)
r.add(Gtk.Switch(active=True)); r.add(Gtk.CheckButton(label="check",active=True))
pb=Gtk.ProgressBar(fraction=0.62); b.add(pb)
b.add(Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1))
nb=Gtk.Notebook(); b.add(nb)
tv=Gtk.TreeView(model=Gtk.ListStore(str,str))
for i,t in enumerate(("Tool","Source")): tv.append_column(Gtk.TreeViewColumn(t,Gtk.CellRendererText(),text=i))
for n,s in (("nmap","Kali"),("sqlmap","Kali"),("0d1n","BlackArch"),("bloodhound","Parrot")): tv.get_model().append([n,s])
tv.get_selection().select_path(Gtk.TreePath.new_from_string("1"))
nb.append_page(tv,Gtk.Label(label="Tools")); nb.append_page(Gtk.TextView(),Gtk.Label(label="Notes"))
w.connect("destroy",Gtk.main_quit); w.show_all(); e.grab_focus()
GLib.timeout_add(100,lambda: w.move(80,60) or False)
Gtk.main()
PY
python3 /tmp/w.py &
sleep 3
import -display :99 -window root /out/widgets.png
