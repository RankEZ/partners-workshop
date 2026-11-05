# Partners Workshop — Isolated Lab Environment

A self-contained Docker lab that simulates a small three-tier environment
(OS / Database / Web) for RankEZ **PAM + AIM + CLM** workshops. Each partner
gets a **partner ID** (1, 2, 3, …) that maps to a **unique subnet** and **unique
SSH ports**, with the web portal always published on host port **8080**.

> **Subnet rule:** partner **N** → subnet `10.1XX.0.0/24` where `XX = 100 + N`.
> Partner 1 → `10.101.0.0/24`, partner 2 → `10.102.0.0/24`, … (max N = 155).

```
                ┌───────────────────────────────────────────────┐
                │                 host machine                  │
                │  10.1XX.0.0/24  (lab-net-N,  one per partner) │
                │                                               │
   :2200N ◄─────┤  proxy-client-N    (10.1XX.0.10, sshd)        │
   :8080  ◄─────┤  target-web-N      (10.1XX.0.30, sshd+app)    │
   :2500N ◄─────┤  target-db-N       (10.1XX.0.20, MySQL 8)     │
                └───────────────────────────────────────────────┘
```

---

## 1. What it demos (the RankEZ mapping)

This lab is a **three-tier target** for a single RankEZ story:

| Tier | Container | What RankEZ manages |
|------|-----------|---------------------|
| **OS** | `proxy-client` (Linux SSH) | CPM rotates the `oper`/`super` account; SSH session brokering |
| **Database** | `target-db` (MySQL 8) | CPM rotates the `app_user` account |
| **Web** | `target-web` (login-form app + sshd) | **AIM** — the app reads its *service-account* DB credential from `/data/db-config.txt`, which CPM edits via **Account Usage Management (CPM-for-File)** on rotation; the human web login verifies a **separate `users` table** (portal accounts, not the DB account), and **RunApp / PSM** injects that portal credential into the login form |

The flow an attendee experiences:

1. **SSH into the proxy** as the `oper` account (CPM-rotated).
2. **Log in to the Web UI** — RunApp injects the portal `users`-table credential (e.g. `demo` / `RankEZ123!`) into the login form. On success the app opens a **separate `/dashboard` page** (customer data + logout button), a normal session-based login.
3. **Drill down** — every customer row is clickable and opens a `/customer/<id>` detail page (orders etc.); the navigation is what a **PSM session recording** captures end-to-end.
4. **Rotate `app_user`** — CPM writes the new password into `/data/db-config.txt` (CPM-for-File, handle account = the Linux `super` account you already manage), so the app keeps *connecting* to the DB with zero restart.

The **login account** (`users` table) and the **DB connection account** (`app_user`) are
deliberately separate: rotating the service account never touches portal logins, and a
portal login never exposes the DB password.

---

## 2. Architecture

| Role | Service | Container / Hostname | IP | Inside (host) |
|------|---------|----------------------|----|---------------|
| Proxy / SSH target | `proxy-client` | `proxy-client-${PARTNER_ID}` | `10.1XX.0.10` | 22 (`:2200N`) |
| Database | `target-db` (MySQL 8) | `target-db-${PARTNER_ID}` | `10.1XX.0.20` | 3306 (via tunnel) |
| Web app | `target-web` (login app + sshd) | `target-web-${PARTNER_ID}` | `10.1XX.0.30` | 80 (`:8080`) + 22 (`:2500N`) |

`XX = 100 + PARTNER_ID`, `N = PARTNER_ID`. All three share bridge network
`lab-net-${PARTNER_ID}` with subnet `10.1XX.0.0/24`.

**Web app porting:** the app listens on **80 inside** the container and is
published to **8080** on the host, so partners open `http://<host-ip>:8080` from
their laptop.

---

## 3. Prerequisites (what the partner needs)

- **Docker Engine** 20.10+ with the **Compose v2** plugin (`docker compose`, not `docker-compose`).
- **Bash 4+** and `curl` (for the quick smoke test).
- **Internet access to Docker Hub** to pull the two public base images (`mysql:8.0`, `ubuntu:22.04`).
- Free **TCP ports** on the host: `8080` (web) plus `2200N` and `2500N` (where `N` = the partner ID).

---

## 4. Distributing this to partners

