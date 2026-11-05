"""Customer portal demo app (RankEZ partner lab).

A multi-page Flask app that demonstrates the RankEZ AIM / CPM-for-File story
alongside a normal, session-based web login:

* App -> DB connection: the app reads its MySQL connection settings
  (host/port/db/user/*password*) from /data/db-config.txt on EVERY request, so
  the service-account password RankEZ rotates and pushes into that file
  (CPM-for-File) is picked up immediately with no restart.

* Human login: portal users live in their OWN `users` table (separate from the
  MySQL service account `app_user`).  On a successful login a server-side
  session is created and the browser is redirected to a separate `/dashboard`
  page that shows the data plus a logout button -- a normal login flow rather
  than re-rendering the same page.
"""
import hashlib
import os

import pymysql
from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

CONFIG_PATH = os.environ.get("CONFIG_PATH", "/data/db-config.txt")
SECRET_KEY = os.environ.get("SECRET_KEY", "rankez-partner-lab-demo-secret")

app = Flask(__name__)
app.secret_key = SECRET_KEY


# --------------------------------------------------------------------------- #
# Config / DB helpers
# --------------------------------------------------------------------------- #
def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except OSError:
        pass
    return cfg


def connect(user, password, cfg):
    return pymysql.connect(
        host=cfg.get("db_host", "127.0.0.1"),
        port=int(cfg.get("db_port", 3306)),
        user=user,
        password=password,
        database=cfg.get("db_name", "customer_db"),
        connect_timeout=5,
    )


def fetch_customers(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, tier, balance FROM customers")
        return cur.fetchall()


def fetch_customer(conn, cid):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, tier, balance FROM customers WHERE id = %s", (cid,)
        )
        return cur.fetchone()


def fetch_orders(conn, cid):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, customer_id, order_ref, description, amount, status "
            "FROM orders WHERE customer_id = %s ORDER BY id",
            (cid,),
        )
        return cur.fetchall()


def fetch_user(conn, username):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, password_salt, password_hash, full_name, role "
            "FROM users WHERE username = %s",
            (username,),
        )
        return cur.fetchone()


def hash_password(salt, password):
    return hashlib.sha256(("%s:%s" % (salt, password)).encode()).hexdigest()


def config_connection_ok(cfg):
    """Return (ok, message) for the app's own service-account connection."""
    try:
        conn = connect(cfg.get("db_user", ""), cfg.get("db_password", ""), cfg)
        conn.close()
        return True, ""
    except Exception as e:  # noqa: BLE001 - surface any connect failure
        return False, str(e)


