# BlackBerry (BB) — Research log

Chronological notes. Add a new dated section after each research session (Claude, reading 10-K, earnings call, etc.).

---

## Template for each entry

```markdown
### YYYY-MM-DD — [Topic, e.g. "Fable 5 initial deep dive"]

**Sources:** (links, filings, prompt session)

**Key findings:**
-

**Changed my view?** (yes/no — how)

**Open questions:**
-
```

---

## Entries

### 2026-07-01 — Multi-agent sell-vs-hold debate (Claude Code session)

**Sources:** See `sources.md` (Q1 FY27 8-K, earnings transcript, Form 4 feed, post-earnings analyst notes). Setup: Bull and Bear research agents ran independent web research in parallel, exchanged rebuttals, verdict arbitrated on Claude Fable 5. Prior standalone Fable 5 deep-dive (owner's pasted research) used as input and independently re-verified against live sources.

**Key findings:**
- **Position reality check:** at ~$13.07 the 5,000 shares are worth ~$65k vs ~$77.5k basis → unrealized LOSS ~$12–14.5k. The "sell the winner at the high" framing was wrong; this is a tax-loss-harvesting decision.
- **Why the stock is running (all public, all verified):** Q1 FY27 blowout June 24–25 (rev $152.9M +26%, ~14% beat; adj EBITDA +144%; 5th straight GAAP-profitable quarter; first positive fiscal-Q1 OCF in 9 years), raised FY27 guidance, April 2026 NVIDIA IGX Thor/QNX "physical AI" expansion (+15% day), post-earnings upgrades (CIBC $13, Stifel Buy $12), record retail volume (Citadel Sec.: May–Jun 2026 broke Jan-2021 records).
- **"AI phone" theory: dead.** BB makes no phones; Clicks/Unihertz keyboard devices are third-party, $0 BB revenue. The AI angle is QNX in robotics/edge ("physical AI"), not handsets.
- **"Insiders know something" theory: dead.** Zero open-market insider buys in 2026; CEO/CFO Form 4 sales were RSU-vesting/tax mechanics at $3.56–$3.88. Company NCIB buyback exists but is ~1 day of volume — negligible support (Bear's point).
- **Debate outcome:** Bull opened "hold all 5,000" (EV ~$14; backlog $950M; SecuSUITE-to-2033; NVIDIA option). Bear opened "sell 90–100%" (~55–60x EV/EBITDA on guidance; RSI 79–88; third euphoric spike; short interest rising into rally; tax asset). After rebuttals BOTH converged toward the middle: Bull → trim 25%, Bear → sell 80% keep 1,000-share runner w/ ~$10 stop. Arbiter: **sell 60–70%, keep 1,500–2,000 runner, hard stop $9.80, reassess at Q2 (~Sept 24)** — see `decision.md`.
- Best single exchange: Bear killed the buyback argument (26.8M-share NCIB ≈ one day's volume); Bull killed the short-interest argument (5.84% of float is low, not meme-crowding; shorts have been wrong all year).

**Changed my view?** Yes — walked in "lean hold, momentum is good"; walked out "sell most into strength, keep a protected runner." The pivotal realizations: (1) underwater means selling is tax-POSITIVE, (2) even the Bull's probability-weighted EV (+7%) doesn't pay for the variance, (3) the rally is fully explained by public news — there is no hidden insider catalyst to wait for.

**Open questions:**
- QNX *royalty* (recognized) revenue vs backlog conversion rate — get the split from the Q2 FY27 print (~Sept 24).
- How much of FY27 Secure Comms guidance is the Canada/DND deployment, and when does it start recognizing?
- Exact share count on latest 10-Q (dilution from converts/RSUs) — verify the ~586M figure.
- Confirm exact lot-level cost basis with the broker before selling (owner's "$15–16" is an estimate; actual harvestable loss depends on real lots).

### 2026-07-01 — Session 2: expanded 4-specialist position-blind team + monitor tool build

**Sources:** Fundamentals / Technicals / Flow / Industry specialist agents (each ran independent web research with no knowledge of the position); outputs synthesized in `outlook.md`. Tool built and tested in `tools/bb_monitor.py`.

**Key findings:**
- **Basis correction from owner:** lots are mixed (~$13 and ~$16, split TBD). At an assumed 50/50 split the blended basis is ~$14.50 → unrealized loss ~$7.2k, not $12–14.5k. Lot selection now matters: sell the $16 lots for the tax loss; the $13 lots are near flat.
- **QNX structure confirmed:** wholly-owned since 2010 (ex-Harman), 100% consolidated — QNX wins flow straight to BB EPS, no leakage. A QNX spin-off was floated in 2023 and shelved in 2024; dormant sum-of-the-parts catalyst.
- **NEW and material — Fairfax Financial is exiting:** sold 5.39M shares (~March 2026 filing) and dropped below the 5% threshold by May 4, 2026, ending 13D obligations. BB's 25-year anchor holder is distributing into this rally. Combined with zero insider buys and short interest RISING into new highs (31.7M → 34.2M shares), the smart-money paper trail leans distribution while retail drives the tape.
- **Next 2–8 weeks (position-blind technical view):** ~45% high-level chop $11–14, ~25% continuation to $14–15 then ~$18, ~30% snap-back to $9.84/$8–9. Only ~1.2 days-to-cover: no short-squeeze fuel. Watch: volume fade at new highs, RSI divergence, failed $13.59 retest, gap-fill risk to ~$11.
- **Fundamental trajectory:** FY28E ~$690–730M rev / ~$155–180M EBITDA, FY29E ~$800–850M / ~$190–220M (agent estimates — no sell-side consensus that far out). 12-mo fair-value map: bear $6–8 (30%), base $12–15 (45%), bull $17–20+ (25%).
- **Industry:** QNX moat (safety microkernel, ASIL-D switching costs) intact and incrementally strengthening; biggest threat is OEM royalty-squeeze economics (~35% prob. by 2028–30), not displacement. Robotics = real but small ($30–60M incremental by FY29, est.). Secure Comms = modest growth with NATO/defense tailwind, not a melting ice cube.
- **Tool:** `tools/bb_monitor.py` built per handoff spec (lot-based CONFIG, hard stop $9.80, tranches 13.60/15.50/18, exhaustion, trailing stop, wash-sale clock, earnings reminder, CSV audit, --once/--loop/--backtest/--csv). Backtest verified on synthetic data: correctly flags the April NVIDIA gap and June 25 earnings gap as exhaustion events. Live yfinance fetch blocked in the research sandbox (network policy) but code path verified; run locally.

**Changed my view?** Refines rather than reverses the Session-1 verdict. The trim-into-strength conclusion actually got *stronger* on the flow evidence (Fairfax exiting, shorts adding, retail-only demand) even as the loss math got *smaller* (blended basis $14.50). The position-blind team's message to a NEW investor — "don't buy a full position at $13, dip zone is $8–11" — is the mirror image of "trim a concentrated 5,000-share position at $13."

**Open questions:**
- Actual lot split between ~$13 and ~$16 purchases (owner's broker records) — drives the harvestable loss.
- Q2 13F season (Aug 14): did active managers chase or trim?
- Short-interest print ~July 24: still rising into strength?
- Any Form 4 discretionary sales at $12–13 filed in early July.
