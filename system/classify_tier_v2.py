"""Market-specific tier classification (v3 — split classifier).

JSE and US markets have fundamentally different signal profiles:
  - JSE B-tier: 54.9% (profitable)  vs  US B-tier: 32.6% (catastrophic)
  - JSE A-tier: 31.8% (anti-signal) vs  US A-tier: n/a (too few)
  - JSE BF:     61.4% (best JSE)    vs  US BF:     58.5% (best US)
  - US F-tier:  56.8% (solid)       vs  JSE F:     57.8% (solid)

This module splits classification into market-specific functions
so each market gets rules backed by its own data.

Signal combo data (April 2026, 600+ closed trades):
JSE best combos:
  up+neutral+neutral   100% on 3 (tiny sample)
  down+neutral+bullish  83% on 6
  up+bullish+neutral    68% on 19
  down+bullish+bullish  67% on 39
  up+bearish+neutral    63% on 8
  up+bullish+bearish    58% on 12
  down+bearish+bearish  57% on 28
  down+bearish+bullish  57% on 37

US best combos:
  down+bullish+bearish  60% on 37  (classic fade: bullish sent but bearish tech)
  up+bullish+bearish    59% on 53  (same pattern: sent/tech disagree)
  down+bearish+bearish  57% on 30
  down+bearish+neutral  53% on 36

Tiers: S > A > AF > BF > B > C > D > E > F(faded disagree)
"""


def classify_tier_jse(direction, layers_agree, hour_utc, confidence,
                      sent_direction="neutral", tech_direction="neutral",
                      sent_score=5.0):
    """JSE-specific tier classification.

    Key JSE findings:
      - BF tier is best (61.4%) — fading UP calls works
      - B tier is profitable (54.9%) — keep as real traded tier
      - A tier is anti-signal (31.8%) — must be faded to AF
      - down+bullish+bullish: 67% on 39 — strong
      - up+bullish+neutral: 68% on 19 — strong
      - down+bullish+bearish: 30% — AVOID (bearish tech + bullish sent + down = bad)
    """
    if not layers_agree:
        return "E"  # Anti-signal: disagreement

    # Sentiment buckets
    bearish_sent = sent_score is not None and sent_score < 4
    bullish_sent = sent_score is not None and sent_score >= 6

    # Close-time window: JSE 13:00-15:00 UTC (15:00-17:00 SAST)
    in_close_time = 13 <= hour_utc <= 15

    # === ANTI-PATTERN: down + bullish sent + bearish tech = 30.4% on 23 ===
    # This is a known trap — looks like a strong setup but fails
    if direction == "down" and bullish_sent and tech_direction == "bearish":
        return "AF"  # Anti-signal: 30.4%% acc -> fade to ~70%%

    # === ANTI-PATTERN: down + neutral sent + bearish tech = 20% on 5 ===
    if direction == "down" and not bullish_sent and not bearish_sent and tech_direction == "bearish":
        return "D"

    # === S-TIER: highest conviction (65%+ acc, decent sample) ===

    # down + neutral sent + bullish tech: 83% on 6 (small but strong)
    if direction == "down" and not bullish_sent and not bearish_sent and tech_direction == "bullish":
        return "S" if in_close_time else "A"

    # up + bullish sent + neutral tech: 68% on 19
    if direction == "up" and bullish_sent and tech_direction == "neutral":
        return "S" if in_close_time else "A"

    # down + bullish sent + bullish tech: 67% on 39 (large sample!)
    if direction == "down" and bullish_sent and tech_direction == "bullish":
        return "S" if in_close_time else "A"

    # === A-TIER: strong combos (55-65% accuracy) ===
    # NOTE: JSE A-tier historically 31.8% — but that was old rules.
    # New A-tier rules are backed by 55%+ combos.

    # up + bearish sent + neutral tech: 63% on 8
    if direction == "up" and bearish_sent and tech_direction == "neutral":
        return "A" if in_close_time else "BF"

    # AF ANTI-SIGNAL: bullish sent + bearish tech → market follows tech 65% of the time
    # These patterns are the ACTUAL anti-signals (30-35% accuracy when traded directly)
    if bullish_sent and tech_direction == "bearish" and direction == "down":
        return "AF"  # Will be faded by ranked_predictor direction flip for AF tier

    # up + bullish sent + bearish tech: 58% on 12
    if direction == "up" and bullish_sent and tech_direction == "bearish":
        return "A" if in_close_time else "BF"

    # down + bearish sent + bearish tech: 57% on 28
    if direction == "down" and bearish_sent and tech_direction == "bearish":
        return "A" if in_close_time else "B"

    # down + bearish sent + bullish tech: 57% on 37
    if direction == "down" and bearish_sent and tech_direction == "bullish":
        return "A" if in_close_time else "B"

    # === BF-TIER: borderline, trade with caution ===

    # down + bullish sent + neutral tech: 52% on 21
    if direction == "down" and bullish_sent and tech_direction == "neutral":
        return "BF" if in_close_time else "B"

    # === B-TIER: JSE B is actually profitable (54.9%) — keep as traded ===
    # Off close-time with some signal
    if not in_close_time:
        return "B"

    # === C-TIER: close-time but weak combo ===
    return "C"


