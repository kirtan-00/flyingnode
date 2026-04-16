import json
import logging
import os
from typing import Optional

from droplet import db
from droplet.deal_rule import Baseline, Observation, evaluate
from droplet.travelpayouts import TPClient

DB_PATH = os.environ.get("FLYINGNODE_DB", "/root/flyingnode/flyingnode.db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("poller")


def load_baseline(conn, route_id: int, travel_month: str) -> Optional[Baseline]:
    r = conn.execute(
        "SELECT median_price_inr, sample_count FROM route_baselines WHERE route_id=? AND travel_month=?",
        (route_id, travel_month),
    ).fetchone()
    return Baseline(r["median_price_inr"], r["sample_count"]) if r else None


def upsert_deal(conn, route_id, travel_month, obs: Observation, baseline: Baseline,
                savings_pct: int, raw: dict, tp: TPClient):
    r = conn.execute("SELECT origin, destination FROM routes WHERE id=?", (route_id,)).fetchone()
    depart = raw.get("depart_date") or f"{travel_month[:7]}-15"
    ret = raw.get("return_date") or f"{travel_month[:7]}-25"
    url = tp.affiliate_url(r["origin"], r["destination"], depart, ret)

    existing = conn.execute(
        "SELECT id, price_inr FROM deals WHERE route_id=? AND travel_month=? AND still_live=1",
        (route_id, travel_month),
    ).fetchone()

    if existing:
        if obs.price_inr <= existing["price_inr"]:
            conn.execute(
                "UPDATE deals SET price_inr=?, savings_pct=?, last_seen_at=datetime('now'), affiliate_url=? WHERE id=?",
                (obs.price_inr, savings_pct, url, existing["id"]),
            )
    else:
        conn.execute(
            """INSERT INTO deals (route_id, travel_month, price_inr, baseline_inr, savings_pct,
                                  stops, layover_hours, airline, affiliate_url)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (route_id, travel_month, obs.price_inr, baseline.median_price_inr, savings_pct,
             obs.stops, obs.layover_hours, raw.get("gate") or raw.get("airline"), url),
        )
        log.info(
            f"NEW DEAL {r['origin']}->{r['destination']} month={travel_month} "
            f"price={obs.price_inr} savings={savings_pct}%"
        )


def mark_stale_deals(conn, route_id: int, travel_month: str, current_price: int):
    conn.execute(
        """UPDATE deals SET still_live=0
           WHERE route_id=? AND travel_month=? AND still_live=1 AND price_inr * 1.10 < ?""",
        (route_id, travel_month, current_price),
    )


def main():
    conn = db.connect(DB_PATH)
    tp = TPClient()
    routes = conn.execute("SELECT id, origin, destination FROM routes WHERE active=1").fetchall()
    log.info(f"polling {len(routes)} routes")
    inserted = 0
    deals_created = 0
    for r in routes:
        try:
            for item in tp.cheapest_by_month(r["origin"], r["destination"], n_months=6):
                conn.execute(
                    """INSERT INTO fare_observations
                       (route_id, travel_month, price_inr, stops, layover_hours, airline,
                        bag_included, raw, source)
                       VALUES (?,?,?,?,?,?,?,?, 'poll')""",
                    (r["id"], item["travel_month"], item["price_inr"], item["stops"],
                     None, item["airline"], None, json.dumps(item["raw"])),
                )
                inserted += 1
                baseline = load_baseline(conn, r["id"], item["travel_month"])
                if baseline is None:
                    continue
                obs = Observation(item["price_inr"], item["stops"], None, None)
                res = evaluate(obs, baseline)
                if res.is_deal:
                    before = conn.total_changes
                    upsert_deal(conn, r["id"], item["travel_month"], obs, baseline,
                                res.savings_pct, item["raw"], tp)
                    if conn.total_changes > before:
                        deals_created += 1
                mark_stale_deals(conn, r["id"], item["travel_month"], item["price_inr"])
            conn.commit()
        except Exception as e:
            log.exception(f"route {r['origin']}-{r['destination']} failed: {e}")
    log.info(f"poll done: {inserted} observations, {deals_created} new deals")


if __name__ == "__main__":
    main()
