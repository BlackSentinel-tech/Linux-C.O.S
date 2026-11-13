"""`cos` -- the Linux-C.O.S command: one entry point for every tool, stack,
mode and effect.  Standard library only (see cos_core)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

import cos_core as core

VERSION = "0.2 (Génesis)"
ES = core.lang() == "es"


def tr(en: str, es: str) -> str:
    return es if ES else en


# --- colour (honours NO_COLOR and pipes) --------------------------------------
_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def cyan(s): return _c("38;5;45", s)
def red(s): return _c("38;5;197", s)
def blue(s): return _c("38;5;75", s)
def green(s): return _c("38;5;48", s)
def dim(s): return _c("2", s)
def bold(s): return _c("1", s)


def _exec(argv: list[str]) -> int:
    """exec, but with a message instead of a traceback when the program is missing."""
    try:
        os.execvp(argv[0], argv)
    except FileNotFoundError:
        return die(tr(f"'{argv[0]}' is not installed on this system", f"'{argv[0]}' no está instalado en este sistema"), 127)
    return 0  # unreachable


SRC_COLOR = {"kali": blue, "parrot": cyan, "blackarch": red, "cos": green}


def src_tag(source: str) -> str:
    return SRC_COLOR.get(source, dim)(core.SOURCE_LABEL.get(source, source).ljust(9))


def die(msg: str, code: int = 1) -> int:
    print(f"{red('cos:')} {msg}", file=sys.stderr)
    return code


HELP = """\
{title}

{usage}
  cos                         {s_status}
  cos tools [list]            {s_list}   [-c CATEGORY] [-s SOURCE] [-i]
  cos tools search <text>     {s_search}
  cos tools info <name>       {s_info}
  cos tools cats              {s_cats}
  cos run <tool> [args...]    {s_run}
  cos install <tool>          {s_install}
  cos mode [dual|red|blue]    {s_mode}
  cos fx [auto|high|low|off]  {s_fx}
  cos hub                     {s_hub}
  cos doctor                  {s_doctor}
  cos stack|ai|shell ...      {s_pass}
  cos version

