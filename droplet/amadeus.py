"""Amadeus Self-Service API client.

Fallback data source when Travelpayouts has no fare data for a route.
Uses OAuth2 (client_credentials) for auth, then Flight Offers Search v2.
Free tier: 2,000 calls/month in test environment.
"""
import os
import time
from datetime import date
from typing import Optional

import requests
from dateutil.relativedelta import relativedelta

TEST_BASE = "https://test.api.amadeus.com"
PROD_BASE = "https://api.amadeus.com"


class AmadeusClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_prod: bool = False,
    ):
        self.client_id = client_id or os.environ.get("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("AMADEUS_CLIENT_SECRET", "")
        self.base = PROD_BASE if use_prod else TEST_BASE
        self._token = ""
        self._token_expires = 0

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _auth(self):
        if time.time() < self._token_expires:
            return
        r = requests.post(
            f"{self.base}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=15,
        )
        r.raise_for_status()
        d = r.json()
        self._token = d["access_token"]
        self._token_expires = time.time() + d.get("expires_in", 1799) - 60

    def search(self, origin: str, destination: str, n_months: int = 6):
        """Search cheapest one-way fares per month for the next n_months.
        Returns list of dicts matching Travelpayouts format for easy merging."""
        if not self.enabled:
            return []
        self._auth()
        results = []
        today = date.today()
        for i in range(n_months):
            depart = today + relativedelta(months=i)
            if depart.day < 15:
                depart = depart.replace(day=15)
            try:
                r = requests.get(
                    f"{self.base}/v2/shopping/flight-offers",
                    headers={"Authorization": f"Bearer {self._token}"},
                    params={
                        "originLocationCode": origin,
                        "destinationLocationCode": destination,
                        "departureDate": depart.isoformat(),
                        "adults": 1,
                        "nonStop": "false",
                        "max": 3,
                        "currencyCode": "INR",
                    },
                    timeout=20,
                )
                if r.status_code != 200:
                    continue
                offers = r.json().get("data", [])
                if not offers:
                    continue
                best = min(offers, key=lambda o: float(o["price"]["grandTotal"]))
                price = int(float(best["price"]["grandTotal"]))
                segments = best["itineraries"][0]["segments"]
                stops = len(segments) - 1
                airline = segments[0].get("carrierCode", "")
                ret_date = depart + relativedelta(days=10)
                results.append({
                    "travel_month": depart.strftime("%Y-%m-01"),
                    "price_inr": price,
                    "stops": stops,
                    "airline": airline,
                    "depart_date": depart.isoformat(),
                    "return_date": ret_date.isoformat(),
                    "raw": {"source": "amadeus", "id": best.get("id", "")},
                })
            except Exception:
                continue
        return results
