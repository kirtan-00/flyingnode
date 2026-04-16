# flyingnode — design spec (v0)

**Date:** 2026-04-16
**Owner:** Kirtan Purohit
**Status:** Draft → pending user review

## One-liner

A curated mistake-fare alert service for Indian travellers. India-first clone of Scott's Cheap Flights / Zomunk, but free, algorithmic, and public. Ships affiliate-monetised from day one.

## Goals

1. Surface round-trip international fares departing from major Indian airports that are ≥45% below their 90-day median — "a deal worth interrupting someone's day for."
2. Do it with zero paid API tiers and zero paid infrastructure beyond the existing Postinnator droplet.
3. Ship a functional public site at `flyingnode.com` inside 3 focused evenings (~10 hrs of build).
4. Look and feel like a product someone would trust. IndiGo-inspired: deep blue, orange price badges, generous whitespace, no clutter.

## Non-goals (v0)

- User signup, accounts, auth.
- Native mobile app or push notifications.
- Domestic Indian flights.
- One-way, multi-city, premium-cabin specialist flows.
- Human-in-the-loop curation.
- Paid subscription / premium tier.
- SMS or WhatsApp alerts.

These are deferred to v1+ once we have baseline data and evidence the deals are good.

## User flow (v0)

1. User lands on `flyingnode.com`.
2. Sees a reverse-chronological feed of live deal cards: `BLR → Tokyo · ₹23,400 · was ₹68,000 · 66% off · Travel Sep-Nov 2026`.
3. Each card has a sparkline of 90-day price history for that route-month bucket.
4. CTA button opens Google Flights in a new tab, pre-filled with the route and date range — affiliate redirect via Travelpayouts so outbound clicks earn commission.
5. Optional sidebar: "email me the daily digest" — single email field, no auth, Brevo stores the list, one email per day at 08:00 IST.

That's the whole product.

## Architecture

Three processes on the droplet (one Flask API, two Python scripts run by cron), one SQLite DB, one Next.js app on Vercel.

```
┌─────────────────────────────────────────────────────────────┐
│  Postinnator droplet (DO, existing, REDACTED_SERVER_IP)         │
│  Code root: /root/flyingnode/   (isolated from Postinnator) │
│                                                             │
│  ┌────────────────┐   ┌─────────────────┐                   │
│  │ poller.py      │──▶│  SQLite         │◀──┐               │
│  │ (cron, 6h)     │   │  flyingnode.db  │   │               │
│  └────────────────┘   │  (separate file,│   │               │
│                       │   never shares  │   │               │
│  ┌────────────────┐   │   postinnator.db)│  │               │
│  │ digest.py      │   └─────────────────┘   │               │
│  │ (cron, 08:00)  │      ▲                  │               │
│  │ — Brevo API    │      │                  │               │
│  └────────────────┘      │                  │               │
│                     ┌────┴─────────┐        │               │
│                     │ api.py       │        │               │
│                     │ Flask :8081  │────────┘               │
│                     │ read-only    │                        │
│                     └──────────────┘                        │
│                            ▲                                │
│                            │ nginx (api.flyingnode.com)     │
└────────────────────────────┼────────────────────────────────┘
                             │ HTTPS JSON
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Vercel — Next.js 15 app                                    │
│  flyingnode.com                                             │
│  Cloudflare DNS + edge cache (revalidate=600)               │
└─────────────────────────────────────────────────────────────┘
```

### Why this shape
- Reuses the Postinnator droplet. Clean isolation via separate code root (`/root/flyingnode/`), separate DB file (`flyingnode.db` vs `postinnator.db`), separate system user (`flyingnode`), separate log dirs. Flyingnode code never reads Postinnator files and vice versa. Per the isolation rules memory, this is the only acceptable shape.
- SQLite not Postgres — matches the Postinnator pattern and the droplet's memory budget (512MB).
- Three responsibilities, three files: poller, digest, read-API. If one fails, the others keep working.
- Next.js on Vercel decouples the frontend from the droplet. The droplet only exposes a tiny JSON API. The frontend has edge caching so the droplet gets very few hits.

## Data model (SQLite file: `/root/flyingnode/flyingnode.db`)

