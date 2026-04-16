import tempfile
from droplet import db, baseline


def test_median_across_observations():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = db.connect(f.name)
        db.init_schema(conn)
        conn.execute("INSERT INTO airports VALUES ('DEL','x','Delhi','India',1)")
        conn.execute("INSERT INTO airports VALUES ('BKK','x','Bangkok','Thailand',0)")
        conn.execute("INSERT INTO routes(origin,destination) VALUES ('DEL','BKK')")
        rid = conn.execute("SELECT id FROM routes").fetchone()[0]
        for price in [20000, 22000, 25000, 27000, 30000, 100000]:
            conn.execute(
                "INSERT INTO fare_observations (route_id,travel_month,price_inr,stops,raw) VALUES (?,?,?,?,?)",
                (rid, "2026-09-01", price, 1, "{}"),
            )
        conn.commit()
        baseline.recompute_all(conn)
        row = conn.execute(
            "SELECT median_price_inr, sample_count FROM route_baselines"
        ).fetchone()
        assert row["sample_count"] == 6
        assert row["median_price_inr"] == 26000  # median of 6 = avg(25k,27k)


def test_skips_observations_older_than_90_days():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = db.connect(f.name)
        db.init_schema(conn)
        conn.execute("INSERT INTO airports VALUES ('DEL','x','Delhi','India',1)")
        conn.execute("INSERT INTO airports VALUES ('BKK','x','Bangkok','Thailand',0)")
        conn.execute("INSERT INTO routes(origin,destination) VALUES ('DEL','BKK')")
        rid = conn.execute("SELECT id FROM routes").fetchone()[0]
        # old observation (200d ago) — should be excluded
        conn.execute(
            "INSERT INTO fare_observations (route_id,travel_month,price_inr,stops,raw,observed_at) VALUES (?,?,?,?,?,datetime('now','-200 days'))",
            (rid, "2026-09-01", 999999, 0, "{}"),
        )
        # recent observations
        for price in [20000, 22000, 25000, 27000, 30000]:
            conn.execute(
                "INSERT INTO fare_observations (route_id,travel_month,price_inr,stops,raw) VALUES (?,?,?,?,?)",
                (rid, "2026-09-01", price, 0, "{}"),
            )
        conn.commit()
        baseline.recompute_all(conn)
        row = conn.execute("SELECT median_price_inr, sample_count FROM route_baselines").fetchone()
        assert row["sample_count"] == 5  # old one excluded
        assert row["median_price_inr"] == 25000
