# Linux-C.O.S user guide

**C**yber **O**ffensive & defensive **S**ecurity. Kali's and Parrot's tools
installed natively, BlackArch's tools in a container, a blue-team stack, and
an OS that is hardened by default.

> Quick start in a terminal: `cos-help` (Spanish: `cos-help --es`).
> The full bilingual guide (English/Español) opens from **Linux-C.O.S → User
> Guide** in the applications menu, or `cos-help guide`; it works offline.

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
    Your container is kept between sessions, so installed tools stay until
    `blackarch-shell --reset`.

## 3. Defensive stack

Running out of the box: **AppArmor** (enforcing), **auditd** (identity, sudo,
sshd and exec rules), **ClamAV** signature updates, **ufw** firewall (set up
before the network comes up), kernel/sysctl hardening.

Installed but off or not configured yet:

* **Suricata**: `sudo systemctl enable --now suricata` when this box should
  watch a network segment.
* **wazuh-agent**: not enrolled -- set the manager address in
  `/var/ossec/etc/ossec.conf`, then `sudo systemctl enable --now wazuh-agent`
  (see `/opt/linux-cos/blueteam-stacks/wazuh/README.md`).
* **AIDE**: build its baseline once, on a system you trust:
  `sudo aideinit` (takes a while), then `sudo aide --check` later.
* **osquery**: `sudo osqueryi` for ad-hoc queries.

Good to know: members of the `docker` group (the live user and the user you
create in the installer) can get root through Docker -- that is how
`blackarch-shell` and `cos-stacks` work without sudo.

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

Every web UI and API listens on `127.0.0.1` only: ports published by Docker
bypass ufw, so binding to all interfaces would expose them to the network.
The one exception is Wazuh's agent ports (1514/1515), so agents can enroll.

Passwords: MISP's are generated at random on the first `up` (see
`cos-stacks creds misp`). TheHive and Wazuh start with their upstream
first-login defaults -- `cos-stacks creds <stack>` shows them; change them on
first login.

## 4. Installing to disk

The installer (Calamares) offers ext4, btrfs or xfs, and **LUKS2 full-disk
encryption** -- tick "Encrypt system" on the partitioning page. Requirements:
60 GB of disk, 2 GB of RAM (4 GB+ recommended). The installer also asks for a
separate root password.

**"Erase disk" erases everything on that disk, including Windows.** To keep
another system, choose "Install alongside" or manual partitioning, and back
up first.

On the first boot of the installed system `linux-cos-firstboot` enables the
firewall before the network starts, and `linux-cos-blackarch-pull` then loads
(or downloads, in the background) the BlackArch image:
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
