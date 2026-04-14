# Gold Nuggets — Actionable Research Findings

*This file is written by dream sessions and read by the main Opus orchestrator.*
*Each nugget is a distilled, actionable insight ready for implementation.*

## Format
Each nugget has:
- **Finding**: What was discovered
- **Evidence**: Data that supports it
- **Action**: Specific code change or parameter adjustment
- **Status**: proposed / implemented / rejected
- **Date**: When discovered

---

## Existing Nuggets (from human-AI sessions)

### N001: A-tier is anti-signal (65.2% when faded)
- **Finding**: A-tier trades (bullish sent + bearish tech) are systematically wrong
- **Evidence**: 23 trades, 34.8% original → 65.2% faded
- **Action**: Implemented as AF-tier in classify_tier_v2.py
- **Status**: implemented
- **Date**: 2026-04-10

### N002: Crypto trap combo (14.3% accuracy)
- **Finding**: long + momentum Hurst + bearish tech = 14.3% accuracy
- **Evidence**: 7 trades, all during Apr 8 drawdown
- **Action**: Gated to tier D in crypto combiner
- **Status**: implemented
- **Date**: 2026-04-10

### N003: Crypto peak hours (14:00-19:00 UTC) massively outperform
- **Finding**: 18:00 UTC = 96.4% accuracy (28 trades), 19:00 = 79.0% (62 trades), 14:00 = 73.7% (38 trades). After 19:00, accuracy collapses: 20:00 = 25.0%, 22:00 = 10.3%.
- **Evidence**: 679 closed crypto trades. 18:00 UTC: binomial p ≈ 2e-10 vs 50%. 19:00 now at 79.0% on 62 trades (was 100% on 15 — still elite but regressed to a realistic mean). 22:00 UTC: 3/29 wins, p < 0.001 anti-signal.
- **Action**: (1) Kelly 1.5x boost for 18:00 UTC trades, (2) Gate or fade 20:00-22:00 UTC trades, (3) Consider adding 14:00 UTC to peak boost
- **Status**: implementing (P0 gate deployed 2026-04-14 for hours 20, 22)
- **Date**: 2026-04-10, updated 2026-04-14 (P0 deployed by Opus morning session)

### N004: Cross-market tempo — JSE↔US ANTI-correlation (MAJOR)
- **Finding**: Original hypothesis REJECTED. Instead: JSE and US are anti-correlated same-day (r=-0.695, p≈0.03). 8/9 days moved in opposite directions. Crypto→JSE lag = 60% (suggestive, not significant at n=15).
- **Evidence**: 9 JSE-US overlap days, Pearson r=-0.695, t=-2.56. 15 crypto→JSE lag pairs, z=0.77. Full analysis in dreams/cross_market_tempo.md.
- **Action**: After JSE close (14:15 UTC), use JSE net direction as CONTRARIAN input for US tier classification at 19:00 UTC. Start with soft weight (0.1) and validate on 20 trades.
- **Risk**: n=9 is small. May be artifact of extreme fear regime (F&G 8-17). Monitor if persists when F&G normalizes.
- **Status**: proposed
- **Date**: 2026-04-10, updated 2026-04-13 (Opus Dream #1 — statistically tested)

### N005: Crypto 22:00 UTC as fade signal
- **Finding**: 22:00 UTC crypto trades are 10.3% accurate (29 trades) — stronger anti-signal than stock disagreement (31%). Fading would yield ~89.7% theoretical accuracy.
- **Evidence**: 29 trades, 3 wins, 26 losses. Binomial p < 0.001 vs 50%.
- **Action**: In crypto_engine/predictor.py, if scan hour == 22 UTC, flip direction. Creates a crypto "F-tier" equivalent.
- **Risk**: Verify 22:00 cron fires consistently. Check if losses cluster on one bad day or spread across dates.
- **Status**: superseded by N003 P0 gate (H22 now gated entirely; fade deferred)
- **Date**: 2026-04-13 (Opus Dream #1)

### N006: Per-stock dogs — SPY, HD, AMZN, MSFT are persistent losers
- **Finding**: Several stocks consistently lose across all tiers. SPY at 12.5% (8t), AMZN at 30.8% (13t), MSFT at 30% (10t), HD at 22.2% (9t).
- **Evidence**: 605 clean closed trades. SPY p≈0.03 for anti-signal (binomial).
- **Action**: Gate SPY/QQQ index ETFs to tier D (no trade). Consider per-stock fade for HD, AMZN, MSFT with more evidence (N>15).
- **Status**: proposed
- **Date**: 2026-04-14 (overnight research: per-stock personalities)

### N007: Stock A-tier DOWN is anti-signal (17.6% acc, 7d)
- **Finding**: A-tier trades predicting DOWN have 17.6% accuracy (17 trades, 7d). A-tier UP is 46.2% (13 trades). The AF fade only catches bullish-sent+bearish-tech, missing bearish A-tier calls.
- **Evidence**: 30 A-tier trades in 7d. DOWN: 3/17=17.6%. UP: 6/13=46.2%. Need all-time data to validate.
- **Action**: Investigate A-tier classification. Possibly extend AF fade to all A-tier predictions (not just bullish-sentiment ones).
- **Risk**: 7d sample may be regime-specific (extreme fear F&G). Need all-time validation.
- **Status**: proposed
- **Date**: 2026-04-14

---
