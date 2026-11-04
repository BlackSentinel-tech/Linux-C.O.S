#!/usr/bin/env python3
"""Build website/assets/data/tools.json from the raw catalogs in data/.

One entry per tool name, merged across sources, so a tool shipped by Kali,
Parrot *and* BlackArch is listed once with all three badges.

Output (compact, ~90 KB):
    {
      "generated": "...",
      "sources": ["kali", "parrot", "blackarch"],
      "categories": ["Information Gathering", ...],
      "counts": {"kali": n, "parrot": n, "blackarch": n, "total": n},
      "tools": [[name, sourceBits, categoryIndex(, url)], ...]
    }
sourceBits: 1 = Kali, 2 = Parrot, 4 = BlackArch (in the container).

    python3 scripts/build-website-data.py          # rewrite
    python3 scripts/build-website-data.py --check  # exit 1 if stale (CI)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "website/assets/data/tools.json"

KALI, PARROT, BLACKARCH = 1, 2, 4

# Kali metapackage -> display category (also the canonical category list)
KALI_CATS = {
    "kali-tools-information-gathering": "Information Gathering",
    "kali-tools-vulnerability": "Vulnerability Analysis",
    "kali-tools-web": "Web Applications",
    "kali-tools-database": "Database Assessment",
    "kali-tools-passwords": "Password Attacks",
    "kali-tools-wireless": "Wireless",
    "kali-tools-802-11": "Wireless",
    "kali-tools-bluetooth": "Bluetooth",
    "kali-tools-rfid": "RFID & NFC",
    "kali-tools-sdr": "Software Defined Radio",
    "kali-tools-reverse-engineering": "Reverse Engineering",
    "kali-tools-exploitation": "Exploitation",
    "kali-tools-social-engineering": "Social Engineering",
    "kali-tools-sniffing-spoofing": "Sniffing & Spoofing",
    "kali-tools-post-exploitation": "Post Exploitation",
    "kali-tools-forensics": "Forensics",
    "kali-tools-reporting": "Reporting",
    "kali-tools-identify": "Defense: Identify",
    "kali-tools-protect": "Defense: Protect",
    "kali-tools-detect": "Defense: Detect",
    "kali-tools-respond": "Defense: Respond",
    "kali-tools-recover": "Defense: Recover",
    "kali-tools-crypto-stego": "Crypto & Stego",
    "kali-tools-fuzzing": "Fuzzing",
    "kali-tools-gpu": "Hardware & GPU",
    "kali-tools-hardware": "Hardware & GPU",
    "kali-tools-voip": "VoIP",
    "kali-tools-windows-resources": "Windows & Active Directory",
}

PARROT_CATS = {
    "parrot-tools-ai": "AI",
    "parrot-tools-infogathering": "Information Gathering",
    "parrot-tools-vuln": "Vulnerability Analysis",
    "parrot-tools-web": "Web Applications",
    "parrot-tools-pwn": "Exploitation",
    "parrot-tools-maintain": "Post Exploitation",
    "parrot-tools-postexploit": "Post Exploitation",
    "parrot-tools-password": "Password Attacks",
    "parrot-tools-wireless": "Wireless",
    "parrot-tools-sniff": "Sniffing & Spoofing",
    "parrot-tools-forensics": "Forensics",
    "parrot-tools-automotive": "Automotive",
    "parrot-tools-reversing": "Reverse Engineering",
    "parrot-tools-reporting": "Reporting",
    "parrot-tools-cloud": "Cloud",
}

# BlackArch group -> display category (unlisted groups map via title-case)
BLACKARCH_CATS = {
    "webapp": "Web Applications", "scanner": "Vulnerability Analysis",
    "recon": "Information Gathering", "exploitation": "Exploitation",
    "cracker": "Password Attacks", "windows": "Windows & Active Directory",
    "networking": "Networking", "misc": "General", "fuzzer": "Fuzzing",
    "forensic": "Forensics", "sniffer": "Sniffing & Spoofing",
    "spoof": "Sniffing & Spoofing", "wireless": "Wireless",
    "bluetooth": "Bluetooth", "reversing": "Reverse Engineering",
    "disassembler": "Reverse Engineering", "decompiler": "Reverse Engineering",
    "debugger": "Reverse Engineering", "binary": "Reverse Engineering",
    "crypto": "Crypto & Stego", "stego": "Crypto & Stego",
    "social": "Social Engineering", "voip": "VoIP", "database": "Database Assessment",
    "backdoor": "Post Exploitation", "keylogger": "Post Exploitation",
    "malware": "Malware Analysis", "defensive": "Defense: Protect",
    "ids": "Defense: Detect", "anti-forensic": "Forensics",
    "automation": "Automation", "proxy": "Networking", "tunnel": "Networking",
    "dos": "Denial of Service", "hardware": "Hardware & GPU",
    "radio": "Software Defined Radio", "nfc": "RFID & NFC",
    "mobile": "Mobile", "code-audit": "Code Audit", "fingerprint": "Information Gathering",
    "honeypot": "Defense: Detect", "threat-model": "Reporting",
    "firmware": "Hardware & GPU", "dump": "Forensics", "packer": "Reverse Engineering",
    "drone": "Hardware & GPU", "automobile": "Automotive", "gpu": "Hardware & GPU",
    "unpacker": "Reverse Engineering", "analysis": "Malware Analysis",
    "wordlist": "Password Attacks", "nfc-tools": "RFID & NFC", "ai": "AI",
}


def load(name: str):
    return json.loads((DATA / name).read_text())


def build() -> dict:
    tools: dict[str, dict] = {}

    def add(name: str, bit: int, cat: str | None, url: str = "") -> None:
        name = name.strip()
        if not name or " " in name:  # skip scraped headings like "Kali Tools TOP-100"
            return
        t = tools.setdefault(name, {"bits": 0, "cat": None, "url": ""})
        t["bits"] |= bit
        if cat and not t["cat"]:
            t["cat"] = cat
        if url and not t["url"]:
            t["url"] = url

    # Kali: official metapackage lists carry the real categories
    for meta, names in load("kali-official-categories.json").items():
        for n in names:
            add(n, KALI, KALI_CATS.get(meta), f"https://www.kali.org/tools/{n}/")
    # Kali: the scraped catalog has many more tools, with unreliable categories
    for name, _cat, url in load("kali-tools-catalog.json"):
        add(name, KALI, None, url)

    for meta, names in load("parrot-official-categories.json").items():
        for n in names:
            add(n, PARROT, PARROT_CATS.get(meta))

    for name, group in load("blackarch-tools-catalog.json"):
        g = group.removeprefix("blackarch-")
        cat = BLACKARCH_CATS.get(g, g.replace("-", " ").title())
        add(name, BLACKARCH, cat,
            f"https://github.com/BlackArch/blackarch/tree/master/packages/{name}")

    for t in tools.values():
        t["cat"] = t["cat"] or "General"

    categories = sorted({t["cat"] for t in tools.values()})
    idx = {c: i for i, c in enumerate(categories)}
    def default_url(name: str, bits: int) -> str:
        if bits & KALI:
            return f"https://www.kali.org/tools/{name}/"
        if bits & BLACKARCH:
            return f"https://github.com/BlackArch/blackarch/tree/master/packages/{name}"
        return ""

    # the URL is only stored when it differs from what the site derives
    # itself (website/assets/js/tools.js: toolUrl) -- keeps the file small
    rows = []
    for n, t in sorted(tools.items(), key=lambda kv: kv[0].lower()):
        url = t["url"]
        if url.rstrip("/") == default_url(n, t["bits"]).rstrip("/"):
            url = ""
        rows.append([n, t["bits"], idx[t["cat"]], url] if url else [n, t["bits"], idx[t["cat"]]])
    counts = {
        "kali": sum(1 for t in tools.values() if t["bits"] & KALI),
        "parrot": sum(1 for t in tools.values() if t["bits"] & PARROT),
        "blackarch": sum(1 for t in tools.values() if t["bits"] & BLACKARCH),
        "total": len(tools),
    }
    return {
        "sources": ["kali", "parrot", "blackarch"],
        "categories": categories,
        "counts": counts,
        "tools": rows,
    }


def main() -> int:
    text = json.dumps(build(), separators=(",", ":"), ensure_ascii=False) + "\n"
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT.relative_to(ROOT)} is stale -- run: python3 scripts/build-website-data.py")
            return 1
        print("website tool data is in sync")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    d = json.loads(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {d['counts']} across {len(d['categories'])} categories, "
          f"{len(text) // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
