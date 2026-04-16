import logging
import os

from droplet import brevo, db

PUBLIC_URL = os.environ.get("PUBLIC_SITE_URL", "https://flyingnode.duckdns.org")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("digest")

CSS = (
    "body{font-family:-apple-system,BlinkMacSystemFont,Inter,sans-serif;"
    "background:#F6F7FB;margin:0;padding:24px;color:#0B1020}"
    ".wrap{max-width:560px;margin:0 auto}"
    "h1{color:#001B94;font-size:22px;margin:0 0 16px;letter-spacing:-0.3px}"
    ".card{background:#fff;border-radius:16px;padding:20px;margin-bottom:12px;"
    "box-shadow:0 8px 32px rgba(0,27,148,.08)}"
    ".route{font-size:18px;font-weight:700;margin:0 0 4px}"
    ".price{font-size:32px;color:#001B94;font-weight:700;letter-spacing:-.5px}"
    ".was{color:#6B7385;text-decoration:line-through;margin-left:8px;font-size:14px}"
    ".badge{background:#FF6B00;color:#fff;border-radius:999px;padding:4px 10px;"
    "font-size:13px;font-weight:700;display:inline-block;margin-left:8px}"
    ".cta{display:inline-block;margin-top:12px;background:#001B94;color:#fff;"
    "text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:600}"
    ".unsub{color:#6B7385;font-size:11px;margin-top:24px;text-align:center}"
    "a{color:#001B94}"
)


def render(deals: list, unsub_token: str) -> str:
    cards = []
    for d in deals:
        cards.append(
            f'<div class="card">'
            f'<p class="route">{d["origin_city"]} ({d["origin"]}) → {d["dest_city"]} ({d["destination"]})</p>'
            f'<p><span class="price">₹{d["price_inr"]:,}</span>'
            f'<span class="was">was ₹{d["baseline_inr"]:,}</span>'
            f'<span class="badge">{d["savings_pct"]}% off</span></p>'
            f'<p style="margin:6px 0 0;color:#6B7385">Travel {d["travel_month"][:7]} · '
            f'{d["stops"]} stop(s) · {d["airline"] or "varied"}</p>'
            f'<a class="cta" href="{d["affiliate_url"]}">Book on Google Flights</a>'
            f'</div>'
        )
    return (
        f"<html><head><style>{CSS}</style></head><body><div class='wrap'>"
        f"<h1>Today's mistake fares</h1>"
        f"{''.join(cards)}"
        f"<p class='unsub'>You subscribed to the flyingnode digest. "
        f"<a href='{PUBLIC_URL}/unsubscribe?token={unsub_token}'>Unsubscribe</a></p>"
        f"</div></body></html>"
    )


def main():
    conn = db.connect(os.environ.get("FLYINGNODE_DB", "/root/flyingnode/flyingnode.db"))
    deals = conn.execute(
        """SELECT d.*, a_o.city AS origin_city, a_d.city AS dest_city,
                  r.origin, r.destination
           FROM deals d
           JOIN routes r ON r.id = d.route_id
           JOIN airports a_o ON a_o.iata = r.origin
           JOIN airports a_d ON a_d.iata = r.destination
           WHERE d.still_live=1
             AND d.first_seen_at >= datetime('now','-24 hours')
           ORDER BY d.savings_pct DESC, d.first_seen_at DESC
           LIMIT 12"""
    ).fetchall()

    if not deals:
        log.info("no new deals in last 24h, skipping digest")
        return

    subs = conn.execute(
        "SELECT email, unsubscribe_token FROM digest_subscribers WHERE unsubscribed=0"
    ).fetchall()

    log.info(f"sending {len(deals)} deals to {len(subs)} subscribers")
    sent = 0
    for s in subs:
        try:
            brevo.send(
                s["email"],
                f"{len(deals)} mistake fares today — flyingnode",
                render([dict(d) for d in deals], s["unsubscribe_token"]),
            )
            sent += 1
        except Exception as e:
            log.exception(f"send failed to {s['email']}: {e}")
    log.info(f"digest done: {sent}/{len(subs)} sent")


if __name__ == "__main__":
    main()
