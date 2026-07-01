# BB Position Monitor — Claude Code handoff prompt

Final deliverable of the July 1, 2026 multi-agent debate (see `stocks/blackberry/`). Paste the block below into a fresh Claude Code session (Fable 5 recommended) in a new/empty project folder to build the execution-and-monitoring tool for the decision in `decision.md`.

---

```
Build me a single-file Python position monitor and exit-strategy tool for BlackBerry (NYSE: BB). It enforces a decision I already made after research — the tool's job is discipline, not new analysis.

MY POSITION (July 1, 2026):
- 5,000 shares BB @ ~$15.50 avg cost ($77,500 basis), long-term (held since ~2021), taxable account, WA resident
- Price reference: ~$13.07 (52-wk range $3.12–$13.59) -> position is UNDERWATER ~$12,000; breakeven $15.50
- Decision already made: SELL 3,000–3,500 shares near $13 now (tax-loss harvest into strength); HOLD 1,500–2,000 as a runner

RULES THE TOOL MUST ENFORCE (from my decision doc):
- HARD STOP: daily CLOSE below $9.80 -> alert "SELL ALL REMAINING — no exceptions"
- TRANCHE ALERTS (trim runner): cross above $13.60 (52-wk-high retest), $15.50 (breakeven), $18.00 (2021 spike zone)
- EXHAUSTION WARNING: RSI(14) > 70 AND price > 25% above 20-day SMA; also flag bearish divergence (price higher high, RSI lower high)
- WASH-SALE GUARD: I sold shares at a loss on [FILL SALE DATE]; warn me on every run until 31 days have passed that buying ANY BB (any account) disallows the loss
- EVENT REMINDER: Q2 FY27 earnings ~Sept 24, 2026 — remind me starting 7 days out to review QNX ROYALTY revenue (not backlog), Secure Comms/DND revenue, and guidance

BUILD REQUIREMENTS:
1. yfinance (or similar free source) for live/delayed price + historical OHLCV; handle network/API errors gracefully.
2. On every run print: current price, position value, unrealized P&L in $ and % vs remaining basis, distance to breakeven, distance to stop.
3. Indicators: RSI(14), SMA 20/50/200, ATR(14), % above/below each SMA.
4. Trailing-stop tracker: record highest close since a configurable start date; alert if drawdown from that high exceeds a configurable % OR the $9.80 hard floor is closed below.
5. Alerts: console summary always; plus email (smtplib) or desktop notification when any stop/tranche/exhaustion/wash-sale/earnings trigger fires. Never auto-trade — alerts only.
6. Audit log: append every check to CSV (timestamp, price, RSI, SMAs, P&L, triggers fired, suggested action).
7. CONFIG dict at top: share count, basis, stop, tranche levels, RSI threshold, trailing %, sale date for wash-sale clock, earnings date — all editable without touching logic.
8. Modes: --once (default), --loop N minutes during market hours, --backtest (replay last 12 months of daily bars and print every trigger that WOULD have fired, so I can sanity-check levels).
9. Startup banner: print my position, all active triggers, and days remaining on the wash-sale clock.
10. Keep it one runnable file + requirements.txt; clear comments; no paid APIs.

Context for calibration (verified July 1, 2026): 20-day SMA ~$9.84, 200-day ~$4.98, RSI(14) ~79–88, avg volume ~28M/day. BB's history: spikes to $28.77 (Jan 2021) and $20.17 (Jun 2021) each gave back 60–70% within months — the stop exists because of this pattern.
```

---

**After it builds:** run `--backtest` first and confirm the $9.80 stop and $13.60 tranche would have fired where you expect, then schedule the `--loop` mode during market hours. Update the CONFIG sale-date the day you execute the trim.
