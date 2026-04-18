import hashlib
import hmac
import json
import os

from flask import Flask, abort, jsonify, request

from droplet import db
from droplet.travelpayouts import TPClient

DB_PATH = os.environ.get("FLYINGNODE_DB", "/root/flyingnode/flyingnode.db")
SECRET = os.environ.get("SUBSCRIBE_UNSUB_SECRET", "change-me")
app = Flask(__name__)


def _conn():
    return db.connect(DB_PATH)


@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "content-type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return r


@app.get("/health")
def health():
    c = _conn()
    last = c.execute("SELECT MAX(observed_at) AS t FROM fare_observations").fetchone()["t"]
    count = c.execute("SELECT COUNT(*) AS n FROM deals WHERE still_live=1").fetchone()["n"]
    obs = c.execute("SELECT COUNT(*) AS n FROM fare_observations").fetchone()["n"]
    return {"last_poll": last, "active_deals": count, "observations": obs}


@app.get("/deals")
def deals():
    origin = request.args.get("origin")
    sql = """
      SELECT d.id, d.price_inr, d.baseline_inr, d.savings_pct, d.stops, d.airline,
             d.travel_month, d.affiliate_url, d.first_seen_at,
             r.origin, r.destination,
             a_o.city AS origin_city, a_o.name AS origin_name,
             a_d.city AS dest_city,   a_d.name AS dest_name, a_d.country AS dest_country
      FROM deals d
      JOIN routes r ON r.id = d.route_id
      JOIN airports a_o ON a_o.iata = r.origin
      JOIN airports a_d ON a_d.iata = r.destination
      WHERE d.still_live = 1
    """
    params: tuple = ()
    if origin:
        sql += " AND r.origin = ?"
        params = (origin,)
    sql += " ORDER BY d.savings_pct DESC, d.first_seen_at DESC LIMIT 60"
    rows = _conn().execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/deal/<int:deal_id>")
def one_deal(deal_id):
    r = _conn().execute(
        """SELECT d.*, r.origin, r.destination,
                  a_o.city AS origin_city, a_d.city AS dest_city, a_d.country AS dest_country
           FROM deals d
           JOIN routes r ON r.id = d.route_id
           JOIN airports a_o ON a_o.iata = r.origin
           JOIN airports a_d ON a_d.iata = r.destination
           WHERE d.id = ?""",
        (deal_id,),
    ).fetchone()
    if not r:
        abort(404)
    obs = _conn().execute(
        """SELECT observed_at, price_inr FROM fare_observations
           WHERE route_id=? AND travel_month=? AND observed_at >= datetime('now','-90 days')
           ORDER BY observed_at ASC""",
        (r["route_id"], r["travel_month"]),
    ).fetchall()
    return jsonify({**dict(r), "history": [dict(o) for o in obs]})


@app.get("/cheapest")
def cheapest():
    """Cheapest current fare per route — shows even when nothing qualifies as a deal."""
    origin = request.args.get("origin")
    sql = """
      SELECT r.origin, r.destination,
             a_o.city AS origin_city, a_d.city AS dest_city, a_d.country AS dest_country,
             fo.travel_month, fo.price_inr, fo.stops, fo.airline
      FROM fare_observations fo
      JOIN routes r ON r.id = fo.route_id
      JOIN airports a_o ON a_o.iata = r.origin
      JOIN airports a_d ON a_d.iata = r.destination
      WHERE fo.id IN (
        SELECT fo2.id FROM fare_observations fo2
        WHERE fo2.route_id = fo.route_id
        ORDER BY fo2.observed_at DESC LIMIT 1
      )
    """
    params: tuple = ()
    if origin:
        sql += " AND r.origin = ?"
        params = (origin,)
    sql += " ORDER BY fo.price_inr ASC LIMIT 40"
    rows = _conn().execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/search")