There are three ways to hand the lab over. **Source is the default** — the two
custom images are tiny, and the two large base images are already public.

### 4.1 Source repo / tarball (recommended)

Ship the whole directory (`git clone` / archive). The partner runs:

```bash
./init-lab.sh          # prompts for their partner ID (or: ./init-lab.sh 3)
docker compose up -d --build
```

- `--build` builds the two local images (`Dockerfile.proxy`, `Dockerfile.target-web`)
  — a few seconds each — and pulls `mysql:8.0` + `ubuntu:22.04` from Docker Hub.
- Partners can read/modify the app, credentials, and Dockerfiles — full transparency.
- Every partner enters their own **ID** → isolated subnet and SSH ports.

### 4.2 Prebuilt images (for partners who can't / shouldn't build)

If a partner must *pull* rather than build, build + push the **two custom images**
to a registry they can reach, then ship a `docker-compose.yml` that references
`image:` instead of `build:`:

```bash
# on your side, once:
docker build -f Dockerfile.proxy     -t yourregistry.example/rankez/proxy-client:v1 .
docker build -f Dockerfile.target-web -t yourregistry.example/rankez/target-web:v1 .
docker push yourregistry.example/rankez/proxy-client:v1
docker push yourregistry.example/rankez/target-web:v1
```

Then swap the two `build:` blocks for `image:` in `docker-compose.yml` (drop
`context`/`dockerfile`). They still pull `mysql:8.0` + `ubuntu:22.04` from Docker
Hub unless you mirror those too.

### 4.3 Fully offline / air-gapped

If the partner has **no Docker Hub access**, hand over tarballs:

```bash
# on your side:
docker pull mysql:8.0 ubuntu:22.04
docker build -f Dockerfile.proxy      -t partners-workshop-proxy-client .
docker build -f Dockerfile.target-web -t partners-workshop-target-web .
docker save mysql:8.0 ubuntu:22.04 \
            partners-workshop-proxy-client partners-workshop-target-web \
  | gzip > partners-workshop-images.tar.gz
```

```bash
# on the partner's side:
docker load < partners-workshop-images.tar.gz
./init-lab.sh && docker compose up -d   # no --build, images already present
```

> Note: `mysql:8.0` is ~600 MB, so this tarball is large (~700 MB+ gzipped). Prefer
> 4.1 or 4.2 whenever the partner has normal Docker Hub access.

---

## 5. Quick start

```bash
./init-lab.sh            # prompts: "Enter partner ID (1, 2, 3, ...):"
#  or pin it non-interactively:
./init-lab.sh 1

docker compose up -d --build
```

### Windows (PowerShell)

Use the PowerShell initializer instead — identical behaviour and output:

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
`partner-${PARTNER_ID}.txt` cheat sheet (also git-ignored):

```
PARTNER_ID=1
LAB_SUBNET=10.101.0
SSH_HOST_PORT=22001
WEB_HOST_PORT=8080
SSH_WEB_HOST_PORT=25001
```

and prints the target map:

```
 Partner Lab #1  ->  subnet 10.101.0.0/24

 Target Type       Target IP          Service Port
 Linux (SSH)       10.101.0.10        22 (SSH)
 Database (MySQL)  10.101.0.20        3306
 Web Portal        10.101.0.30        80 (HTTP)
```

### 5.1 Verify it works (partner 1)

```bash
docker compose ps
# proxy-client-1  Up   ...  0.0.0.0:22001->22/tcp
# target-db-1     Up   ...  3306/tcp
# target-web-1    Up   ...  0.0.0.0:8080->80/tcp, 0.0.0.0:25001->22/tcp

curl -s http://127.0.0.1:8080/health
# OK (config-file credential valid, 3 customer rows)

# Login (normal session flow): POST /login, follow the redirect, then hit /dashboard
curl -s -c /tmp/cj -X POST -d 'username=demo&password=RankEZ123!' \
     -L http://127.0.0.1:8080/login
# ... redirects to /dashboard, which lists Acme Corp / Globex Industries / Initech

ssh -p 22001 super@127.0.0.1      # password RankEZ123!
```

(Give MySQL ~15–20 s after first boot to initialize before the `/health` check.)

---

## 6. Lab credentials

