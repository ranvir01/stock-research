# BlackBerry (BB) — Claude Fable 5 starter prompt

Copy everything inside the fenced block below into Claude. Replace every `[FILL IN]` with your real numbers and context before sending.

---

## How to use this prompt

1. Fill in [`../stocks/blackberry/position.md`](../stocks/blackberry/position.md) first (even rough numbers).
2. Paste the prompt below into **Claude Fable 5** (or Claude with extended thinking enabled).
3. Save Claude's response into `research-log.md` with today's date.
4. Iterate: reply with *"Challenge my sell bias"* or *"Play devil's advocate for holding"* until you're satisfied.
5. Summarize your own conclusion in `decision.md` — in **your words**, not a copy-paste.

---

## THE PROMPT (copy from here)

```
You are my equity research partner. I am deciding what to do with my BlackBerry Limited (NYSE: BB) position. Be rigorous, skeptical, and specific. Cite recent public data where you can (latest reported quarter, approximate price range, major news). Flag when you are estimating vs. when you are stating reported facts. This is for my personal learning — not investment advice to others.

---

## MY SITUATION

- Ticker: BB (BlackBerry Limited)
- Exchange: NYSE (also trades TSX: BB)
- Shares held: [FILL IN]
- Average cost basis: [FILL IN] per share
- Current market value (approx): [FILL IN]
- Unrealized gain/loss: [FILL IN] ([FILL IN]%)
- How long I've held: [FILL IN]
- Why I originally bought: [FILL IN — e.g. QNX, turnaround, meme-era, dividend hope, etc.]
- My emotional state about the position: [FILL IN — frustrated, hopeful, indifferent, etc.]
- Tax situation (if relevant): [FILL IN — e.g. short-term vs long-term, loss harvesting interest]
- Portfolio context: BB is [FILL IN]% of my portfolio; I can [FILL IN — tolerate full loss / need to redeploy capital / etc.]

---

## PRIMARY QUESTION

Given my position above, should I **sell**, **hold**, **trim**, or **add**? Give a clear recommendation with reasoning, then show what would change your mind.

---

## RESEARCH FRAMEWORK — work through each section

### 1. Company snapshot (2024–2026 reality check)

- What does BlackBerry actually do today? Split revenue/margin story across:
  - **QNX** (embedded OS, automotive, IoT)
  - **BlackBerry Cybersecurity** (Cylance, unified endpoint, government)
  - **Legacy / other** (patents, licensing if still material)
- Is this still a "phone company" in investors' minds, and does that mispricing matter?
- Who are the real competitors in each segment?
- Latest known revenue mix and trend direction (growing vs shrinking segments).

### 2. Financial health

- Latest quarterly revenue, gross margin, operating income/loss, cash, debt.
- Free cash flow trend — burning or generating?
- Runway: months/quarters of cash at current burn (if applicable).
- Stock-based compensation dilution — material?
- Any going-concern or liquidity red flags in recent filings?
- Compare valuation vs. peers (cybersecurity SaaS, auto software) on EV/Revenue, EV/EBITDA, P/S — note BB's quirks (loss-making, lumpy licensing).

### 3. Business quality & moat

- QNX: switching costs, design-win pipeline, automotive design-win narrative vs. reality (Qualcomm, Android Automotive, etc.).
- Cybersecurity: differentiation vs. CrowdStrike, Microsoft, Palo Alto, etc. — win rates, churn, ARR if disclosed.
- Recurring vs one-time revenue — predictability of earnings.
- Management credibility: track record of guidance, M&A, pivots.

### 4. Catalysts (next 6–18 months)

- Earnings dates and what the street will focus on.
- Product launches, major automotive OEM wins, government contracts.
- Potential M&A (BB as target or acquirer), patent monetization, segment spin-offs.
- Index inclusion/exclusion, short interest, institutional flow.

### 5. Risks (be harsh)

- Execution risk on turnaround.
- Competition eroding QNX or endpoint share.
- Dilution, debt, or covenant risk.
- Binary legal/regulatory outcomes.
- "Value trap" pattern: cheap for a reason?
- If I sell now, what am I giving up? If I hold, what am I risking?

### 6. Technical & sentiment (secondary, not decisive)

- Approximate support/resistance levels on daily/weekly chart.
- Trend: above/below 50-day and 200-day moving averages?
- Volume, relative strength vs. QQQ / cyber ETF.
- Short interest and recent price action around earnings.
- How much of BB's move is macro (rates, small-cap risk) vs idiosyncratic?

### 7. Position decision matrix

Build a table:

| Action | Pros for me | Cons for me | Best if... |
|--------|-------------|-------------|------------|
| Sell all | | | |
| Trim 25–50% | | | |
| Hold | | | |
| Add | | | |

Then give **one primary recommendation** for my situation (not a generic "it depends" without a default).

### 8. Scenario analysis

| Scenario | Probability (your estimate) | 12-month price range | Impact on my P&L |
|----------|----------------------------|----------------------|------------------|
| Bull | | | |
| Base | | | |
| Bear | | | |

### 9. If I sell — execution plan

- Market vs limit order considerations (liquidity, spread).
- Tax-loss harvesting notes if I'm at a loss.
- What I'd redeploy into (stay in cyber/auto software theme or diversify?) — optional, 2–3 bullet ideas only.
- How to avoid regret: write down "I'll reconsider buying if ___ happens."

### 10. If I hold or add — rules

- Explicit **stop-loss or review triggers** (price level, earnings miss, segment revenue decline, etc.).
- Position size cap as % of portfolio.
- Next mandatory review date.

---

## OUTPUT FORMAT

1. **Executive summary** (≤ 200 words): recommendation + top 3 reasons.
2. **Detailed sections** 1–10 above.
3. **Open questions** I should research manually (SEC filings, specific 10-K line items, etc.).
4. **Suggested reading list**: latest 10-K/10-Q, last earnings call transcript, 2–3 credible analyst or industry sources.
5. **Questions for me** — 5 things you need from me to refine the recommendation.

---

## TONE & RULES

- Don't flatter the stock because I already own it. Steel-man the sell case first.
- Separate **facts**, **inferences**, and **speculation**.
- If data is stale, say so and tell me what to verify on BlackBerry's investor relations site or SEC EDGAR.
- End with: **"If I were in your shoes with [my cost basis] and [my % of portfolio], I would ___ because ___."**
```