def search():
    """Live search: user picks origin + destination, we hit Travelpayouts in real-time."""
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    if len(origin) != 3 or len(destination) != 3:
        return jsonify({"error": "origin and destination must be 3-letter IATA codes"}), 400
    try:
        tp = TPClient()
        fares = tp.search_with_fallback(origin, destination, n_months=6)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    # auto-add searched route to watchlist for future monitoring
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO airports VALUES (?,?,?,?,?)",
                 (origin, origin, origin, "User-searched", 0))
    conn.execute("INSERT OR IGNORE INTO airports VALUES (?,?,?,?,?)",
                 (destination, destination, destination, "User-searched", 0))
    conn.execute("INSERT OR IGNORE INTO routes (origin, destination) VALUES (?,?)",
                 (origin, destination))
    # store observations so baselines build over time
    route = conn.execute("SELECT id FROM routes WHERE origin=? AND destination=?",
                         (origin, destination)).fetchone()
    if route:
        for f in fares:
            conn.execute(
                """INSERT INTO fare_observations
                   (route_id, travel_month, price_inr, stops, layover_hours, airline, raw, source)
                   VALUES (?,?,?,?,?,?,?, 'search')""",
                (route["id"], f["travel_month"], f["price_inr"], f["stops"],
                 None, f["airline"], json.dumps(f["raw"])),
            )
    conn.commit()
    results = []
    for f in fares:
        depart = f.get("depart_date") or f"{f['travel_month'][:7]}-15"
        ret = f.get("return_date") or f"{f['travel_month'][:7]}-25"
        results.append({
            "origin": origin,
            "destination": destination,
            "travel_month": f["travel_month"],
            "price_inr": f["price_inr"],
            "stops": f["stops"],
            "airline": f["airline"],
            "affiliate_url": tp.affiliate_url(origin, destination, depart, ret),
        })
    return jsonify(results)


@app.get("/airports")
def airports():
    """Autocomplete for the search bar."""
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify([])
    rows = _conn().execute(
        """SELECT iata, name, city, country FROM airports
           WHERE lower(city) LIKE ? OR lower(iata) LIKE ? OR lower(name) LIKE ?
           ORDER BY is_origin DESC, city ASC LIMIT 15""",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/deal-history")
def deal_history():
    """All past deals that are no longer live."""
    page = int(request.args.get("page", 0))
    limit = 30
    rows = _conn().execute(
        """SELECT d.id, d.price_inr, d.baseline_inr, d.savings_pct, d.stops, d.airline,
                  d.travel_month, d.affiliate_url, d.first_seen_at, d.last_seen_at,
                  r.origin, r.destination,
                  a_o.city AS origin_city, a_d.city AS dest_city, a_d.country AS dest_country
           FROM deals d
           JOIN routes r ON r.id = d.route_id
           JOIN airports a_o ON a_o.iata = r.origin
           JOIN airports a_d ON a_d.iata = r.destination
           WHERE d.still_live = 0
           ORDER BY d.first_seen_at DESC
           LIMIT ? OFFSET ?""",
        (limit, page * limit),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/subscribe")
def subscribe():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    if "@" not in email or len(email) > 200:
        abort(400)
    token = hmac.new(SECRET.encode(), email.encode(), hashlib.sha256).hexdigest()[:32]
    conn = _conn()
    conn.execute(
        """INSERT OR REPLACE INTO digest_subscribers
           (email, unsubscribed, unsubscribe_token, subscribed_at)
           VALUES (?, 0, ?, datetime('now'))""",
        (email, token),
    )
    conn.commit()
    return {"ok": True}


@app.get("/unsubscribe")
def unsubscribe():
    token = request.args.get("token", "")
    conn = _conn()
    conn.execute(
        "UPDATE digest_subscribers SET unsubscribed=1 WHERE unsubscribe_token=?",
        (token,),
    )
    conn.commit()
    return "<h2 style='font-family:system-ui'>You're unsubscribed. Sorry to see you go ✈️</h2>"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081)
