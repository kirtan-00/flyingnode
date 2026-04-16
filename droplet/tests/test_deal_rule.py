from droplet.deal_rule import evaluate, Observation, Baseline

B5 = Baseline(median_price_inr=60000, sample_count=5)


def test_qualifies_at_45_pct_off_with_good_itinerary():
    o = Observation(price_inr=33000, stops=0, layover_hours=None, bag_included=True)
    result = evaluate(o, B5)
    assert result.is_deal
    assert result.savings_pct == 45


def test_rejects_when_under_threshold():
    o = Observation(price_inr=35000, stops=0, layover_hours=0, bag_included=True)
    assert not evaluate(o, B5).is_deal  # 41.6% off, below 45%


def test_rejects_two_stops():
    o = Observation(price_inr=20000, stops=2, layover_hours=4, bag_included=True)
    assert not evaluate(o, B5).is_deal


def test_rejects_long_layover():
    o = Observation(price_inr=20000, stops=1, layover_hours=7, bag_included=True)
    assert not evaluate(o, B5).is_deal


def test_rejects_no_bag_at_moderate_discount():
    o = Observation(price_inr=30000, stops=0, layover_hours=None, bag_included=False)
    assert not evaluate(o, B5).is_deal  # 50% off but no bag — needs 55%+


def test_accepts_no_bag_at_extreme_discount():
    o = Observation(price_inr=26000, stops=0, layover_hours=None, bag_included=False)
    assert evaluate(o, B5).is_deal  # 56.7% off, bag-unknown override kicks in


def test_rejects_insufficient_baseline_samples():
    o = Observation(price_inr=20000, stops=0, layover_hours=None, bag_included=True)
    assert not evaluate(o, Baseline(60000, sample_count=4)).is_deal


def test_accepts_missing_bag_info_at_normal_threshold():
    # bag_included is None (not False) — should pass at ≥45% off
    o = Observation(price_inr=33000, stops=0, layover_hours=None, bag_included=None)
    assert evaluate(o, B5).is_deal