---

## Follow-up prompts (after the first reply)

Use these in the same chat or a new one with context pasted in.

**Challenge the recommendation**
```
You recommended [SELL/HOLD/etc.]. Argue the opposite side as strongly as possible using the same facts. Then reconcile which argument is stronger for my specific situation.
```

**Earnings prep**
```
BB reports earnings on [DATE]. What 5 metrics from the press release and call should I watch? What results would confirm hold vs force a sell?
```

**Compare to alternatives**
```
If I sell BB and want [cyber exposure / auto software / cash], compare 3 alternative tickers to BB on growth, valuation, and balance sheet risk. Rank them for a small retail investor.
```

**Update my thesis**
```
Here is my updated research log: [PASTE]. Has my thesis improved or deteriorated? Update bull/base/bear probabilities.
```

**Devil's advocate on QNX**
```
Many BB bulls cite QNX in automotive. Give me the bear case that QNX is a slow-growth niche with limited upside to the stock. What OEM wins would prove the bulls right?
```

---

## Where to save answers

| Claude output section | Save to |
|-----------------------|---------|
| Executive summary + recommendation | `stocks/blackberry/decision.md` (draft) |
| Full research | `stocks/blackberry/research-log.md` (dated entry) |
| Bull/base/bear | `stocks/blackberry/thesis.md` |
| Links & filings | `stocks/blackberry/sources.md` |
