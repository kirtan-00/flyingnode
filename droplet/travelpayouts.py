import os
from datetime import date
from typing import Optional
import requests
from dateutil.relativedelta import relativedelta

BASE = "https://api.travelpayouts.com"


class TPClient:
    """Thin wrapper around Travelpayouts' public price endpoints.

    Uses v2 month-matrix for cheapest round-trip per (origin, destination, month).
    Currency fixed to INR for the India-first use case.
    """

    def __init__(self, token: Optional[str] = None, marker: Optional[str] = None):
        self.token = token or os.environ["TRAVELPAYOUTS_TOKEN"]
        self.marker = marker or os.environ.get("TRAVELPAYOUTS_MARKER", "")
        self.s = requests.Session()
        self.s.headers["X-Access-Token"] = self.token

    def month_matrix(self, origin: str, destination: str, month_iso: str, currency: str = "inr"):
        r = self.s.get(
            f"{BASE}/v2/prices/month-matrix",
            params={
                "currency": currency,
                "origin": origin,
                "destination": destination,
                "month": month_iso,
                "show_to_affiliates": "true",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        # Travelpayouts returns either a list of dicts or a dict keyed by date.
        # Normalise to a list of dicts.
        if isinstance(data, dict):
            data = list(data.values())
        return [d for d in data if isinstance(d, dict)]

    def cheapest_by_month(self, origin: str, destination: str, n_months: int = 6):
        out = []
        today = date.today().replace(day=1)
        for i in range(n_months):
            month = (today + relativedelta(months=i)).isoformat()
            try:
                rows = self.month_matrix(origin, destination, month)
            except requests.HTTPError:
                continue
            if not rows:
                continue
            best = min(rows, key=lambda r: r.get("value", 10**9))
            if not best.get("value"):
                continue
            out.append({
                "travel_month": month,
                "price_inr": int(best["value"]),
                "stops": int(best.get("number_of_changes", 1)),
                "airline": best.get("gate") or best.get("airline"),
                "depart_date": best.get("depart_date"),
                "return_date": best.get("return_date"),
                "raw": best,
            })
        return out

    def affiliate_url(self, origin: str, destination: str, depart: str, ret: str) -> str:
        """Return Aviasales deep-link with our marker for commission attribution."""
        d = depart.replace("-", "")[2:]  # YYMMDD
        r = ret.replace("-", "")[2:]
        return f"https://www.aviasales.com/search/{origin}{d}{destination}{r}1?marker={self.marker}"
