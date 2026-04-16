"""Day-1 baseline seeding.

Pulls current month-matrix lows for each (route, travel_month) and spreads 10
synthetic historical samples ±15% around the observed low, dated across the
last 90 days. Gives the median-based baseline enough samples to function
immediately; real observations take over within 2-3 weeks of polling.
"""
import json
import logging
import os

from droplet import baseline as bl
from droplet import db
from droplet.travelpayouts import TPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bootstrap")

SPREAD = [
    (-85, 0.95), (-70, 1.05), (-55, 0.90), (-40, 1.10),
    (-25, 0.97), (-15, 1.02), (-5, 0.99), (0, 1.0),
    (-60, 1.08), (-45, 0.93),
]


def main():
    conn = db.connect(os.environ.get("FLYINGNODE_DB", "/root/flyingnode/flyingnode.db"))
    tp = TPClient()
    routes = conn.execute("SELECT id, origin, destination FROM routes WHERE active=1").fetchall()
    for r in routes:
        try:
            items = tp.cheapest_by_month(r["origin"], r["destination"], n_months=6)
            for it in items:
                mid = it["price_inr"]
                raw = json.dumps(it["raw"])
                for offset_days, factor in SPREAD:
                    conn.execute(
                        """INSERT INTO fare_observations
                           (route_id, travel_month, price_inr, stops, raw, source, observed_at)
                           VALUES (?, ?, ?, ?, ?, 'bootstrap', datetime('now', ? || ' days'))""",
                        (r["id"], it["travel_month"], int(mid * factor), it["stops"], raw, str(offset_days)),
                    )
            log.info(f"bootstrapped {r['origin']}->{r['destination']}: {len(items)} months × 10 samples")
        except Exception as e:
            log.exception(f"{r['origin']}-{r['destination']}: {e}")
    conn.commit()
    bl.recompute_all(conn)
    n = conn.execute("SELECT COUNT(*) FROM route_baselines").fetchone()[0]
    log.info(f"baselines seeded: {n}")


if __name__ == "__main__":
    main()