{foot}
"""


def usage() -> str:
    return HELP.format(
        title=bold(cyan("Linux-C.O.S")) + dim(" -- " + tr("Cyber Offensive & defensive Security", "Ciberseguridad ofensiva y defensiva")),
        usage=bold(tr("usage:", "uso:")),
        s_status=tr("status of this system", "estado del sistema"),
        s_list=tr("every tool, one catalog", "todas las herramientas, un solo catálogo"),
        s_search=tr("find a tool by name", "buscar una herramienta"),
        s_info=tr("category, origin, how it runs", "categoría, origen, cómo se ejecuta"),
        s_cats=tr("the unified categories", "las categorías unificadas"),
        s_run=tr("run a tool (native or BlackArch, same command)", "ejecutar (nativa o BlackArch, igual)"),
        s_install=tr("install a tool that is not here yet", "instalar una herramienta que falta"),
        s_mode=tr("red / blue / dual colour mode", "modo de color rojo / azul / dual"),
        s_fx=tr("visual effects level", "nivel de efectos visuales"),
        s_hub=tr("open the COS Hub (dashboard)", "abrir el COS Hub (panel)"),
        s_doctor=tr("check this system is healthy", "comprobar la salud del sistema"),
        s_pass=tr("shortcuts to cos-stacks, cos-ai, blackarch-shell", "atajos a cos-stacks, cos-ai, blackarch-shell"),
        foot=dim(tr("Tools from Kali, Parrot and BlackArch all run as plain commands:\n"
                    "type the name -- if it lives in the BlackArch container, cos runs it there.",
                    "Las herramientas de Kali, Parrot y BlackArch se ejecutan como comandos normales:\n"
                    "escribe el nombre -- si vive en el contenedor BlackArch, cos lo ejecuta allí.")),
    )


# --- tools --------------------------------------------------------------------
def _state_mark(name: str) -> str:
    r = core.resolve(name)
    return {"native": green("●"), "container": red("◆"), "installable": dim("○")}.get(r.kind, dim("?"))


def cmd_list(args: list[str]) -> int:
    cat = src = None
    only_installed = count = False
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-c", "--category") and i + 1 < len(args):
            cat = args[i + 1]; i += 2
        elif a in ("-s", "--source") and i + 1 < len(args):
            src = args[i + 1]; i += 2
        elif a in ("-i", "--installed"):
            only_installed = True; i += 1
        elif a == "--count":
            count = True; i += 1
        else:
            return die(tr(f"unknown option '{a}'", f"opción desconocida '{a}'"))
    if cat and cat not in core.categories():
        return die(tr(f"no category '{cat}' -- see: cos tools cats", f"no existe la categoría '{cat}' -- ver: cos tools cats"))
    items = core.search("", cat, src)
    if only_installed:
        items = [t for t in items if core.resolve(t.name).available]
    if count:
        print(len(items))
        return 0
    cats = core.categories()
    for t in items:
        c = cats.get(t.cat)
        print(f"{_state_mark(t.name)} {t.name.ljust(30)} {src_tag(t.source)} {dim(c.name if c else t.cat)}")
    if sys.stdout.isatty():
        print(dim(f"\n{len(items)} " + tr("tools", "herramientas") + "   ● " + tr("here", "aquí") +
                  "  ◆ " + tr("BlackArch container", "contenedor BlackArch") + "  ○ " + tr("installable", "instalable")))
    return 0


def cmd_cats() -> int:
    counts: dict[str, int] = {}
    for t in core.tools().values():
        counts[t.cat] = counts.get(t.cat, 0) + 1
    for c in sorted(core.categories().values(), key=lambda c: c.order):
        team = {"red": red("red "), "blue": blue("blue"), "both": cyan("both")}[c.team]
        print(f"{c.id.ljust(10)} {team}  {str(counts.get(c.id, 0)).rjust(4)}  {c.name}")
    return 0


def cmd_search(args: list[str]) -> int:
    if not args:
        return die(tr("what should I look for?", "¿qué busco?"))
    res = core.search(" ".join(args))
    if not res:
        print(tr("no tool matches", "ninguna herramienta coincide"))
        return 1
    cats = core.categories()
    for t in res[:60]:
        c = cats.get(t.cat)
        print(f"{_state_mark(t.name)} {t.name.ljust(30)} {src_tag(t.source)} {dim(c.name if c else t.cat)}")
    if len(res) > 60:
        print(dim(f"... +{len(res) - 60}"))
    return 0


def cmd_info(args: list[str]) -> int:
    if not args:
        return die(tr("which tool?", "¿qué herramienta?"))
    name = args[0]
    t = core.tools().get(name)
    r = core.resolve(name)
    if t is None and r.kind == "unknown":
        return die(tr(f"unknown tool '{name}' (try: cos tools search {name})", f"herramienta desconocida '{name}' (prueba: cos tools search {name})"))
    print(bold(name))
    if t:
        c = core.categories().get(t.cat)
        print(f"  {tr('category', 'categoría')}: {c.name if c else t.cat}")
        print(f"  {tr('origin', 'origen')}:    {core.SOURCE_LABEL.get(t.source, t.source)}  {dim('(' + t.group + ')')}")
    how = {
        "native": tr(f"installed natively: {r.detail}", f"instalada de forma nativa: {r.detail}"),
        "container": tr("runs from the BlackArch container (cos run does it for you)", "se ejecuta desde el contenedor BlackArch (cos run lo hace por ti)"),
        "installable": tr(f"not installed -- cos install {name}", f"no instalada -- cos install {name}"),
        "unknown": tr("not available", "no disponible"),
    }[r.kind]
    print(f"  {tr('status', 'estado')}:    {how}")
    return 0


def cmd_tools(args: list[str]) -> int:
    if not args or args[0].startswith("-"):
        return cmd_list(args)
    sub, rest = args[0], args[1:]
    return {"list": lambda: cmd_list(rest), "ls": lambda: cmd_list(rest),
            "search": lambda: cmd_search(rest), "find": lambda: cmd_search(rest),
            "info": lambda: cmd_info(rest), "cats": cmd_cats, "categories": cmd_cats,
            }.get(sub, lambda: die(tr(f"unknown: cos tools {sub}", f"desconocido: cos tools {sub}")))()


def cmd_run(args: list[str]) -> int:
    if not args:
        return die(tr("usage: cos run <tool> [args...]", "uso: cos run <herramienta> [args...]"))
    name, rest = args[0], args[1:]
    argv = core.run_argv(name, rest)
    if argv is None:
        r = core.resolve(name)
        if r.kind == "installable":
            return die(tr(f"'{name}' is not installed -- run: cos install {name}", f"'{name}' no está instalada -- ejecuta: cos install {name}"), 127)
        return die(tr(f"unknown tool '{name}'", f"herramienta desconocida '{name}'"), 127)
    if argv[0] == "blackarch-shell":
        if not core.docker_has_image():
            return die(tr(f"{name} is a BlackArch tool and the container is not on this machine yet -- run: blackarch-shell --update",
                          f"{name} es de BlackArch y el contenedor aún no está en este equipo -- ejecuta: blackarch-shell --update"), 127)
        print(dim(tr(f"[cos] {name} runs from the BlackArch container", f"[cos] {name} se ejecuta desde el contenedor BlackArch")), file=sys.stderr)
    return _exec(argv)


def cmd_install(args: list[str]) -> int:
    if not args:
        return die(tr("usage: cos install <tool>", "uso: cos install <herramienta>"))
    name = args[0]
    if core.resolve(name).kind == "native":
        print(tr(f"{name} is already here", f"{name} ya está instalada"))
        return 0
    argv = core.install_argv(name)
    if argv is None:
        return die(tr(f"don't know how to install '{name}'", f"no sé instalar '{name}'"))
    print(dim("$ " + " ".join(argv)))
    return _exec(argv)


def cmd_cnf(args: list[str]) -> int:
    """command-not-found hook for bash/zsh: BlackArch tools behave like native ones."""
    if not args:
        return 127
    name, rest = args[0], args[1:]
    t = core.tools().get(name)
    if t is None or name.startswith("-") or "/" in name:
        return 127
    r = core.resolve(name)
    if r.kind == "container" and core.docker_has_image():
        argv = core.run_argv(name, rest)
        print(dim(tr(f"[cos] {name} → BlackArch container", f"[cos] {name} → contenedor BlackArch")), file=sys.stderr)
        return _exec(argv)
    if r.kind == "container":
        print(tr(f"{name} is a BlackArch tool; the container is not on this machine yet:  blackarch-shell --update",
                 f"{name} es una herramienta de BlackArch; el contenedor aún no está en este equipo:  blackarch-shell --update"),
              file=sys.stderr)
        return 127
    if r.kind == "installable":
        print(tr(f"{name} ({core.SOURCE_LABEL.get(t.source)}) is not installed:  cos install {name}",
                 f"{name} ({core.SOURCE_LABEL.get(t.source)}) no está instalada:  cos install {name}"), file=sys.stderr)
        return 127
    return 127


# --- mode / fx ----------------------------------------------------------------
def _apply() -> None:
    try:
        import cos_session
        cos_session.apply()
    except Exception as e:  # not on a desktop (ssh, tests): the setting is still saved
        print(dim(tr(f"(saved; not applied here: {e})", f"(guardado; no aplicado aquí: {e})")), file=sys.stderr)


def cmd_mode(args: list[str]) -> int:
    if not args or args[0] == "status":
        m = core.get_mode()
        print(f"{tr('mode', 'modo')}: {bold(m)}   ({core.palette(m).get('name', m)})")
        return 0
    if args[0] not in core.MODES:
        return die(tr("modes: dual, red, blue", "modos: dual, red, blue"))
    core.set_mode(args[0])
    _apply()
    print(tr(f"mode: {args[0]}", f"modo: {args[0]}"))
    return 0


def cmd_fx(args: list[str]) -> int:
    if not args or args[0] == "status":
        print(f"fx: {bold(core.get_fx())}  → {core.effective_fx()}   (virt: {core.virt()})")
        return 0
    if args[0] not in core.FX_LEVELS:
        return die(tr("levels: auto, high, low, off", "niveles: auto, high, low, off"))
    core.set_fx(args[0])
    _apply()
    print(f"fx: {args[0]}")
    return 0


# --- status / doctor ----------------------------------------------------------
def cmd_status() -> int:
    ts = core.tools().values()
    n = {s: sum(1 for t in ts if t.source == s) for s in ("kali", "parrot", "blackarch")}
    print(bold(cyan("Linux-C.O.S ")) + dim(VERSION))
    print(f"  {tr('mode', 'modo')}:       {core.get_mode()}   fx: {core.get_fx()} → {core.effective_fx()}")
    print(f"  {tr('tools', 'herramientas')}: {len(core.tools())}   "
          f"{blue('Kali')} {n['kali']}  {cyan('Parrot')} {n['parrot']}  {red('BlackArch')} {n['blackarch']}")
    print(f"  BlackArch:  {green(tr('container ready', 'contenedor listo')) if core.docker_has_image() else dim(tr('container not downloaded', 'contenedor sin descargar'))}")
    print(f"  AI:         {green('ollama') if shutil.which('ollama') else dim(tr('run: cos-ai setup', 'ejecuta: cos-ai setup'))}")
    print(dim("\n  cos --help"))
    return 0


def cmd_doctor() -> int:
    bad = 0

    def line(ok: bool, what: str, hint: str = "") -> None:
        nonlocal bad
        print(f"  {green('ok  ') if ok else red('FAIL')} {what}" + ("" if ok or not hint else dim("  → " + hint)))
        bad += 0 if ok else 1

    print(bold(tr("Linux-C.O.S health", "Salud de Linux-C.O.S")))
    line(bool(core.tools()), tr("tool catalog", "catálogo de herramientas"), "/usr/share/linux-cos/tools.tsv")
    line(bool(shutil.which("docker")), "docker", "sudo apt install docker.io")
    if shutil.which("docker"):
        line(core.docker_has_image(), tr("BlackArch image", "imagen BlackArch"), "blackarch-shell --update")
    for tool in ("nmap", "msfconsole", "wireshark"):
        line(bool(shutil.which(tool)), tool)
    line(subprocess.run(["systemctl", "is-active", "--quiet", "ufw"]).returncode == 0 if shutil.which("systemctl") else False,
         tr("firewall (ufw)", "cortafuegos (ufw)"), "sudo ufw enable")
    line(subprocess.run(["systemctl", "is-active", "--quiet", "apparmor"]).returncode == 0 if shutil.which("systemctl") else False,
         "AppArmor", "sudo systemctl enable --now apparmor")
    print(dim(f"\n  virt: {core.virt()}   fx: {core.effective_fx()}"))
    return 1 if bad else 0


def cmd_session(args: list[str]) -> int:
    import cos_session
    sub = args[0] if args else "apply"
    if sub == "start":
        cos_session.start()
    elif sub == "apply":
        cos_session.apply()
    elif sub == "prompt":
        cos_session.prompt()
    else:
        return die(tr("usage: cos session [start|apply]", "uso: cos session [start|apply]"))
    return 0


def cmd_menu() -> int:
    import cos_menu
    return cos_menu.main([])


def cmd_hub() -> int:
    hub = os.environ.get("COS_HUB", "/usr/lib/linux-cos/cos_hub.py")
    if not os.path.exists(hub):
        return die(tr("COS Hub is not installed", "COS Hub no está instalado"))
    return _exec(["python3", hub])


def main(argv: list[str]) -> int:
    if not argv:
        return cmd_status()
    cmd, rest = argv[0], argv[1:]
    table = {
        "status": lambda: cmd_status(), "tools": lambda: cmd_tools(rest), "t": lambda: cmd_tools(rest),
        "run": lambda: cmd_run(rest), "x": lambda: cmd_run(rest),
        "install": lambda: cmd_install(rest), "mode": lambda: cmd_mode(rest),
        "fx": lambda: cmd_fx(rest), "doctor": lambda: cmd_doctor(), "hub": lambda: cmd_hub(),
        "session": lambda: cmd_session(rest), "menu": lambda: cmd_menu(),
        "_cnf": lambda: cmd_cnf(rest),
        "version": lambda: (print("Linux-C.O.S " + VERSION), 0)[1],
    }
    if cmd in ("-h", "--help", "help"):
        print(usage())
        return 0
    if cmd in ("stack", "stacks", "ai", "shell"):
        target = {"stack": "cos-stacks", "stacks": "cos-stacks", "ai": "cos-ai", "shell": "blackarch-shell"}[cmd]
        if not shutil.which(target):
            return die(tr(f"{target} not found", f"{target} no encontrado"))
        return _exec([target, *rest])
    if cmd in table:
        return table[cmd]()
    # `cos nmap -sV host` is a shorthand for `cos run nmap -sV host`
    if cmd in core.tools():
        return cmd_run(argv)
    return die(tr(f"unknown command '{cmd}' -- try: cos --help", f"comando desconocido '{cmd}' -- prueba: cos --help"))
