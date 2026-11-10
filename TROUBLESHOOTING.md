# Troubleshooting

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