```sql
-- canonical airport reference
CREATE TABLE airports (
  iata          TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  city          TEXT NOT NULL,
  country       TEXT NOT NULL,
  is_origin     INTEGER DEFAULT 0          -- 1 for our 3 seed Indian origins
);

-- route watchlist
CREATE TABLE routes (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  origin        TEXT NOT NULL REFERENCES airports(iata),
  destination   TEXT NOT NULL REFERENCES airports(iata),
  active        INTEGER DEFAULT 1,
  UNIQUE (origin, destination)
);

-- every fare observation we pull
CREATE TABLE fare_observations (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  route_id       INTEGER NOT NULL REFERENCES routes(id),
  travel_month   TEXT NOT NULL,              -- 'YYYY-MM-01'
  price_inr      INTEGER NOT NULL,
  stops          INTEGER NOT NULL,
  layover_hours  REAL,
  airline        TEXT,
  bag_included   INTEGER,                    -- 1/0/NULL
  raw            TEXT NOT NULL,              -- full API payload JSON
  source         TEXT NOT NULL DEFAULT 'poll', -- 'poll' | 'bootstrap'
  observed_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_fare_obs_route_month ON fare_observations(route_id, travel_month, observed_at DESC);

-- 90-day rolling median baseline, recomputed nightly
CREATE TABLE route_baselines (
  route_id         INTEGER NOT NULL REFERENCES routes(id),
  travel_month     TEXT NOT NULL,
  median_price_inr INTEGER NOT NULL,
  sample_count     INTEGER NOT NULL,
  computed_at      TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (route_id, travel_month)
);

-- live deals surfaced on the site
CREATE TABLE deals (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  route_id          INTEGER NOT NULL REFERENCES routes(id),
  travel_month      TEXT NOT NULL,
  price_inr         INTEGER NOT NULL,
  baseline_inr      INTEGER NOT NULL,
  savings_pct       INTEGER NOT NULL,
  stops             INTEGER NOT NULL,
  layover_hours     REAL,
  airline           TEXT,
  affiliate_url     TEXT NOT NULL,
  first_seen_at     TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at      TEXT NOT NULL DEFAULT (datetime('now')),
  still_live        INTEGER DEFAULT 1
);
CREATE INDEX idx_deals_live ON deals(still_live, first_seen_at DESC);

-- digest subscribers (no auth, just email)
CREATE TABLE digest_subscribers (
  email          TEXT PRIMARY KEY,
  subscribed_at  TEXT NOT NULL DEFAULT (datetime('now')),
  unsubscribed   INTEGER DEFAULT 0,
  unsubscribe_token TEXT NOT NULL
);
```

Booleans stored as `INTEGER 0/1` (SQLite convention). Dates stored as `TEXT` in ISO 8601 for simplicity and sortability.

## Seed data (v0)

**Origins (3):** DEL, BOM, BLR. Chosen because they cover ~70% of Indian international traffic and keep poll volume low. More origins added in v1 after we see detection quality.

**Destinations (~50):** curated manually — popular Indian diaspora + tourist routes: BKK, SIN, KUL, DXB, AUH, DOH, IST, LHR, CDG, FRA, AMS, JFK, EWR, SFO, YYZ, SYD, MEL, NRT, HND, ICN, HKG, TPE, CAI, ZRH, BCN, FCO, ATH, BLI (Bali/DPS), CMB, KTM, MLE, and similar.

3 origins × ~50 destinations = ~150 route-pairs to start. Poll volume: 150 × 4 times/day = 600 requests/day. Well under Travelpayouts' free tier.

## Deal pipeline

### Poller (every 6 hrs)