| Target | Value | Notes |
|--------|-------|-------|
| Linux users (`proxy-client` **and** `target-web`) | `super` / `oper` / `root`, password `RankEZ123!` | `super` = passwordless `sudo`, the CPM-for-File handle account |
| MySQL root | `DBRootPassword123!` | |
| MySQL app user | `app_user` / `AppPassword123!` | **service account** — the app's own DB connection (rotated via CPM-for-File); NOT a login account |
| MySQL database | `customer_db` | seeded by `init-sql/01_seed.sql` — `customers`, `users`, and `orders` tables + grants |
| Portal login accounts | `demo` / `RankEZ123!`  and `admin` / `Admin@Demo1` | **`users` table** — the human web-login identities (separate from `app_user`) |
| Auth plugin | `mysql_native_password` | |
| Web app | Flask session login at `/login` → redirect to `/dashboard` (customer data + **Log out**) | reads DB creds from `/data/db-config.txt`; passwords stored as salted SHA-256 |

### Connecting through the proxy (the intended attendee path)

The **database** is not exposed on host ports — reach it by SSH-tunnelling through
`proxy-client`, exactly as a real proxied session would (the web app is directly
reachable at `http://<host-ip>:8080`):

```bash
ssh -p 2200N \
    -L 13306:target-db-N:3306 \
    -L 18080:target-web-N:80 \
    super@127.0.0.1
# then: mysql -h 127.0.0.1 -P 13306 -u app_user -p
#       open http://127.0.0.1:18080
```

`WEB_HOST_PORT` (8080) is the laptop-facing web URL; the *demo* path for the
attendee is via the proxy / RunApp. (`N` = partner ID.)

---

## 7. Directory layout

```
partners-workshop/
├── docker-compose.yml         # three services + lab-net + named volumes
├── Dockerfile.proxy           # proxy-client: systemd + sshd + super/oper/root
├── Dockerfile.target-web      # target-web: sshd + Flask login-form app
├── entrypoint-web.sh          # target-web boot: write db-config.txt, start sshd + app
├── web-app/app.py             # Flask login + dashboard app; session login against the users table, reads /data/db-config.txt every request
├── init-sql/01_seed.sql       # seeds customer_db (customers + users + orders tables + grants)
├── init-lab.sh                # prompts for partner ID, writes .env + cheat-sheet file
├── init-lab.ps1               # Windows PowerShell equivalent of init-lab.sh
├── .gitignore                 # ignores .env, partner-*.txt, tarballs, pycache
├── .env                       # created by init-lab.sh (do NOT commit)
└── README.md
```

---

## 8. Teardown & reset

```bash
docker compose down            # stop; keeps db-data + web-data volumes (DB persists)
docker compose down -v         # also WIPE volumes → truly fresh lab next run
./init-lab.sh                  # pick a new partner ID
docker compose up -d --build
```

---

## 9. Troubleshooting

- **`docker compose: command not found`** — you have the v1 `docker-compose`
  binary; install the Compose **v2** plugin (`docker compose`).
- **Port already in use** — pick a different partner ID so `2200N`/`2500N` are
  free; the web portal needs host port **8080** free (clash with a local dev
  server is the common one).
- **Subnet / ID range** — partner ID must be **1 ≤ N ≤ 155** (third octet
  `100 + N` must stay ≤ 255). `init-lab.sh` rejects non-integers and out-of-range
  IDs with a clear message.
- **MySQL auth errors (`Access denied` / plugin mismatch)** — the DB container
  forces `mysql_native_password`; ensure your client isn't forcing
  `caching_sha2_password`.
- **`/health` fails right after boot** — MySQL is still initializing; wait ~15–20 s
  and retry (`docker logs target-db-${PARTNER_ID}` for progress).
- **proxy-client installer fails (`crontab`/`systemctl` not found)** — the
  `proxy-client` image now runs **systemd** as PID 1 and ships `cron`, so both
  commands exist; rebuild the image if you're on an older copy.

---

## 10. Notes

- The cheat sheet labels the SSH target by its tier purpose (`Linux (SSH)`), while
  the container hostname is `proxy-client-${PARTNER_ID}` — the same box.
- **Full reset** needs `down -v`; plain `down` keeps DB contents and the generated
  `db-config.txt`, so a re-`up` resumes the same lab.
- No `HEALTHCHECK` is defined yet; consider adding one to `target-db` and
  `target-web` so `docker compose ps` reports healthy/starting status.