# --------------------------------------------------------------------------- #
# Styling (RankEZ brand palette)
# --------------------------------------------------------------------------- #
STYLE = """
  :root {
    --ink: #10211c;
    --ink-soft: #1a2f28;
    --brand: #34a93f;
    --brand-strong: #2b8e34;
    --accent: #1d7cc9;
    --paper: #f3f8f5;
    --cloud: #eef3f0;
    --card: #fff;
    --line: #e2eae6;
    --slate: #4f615b;
    --steel: #647871;
    --mist: #94a39d;
    --danger: #bf000f;
    --ok: #2b8e34;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Figtree", -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--ink);
    background: var(--paper);
    min-height: 100vh;
  }
  a { color: var(--accent); }

  /* top bar */
  .topbar {
    background: var(--ink);
    color: #fff;
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 28px;
  }
  .logo { font-weight: 700; font-size: 20px; letter-spacing: .3px; }
  .logo .dot { color: var(--brand); }
  .topbar .sub { color: var(--mist); font-size: 14px; }
  .topbar .spacer { flex: 1 1 auto; }
  .userchip { display: flex; align-items: center; gap: 10px; font-size: 14px; }
  .userchip .who { color: var(--mist); }
  .userchip .name { color: #fff; font-weight: 600; }
  .btn {
    display: inline-block; border: 1px solid var(--line); border-radius: 8px;
    padding: 8px 16px; font-size: 14px; font-weight: 600; cursor: pointer;
    text-decoration: none; background: var(--card); color: var(--ink);
  }
  .btn:hover { border-color: var(--slate); }
  .btn-primary { background: var(--brand); border-color: var(--brand); color: #fff; }
  .btn-primary:hover { background: var(--brand-strong); border-color: var(--brand-strong); }
  .btn-ghost { background: transparent; border-color: rgba(255,255,255,.35); color: #fff; }
  .btn-ghost:hover { border-color: #fff; }

  /* login */
  .login-wrap {
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    padding: 24px;
  }
  .login-card {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    width: 100%; max-width: 400px; padding: 40px 36px;
    box-shadow: 0 18px 50px -24px rgba(16,33,28,.35);
  }
  .login-card .logo { color: var(--ink); font-size: 24px; text-align: center; }
  .login-card .tagline {
    text-align: center; color: var(--steel); font-size: 14px; margin: 6px 0 28px;
  }
  label { display: block; font-size: 13px; font-weight: 600; color: var(--slate); margin: 16px 0 6px; }
  input[type=text], input[type=password] {
    width: 100%; padding: 11px 12px; border: 1px solid var(--line); border-radius: 8px;
    font-size: 15px; font-family: inherit;
  }
  input:focus { outline: none; border-color: var(--brand); box-shadow: 0 0 0 3px rgba(52,169,63,.15); }
  .login-card .btn-primary { width: 100%; margin-top: 24px; padding: 12px; font-size: 15px; }
  .hint {
    margin-top: 22px; padding: 12px; border-radius: 8px; background: var(--cloud);
    font-size: 13px; color: var(--steel); line-height: 1.5;
  }
  .hint code { font-family: "Space Mono", ui-monospace, monospace; color: var(--ink-soft); }

  /* alerts */
  .alert { border-radius: 8px; padding: 12px 14px; font-size: 14px; margin: 0 0 16px; }
  .alert-err { background: #fef2f2; border: 1px solid #ffcaca; color: var(--danger); }

  /* body */
  .wrap { max-width: 960px; margin: 0 auto; padding: 32px 24px; }
  .panel {
    background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 22px 24px; margin: 0 0 20px;
  }
  .panel h2 { font-size: 16px; margin: 0 0 12px; }
  .mono { font-family: "Space Mono", ui-monospace, monospace; font-size: 13px; }
  .ok { color: var(--ok); font-weight: 600; }
  .err { color: var(--danger); font-weight: 600; }

  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); }
  th { background: var(--cloud); color: var(--slate); font-size: 13px; font-weight: 600; }
  td { font-size: 14px; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .b-gold { background: #fdf4d5; color: #8a6d1a; }
  .b-silver { background: #eef3f0; color: var(--slate); }
  .b-bronze { background: #f2e7dc; color: #8a5a2b; }
  .b-paid { background: #eaf6ed; color: var(--ok); }
  .b-pending { background: #fdf4d5; color: #8a6d1a; }

  /* clickable customer rows (drill-down) */
  .customer-link { color: var(--accent); font-weight: 600; text-decoration: none; }
  .customer-link:hover { text-decoration: underline; }
  .view-link { color: var(--steel); font-size: 13px; text-decoration: none; white-space: nowrap; }
  .view-link:hover { color: var(--accent); }
  tbody tr.clickable { cursor: pointer; }
  tbody tr.clickable:hover { background: var(--paper); }

  .backlink { display: inline-block; margin: 0 0 16px; color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 600; }
  .backlink:hover { text-decoration: underline; }
  .cust-head { display: flex; align-items: center; gap: 14px; }
"""

# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
LOGIN_PAGE = """
<!doctype html>
<html><head><title>Sign in &middot; RankEZ Customer Portal</title>
<style>{{ style }}</style></head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="logo">RankEZ<span class="dot">.</span></div>
    <div class="tagline">Customer Portal &mdash; Partner Lab</div>

    {% if msg %}<div class="alert alert-err">{{ msg }}</div>{% endif %}

    <form method="post" action="{{ url_for('login') }}">
      <label for="username">Username</label>
      <input type="text" id="username" name="username" value="{{ username }}" autofocus autocomplete="username">
      <label for="password">Password</label>
      <input type="password" id="password" name="password" autocomplete="current-password">
      <button type="submit" class="btn btn-primary">Sign in</button>
    </form>

    <div class="hint">
      Demo login: <code>demo</code> / <code>RankEZ123!</code><br>
      Admin login: <code>admin</code> / <code>Admin@Demo1</code>
    </div>
  </div>
</div>
</body></html>
"""

DASHBOARD_PAGE = """
<!doctype html>
<html><head><title>Dashboard &middot; RankEZ Customer Portal</title>
<style>{{ style }}</style></head>
<body>
<div class="topbar">
  <div class="logo">RankEZ<span class="dot">.</span></div>
  <div class="sub">Customer Portal</div>
  <div class="spacer"></div>
  <div class="userchip">
    <span class="who">Signed in as</span>
    <span class="name">{{ user_name }}</span>
    <a class="btn btn-ghost" href="{{ url_for('logout') }}">Log out</a>
  </div>
</div>

<div class="wrap">
  <div class="panel">
    <h2>Application DB connection <span class="mono">(from db-config.txt)</span></h2>
    <p class="mono">
      host: <b>{{ cfg.db_host or '?' }}</b> &middot; port: <b>{{ cfg.db_port or '?' }}</b>
      &middot; db: <b>{{ cfg.db_name or '?' }}</b> &middot; user: <b>{{ cfg.db_user or '?' }}</b>
    </p>
    {% if status_ok %}
      <p class="ok">&#10004; Connected as <b>{{ cfg.db_user }}</b> &mdash; the rotated
         credential in the config file is valid.</p>
    {% else %}
      <p class="err">&#10008; Could not connect using the config-file credential:
         <span class="mono">{{ status_err }}</span></p>
    {% endif %}
  </div>

  <div class="panel">
    <h2>Customers</h2>
    <table>
      <tr><th>ID</th><th>Customer</th><th>Tier</th><th>Balance</th><th></th></tr>
      {% for r in data %}
      <tr class="clickable" onclick="location.href='{{ url_for('customer', cid=r[0]) }}'">
        <td>{{ r[0] }}</td>
        <td><a class="customer-link" href="{{ url_for('customer', cid=r[0]) }}">{{ r[1] }}</a></td>
        <td><span class="badge {{ 'b-' + r[2]|lower }}">{{ r[2] }}</span></td>
        <td>{{ "{:,.2f}".format(r[3]) }}</td>
        <td><a class="view-link" href="{{ url_for('customer', cid=r[0]) }}">Details &#8594;</a></td>
      </tr>
      {% endfor %}
    </table>
  </div>
</div>
</body></html>
"""

