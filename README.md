## Super Protocol VM Downloader Daemon – Build & Run Guide

This document explains how to **build**, **package (.deb)** and **run** the `sp-vm-downloader-daemon`, which is responsible for downloading and caching Super Protocol VM images.

All instructions target a Debian-based Linux distribution (Ubuntu, Debian, etc.).

---

## 1. Repositories & Layout

- Downloader daemon repo: https://github.com/Super-Protocol/sp-vm-downloader-daemon
- Watchdog daemon repo:  https://github.com/Super-Protocol/sp-vm-watchdog-daemon
- VM image repo: https://github.com/Super-Protocol/sp-vm

The daemons are designed to be installed as system services and communicate over a UNIX socket:

- Images stored under: `/var/lib/sp/images`
- Watchdog VM cache: `/var/lib/sp/watchdog/cache`
- Watchdog runtime data (pids, logs): `/var/run/sp/watchdog/vms`
- Downloader gRPC socket: `/var/run/sp-vm-downloader.sock`

---

## 2. Prerequisites

On a build host you will need:

- Python 3 (3.10+ recommended)
- `python3-venv`
- `git`
- `make`
- `dpkg-deb`
- A Debian-based system (for `.deb` packaging)

Install base tools:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv git make dpkg-dev
```

---

## 3. Building From Source (Without .deb)

### 3.1. Local Run

```bash
cd sp-vm-downloader-daemon

# Create venv, generate protobuf, install deps and run once
make run ARGS="--log-level INFO --onetime"
```

Useful `main.py` arguments:

- `--update-time HH:MM` – schedule time when daemon checks for new releases (default `00:00`)
- `--keep-versions N` – how many previous versions should be kept (default `3`)
- `--log-level LEVEL` – logging level (`INFO`, `DEBUG`, etc.)
- `--onetime` – run a single update cycle and exit (no scheduler)

Typical long‑running command (foreground):

```bash
cd sp-vm-downloader-daemon
make run ARGS="--log-level INFO"
```

This will:

- Create the virtualenv under `build/`
- Generate gRPC client/server stubs from `sp_vm_downloader.proto`
- Start the gRPC server listening on `unix:///var/run/sp-vm-downloader.sock`
- Download and cache VM releases under `/var/lib/sp/images`

> **Note:** in production the daemon should run as **root** (file permissions under `/var/lib/sp`, `/var/run`, etc). For local testing you can run it with `sudo make run ...`.

---

## 4. Building .deb Package

The packaging flow is handled by the `Makefile`.

```bash
cd sp-vm-downloader-daemon

# VERSION is used in the package name: sp-vm-downloader-daemon_<VERSION>-1_amd64.deb
make clean
make VERSION=1.0.0
```

This will:

- Initialize the `lib/sp-vm-proto` submodule
- Create a virtualenv in `build/sp-vm-downloader-daemon_<VERSION>-1_amd64/usr/bin/sp-vm-downloader-daemon`
- Install Python dependencies from:
  - `app/requirements.txt`
  - `app/lint_requirements.txt`
- Generate gRPC Python modules into `app/modules/proto`
- Assemble a Debian package tree:
  - `DEBIAN/control` (from `misc/control` via `envsubst`)
  - `DEBIAN/postinst`, `DEBIAN/prerm`, `DEBIAN/postrm`
  - `etc/systemd/system/sp-vm-downloader-daemon.service`
  - `usr/bin/sp-vm-downloader-daemon/app`
- Build `.deb` with `dpkg-deb --build --root-owner-group`

The resulting package will be:

```bash
build/sp-vm-downloader-daemon_1.0.0-1_amd64.deb
```

---

## 5. Installing the .deb Package

Copy the `.deb` file to the target host and install:

```bash
cd /path/to/packages
sudo dpkg -i sp-vm-downloader-daemon_1.0.0-1_amd64.deb
```

The `postinst` script and systemd unit will:

- Register the service: `sp-vm-downloader-daemon.service`
- Place code and the virtualenv under `/usr/bin/sp-vm-downloader-daemon`
- Ensure runtime directories exist under `/var/run` and `/var/lib/sp/images`

Enable the service on boot (if not already enabled by `postinst`):

```bash
sudo systemctl enable sp-vm-downloader-daemon
```

Start it:

```bash
sudo systemctl start sp-vm-downloader-daemon
```

Check status:

```bash
sudo systemctl status sp-vm-downloader-daemon
```

---

## 6. Configuration & CLI

The downloader daemon is configured via CLI arguments only (no separate config file):

- `--update-time HH:MM` – time of day when the daemon checks for a new GitHub release (default `00:00`)
- `--keep-versions N` – how many previous releases to retain on disk (default `3`)
- `--log-level LEVEL` – log level (`INFO`, `DEBUG`, etc.)
- `--onetime` – perform a single check/download cycle and exit

Persistent storage layout:

- `/var/lib/sp/images/<release-name>/` – VM release directory:
  - `vm.json`
  - `sp-vm-<release-name>.img`
  - `vmlinuz`
  - `OVMF.fd` / `OVMF_AMD.fd`
  - `rootfs_hash.txt`
- `/var/lib/sp/images/latest` – marker of the latest release (managed by `LocalStorage`)

---

## 7. Runtime Management & Diagnostics

### 7.1. Service Management

```bash
# Start service
sudo systemctl start sp-vm-downloader-daemon

# Stop service
sudo systemctl stop sp-vm-downloader-daemon

# Restart service
sudo systemctl restart sp-vm-downloader-daemon

# Enable on boot
sudo systemctl enable sp-vm-downloader-daemon
```

### 7.2. Logs

```bash
sudo journalctl -u sp-vm-downloader-daemon -f
```

### 7.3. Verifying Image Cache

```bash
ls -la /var/lib/sp/images/
ls -la /var/lib/sp/images/<release-name>/
cat /var/lib/sp/images/<release-name>/vm.json
```

You should see:

- Release directories (`build-XXX` or similar)
- A valid `vm.json` and artifacts inside each release directory

---

## 8. Interaction with Watchdog Daemon

The watchdog daemon uses the downloader daemon via a UNIX gRPC socket at `/var/run/sp-vm-downloader.sock`.

The downloader exposes:

- `GetRelease(name)` – returns a local path for a specific release, downloading it from StorJ/GitHub if needed
- `GetLatestGithubReleaseName()` – returns the latest GitHub release name for the VM image

The watchdog’s `image_manager` then uses the returned release path to locate:

- Rootfs image
- Kernel (`vmlinuz`)
- BIOS images (`OVMF.fd`, `OVMF_AMD.fd`)
- Rootfs hash (`rootfs_hash.txt`)

In a typical setup, you run:

1. `sp-vm-downloader-daemon` to cache images
2. `sp-vm-watchdog-daemon` to start and maintain VMs based on those images

---

## 9. Using a Separate Data Disk for Images

By default, VM images are stored under `/var/lib/sp/images`.
If you have a large data disk mounted at `/data` and want to store images under `/data/vm/images`, you can use a symlink.

Example:

```bash
sudo mkdir -p /data/vm/images

# (optional) move existing images to the new location
sudo rsync -a /var/lib/sp/images/ /data/vm/images/

# replace the original directory with a symlink
sudo rm -rf /var/lib/sp/images
sudo ln -s /data/vm/images /var/lib/sp/images
```

After this, the downloader daemon will continue to use `/var/lib/sp/images` as before,
but all actual data will be stored on the larger `/data` disk.

