# Lab Guide — Hands-On Walkthrough

The full workshop flow: what the lab demos, how it's laid out, and the exact
steps attendees take.

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

## 3. Verify it works (partner 1)

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

## 4. Lab credentials

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

## 5. Teardown & reset

```bash
docker compose down            # stop; keeps db-data + web-data volumes (DB persists)
docker compose down -v         # also WIPE volumes → truly fresh lab next run
./init-lab.sh                  # pick a new partner ID
docker compose up -d --build
```

---

## 6. Notes

- The cheat sheet labels the SSH target by its tier purpose (`Linux (SSH)`), while
  the container hostname is `proxy-client-${PARTNER_ID}` — the same box.
- **Full reset** needs `down -v`; plain `down` keeps DB contents and the generated
  `db-config.txt`, so a re-`up` resumes the same lab.
- No `HEALTHCHECK` is defined yet; consider adding one to `target-db` and
  `target-web` so `docker compose ps` reports healthy/starting status.