CUSTOMER_PAGE = """
<!doctype html>
<html><head><title>{{ cust[1] }} &middot; RankEZ Customer Portal</title>
<style>{{ style }}</style></head>
<body>
<div class="topbar">
  <div class="logo">RankEZ<span class="dot">.</span></div>
  <div class="sub">Customer Portal</div>
  <div class="spacer"></div>
  <div class="userchip">
    <span class="who">Signed in as</span>
    <span class="name">{{ user_name }}</span>
    <a class="btn btn-ghost" href="{{ url_for('logout') }}">Log out</a>
  </div>
</div>

<div class="wrap">
  <a class="backlink" href="{{ url_for('dashboard') }}">&larr; Back to customers</a>

  <div class="panel">
    <div class="cust-head">
      <h2 style="margin:0">{{ cust[1] }}</h2>
      <span class="badge {{ 'b-' + cust[2]|lower }}">{{ cust[2] }}</span>
    </div>
    <p class="mono" style="color:var(--steel); margin:10px 0 0;">
      Customer #{{ cust[0] }} &middot; Balance {{ "{:,.2f}".format(cust[3]) }}
    </p>
  </div>

  <div class="panel">
    <h2>Orders</h2>
    <table>
      <tr><th>Order ref</th><th>Description</th><th>Amount</th><th>Status</th></tr>
      {% for o in orders %}
      <tr>
        <td class="mono">{{ o[2] }}</td>
        <td>{{ o[3] }}</td>
        <td>{{ "{:,.2f}".format(o[4]) }}</td>
        <td><span class="badge b-{{ o[5]|lower }}">{{ o[5] }}</span></td>
      </tr>
      {% endfor %}
    </table>
  </div>
</div>
</body></html>
"""


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_PAGE, style=STYLE, msg=None, username="")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    cfg = load_config()

    try:
        conn = connect(cfg.get("db_user", ""), cfg.get("db_password", ""), cfg)
        row = fetch_user(conn, username)
        conn.close()
    except Exception as e:  # noqa: BLE001
        return render_template_string(
            LOGIN_PAGE, style=STYLE,
            msg="Login error: %s" % e, username=username,
        ), 500

    if row is None or hash_password(row[2], password) != row[3]:
        return render_template_string(
            LOGIN_PAGE, style=STYLE,
            msg="Invalid username or password.", username=username,
        ), 401

    session.clear()
    session["user_id"] = row[0]
    session["username"] = row[1]
    return redirect(url_for("dashboard"))


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))

    cfg = load_config()
    status_ok, status_err = config_connection_ok(cfg)

    user_name = session.get("username")
    data = []
    try:
        conn = connect(cfg.get("db_user", ""), cfg.get("db_password", ""), cfg)
        data = fetch_customers(conn)
        row = fetch_user(conn, session["username"])
        conn.close()
        if row:
            user_name = row[4]
    except Exception as e:  # noqa: BLE001
        pass

    return render_template_string(
        DASHBOARD_PAGE, style=STYLE, cfg=cfg, data=data,
        user_name=user_name, status_ok=status_ok, status_err=status_err,
    )


@app.route("/customer/<int:cid>", methods=["GET"])
def customer(cid):
    if "user_id" not in session:
        return redirect(url_for("index"))

    cfg = load_config()
    user_name = session.get("username")
    cust = None
    orders = []
    try:
        conn = connect(cfg.get("db_user", ""), cfg.get("db_password", ""), cfg)
        cust = fetch_customer(conn, cid)
        if cust:
            orders = fetch_orders(conn, cid)
        conn.close()
    except Exception as e:  # noqa: BLE001
        pass

    if cust is None:
        return redirect(url_for("dashboard"))

    return render_template_string(
        CUSTOMER_PAGE, style=STYLE, cust=cust, orders=orders, user_name=user_name
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/health")
def health():
    cfg = load_config()
    try:
        conn = connect(cfg.get("db_user", ""), cfg.get("db_password", ""), cfg)
        rows = fetch_customers(conn)
        conn.close()
        return "OK (config-file credential valid, %d customer rows)" % len(rows), 200
    except Exception as e:  # noqa: BLE001
        return "ERROR: %s" % e, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False, threaded=True)