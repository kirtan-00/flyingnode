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

    def cheap_prices(self, origin: str, destination: str):
        """v1/prices/cheap — broader coverage, returns cheapest fare(s) for a route.
        Travelpayouts uses city codes internally (NYC for JFK, PAR for CDG) but
        accepts airport codes and maps them. Returns dict keyed by city code."""
        r = self.s.get(
            f"{BASE}/v1/prices/cheap",
            params={
                "origin": origin,
                "destination": destination,
                "currency": "inr",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        results = []
        for city_code, transfers in data.items():
            for num_stops, fare in transfers.items():
                if not isinstance(fare, dict):
                    continue
                depart_at = fare.get("departure_at", "")
                return_at = fare.get("return_at", "")
                depart_date = depart_at[:10] if depart_at else None
                return_date = return_at[:10] if return_at else None
                travel_month = (depart_date[:7] + "-01") if depart_date else None
                results.append({
                    "travel_month": travel_month or "2026-06-01",
                    "price_inr": int(fare.get("price", 0)),
                    "stops": int(num_stops),
                    "airline": fare.get("airline"),
                    "depart_date": depart_date,
                    "return_date": return_date,
                    "raw": fare,
                })
        return results

    def search_with_fallback(self, origin: str, destination: str, n_months: int = 6):
        """Try v2/month-matrix first, fallback to v1/prices/cheap for broader coverage."""
        results = self.cheapest_by_month(origin, destination, n_months)
        if results:
            return results
        return self.cheap_prices(origin, destination)

    def affiliate_url(self, origin: str, destination: str, depart: str, ret: str) -> str:
        """Return Aviasales deep-link with our marker for commission attribution.
        Aviasales URL format: /search/{origin}{DDMM}{destination}{DDMM}{passengers}
        """
        # depart/ret are "YYYY-MM-DD"
        dd = depart[8:10] + depart[5:7]  # DDMM
        rd = ret[8:10] + ret[5:7]        # DDMM
        return f"https://www.aviasales.com/search/{origin}{dd}{destination}{rd}1?marker={self.marker}"
