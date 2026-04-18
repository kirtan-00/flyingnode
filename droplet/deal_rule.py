from dataclasses import dataclass
from typing import Optional  # for 3.8+ compat on droplet


@dataclass(frozen=True)
class Observation:
    price_inr: int
    stops: int
    layover_hours: Optional[float]
    bag_included: Optional[bool]


@dataclass(frozen=True)
class Baseline:
    median_price_inr: int
    sample_count: int


@dataclass(frozen=True)
class DealResult:
    is_deal: bool
    savings_pct: int


MIN_SAMPLES = 5
STD_THRESHOLD = 0.55      # price must be < 55% of baseline (≥45% off)
STRICT_THRESHOLD = 0.45   # 55%+ off overrides missing-bag rejection
MAX_STOPS = 2
MAX_LAYOVER_HOURS = 6


def evaluate(obs: Observation, baseline: Baseline) -> DealResult:
    if baseline.sample_count < MIN_SAMPLES:
        return DealResult(False, 0)
    if obs.stops > MAX_STOPS:
        return DealResult(False, 0)
    if obs.layover_hours is not None and obs.layover_hours > MAX_LAYOVER_HOURS:
        return DealResult(False, 0)
    ratio = obs.price_inr / baseline.median_price_inr
    if ratio > STD_THRESHOLD:
        return DealResult(False, 0)
    if obs.bag_included is False and ratio > STRICT_THRESHOLD:
        return DealResult(False, 0)
    savings = int(round((1 - ratio) * 100))
    return DealResult(True, savings)
