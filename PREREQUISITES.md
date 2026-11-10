# Prerequisites — RankEZ Partners Workshop

Everything an attendee needs **before** the workshop starts. Please verify each
item against the checklist at the bottom *ahead of time* so time isn't lost
debugging installations on the day.

---

## 1. Supported platforms

| Platform | Notes |
|----------|-------|
| **macOS** | Docker Desktop |
| **Windows** | Docker Desktop (WSL2 backend) + PowerShell, or WSL2 Ubuntu |
| **Linux** | Docker Engine + Compose plugin |

Anything that can run Docker Engine with the Compose v2 plugin works. The lab
itself is a set of containers; the host OS only needs to run Docker.

---

## 2. Software requirements

| Requirement | Version | Why |
|-------------|---------|-----|
| **Docker Engine** | 20.10+ | Runs the three lab containers |
| **Docker Compose** | v2 plugin (`docker compose`, *not* the legacy `docker-compose`) | Orchestrates the stack |
| **Shell** | Bash 4+ (macOS/Linux) **or** PowerShell (Windows) | Runs `init-lab.sh` / `init-lab.ps1` |
| **SSH client** | installed & on `PATH` | `ssh` to reach the proxy / web targets |
| **`curl`** | any recent version | quick smoke test |

- **Windows** ships an OpenSSH client by default (10.1803+). PowerShell handles
  the initializer; Bash is *not* required on Windows.
- **macOS / Linux** ship both `ssh` and `curl` already.

---

## 3. Network & ports

- **Internet access to Docker Hub** — the lab pulls two public images:
  `mysql:8.0` (~600 MB) and `ubuntu:22.04`. *(No Docker Hub access? Ask the
  organizer for the offline tarball — see DISTRIBUTION.md.)*
- **Free TCP ports on the host**:
  - `8080` — the web portal (published from the container's port 80).
  - `2200N` — SSH to the proxy target (`N` = your partner ID).
  - `2500N` — SSH to the web target (`N` = your partner ID).

  > A locally running dev server on `8080` is the most common clash — free it
  > up, or the web portal won't bind.

---

## 4. Suggested host resources

Modest — the stack is one small web app, one Linux box, and one MySQL instance.

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Disk free | ~2 GB | 4 GB+ (image pulls + named volumes) |
| RAM | 4 GB | 8 GB (Docker Desktop/WSL2 default works) |
| CPU | 2 cores | 4 cores |

---

## 5. Pre-flight verification checklist

Run these before the workshop and you're ready:

```bash
# 1. Docker present and running
docker version

# 2. Compose v2 (NOT the legacy v1 binary)
docker compose version          # ✅ "Docker Compose version v2.x.x"
                                # ❌ "command not found" → install Compose v2

# 3. SSH client on PATH
ssh -V

# 4. curl on PATH (macOS/Linux smoke test)
curl --version
```

On **Windows**, confirm in a PowerShell window:

```powershell
docker --version
docker compose version
ssh -V
```

---

## 6. If something is missing

| Symptom | Fix |
|---------|-----|
| `docker: command not found` | Install Docker Engine / Docker Desktop |
| `docker compose: command not found` | You have the legacy `docker-compose`; install the Compose **v2** plugin (`docker compose`) |
| `docker version` returns a client *and* a server error | Docker daemon isn't running — start Docker Desktop / `systemctl start docker` |
| Port 8080 already in use | Free it, or note it for the lab lead |

**Still stuck?** Contact the organizer before the session — don't wait to debug
on the day.