For each active route:
1. Call Travelpayouts `v1/prices/cheap` for the next 6 months.
2. For each monthly-cheapest result, insert into `fare_observations`. Store the full response in `raw` jsonb for debugging and future feature-engineering.
3. Immediately evaluate deal rule (see below) using the current baseline. If a deal is found, upsert into `deals` with `still_live=true`.
4. For existing `still_live=true` deals on this route-month, if today's observation is ≥10% above the deal's recorded price, mark `still_live=false` (price has moved on — don't send stale users to dead fares).

### Baseline bootstrap (once, day 1)

For each active route:
1. Call Travelpayouts `v1/prices/calendar` or `prices_for_dates` to pull 12 months of historical monthly lows.
2. Populate `fare_observations` with `observed_at = now() - synthetic offset` so the median computation treats them as historical.
3. Run the nightly baseline job once manually to seed `route_baselines`.

This is the 2-hour bootstrap investment — pays for itself vs waiting 3 weeks.

### Nightly baseline job (03:00 IST)

For each `(route_id, travel_month)`:
- Compute median of `price_inr` from `fare_observations` in the last 90 days.
- Require `sample_count >= 5` before the baseline is usable.
- Upsert into `route_baselines`.

### Deal rule

A fare observation becomes a candidate deal when **all** of these hold:
- `price_inr < 0.55 × baseline_inr`  (at least 45% below median)
- `stops <= 1`
- `layover_hours <= 6`
- `bag_included = true` OR (bag info missing AND price still < 0.45 × baseline — exceptionally cheap overrides missing baggage data)
- Baseline has `sample_count >= 5`
- Not already present in `deals` as `still_live=true` for the same `(route, travel_month)`

### Affiliate URL construction

Travelpayouts provides a `trip.com` / `kiwi` / Google Flights redirect template per result. We construct the outbound URL server-side and store it on the deal — never regenerate on click. Marketing parameter `utm_source=flyingnode` on every redirect.

## Alert pipeline

### Daily digest (08:00 IST)

1. Select all deals where `still_live=true` AND `first_seen_at >= now() - interval '24 hours'`.
2. Group by origin airport.
3. Render HTML email from a template. One card per deal, same visual language as the site.
4. For each subscriber in `digest_subscribers` where `unsubscribed=false`, send via Brevo.
5. Every email includes a one-click unsubscribe link hitting `/api/unsubscribe?token=...`.

No digest if there are zero new deals. Do not send a "nothing today" email — that trains users to ignore you.

## UI spec

### Brand

- **Primary:** IndiGo blue `#001B94` (backgrounds, CTA, logo mark)
- **Accent:** orange `#FF6B00` (price badges, savings %, "hot deal" indicators)
- **Neutral:** `#F6F7FB` background, `#0B1020` body text, `#6B7385` secondary text
- **Type:** Manrope (variable, tight tracking at display sizes) + Inter for UI body
- **Radius:** 16px on cards, 8px on inputs, 999px on badges
- **Shadow:** single layer `0 8px 32px rgba(0, 27, 148, 0.08)` — soft blue bloom, not grey

### Pages

**`/`** — deals feed
- Hero: one-liner ("Flights so cheap they feel like a glitch"), origin-picker chip row (Delhi / Mumbai / Bangalore · defaults to Delhi, persists in localStorage)
- Deal cards in a 2-column grid on desktop, stacked on mobile. Each card:
  - Route headline with airport codes and city names
  - Price in large numerals, `was ₹X` struck through, orange savings badge
  - Travel window pill (`Sep – Nov 2026`)
  - Airline + stops + layover line
  - Sparkline of last 90 days of price observations for this route-month
  - Primary CTA button "Book on Google Flights" (outbound to affiliate URL)
  - Secondary: "Share" (copies the deal URL)
- Footer: email capture for daily digest, unsubscribe link, "How this works" link

**`/how-it-works`** — one scroll page explaining the pipeline in plain English. No dark patterns, no marketing fluff.

**`/deal/[id]`** — permalink per deal, same card expanded, useful for sharing.

### Motion / polish
- Cards fade + slide up 8px on mount, staggered 40ms.
- Price number counts up on first view (framer-motion).
- No carousels. No auto-playing anything. No popups.

### Apple-fluid bar
- Every interactive element has a hover + pressed + focus state.
- Dev-tested in Safari iOS + Chrome Android before "done".
- Lighthouse ≥ 95 on mobile.

## Infrastructure

### Droplet changes
- New code root `/root/flyingnode/`.
- Python 3.12 venv under `/root/flyingnode/venv/`.
- SQLite DB at `/root/flyingnode/flyingnode.db` — mode 640, owned by root.
- Three root-crontab entries:
  - `0 */6 * * *` → `/root/flyingnode/venv/bin/python /root/flyingnode/poller.py`
  - `0 2 * * *` → `/root/flyingnode/venv/bin/python /root/flyingnode/baseline.py` (03:00 IST via server UTC)
  - `30 2 * * *` → `/root/flyingnode/venv/bin/python /root/flyingnode/digest.py` (08:00 IST — use `TZ=Asia/Kolkata` in crontab prefix for clarity)
- A small Flask app `api.py` as a systemd service on port 8081, serving `/deals`, `/airports`, `/subscribe`, `/unsubscribe`.
- Nginx server block for `api.flyingnode.com` → `127.0.0.1:8081`, Let's Encrypt cert.
- Logs to `/root/flyingnode/logs/`, rotated via logrotate.

### Vercel
- Next.js 15 app, Node 20 runtime.
- Env vars: `DATABASE_URL` (ro user, pgbouncer), `RESEND_API_KEY`, `TRAVELPAYOUTS_MARKER` (affiliate).
- Edge ISR on `/` and `/deal/[id]` with `revalidate = 600`.

### DNS (Cloudflare)
- `flyingnode.com` → Vercel.
- `api.flyingnode.com` → droplet nginx (reserved for v1, not used in v0).

## APIs used

| API | Purpose | Auth | Cost |
|---|---|---|---|
| Travelpayouts | primary fare data + affiliate redirects | `X-Access-Token` header | free, earns commission |
| Duffel (test mode) | optional baggage/fare-family enrichment when Travelpayouts is silent | bearer token | free in test |
| Amadeus self-service | nightly sanity check on 20 top routes to catch Travelpayouts price drift | OAuth2 | 2k calls/mo free |
| Brevo | email delivery | bearer token | free 3k/mo, 100/day |

All keys in droplet env file `/etc/flyingnode/env`, mode 600, owned by `flyingnode` system user.

## Observability

- Structured JSON logs (`{level, component, route, price, savings_pct, ...}`).
- `/api/health` on the droplet: returns last successful poll time, total deals active, subscriber count.
- Simple Grafana panel or just `curl | jq` — no fancy stack v0.
- A single "dead man" alert: if no poll has succeeded in 12 hours, email `REDACTED_EMAIL`.

## Timeline (commitment)

| Evening | Output |
|---|---|
| **Evening 1 (~4h)** | Droplet schema + poller running + baseline bootstrap done. Deals table populating. No frontend yet. |
| **Evening 2 (~4h)** | Next.js frontend on Vercel, IndiGo theme, live deals rendering, domain pointed, SSL live. |
| **Evening 3 (~2h)** | Daily digest live, email template polished, click-through QA, Lighthouse pass. |

**Target: flyingnode.com live with real deals by end of evening 3.**

## Open questions (with defaults)

All three have defaults I'm committing to unless user overrides during spec review.

1. **Origins v0** → DEL + BOM + BLR (3). *Override: say "add X" or "just DEL".*
2. **Droplet reuse** → yes, reuse Postinnator droplet with clean schema + user isolation. *Override: say "new box".*
3. **Public from day 1** → yes, no invite gate. *Override: say "invite-only".*

## Out of scope v0 (explicit)

- User accounts, OAuth, profiles
- Push notifications, mobile app
- Domestic flights
- Multi-city / one-way / premium cabin
- Human curation
- Paid premium tier
- SMS / WhatsApp
- A/B testing framework
- Multi-currency (INR only)

## Risks

- **Travelpayouts API rate limits or schema changes.** Mitigation: store raw jsonb so we can re-derive; add Duffel + Amadeus as redundant sources in v1.
- **Poll returns same cached price for a dead fare.** Mitigation: `still_live` freshness check each poll; stale deals auto-hide.
- **Email domain reputation.** Mitigation: SPF/DKIM/DMARC on `flyingnode.com` before first send; warm up via small list.
- **Baselines mislead during price shocks (fuel spike, festival season).** Mitigation: 90-day rolling median (not mean) handles outliers; sample_count gate prevents premature deals.
- **Shared droplet with Postinnator — cross-contamination.** Mitigation: separate Postgres schema, separate DB user, separate systemd unit names, separate log dirs, separate env file. Per the Postinnator isolation rules memory, **nothing in flyingnode ever reads from Postinnator tables or vice versa.**
