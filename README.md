# Partners Workshop — Isolated Lab Environment

A self-contained Docker lab that simulates a small three-tier environment
(OS / Database / Web) for RankEZ **PAM + AIM + CLM** workshops. Each partner
gets a **partner ID** (1, 2, 3, …) that maps to a **unique subnet** and **unique
SSH ports**, with the web portal always published on host port **8080**.

> **Subnet rule:** partner **N** → subnet `10.1XX.0.0/24` where `XX = 100 + N`.
> Partner 1 → `10.101.0.0/24`, partner 2 → `10.102.0.0/24`, … (max N = 155).

## What's where

| Doc | Purpose |
|-----|---------|
| **[PREREQUISITES.md](PREREQUISITES.md)** | What you need installed *before* the workshop — attention, **attendees** |
| **[LAB-GUIDE.md](LAB-GUIDE.md)** | Architecture, RankEZ mapping, credentials, and the hands-on flow |
| **[DISTRIBUTION.md](DISTRIBUTION.md)** | How to ship this to partners (source / prebuilt / image-only offline) — for **organizers** |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common failures and fixes |

---

## Quick start

```bash
./init-lab.sh            # prompts: "Enter partner ID (1, 2, 3, ...):"
#  or pin it non-interactively:
./init-lab.sh 1

docker compose up -d --build
```

### Windows (PowerShell)

```powershell
.\init-lab.ps1            # prompts for the partner ID
#  or pin it non-interactively:
.\init-lab.ps1 1

docker compose up -d --build
```

If PowerShell blocks the script (default execution policy), run it once with
`powershell -ExecutionPolicy Bypass -File .\init-lab.ps1`, or relax the policy
for the current user with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

`init-lab.sh` writes `.env` (git-ignored — don't commit it) and a
`partner-${PARTNER_ID}.txt` cheat sheet (also git-ignored) and prints your
target map + credentials. See **[LAB-GUIDE.md](LAB-GUIDE.md)** for the full flow.

---

## Directory layout

```
partners-workshop/
├── README.md                   # this file
├── PREREQUISITES.md            # attendee pre-flight checklist
├── LAB-GUIDE.md                # architecture, credentials, hands-on flow
├── DISTRIBUTION.md             # shipping options (organizer-facing)
├── TROUBLESHOOTING.md          # common failures and fixes
├── docker-compose.yml          # three services + lab-net + named volumes
├── Dockerfile.proxy            # proxy-client: systemd + sshd + super/oper/root
├── Dockerfile.target-web       # target-web: sshd + Flask login-form app
├── entrypoint-web.sh           # target-web boot: write db-config.txt, start sshd + app
├── web-app/app.py              # Flask login + dashboard app; session login against the users table, reads /data/db-config.txt every request
├── init-sql/01_seed.sql        # seeds customer_db (customers + users + orders tables + grants)
├── init-lab.sh                 # prompts for partner ID, writes .env + cheat-sheet file
├── init-lab.ps1                # Windows PowerShell equivalent of init-lab.sh
├── .gitignore                  # ignores .env, partner-*.txt, tarballs, pycache
└── .env                        # created by init-lab.sh (do NOT commit)
```