def classify_tier_us(direction, layers_agree, hour_utc, confidence,
                     sent_direction="neutral", tech_direction="neutral",
                     sent_score=5.0):
    """US-specific tier classification.

    Key US findings:
      - B tier is catastrophic (32.6%) — MUST be tracking-only
      - C tier is bad (41.4%) — tracking-only
      - BF tier works (58.5%) — fading bullish calls is the best US strategy
      - F tier solid (56.8%) — faded disagreement works
      - S tier mediocre (52.9%) — old S rules don't work for US
      - down+bullish+bearish: 60% on 37 — BEST US combo (fade pattern)
      - up+bullish+bearish: 59% on 53 — second best (also a fade)
      - up+bullish+bullish: 10% on 10 — CATASTROPHIC, must avoid
    """
    if not layers_agree:
        return "E"  # Anti-signal: disagreement

    # Sentiment buckets
    bearish_sent = sent_score is not None and sent_score < 4
    bullish_sent = sent_score is not None and sent_score >= 6

    # Close-time window: US 19:00-21:00 UTC
    in_close_time = 19 <= hour_utc <= 21

    # === CATASTROPHIC: up + bullish sent + bullish tech = 10% on 10 ===
    # Everything agrees bullish -> model is almost always wrong
    if direction == "up" and bullish_sent and tech_direction == "bullish":
        return "D"  # Never trade this — 90% loss rate

    # === ANTI-PATTERN: down + neutral sent + bearish tech = 17% on 6 ===
    if direction == "down" and not bullish_sent and not bearish_sent and tech_direction == "bearish":
        return "D"

    # === ANTI-PATTERN: down + bullish sent + neutral tech = 31% on 26 ===
    if direction == "down" and bullish_sent and tech_direction == "neutral":
        return "D"

    # === S-TIER: best US combos (58%+ accuracy, good sample) ===

    # down + bullish sent + bearish tech: 60% on 37 (best US combo)
    # This is a fade pattern: sentiment says up, technicals say down
    if direction == "down" and bullish_sent and tech_direction == "bearish":
        return "S" if in_close_time else "A"

    # up + bullish sent + bearish tech: 59% on 53 (large sample!)
    # Another fade: model says up but technicals disagree
    if direction == "up" and bullish_sent and tech_direction == "bearish":
        return "S" if in_close_time else "A"

    # === A-TIER: solid combos (53-58%) ===

    # down + bearish sent + bearish tech: 57% on 30
    if direction == "down" and bearish_sent and tech_direction == "bearish":
        return "A" if in_close_time else "BF"

    # down + bearish sent + neutral tech: 53% on 36
    if direction == "down" and bearish_sent and tech_direction == "neutral":
        return "A" if in_close_time else "BF"

    # === BF-TIER: borderline trades ===

    # up + bullish sent + neutral tech: 41% on 32
    # Marginal — only trade as fade (flip direction)
    if direction == "up" and bullish_sent and tech_direction == "neutral":
        return "BF"

    # down + bearish sent + bullish tech: 42% on 12
    if direction == "down" and bearish_sent and tech_direction == "bullish":
        return "BF"

    # === B-TIER: US B is catastrophic (32.6%) — tracking only ===
    if not in_close_time:
        return "B"

    # === C-TIER: US C is also bad (41.4%) — tracking only ===
    return "C"


def classify_tier(market_type, layers_agree, hour_utc, confidence,
                  sent_direction="neutral", tech_direction="neutral",
                  sent_score=5.0, direction="neutral"):
    """Dispatcher: routes to market-specific classifier.

    Crypto uses simple rules (no close-time advantage).
    JSE and US have completely different optimal rules.
    """
    if not layers_agree:
        return "E"

    # Crypto — separate simple rules, no close-time advantage
    if market_type == "crypto":
        strong_agree = (sent_direction != "neutral" and tech_direction != "neutral")
        if strong_agree and confidence > 0.25:
            return "C"
        return "D"

    if market_type == "jse":
        return classify_tier_jse(
            direction=direction,
            layers_agree=layers_agree,
            hour_utc=hour_utc,
            confidence=confidence,
            sent_direction=sent_direction,
            tech_direction=tech_direction,
            sent_score=sent_score,
        )

    if market_type == "us":
        return classify_tier_us(
            direction=direction,
            layers_agree=layers_agree,
            hour_utc=hour_utc,
            confidence=confidence,
            sent_direction=sent_direction,
            tech_direction=tech_direction,
            sent_score=sent_score,
        )

    # Unknown market — fall back to conservative
    return "C"


def kelly_for_tier(tier, market_type="us"):
    """Fractional Kelly based on tier + market.

    JSE B-tier is tradeable (54.9% acc) so it gets Kelly > 0.
    US B-tier is catastrophic (32.6%) so Kelly = 0 (tracking only).
    US C-tier is also bad (41.4%) so Kelly = 0.
    """
    # Base Kelly by tier
    base = {
        "E": 0,          # Anti-signal: never trade original direction
        "D": 0,          # Known anti-pattern: never trade
        "C": 0.05,       # Low conviction (JSE only; US overridden below)
        "B": 0,          # Default tracking only (overridden for JSE)
        "BF": 0.10,      # Faded bullish: flip UP->DOWN
        "F": 0.10,       # Faded disagree: flip direction
        "AF": 0.15,      # Faded A-tier
        "A": 0.20,       # High conviction
        "S": 0.25,       # Full conviction
    }.get(tier, 0)

    # Market-specific overrides
    if market_type == "jse":
        if tier == "B":
            return 0.08   # JSE B-tier is profitable (54.9%) — small position
        if tier == "C":
            return 0.05   # JSE C-tier marginal (52.1%) — tiny position
    elif market_type == "us":
        if tier == "B":
            return 0       # US B-tier: 32.6% — tracking only
        if tier == "C":
            return 0       # US C-tier: 41.4% — tracking only

    return base
