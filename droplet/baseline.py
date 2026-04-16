import os
import sqlite3
import statistics
from datetime import datetime, timedelta

LOOKBACK_DAYS = 90


def recompute_all(conn: sqlite3.Connection) -> None:
    cutoff = (datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)).isoformat(sep=" ", timespec="seconds")
    rows = conn.execute(
        """
        SELECT route_id, travel_month, price_inr
        FROM fare_observations
        WHERE observed_at >= ?
        """,
        (cutoff,),
    ).fetchall()
    by_key: dict[tuple[int, str], list[int]] = {}
    for r in rows:
        by_key.setdefault((r["route_id"], r["travel_month"]), []).append(r["price_inr"])
    conn.execute("DELETE FROM route_baselines")
    for (rid, month), prices in by_key.items():
        med = int(statistics.median(prices))
        conn.execute(
            "INSERT INTO route_baselines (route_id, travel_month, median_price_inr, sample_count) VALUES (?,?,?,?)",
            (rid, month, med, len(prices)),
        )
    conn.commit()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("baseline")
    conn = sqlite3.connect(os.environ.get("FLYINGNODE_DB", "/root/flyingnode/flyingnode.db"))
    conn.row_factory = sqlite3.Row
    recompute_all(conn)
    n = conn.execute("SELECT COUNT(*) FROM route_baselines").fetchone()[0]
    log.info(f"baselines updated: {n}")
