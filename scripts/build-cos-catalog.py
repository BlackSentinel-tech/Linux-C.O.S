#!/usr/bin/env python3
"""Build the unified Linux-C.O.S tool catalog.

Kali, Parrot and BlackArch each have their own category scheme.  Linux-C.O.S
presents ONE taxonomy, so every tool -- whatever repository it comes from --
lives in the same menu, the same `cos tools` listing and the same Hub.

Inputs  (data/):   kali-official-categories.json   (Kali metapackage -> tools)
                   parrot-official-categories.json (Parrot metapackage -> tools)
                   blackarch-tools-catalog.json    ([name, blackarch-group])
Outputs (build/config/includes.chroot/usr/share/linux-cos/):
                   categories.tsv   id, order, EN name, ES name, icon, blue/red
                   tools.tsv        name, category id, source, origin group

Source precedence: a tool that Kali ships is "kali" (native apt); else one that
Parrot ships is "parrot" (native apt, Parrot repo); else "blackarch" (runs in
the BlackArch container, but behaves like a native command -- see `cos`).

    python3 scripts/build-cos-catalog.py           # rewrite the outputs
    python3 scripts/build-cos-catalog.py --check   # exit 1 if stale (CI)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "build/config/includes.chroot/usr/share/linux-cos"

# id, EN, ES, icon (freedesktop name), team (red|blue|both)
CATEGORIES = [
    ("recon",     "Reconnaissance",          "Reconocimiento",            "system-search",              "red"),
    ("vuln",      "Vulnerability Analysis",  "Análisis de vulnerabilidades", "security-medium",          "red"),
    ("web",       "Web Applications",        "Aplicaciones web",          "applications-internet",      "red"),
    ("exploit",   "Exploitation",            "Explotación",               "application-x-executable",   "red"),
    ("post",      "Post-Exploitation",       "Post-explotación",          "utilities-terminal",         "red"),
    ("passwords", "Passwords & Cracking",    "Contraseñas y cracking",    "dialog-password",            "red"),
    ("wireless",  "Wireless & RF",           "Inalámbrico y RF",          "network-wireless",           "red"),
    ("network",   "Network, Sniffing & Spoofing", "Red, sniffing y spoofing", "network-workgroup",      "both"),
    ("windows",   "Windows & Active Directory", "Windows y Active Directory", "computer",               "red"),
    ("social",    "Social Engineering",      "Ingeniería social",         "system-users",               "red"),
    ("reverse",   "Reverse Engineering & Binary", "Ingeniería inversa y binarios", "applications-debugging", "both"),
    ("database",  "Databases",               "Bases de datos",            "network-server-database",    "red"),
    ("mobile",    "Mobile, Hardware & Auto", "Móvil, hardware y automoción", "phone",                   "red"),
    ("cloud",     "Cloud & Containers",      "Nube y contenedores",       "weather-overcast",           "both"),
    ("crypto",    "Cryptography & Stego",    "Criptografía y esteganografía", "emblem-system",          "both"),
    ("forensics", "Forensics & Recovery",    "Forense y recuperación",    "drive-harddisk",             "blue"),
    ("defense",   "Defense & Detection",     "Defensa y detección",       "security-high",              "blue"),
    ("reporting", "Reporting",               "Informes",                  "x-office-document",          "both"),
    ("ai",        "AI & Automation",         "IA y automatización",       "applications-science",       "both"),
    ("utils",     "Utilities",               "Utilidades",                "applications-utilities",     "both"),
]

KALI = {
    "kali-tools-information-gathering": "recon", "kali-tools-identify": "recon",
    "kali-tools-vulnerability": "vuln", "kali-tools-web": "web",
    "kali-tools-database": "database", "kali-tools-passwords": "passwords",
    "kali-tools-wireless": "wireless", "kali-tools-802-11": "wireless",
    "kali-tools-bluetooth": "wireless", "kali-tools-sdr": "wireless",
    "kali-tools-rfid": "wireless", "kali-tools-exploitation": "exploit",
    "kali-tools-post-exploitation": "post", "kali-tools-social-engineering": "social",
    "kali-tools-sniffing-spoofing": "network", "kali-tools-voip": "network",
    "kali-tools-reverse-engineering": "reverse", "kali-tools-fuzzing": "reverse",
    "kali-tools-forensics": "forensics", "kali-tools-recover": "forensics",
    "kali-tools-reporting": "reporting", "kali-tools-crypto-stego": "crypto",
    "kali-tools-hardware": "mobile", "kali-tools-windows-resources": "windows",
    "kali-tools-protect": "defense", "kali-tools-detect": "defense",
    "kali-tools-respond": "defense", "kali-tools-gpu": "passwords",
}
PARROT = {
    "parrot-tools-ai": "ai", "parrot-tools-infogathering": "recon",
    "parrot-tools-vuln": "vuln", "parrot-tools-web": "web", "parrot-tools-pwn": "exploit",
    "parrot-tools-maintain": "utils", "parrot-tools-postexploit": "post",
    "parrot-tools-password": "passwords", "parrot-tools-wireless": "wireless",
    "parrot-tools-sniff": "network", "parrot-tools-forensics": "forensics",
    "parrot-tools-automotive": "mobile", "parrot-tools-reversing": "reverse",
    "parrot-tools-reporting": "reporting", "parrot-tools-cloud": "cloud",
}
BLACKARCH = {
    "webapp": "web", "proxy": "web", "scanner": "vuln", "recon": "recon",
    "fingerprint": "recon", "exploitation": "exploit", "backdoor": "post",
    "tunnel": "post", "keylogger": "post", "cracker": "passwords",
    "wordlist": "passwords", "windows": "windows", "networking": "network",
    "sniffer": "network", "spoof": "network", "voip": "network", "dos": "exploit",
    "misc": "utils", "automation": "utils", "forensic": "forensics",
    "anti-forensic": "forensics", "fuzzer": "reverse", "binary": "reverse",
    "reversing": "reverse", "decompiler": "reverse", "disassembler": "reverse",
    "debugger": "reverse", "code-audit": "reverse", "malware": "reverse",
    "packer": "reverse", "firmware": "mobile", "crypto": "crypto", "stego": "crypto",
    "wireless": "wireless", "bluetooth": "wireless", "radio": "wireless",
    "nfc": "wireless", "drone": "mobile", "social": "social", "mobile": "mobile",
    "hardware": "mobile", "automobile": "mobile", "defensive": "defense",
    "honeypot": "defense", "ids": "defense", "threat-model": "defense",
    "database": "database", "ai": "ai",
}

# Native blue-team tools Linux-C.O.S installs itself (package-lists/blueteam-native)
NATIVE_DEFENSE = ["suricata", "suricata-update", "yara", "clamav", "aide", "lynis",
                  "rkhunter", "tiger", "wireshark", "tshark", "tcpdump", "osquery",
                  "wazuh-agent", "ufw", "gufw", "auditd", "fail2ban", "apparmor-utils"]
PARROT_NATIVE = [l.strip() for l in (ROOT / "build/config/package-lists/parrot-exclusive.list.chroot")
                 .read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]


# When a tool sits in several metapackages, the more specific category wins
# (recon/vuln are catch-alls that many tools are also listed under).
PRIORITY = ["exploit", "web", "passwords", "wireless", "social", "post", "windows",
            "database", "forensics", "reverse", "crypto", "network", "defense",
            "reporting", "mobile", "cloud", "ai", "recon", "vuln", "utils"]
OVERRIDES = {"nmap": "recon", "masscan": "recon", "zmap": "recon", "wireshark": "network",
             "tshark": "network", "tcpdump": "network", "nikto": "vuln", "gvm": "vuln",
             "lynis": "defense", "metasploit-framework": "exploit", "sqlmap": "web",
             "burpsuite": "web", "john": "passwords", "hashcat": "passwords",
             "hydra": "passwords", "bettercap": "network", "responder": "network",
             "enum4linux": "windows", "crackmapexec": "windows", "netexec": "windows",
             "bloodhound": "windows", "setoolkit": "social", "gophish": "social",
             "autopsy": "forensics", "volatility3": "forensics", "ghidra": "reverse",
             "radare2": "reverse", "cutter": "reverse", "gdb": "reverse"}


def load() -> dict[str, tuple[str, str, str]]:
    cand: dict[str, dict[str, list[tuple[str, str]]]] = {}  # tool -> source -> [(cat, group)]
    for src, path, mapping in (("kali", "kali-official-categories.json", KALI),
                               ("parrot", "parrot-official-categories.json", PARROT)):
        for meta, tl in json.loads((DATA / path).read_text()).items():
            if meta in mapping:
                for t in tl:
                    cand.setdefault(t, {}).setdefault(src, []).append((mapping[meta], meta))
    for t, grp in json.loads((DATA / "blackarch-tools-catalog.json").read_text()):
        cat = BLACKARCH.get(grp.removeprefix("blackarch-"), "utils")
        cand.setdefault(t, {}).setdefault("blackarch", []).append((cat, grp or "blackarch"))
    tools: dict[str, tuple[str, str, str]] = {}
    for t, srcs in cand.items():
        src = next(s for s in ("kali", "parrot", "blackarch") if s in srcs)
        cat, grp = min(srcs[src], key=lambda cg: PRIORITY.index(cg[0]))
        tools[t] = (OVERRIDES.get(t, cat), src, grp)
    for t in NATIVE_DEFENSE:
        tools[t] = (OVERRIDES.get(t, "defense"), "kali", "linux-cos-blueteam")
    tools.setdefault("cos-ai", ("ai", "cos", "linux-cos"))
    return {k: v for k, v in tools.items() if k and "\t" not in k}


def render() -> dict[str, str]:
    cats = "".join(f"{c[0]}\t{i}\t{c[1]}\t{c[2]}\t{c[3]}\t{c[4]}\n" for i, c in enumerate(CATEGORIES, 1))
    rows = "".join(f"{n}\t{c}\t{s}\t{g}\n" for n, (c, s, g) in sorted(load().items()))
    return {"categories.tsv": cats, "tools.tsv": rows}


def main() -> int:
    files = render()
    if "--check" in sys.argv:
        stale = [n for n, body in files.items() if not (OUT / n).exists() or (OUT / n).read_text() != body]
        if stale:
            print("stale: " + ", ".join(stale) + " -- run: python3 scripts/build-cos-catalog.py", file=sys.stderr)
            return 1
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n, body in files.items():
        (OUT / n).write_text(body)
    tools = load()
    by_src = {}
    for _, (_, s, _) in tools.items():
        by_src[s] = by_src.get(s, 0) + 1
    print(f"{len(tools)} tools, {len(CATEGORIES)} categories, by source: {by_src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
