# Stock Research Lab

A personal workspace for studying stocks before making buy, hold, or sell decisions. Each ticker gets its own folder with structured notes, a decision framework, and prompts you can paste into Claude (Fable 5 or any model).

**This is not financial advice.** Use this repo to organize your thinking, document assumptions, and track how your view changes over time.

## Quick start (BlackBerry first)

1. Open [`prompts/blackberry-fable5-starter.md`](prompts/blackberry-fable5-starter.md).
2. Copy the full prompt block into Claude Fable 5 (or Claude with extended thinking).
3. Fill in your answers in [`stocks/blackberry/position.md`](stocks/blackberry/position.md) as you go.
4. Save Claude's output into the files under `stocks/blackberry/` — or paste sections into the matching templates.
5. When you have a view, write it up in [`stocks/blackberry/decision.md`](stocks/blackberry/decision.md).

## Repo layout

```
stock-research/
├── prompts/                    # Copy-paste prompts for AI-assisted research
│   └── blackberry-fable5-starter.md
├── stocks/
│   └── blackberry/             # First ticker — BB (BlackBerry Limited)
│       ├── position.md         # Your current holdings & cost basis
│       ├── research-log.md     # Dated notes as you learn
│       ├── thesis.md           # Bull / bear / base case
│       ├── decision.md         # Final action & rationale
│       └── sources.md          # Links, filings, transcripts
└── templates/                  # Duplicate for the next stock
    └── new-stock/
```

## Workflow

| Step | What you do | Where it lives |
|------|-------------|----------------|
| 1. State position | Shares, avg cost, account, emotional attachment | `position.md` |
| 2. Deep research | Business model, financials, moat, risks | Prompt → save to `research-log.md` |
| 3. Form thesis | What has to be true for the stock to work | `thesis.md` |
| 4. Decide | Hold, trim, sell, or add — with triggers | `decision.md` |
| 5. Review | Re-run prompt quarterly or after earnings | New dated entry in `research-log.md` |

## Adding another stock

```bash
cp -r templates/new-stock stocks/your-ticker
# Rename files, update ticker in prompts, add a new prompt under prompts/ if needed
```

## Tips for Claude Fable 5

- **One job per session:** Position review first, then fundamentals, then technicals — or use the single mega-prompt and ask it to section the reply.
- **Ground it in your numbers:** Always paste your actual cost basis and share count from `position.md`.
- **Ask for uncertainty:** Request bull/base/bear with probabilities and what would change your mind.
- **Commit your thinking:** After each session, edit the markdown files so future-you sees your reasoning, not just AI output.
