#!/usr/bin/env bash
set -e

# ---------------------------------------------------------------------------
# Partner lab initializer.
#   ./init-lab.sh 7        -> non-interactive (partner 7)
#   ./init-lab.sh          -> prompts for the partner ID
# Partner 1 -> subnet 10.101.0.0/24, partner 2 -> 10.102.0.0/24, etc.
# ---------------------------------------------------------------------------

# Partner ID: from $1, or prompted
if [ -n "$1" ]; then
  PARTNER_ID="$1"
else
  read -r -p "Enter partner ID (1, 2, 3, ...): " PARTNER_ID
fi

# Validate: a positive integer whose derived subnet octet fits in 0-255
case "$PARTNER_ID" in
  ''|*[!0-9]*)
    echo "ERROR: partner ID must be a positive integer (e.g. 1, 2, 3)." >&2
    exit 1
    ;;
esac
if [ "$PARTNER_ID" -lt 1 ]; then
  echo "ERROR: partner ID must be >= 1." >&2
  exit 1
fi

# Subnet third octet = 100 + partner ID  (1 -> 101, 2 -> 102, ...)
SUBNET_OCTET=$((100 + PARTNER_ID))
if [ "$SUBNET_OCTET" -gt 255 ]; then
  echo "ERROR: partner ID $PARTNER_ID -> subnet 10.${SUBNET_OCTET}.0.0/24 is out of range (max ID 155)." >&2
  exit 1
fi
LAB_SUBNET="10.${SUBNET_OCTET}.0"

# Host convenience ports (for direct local testing only)
SSH_HOST_PORT=$((22000 + PARTNER_ID))     # proxy-client SSH
WEB_HOST_PORT=8080                        # target-web HTTP — fixed conventional port (80 inside)
SSH_WEB_HOST_PORT=$((25000 + PARTNER_ID)) # target-web SSH (CPM-for-File)

# ---------------------------------------------------------------------------
# Preflight: fail clearly before the partner has to debug Docker internals
# ---------------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || {
  echo "ERROR: 'docker' not found in PATH. Install Docker Engine first." >&2
  exit 1
}
docker compose version >/dev/null 2>&1 || {
  echo "ERROR: 'docker compose' (v2 plugin) not found. Install Docker Compose v2." >&2
  exit 1
}

# Write out the .env file for docker-compose
cat <<EOF > .env
PARTNER_ID=${PARTNER_ID}
LAB_SUBNET=${LAB_SUBNET}
SSH_HOST_PORT=${SSH_HOST_PORT}
WEB_HOST_PORT=${WEB_HOST_PORT}
SSH_WEB_HOST_PORT=${SSH_WEB_HOST_PORT}
EOF

# Write a keep-it-handy file with targets + passwords (partners forget these)
INFO_FILE="partner-${PARTNER_ID}.txt"
cat <<EOF > "${INFO_FILE}"
==========================================================
 RankEZ Partner Lab #${PARTNER_ID}   subnet ${LAB_SUBNET}.0/24
==========================================================

Targets (inside the lab network):
  Linux (SSH)       ${LAB_SUBNET}.10   port 22   (SSH)
  Database (MySQL)  ${LAB_SUBNET}.20   port 3306
  Web Portal        ${LAB_SUBNET}.30   port 80   (HTTP)

Local test access (from the host):
  SSH        ssh super@127.0.0.1 -p ${SSH_HOST_PORT}
  Web        http://127.0.0.1:${WEB_HOST_PORT}
  Web SSH    ssh super@127.0.0.1 -p ${SSH_WEB_HOST_PORT}

Credentials:
  Linux users : super / oper / root
  Linux pass  : RankEZ123!
  MySQL root  : DBRootPassword123!
  MySQL app   : app_user / AppPassword123!   (db: customer_db; app->DB service account)
  Web logins  : demo / RankEZ123!  and  admin / Admin@Demo1  (portal users table)
==========================================================
EOF

# Display the target map: IP + service port per tier
echo "=========================================================="
echo " Partner Lab #${PARTNER_ID}  ->  subnet ${LAB_SUBNET}.0/24"
echo "=========================================================="
echo ""
printf "%-16s %-18s %-8s\n" "Target Type" "Target IP" "Service Port"
printf "%-16s %-18s %-8s\n" "----------------" "------------------" "------------"
printf "%-16s %-18s %-8s\n" "Linux (SSH)"     "${LAB_SUBNET}.10" "22 (SSH)"
printf "%-16s %-18s %-8s\n" "Database (MySQL)" "${LAB_SUBNET}.20" "3306"
printf "%-16s %-18s %-8s\n" "Web Portal"      "${LAB_SUBNET}.30" "80 (HTTP)"
echo ""
echo "Local test ports (host): SSH ${SSH_HOST_PORT} | Web ${WEB_HOST_PORT} | Web-SSH ${SSH_WEB_HOST_PORT}"
echo ""
echo "Accounts: super / oper / root  (password: RankEZ123!)"
echo "MySQL:    app_user / AppPassword123!  (db: customer_db; app->DB service account)"
echo "Web:      demo / RankEZ123!  and  admin / Admin@Demo1  (portal login, users table)"
echo "=========================================================="
echo "Saved cheat sheet (targets + passwords): ${INFO_FILE}  (git-ignored)"
echo "Next step: Run 'docker compose up -d --build'"