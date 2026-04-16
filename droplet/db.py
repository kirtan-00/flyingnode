import sqlite3
import csv

SCHEMA = """
CREATE TABLE IF NOT EXISTS airports (
  iata TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL,
  is_origin INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS routes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  origin TEXT NOT NULL REFERENCES airports(iata),
  destination TEXT NOT NULL REFERENCES airports(iata),
  active INTEGER DEFAULT 1,
  UNIQUE(origin, destination)
);
CREATE TABLE IF NOT EXISTS fare_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route_id INTEGER NOT NULL REFERENCES routes(id),
  travel_month TEXT NOT NULL,
  price_inr INTEGER NOT NULL,
  stops INTEGER NOT NULL,
  layover_hours REAL,
  airline TEXT,
  bag_included INTEGER,
  raw TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'poll',
  observed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fare_obs_route_month
  ON fare_observations(route_id, travel_month, observed_at DESC);
CREATE TABLE IF NOT EXISTS route_baselines (
  route_id INTEGER NOT NULL REFERENCES routes(id),
  travel_month TEXT NOT NULL,
  median_price_inr INTEGER NOT NULL,
  sample_count INTEGER NOT NULL,
  computed_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (route_id, travel_month)
);
CREATE TABLE IF NOT EXISTS deals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route_id INTEGER NOT NULL REFERENCES routes(id),
  travel_month TEXT NOT NULL,
  price_inr INTEGER NOT NULL,
  baseline_inr INTEGER NOT NULL,
  savings_pct INTEGER NOT NULL,
  stops INTEGER NOT NULL,
  layover_hours REAL,
  airline TEXT,
  affiliate_url TEXT NOT NULL,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  still_live INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_deals_live ON deals(still_live, first_seen_at DESC);
CREATE TABLE IF NOT EXISTS digest_subscribers (
  email TEXT PRIMARY KEY,
  subscribed_at TEXT NOT NULL DEFAULT (datetime('now')),
  unsubscribed INTEGER DEFAULT 0,
  unsubscribe_token TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def seed_from_csv(conn: sqlite3.Connection, airports_csv: str, routes_csv: str) -> None:
    with open(airports_csv) as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT OR IGNORE INTO airports (iata,name,city,country,is_origin) VALUES (?,?,?,?,?)",
                (row["iata"], row["name"], row["city"], row["country"], int(row["is_origin"])),
            )
    with open(routes_csv) as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT OR IGNORE INTO routes (origin,destination) VALUES (?,?)",
                (row["origin"], row["destination"]),
            )
    conn.commit()
