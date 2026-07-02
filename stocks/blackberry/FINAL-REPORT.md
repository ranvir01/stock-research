# BlackBerry (BB) — Final Report & Action Plan

**Prepared:** July 2, 2026 · **Price reference:** ~$13.07 (52-wk $3.12–$13.59) · **Position:** 5,000 shares in two lots (~2,500 @ ~$13, ~2,500 @ ~$16; blended ~$14.50, basis ~$72,500)

**How this was produced:** two research sessions totaling **seven independent AI analyst perspectives** — a Bull-vs-Bear adversarial debate with rebuttal rounds, then a position-blind team of Fundamentals, Technicals, Flow, and Industry specialists, all synthesized and arbitrated on Claude Fable 5, every material fact verified against primary sources (SEC filings, Form 4s, 13D/13F, earnings releases). Full workings: `thesis.md`, `decision.md`, `outlook.md`, `research-log.md`, `sources.md`.

*This is rigorous decision-support, not licensed personalized financial advice — the honest version of "best advice" is that discipline and tax mechanics are the only edges reliably available to a retail holder, and this plan maximizes both. Confirm lots with your broker and tax treatment with a CPA.*

---

## 1. The Verdict

**Sell ~70% into this strength — tax-smart by lot — and run the rest with mechanical rules.**

| # | Action | Detail |
|---|--------|--------|
| 1 | **SELL the entire ~$16 lot (≈2,500 sh) now** | At ~$13.07 this harvests ≈ **$7,300 of long-term capital loss** (≈$2.93/sh) while exiting at multi-year highs. The loss offsets other gains 1:1, then $3,000/yr vs ordinary income, carries forward forever. **Instruct the broker to sell these specific lots — do not let it default to FIFO.** |
| 2 | **SELL ~1,000 sh of the ~$13 lot** | Roughly tax-neutral (that lot is ~flat). Brings total trim to ~3,500 sh (70%), proceeds ≈ **$45,700**. |
| 3 | **KEEP ~1,500 sh as the runner** | ≈$19,600 exposure — small enough that a 40% drawdown doesn't hurt you, big enough to pay if the QNX story keeps re-rating. |
| 4 | **Set the stop the same day** | GTC alert/stop: **any daily close below $9.80 → sell the runner, no exceptions.** |
| 5 | **Optional income:** sell 15 covered calls at the **$15 strike**, 1–2 months out | IV is ~100%+ — premium is rich. If assigned you exit above your blended basis; if not, you keep the premium. |
| 6 | **Park proceeds in cash/T-bills** | Redeployment is a separate decision. Do not auto-roll into another momentum name. |
| 7 | **Run the monitor daily** | `python tools/bb_monitor.py --once` (or `--loop 30`). Fill `loss_sale_date` in CONFIG the day you sell. Every run regenerates **`tools/bb_report.html`** — this entire report as a live page with current price, P&L, and each trigger's ARMED/FIRED status. Test offline anytime with `--csv sample_bb.csv`. |

Execution mechanics: use **limit orders** near the ask in 2–3 slices (liquidity is deep — ~28M sh/day — but avoid market orders at the open). The exit *window* matters more than the exact print.

---

## 2. Why — the five facts that decided it

1. **You hold a loss, not a win.** Even at the 52-week high the stock sits below your blended basis. Selling the $16 lot converts five dead years into a ~$7,300 tax asset — the only guaranteed return available in this whole situation.
2. **The smart-money paper trail points the other way.** Fairfax Financial — BB's anchor investor for 25 years — sold 5.39M shares and dropped below the 5% disclosure threshold in May. Insiders bought **zero** shares all year. Short interest **rose** into the highs. Retail volume (record-breaking, per Citadel Securities) is the only bid.
3. **The price already pays for FY29.** ~55x forward EV/EBITDA on management's own guidance; trading at/above nearly every analyst target ($7.58–$13 range). The fundamentals agents' own FY29 model ($800–850M revenue) supports today's price only if execution is flawless *and* the multiple holds.
4. **The tape is stretched to historical extremes.** RSI 79–88, price 29% above the 20-day SMA, 155% above the 200-day — and BB's own history (Jan 2021: $28.77, Jun 2021: $20.17) gave back 60–70% within months from exactly this profile, both times.
5. **But the turnaround is real** — 5 straight GAAP-profitable quarters, $950M QNX royalty backlog, NVIDIA physical-AI optionality, SecuSUITE locked to 2033, and QNX is 100% wholly-owned so every QNX dollar is a BB dollar. That's why the answer is a **runner with rules**, not zero.

## 3. What to expect next (probability map)

| Horizon | Bear | Base | Bull |
|---|---|---|---|
| **2–8 weeks** | 30% — snap-back to $9.84 or the $8–9 base | **45% — chop $11–14 while RSI cools** | 25% — through $13.59 → $14–15 → ~$18 |
| **12 months** | 30% — $6–8 (multiple compression) | **45% — $12–15 (grows into valuation)** | 25% — $17–20+ (re-rating persists) |

Implication: ~70–75% odds the stock is **not** meaningfully higher in 8 weeks. The plan doesn't need the bull case to work — the runner captures it if it comes, the tranche alerts sell it on the way up ($13.60 / $15.50 / $18), and the stop caps the bear case.

## 4. The calendar (set these reminders)

| Date | Event | What to do |
|---|---|---|
| **Today** | Execute §1 | Confirm actual lots with broker first; fill tool CONFIG |
| **Sale date + 31 days** (~Aug 2 if sold Jul 2) | Wash-sale clock ends | Until then: buy NO BB in ANY account (incl. IRA/spouse) |
| **~Jul 24** | NYSE short-interest print (Jul 15 settle) | Still rising into strength = distribution confirmed |
| **Aug 14** | Q2 13F deadline | Did active managers chase or trim? Fairfax follow-through? |
| **~Sep 24** | **Q2 FY27 earnings** | Checklist: QNX *royalty* revenue (not backlog) accelerating? Secure Comms/DND revenue recognizing? Guidance reiterated? |

## 5. Decision tree for the runner

- **Daily close < $9.80** → sell everything. No debate, no "one more day."
- **Crosses $13.60** → trim ~500 sh · **$15.50** → trim ~500 sh (above blended basis) · **$18.00** → exit the runner (2021 spike zone).
- **Q2 print (Sep 24):** royalties accelerate AND price holds >$11 → keep runner to $15.50+. Guidance cut or QNX stalls → exit on the print.
- **Re-enter later only if ALL three:** wash-sale window passed · pullback to $8–11 holds on a closing basis · a genuine insider open-market buy or royalty acceleration shows up. Write it down now so future-you doesn't chase at $16.
- **Signs we were wrong to trim** (and that's okay): volume-backed weekly closes above $15.50 with institutions adding in the Aug 13Fs — the runner still participates; you were paid ~$45.7k + the tax asset to be wrong smaller.

## 6. What would flip the whole view

**More bullish:** an insider finally buys in the open market (first of 2026 = real signal) · QNX royalty conversion beats two quarters straight · a revived QNX spin-off/IPO (floated 2023, shelved 2024 — dormant sum-of-the-parts catalyst).
**More bearish:** a major OEM drops QNX from the *safety layer* of a next-gen platform · Fairfax keeps liquidating · close below $8 on volume (failed breakout → $6–7).

---

*Sources for every claim: `sources.md` and `outlook.md`. Tool: `tools/bb_monitor.py` (tested; alerts only, never trades). Prices move — verify live quotes before entering orders.*
