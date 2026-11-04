# Linux-C.O.S user guide

**C**yber **O**ffensive & defensive **S**ecurity. Kali's and Parrot's tools
installed natively, BlackArch's tools in a container, a blue-team stack, and
an OS that is hardened by default.

> Quick start in a terminal: `cos-help` (Spanish: `cos-help --es`).
> Everything below is also in the **Linux-C.O.S** folder of the applications
> menu.

---

## 1. Live session

| | |
|---|---|
| User / password | `kali` / `kali` (autologin is on) |
| Persistence | none -- everything is lost at shutdown |
| Firewall | ufw, default deny incoming, enabled at boot |
| Install to disk | double-click **Install Linux-C.O.S** on the desktop |

The live session never downloads the BlackArch image by itself (it would
fill your RAM). Run `blackarch-shell --update` if you really want it there.

## 2. Offensive tools

* **Kali + Parrot (native):** every `kali-tools-*` category plus the
  Parrot-only extras. Find them in the applications menu, or list them:
  `apt list --installed 'kali-tools-*'`.
* **BlackArch (container):** `blackarch-shell` opens a shell with
  BlackArch's tools. Your home directory is mounted at the same path inside.
  * `blackarch-shell nmap -h` runs a single command.
  * `blackarch-shell --status` / `--update` / `--help`.
  * Inside: `pacman -Ss <name>` to search, `pacman -S <name>` to install.

## 3. Defensive stack

Running out of the box: **AppArmor** (enforcing), **auditd** (identity, sudo,
sshd and exec rules), **ClamAV** signature updates, **ufw** firewall,
**wazuh-agent**, kernel/sysctl hardening.

Installed but off (enable when this box should watch a network):
`sudo systemctl enable --now suricata`.

Installed on demand: `sudo apt install falco sysdig` -- both build a kernel
driver, which only works on the running system, never at build time.

### Heavy platforms: `cos-stacks`

| Stack | What | Web UI |
|---|---|---|
| `thehive-cortex` | case management + IOC analysis | http://localhost:9000 / :9001 |
| `misp` | threat-intelligence sharing | https://localhost:8443 |
| `wazuh` | full SIEM (manager + indexer + dashboard) | https://localhost |

```
cos-stacks                 # interactive menu
cos-stacks list            # status of every stack
cos-stacks up misp         # start (first run generates random passwords)
cos-stacks creds misp      # show them
cos-stacks logs misp       # follow logs
cos-stacks down misp       # stop (data is kept)
```

Every web UI listens on `127.0.0.1` only: ports published by Docker bypass
ufw, so binding to all interfaces would expose them to the network.

## 4. Installing to disk

The installer (Calamares) offers ext4, btrfs or xfs, and **LUKS2 full-disk
encryption** -- tick "Encrypt system" on the partitioning page. Requirements:
20 GB of disk, 2 GB of RAM (4 GB+ recommended).

On the first boot of the installed system `linux-cos-firstboot` enables the
firewall and loads (or downloads, in the background) the BlackArch image:
`journalctl -u linux-cos-firstboot -u linux-cos-blackarch-pull`.

## 5. Hardening reference

| File | What |
|---|---|
| `/etc/sysctl.d/99-linux-cos-hardening.conf` | network + kernel sysctls |
| `/etc/audit/rules.d/linux-cos.rules` | auditd ruleset |
| `/etc/ssh/sshd_config.d/99-linux-cos.conf` | sshd defaults (sshd itself is off) |
| `/etc/apt/apt.conf.d/50unattended-upgrades-linux-cos` | opt-in auto-updates (`sudo dpkg-reconfigure -plow unattended-upgrades`) |

## 6. Help & bugs

* Project: https://github.com/BlackSentinel-tech/Linux-C.O.S
* Report a bug: https://github.com/BlackSentinel-tech/Linux-C.O.S/issues
