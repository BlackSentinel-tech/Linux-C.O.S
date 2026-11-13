"""Linux-C.O.S core -- the one place that knows every tool.

Kali and Parrot tools are native apt packages; BlackArch tools live in a
container.  This module hides that difference: callers ask for a tool by name
and get back how to run it.  Used by the `cos` CLI, the COS Hub, the menu
generator and the shell's command-not-found hook.  Standard library only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache

SHARE = os.environ.get("COS_SHARE", "/usr/share/linux-cos")
CONF_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "linux-cos")
BLACKARCH_IMAGE = "linux-cos/blackarch:latest"

SOURCE_LABEL = {"kali": "Kali", "parrot": "Parrot", "blackarch": "BlackArch", "cos": "Linux-C.O.S"}


def lang() -> str:
    for v in ("COS_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(v, "")
        if val:
            return "es" if val.lower().startswith("es") else "en"
    return "en"


@dataclass(frozen=True)
class Category:
    id: str
    order: int
    en: str
    es: str
    icon: str
    team: str

    @property
    def name(self) -> str:
        return self.es if lang() == "es" else self.en


@dataclass(frozen=True)
class Tool:
    name: str
    cat: str
    source: str
    group: str


@lru_cache(maxsize=1)
def categories() -> dict[str, Category]:
    out: dict[str, Category] = {}
    try:
        with open(os.path.join(SHARE, "categories.tsv"), encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) == 6:
                    out[p[0]] = Category(p[0], int(p[1]), p[2], p[3], p[4], p[5])
    except OSError:
        pass
    return out


@lru_cache(maxsize=1)
def tools() -> dict[str, Tool]:
    out: dict[str, Tool] = {}
    try:
        with open(os.path.join(SHARE, "tools.tsv"), encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) == 4:
                    out[p[0]] = Tool(*p)
    except OSError:
        pass
    return out


@lru_cache(maxsize=1)
def _dpkg_installed() -> frozenset[str]:
    try:
        r = subprocess.run(["dpkg-query", "-W", "-f", "${binary:Package} ${db:Status-Status}\n"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    return frozenset(l.split()[0].split(":")[0] for l in r.stdout.splitlines()
                     if l.endswith(" installed"))


def _package_binary(pkg: str) -> str | None:
    """First executable a package ships (the apt name is often not the command)."""
    try:
        r = subprocess.run(["dpkg", "-L", pkg], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    cands = [p for p in r.stdout.splitlines()
             if p.startswith(("/usr/bin/", "/usr/sbin/", "/usr/local/bin/", "/bin/", "/sbin/"))]
    cands = [p for p in cands if os.access(p, os.X_OK) and not os.path.isdir(p)]
    named = [p for p in cands if os.path.basename(p) == pkg]
    return (named or cands or [None])[0]


@dataclass
class Resolution:
    kind: str          # native | container | installable | unknown
    detail: str = ""   # path / image / apt package

    @property
    def available(self) -> bool:
        return self.kind in ("native", "container")


def docker_has_image() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        r = subprocess.run(["docker", "image", "inspect", BLACKARCH_IMAGE],
                           capture_output=True, timeout=10)
        if r.returncode == 0:
            return True
        r = subprocess.run(["sudo", "-n", "docker", "image", "inspect", BLACKARCH_IMAGE],
                           capture_output=True, timeout=10)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def resolve(name: str) -> Resolution:
    """How can this tool be run on this machine right now?"""
    path = shutil.which(name)
    if path:
        return Resolution("native", path)
    t = tools().get(name)
    if t is None:
        return Resolution("unknown")
    if t.source in ("kali", "parrot"):
        if name in _dpkg_installed():
            exe = _package_binary(name)
            if exe:
                return Resolution("native", exe)
        return Resolution("installable", name)
    if t.source == "blackarch":
        return Resolution("container", BLACKARCH_IMAGE)
    return Resolution("unknown")


def run_argv(name: str, args: list[str]) -> list[str] | None:
    """argv that runs the tool, or None if it cannot be run yet."""
    r = resolve(name)
    if r.kind == "native":
        return [r.detail, *args]
    if r.kind == "container":
        return ["blackarch-shell", "--", name, *args]
    return None


def install_argv(name: str) -> list[str] | None:
    t = tools().get(name)
    if t is None:
        return None
    if t.source in ("kali", "parrot"):
        return ["sudo", "apt-get", "install", "-y", name]
    if t.source == "blackarch":
        return ["blackarch-shell", "--", "sudo", "pacman", "-S", "--noconfirm", "--needed", name]
    return None


def search(query: str, cat: str | None = None, source: str | None = None) -> list[Tool]:
    q = query.lower().strip()
    res = [t for t in tools().values()
           if (not q or q in t.name.lower() or q in t.group.lower())
           and (not cat or t.cat == cat) and (not source or t.source == source)]
    res.sort(key=lambda t: (not t.name.lower().startswith(q), t.name))
    return res


# --- user state: red/blue mode and effects level -----------------------------
MODES = ("dual", "red", "blue")
FX_LEVELS = ("auto", "high", "low", "off")


def _read(name: str, default: str) -> str:
    try:
        with open(os.path.join(CONF_DIR, name), encoding="utf-8") as f:
            return f.read().strip() or default
    except OSError:
        return default


def _write(name: str, value: str) -> None:
    os.makedirs(CONF_DIR, exist_ok=True)
    with open(os.path.join(CONF_DIR, name), "w", encoding="utf-8") as f:
        f.write(value + "\n")


def get_mode() -> str:
    m = _read("mode", "dual")
    return m if m in MODES else "dual"


def set_mode(m: str) -> None:
    if m not in MODES:
        raise ValueError(m)
    _write("mode", m)


def get_fx() -> str:
    v = _read("fx", "auto")
    return v if v in FX_LEVELS else "auto"


def set_fx(v: str) -> None:
    if v not in FX_LEVELS:
        raise ValueError(v)
    _write("fx", v)


def virt() -> str:
    """Hypervisor name or 'none' (effects default to a lighter set in VMs)."""
    try:
        r = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=5)
        out = r.stdout.strip()
        return out or "none"
    except (OSError, subprocess.SubprocessError):
        return "none"


def effective_fx() -> str:
    v = get_fx()
    if v != "auto":
        return v
    return "low" if virt() != "none" else "high"


def palette(mode: str | None = None) -> dict[str, str]:
    import json
    try:
        with open(os.path.join(SHARE, "palettes.json"), encoding="utf-8") as f:
            allp = json.load(f)
    except (OSError, ValueError):
        allp = {}
    return allp.get(mode or get_mode(), allp.get("dual", {}))
