# Linux-C.O.S

**C**yber **O**ffensive & defensive **S**ecurity — a Debian/Kali-based security
Linux distribution (ISO). See [`build/README.md`](build/README.md) for the full
project description, status and architecture.

## What this repository produces

A bootable **Linux** operating system image (`build/output/*.iso`). The product
is an operating system in its own right (like Kali or Parrot): you boot it on
hardware or in a VM. It is not an application that "runs on" another OS, so the
cross-platform question here is about the **build host**, not the product.

## Build host — supported platforms

The ISO is assembled inside a Docker container (Debian + `live-build`), so the
build *host* can be any OS that runs Docker; the build itself always happens in
Linux inside that container.

| Build host | Support | Notes |
|------------|---------|-------|
| **Linux** | ✅ Full | Native. Docker with `--privileged` (live-build needs real chroot/mount). |
| **macOS** (Intel & Apple Silicon) | ✅ Full | Via Docker Desktop. `build/build.sh` is written to run from macOS. |
| **Windows** (10/11) | ✅ via Docker Desktop | Run `build/build.sh` from a WSL2 or Git-Bash shell, with Docker Desktop using the WSL2 backend. |

### Build

```sh
cd build
./build.sh        # builds the cos-builder image, then build/output/*.iso
```

> Requirements: Docker (privileged containers allowed), tens of GB of free disk
> and bandwidth, and over an hour of build time. Run it in the background and
> tail `build/output/build.log`.

## Running the result

Boot `build/output/live-image-amd64.hybrid.iso` on real hardware or in a VM
(VirtualBox, VMware, QEMU/KVM, or Hyper-V). As a Linux OS it then runs natively
on that machine regardless of which host you built it from.
