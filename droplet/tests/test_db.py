import tempfile
from droplet import db


def test_init_creates_all_tables():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = db.connect(f.name)
        db.init_schema(conn)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = {r[0] for r in cur.fetchall()}
        assert tables == {
            "airports",
            "routes",
            "fare_observations",
            "route_baselines",
            "deals",
            "digest_subscribers",
        }


def test_seed_loads_airports_and_routes():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = db.connect(f.name)
        db.init_schema(conn)
        db.seed_from_csv(conn, "droplet/seeds/airports.csv", "droplet/seeds/routes.csv")
        assert conn.execute("SELECT COUNT(*) FROM airports").fetchone()[0] >= 50
        assert conn.execute("SELECT COUNT(*) FROM routes").fetchone()[0] >= 150
        # origins flagged correctly
        assert conn.execute("SELECT COUNT(*) FROM airports WHERE is_origin=1").fetchone()[0] == 3
