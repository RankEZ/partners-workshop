USE customer_db;

CREATE TABLE IF NOT EXISTS customers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  tier VARCHAR(20) NOT NULL,
  balance DECIMAL(12,2) NOT NULL
);

INSERT INTO customers (name, tier, balance) VALUES
  ('Acme Corp', 'Gold', 125000.00),
  ('Globex Industries', 'Silver', 45000.50),
  ('Initech', 'Bronze', 8900.00);

-- Orders per customer: gives the portal a drill-down so every customer row can
-- open a detail page (the navigation a PSM session recording would capture).
CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_ref VARCHAR(40) NOT NULL,
  description VARCHAR(200) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  status VARCHAR(20) NOT NULL
);

INSERT INTO orders (customer_id, order_ref, description, amount, status) VALUES
  (1, 'PO-2026-001', 'Enterprise Support Renewal', 48000.00, 'Paid'),
  (1, 'PO-2026-002', 'Additional Seats (250)',       12500.00, 'Pending'),
  (1, 'PO-2026-003', 'Custom Integration Build',     22000.00, 'Paid'),
  (1, 'PO-2026-004', 'On-site Training (2 days)',     6800.00, 'Pending'),
  (2, 'PO-2026-010', 'Standard Support',              9000.00, 'Paid'),
  (2, 'PO-2026-011', 'Remote Training Package',       3500.00, 'Pending'),
  (2, 'PO-2026-012', 'Security Module Add-on',       7800.00, 'Paid'),
  (3, 'PO-2026-020', 'Startup Starter Plan',         2500.00, 'Paid'),
  (3, 'PO-2026-021', 'Additional Storage (500GB)',   1100.00, 'Pending');

-- ---------------------------------------------------------------------------
-- Portal login accounts, stored in their OWN table -- deliberately SEPARATE
-- from the MySQL service account (`app_user`) the app itself uses to open the
-- database connection.  `app_user` lives in MySQL's mysql.user table and its
-- password is the one CPM-for-File rotates in /data/db-config.txt; these
-- `users` rows are the *human* login identities the web portal verifies.
--
-- password_hash = SHA-256('password_salt:password')  (salted, stored as hex)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_salt VARCHAR(32) NOT NULL,
  password_hash VARCHAR(64) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  role VARCHAR(32) NOT NULL
);

-- demo / RankEZ123!
INSERT INTO users (username, password_salt, password_hash, full_name, role) VALUES
  ('demo',  'c3e9b12382122f41',
   '1a55f5ef78f470f432195cf01a73d71903d35a9a884a5bcfaf2c6450069d9829',
   'Demo Partner', 'Sales'),
  ('admin', 'f49f6f22b020e332',
   '1ebcf723a620dff9c556d81bdd4063f60f2cd7eb632a28865273519d482ce62a',
   'Portal Admin', 'Admin');

-- app_user is created with ALL privs on customer_db via MYSQL_USER, but be explicit
-- so the demo's DB-connection account is well-defined (this is the service account,
-- NOT a login account -- see the users table above).
GRANT SELECT, INSERT, UPDATE, DELETE ON customer_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;