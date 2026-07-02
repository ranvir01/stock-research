#!/usr/bin/env python3
"""
BlackBerry (NYSE: BB) position monitor & exit-strategy tool.

Enforces a decision already made after research (see stocks/blackberry/decision.md).
The tool's job is DISCIPLINE, not new analysis. It never trades — alerts only.

Usage:
    python bb_monitor.py                  # single check (default: --once)
    python bb_monitor.py --loop 30        # re-check every 30 min during market hours
    python bb_monitor.py --backtest       # replay last 12 months, show triggers that WOULD have fired
    python bb_monitor.py --csv FILE       # offline mode: read OHLCV from a CSV (Date,Open,High,Low,Close,Volume)

Requirements: pip install -r requirements.txt   (yfinance, pandas)
"""

import argparse
import csv
import json
import os
import smtplib
import string
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from email.message import EmailMessage

try:
    from zoneinfo import ZoneInfo
except ImportError:  # py<3.9
    ZoneInfo = None

# ============================= CONFIG =============================
# Everything the tool enforces lives here. Edit values, not logic.
CONFIG = {
    "ticker": "BB",

    # Tax lots: (shares, avg_cost). EDIT to your broker's actual lots.
    # Owner note July 2026: "some average around 13 and some 16".
    "lots": [
        (2500, 13.00),
        (2500, 16.00),
    ],

    # --- Exit rules from decision.md ---
    "hard_stop": 9.80,            # daily CLOSE below this => SELL ALL REMAINING
    "tranche_levels": {           # cross above => trim alert
        13.60: "52-wk-high retest — trim a tranche of the runner",
        15.50: "breakeven zone — strong exit candidate for remaining shares",
        18.00: "2021 secondary-spike zone — exit the runner",
    },

    # --- Momentum-exhaustion warning ---
    "rsi_period": 14,
    "rsi_overbought": 70.0,
    "sma_extension_pct": 25.0,    # close >25% above 20-day SMA + RSI>70 => warning
    "divergence_lookback": 60,    # bars scanned for bearish RSI divergence

    # --- Trailing stop ---
    "trailing_start_date": "2026-07-01",  # track highest close since this date
    "trailing_stop_pct": 15.0,            # alert if drawdown from that high exceeds this

    # --- Wash-sale clock ---
    "loss_sale_date": None,       # e.g. "2026-07-02" — set the day you sell at a loss
    "wash_sale_days": 31,         # calendar days to stay out of BB after (and before) the sale

    # --- Event reminders ---
    "earnings_date": "2026-09-24",        # Q2 FY27 (approx) — verify on BB IR page
    "earnings_warn_days": 7,
    "earnings_checklist": "review QNX ROYALTY revenue (not backlog), Secure Comms/DND revenue, FY27 guidance",

    # --- Output / alerting ---
    "csv_log": "bb_monitor_log.csv",      # audit trail, appended every run
    "state_file": "bb_monitor_state.json",# persists trailing high + already-fired tranches
    "html_report": "bb_report.html",      # live report regenerated every check — open in a browser
    "desktop_notify": True,               # best-effort notify-send / osascript
    "email": {
        "enabled": False,                 # set True + fill below to get emails
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",                   # app password, NOT your real password
        "to": "",
    },
}
# =================================================================


# ----------------------------- data ------------------------------

def fetch_history(ticker: str, csv_path: str | None = None):
    """Return a daily OHLCV DataFrame (~15 months). CSV file if given, else yfinance."""
    import pandas as pd

    if csv_path:
        df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
        need = {"Open", "High", "Low", "Close"}
        if not need.issubset(df.columns):
            sys.exit(f"CSV must have columns Date,{','.join(sorted(need))}[,Volume]")
        return df.sort_index()

    try:
        import yfinance as yf
    except ImportError:
        sys.exit("yfinance not installed — run: pip install -r requirements.txt")

    last_err = None
    for attempt in range(3):  # network hiccups happen; retry with backoff
        try:
            df = yf.Ticker(ticker).history(period="15mo", interval="1d", auto_adjust=False)
            if df is not None and len(df) > 0:
                df.index = df.index.tz_localize(None)
                return df
            last_err = "empty response"
        except Exception as e:  # noqa: BLE001 — any network/API error is retryable here
            last_err = e
        time.sleep(2 ** attempt)
    sys.exit(f"Could not fetch {ticker} data after 3 tries ({last_err}). "
             f"Check your connection, or run with --csv FILE for offline data.")


# --------------------------- indicators --------------------------

def rsi(close, period: int):
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, min_periods=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def atr(df, period: int = 14):
    import pandas as pd
    prev_close = df["Close"].shift()
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period).mean()


def add_indicators(df):
    c = CONFIG
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["RSI"] = rsi(df["Close"], c["rsi_period"])
    df["ATR"] = atr(df, 14)
    return df


def bearish_divergence(df) -> str | None:
    """Price higher high while RSI makes a lower high, over the lookback window."""
    win = df.tail(CONFIG["divergence_lookback"])
    if len(win) < 20:
        return None
    close, rsi_s = win["Close"], win["RSI"]
    # swing highs = local maxima with 3 bars each side
    highs = [i for i in range(3, len(win) - 3)
             if close.iloc[i] == close.iloc[i - 3:i + 4].max()]
    if len(highs) < 2:
        return None
    a, b = highs[-2], highs[-1]
    if close.iloc[b] > close.iloc[a] and rsi_s.iloc[b] < rsi_s.iloc[a] - 2:
        return (f"bearish divergence: price high {close.iloc[b]:.2f} > {close.iloc[a]:.2f} "
                f"but RSI {rsi_s.iloc[b]:.0f} < {rsi_s.iloc[a]:.0f}")
    return None


# ---------------------------- position ---------------------------

def position():
    shares = sum(s for s, _ in CONFIG["lots"])
    basis = sum(s * p for s, p in CONFIG["lots"])
    avg = basis / shares if shares else 0.0
    return shares, basis, avg


# ------------------------- state & logging -----------------------

def load_state():
    if os.path.exists(CONFIG["state_file"]):
        with open(CONFIG["state_file"]) as f:
            return json.load(f)
    return {"trailing_high": None, "fired_tranches": []}


def save_state(state):
    with open(CONFIG["state_file"], "w") as f:
        json.dump(state, f, indent=2)


def log_csv(row: dict):
    new = not os.path.exists(CONFIG["csv_log"])
    with open(CONFIG["csv_log"], "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


# ---------------------------- alerting ---------------------------

def desktop_notify(title: str, body: str):
    if not CONFIG["desktop_notify"]:
        return
    for cmd in (["notify-send", title, body],
                ["osascript", "-e", f'display notification "{body}" with title "{title}"']):
        try:
            subprocess.run(cmd, capture_output=True, timeout=5, check=False)
            return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue


def email_alert(subject: str, body: str):
    e = CONFIG["email"]
    if not e["enabled"]:
        return
    try:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = subject, e["username"], e["to"]
        msg.set_content(body)
        with smtplib.SMTP(e["smtp_host"], e["smtp_port"], timeout=20) as s:
            s.starttls()
            s.login(e["username"], e["password"])
            s.send_message(msg)
    except Exception as err:  # noqa: BLE001 — alerting must never crash the monitor
        print(f"  [email failed: {err}]")


def dispatch(alerts: list[str]):
    if not alerts:
        return
    body = "\n".join(alerts)
    print("\n" + "!" * 64)
    for a in alerts:
        print(f"  ALERT: {a}")
    print("!" * 64)
    desktop_notify(f"BB monitor: {len(alerts)} trigger(s)", body)
    email_alert(f"[BB monitor] {len(alerts)} trigger(s) fired", body)


# ------------------------- trigger engine ------------------------

def evaluate(df, state, as_of=None):
    """Evaluate all rules on data up to `as_of` (or latest). Returns (alerts, metrics)."""
    c = CONFIG
    data = df.loc[:as_of] if as_of is not None else df
    row = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else row
    close, today = float(row["Close"]), data.index[-1].date()
    alerts, shares, basis, avg = [], *position()

    # 1) hard stop — daily close below the floor
    if close < c["hard_stop"]:
        alerts.append(f"HARD STOP: close {close:.2f} < {c['hard_stop']:.2f} "
                      f"-> SELL ALL REMAINING — no exceptions")

    # 2) tranche crossings (each fires once; reset by deleting state file)
    for level, advice in c["tranche_levels"].items():
        key = f"{level:.2f}"
        if close >= level > float(prev["Close"]) and key not in state["fired_tranches"]:
            alerts.append(f"TRANCHE {level:.2f} crossed: {advice}")
            state["fired_tranches"].append(key)

    # 3) trailing stop from highest close since start date
    start = date.fromisoformat(c["trailing_start_date"])
    if today >= start:
        hi = max(state["trailing_high"] or 0.0, close)
        state["trailing_high"] = hi
        dd = (hi - close) / hi * 100 if hi else 0.0
        if dd >= c["trailing_stop_pct"]:
            alerts.append(f"TRAILING STOP: {dd:.1f}% below the {hi:.2f} high "
                          f"(threshold {c['trailing_stop_pct']:.0f}%)")
    else:
        dd = 0.0

    # 4) momentum exhaustion
    rsi_v, sma20 = float(row["RSI"]), float(row["SMA20"])
    ext = (close / sma20 - 1) * 100 if sma20 else 0.0
    if rsi_v > c["rsi_overbought"] and ext > c["sma_extension_pct"]:
        alerts.append(f"EXHAUSTION: RSI {rsi_v:.0f} > {c['rsi_overbought']:.0f} "
                      f"and price {ext:.0f}% above 20-day SMA — overextension warning")
    div = bearish_divergence(data)
    if div:
        alerts.append(f"EXHAUSTION: {div}")

    # 5) wash-sale clock
    if c["loss_sale_date"]:
        days_left = (date.fromisoformat(c["loss_sale_date"])
                     + timedelta(days=c["wash_sale_days"]) - today).days
        if days_left > 0:
            alerts.append(f"WASH-SALE GUARD: {days_left} day(s) left — buying ANY BB in ANY "
                          f"account disallows the harvested loss")

    # 6) earnings reminder
    days_to_earn = (date.fromisoformat(c["earnings_date"]) - today).days
    if 0 <= days_to_earn <= c["earnings_warn_days"]:
        alerts.append(f"EARNINGS in {days_to_earn} day(s) (~{c['earnings_date']}): "
                      f"{c['earnings_checklist']}")

    metrics = {
        "date": str(today), "close": round(close, 2),
        "rsi": round(rsi_v, 1) if rsi_v == rsi_v else "",
        "sma20": round(sma20, 2) if sma20 == sma20 else "",
        "sma50": round(float(row["SMA50"]), 2) if row["SMA50"] == row["SMA50"] else "",
        "sma200": round(float(row["SMA200"]), 2) if row["SMA200"] == row["SMA200"] else "",
        "atr": round(float(row["ATR"]), 2) if row["ATR"] == row["ATR"] else "",
        "ext_vs_sma20_pct": round(ext, 1),
        "trail_drawdown_pct": round(dd, 1),
        "value": round(close * shares, 2),
        "pnl": round((close - avg) * shares, 2),
        "pnl_pct": round((close / avg - 1) * 100, 1),
        "triggers": " | ".join(alerts),
    }
    return alerts, metrics


# ----------------------------- output ----------------------------

def banner():
    c = CONFIG
    shares, basis, avg = position()
    lots = ", ".join(f"{s}@{p:.2f}" for s, p in c["lots"])
    print("=" * 64)
    print(f"BB POSITION MONITOR — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"  Position : {shares:,} sh ({lots})  basis ${basis:,.0f}  avg ${avg:.2f}")
    print(f"  Hard stop: close < ${c['hard_stop']:.2f} -> sell all remaining")
    print(f"  Tranches : {', '.join(f'${l:.2f}' for l in c['tranche_levels'])}")
    print(f"  Trailing : {c['trailing_stop_pct']:.0f}% off highest close since {c['trailing_start_date']}")
    print(f"  Exhaustion: RSI>{c['rsi_overbought']:.0f} & >{c['sma_extension_pct']:.0f}% above SMA20")
    if c["loss_sale_date"]:
        left = (date.fromisoformat(c["loss_sale_date"])
                + timedelta(days=c["wash_sale_days"]) - date.today()).days
        print(f"  Wash-sale: {max(left, 0)} day(s) remaining on the clock")
    else:
        print("  Wash-sale: no sale date set (fill CONFIG['loss_sale_date'] when you sell)")
    print(f"  Earnings : ~{c['earnings_date']} (reminder {c['earnings_warn_days']}d out)")
    print("=" * 64)


def summary(metrics):
    shares, basis, avg = position()
    m = metrics
    print(f"\n  {m['date']}  close ${m['close']:.2f}   RSI {m['rsi']}   ATR {m['atr']}")
    print(f"  SMA20 ${m['sma20']} ({m['ext_vs_sma20_pct']:+.1f}%)   "
          f"SMA50 ${m['sma50']}   SMA200 ${m['sma200']}")
    print(f"  Value ${m['value']:,.0f}   P&L ${m['pnl']:+,.0f} ({m['pnl_pct']:+.1f}%)   "
          f"breakeven ${avg:.2f} ({(avg / m['close'] - 1) * 100:+.1f}% away)   "
          f"hard stop ${CONFIG['hard_stop']:.2f} ({(CONFIG['hard_stop'] / m['close'] - 1) * 100:+.1f}%)")


# ------------------------- live html report ----------------------
# The action plan from stocks/blackberry/FINAL-REPORT.md, fused with live data.
# Regenerated on every check so the advice sheet is never stale.

REPORT_TEMPLATE = string.Template("""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BB Live Report — $stamp</title>
<style>
 :root{--ink:#1a2332;--muted:#5a6678;--line:#dde3ec;--bg:#fff;--soft:#f5f7fa;
   --sell:#8a2f2f;--sellbg:#faf1f0;--hold:#2f5c46;--holdbg:#eff6f1;--accent:#28415e;--warn:#8a6d1f;--warnbg:#faf6e9}
 @media (prefers-color-scheme:dark){:root{--ink:#e8ecf3;--muted:#9aa5b5;--line:#333c4c;--bg:#141922;
   --soft:#1c2330;--sell:#e09a93;--sellbg:#2a1e1d;--hold:#93c7ab;--holdbg:#1a2822;--accent:#9db8d9;--warn:#d9c27a;--warnbg:#2a2517}}
 *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Georgia,serif}
 .page{max-width:880px;margin:0 auto;padding:40px 36px 60px}
 .kicker{font:600 11px/1 -apple-system,'Segoe UI',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
 h1{font-size:26px;margin:0 0 4px}.meta{color:var(--muted);font-size:13px}
 .rule{border:0;border-top:2px solid var(--ink);margin:18px 0 22px}
 h2{font:700 12.5px/1.3 -apple-system,'Segoe UI',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:30px 0 10px}
 table{width:100%;border-collapse:collapse;margin:10px 0 18px;font:13.5px/1.5 -apple-system,'Segoe UI',sans-serif}
 th{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:left;padding:7px 9px;border-bottom:2px solid var(--ink)}
 td{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
 td.num{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
 .alerts{border-left:4px solid var(--sell);background:var(--sellbg);padding:14px 18px;margin:16px 0;font:14px/1.6 -apple-system,sans-serif}
 .quiet{border-left:4px solid var(--hold);background:var(--holdbg);padding:14px 18px;margin:16px 0;font:14px/1.6 -apple-system,sans-serif}
 .pill{display:inline-block;font:700 10.5px/1 -apple-system,sans-serif;letter-spacing:.06em;padding:4px 8px;border-radius:3px;text-transform:uppercase}
 .pill.fired{background:var(--sellbg);color:var(--sell)}.pill.armed{background:var(--soft);color:var(--muted)}
 .pill.watch{background:var(--warnbg);color:var(--warn)}.pill.ok{background:var(--holdbg);color:var(--hold)}
 .act-sell td:first-child{color:var(--sell);font-weight:700;white-space:nowrap}
 .act-hold td:first-child{color:var(--hold);font-weight:700;white-space:nowrap}
 .base{background:var(--soft);font-weight:600}
 .fine{font-size:12px;color:var(--muted);font-style:italic}
 .footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted)}
 @media print{.page{padding:0}}
</style></head><body><div class="page">

<div class="kicker">BB Position Monitor · Live Report · data: $source</div>
<h1>BlackBerry (BB) — Position &amp; Exit Discipline</h1>
<div class="meta">Generated $stamp · bar date $bar_date · plan of record: stocks/blackberry/FINAL-REPORT.md</div>
<hr class="rule">

$alert_block

<h2>Position now</h2>
<table>
<tr><th>Price</th><th>Position value</th><th>Unrealized P&amp;L</th><th>Breakeven (blended)</th><th>Hard stop</th></tr>
<tr><td class="num">$$$price</td><td class="num">$$$value</td><td class="num">$pnl ($pnl_pct)</td>
<td class="num">$$$avg ($to_breakeven away)</td><td class="num">$$$stop ($to_stop below)</td></tr>
</table>
<table>
<tr><th>RSI(14)</th><th>vs 20-day SMA $$$sma20</th><th>50-day SMA</th><th>200-day SMA</th><th>ATR(14)</th><th>Trail high / drawdown</th></tr>
<tr><td class="num">$rsi</td><td class="num">$ext</td><td class="num">$$$sma50</td><td class="num">$$$sma200</td>
<td class="num">$$$atr</td><td class="num">$$$trail_high / $trail_dd</td></tr>
</table>

<h2>Trigger board</h2>
<table>
<tr><th style="width:110px">Status</th><th>Rule</th><th>Where we stand</th></tr>
$trigger_rows
</table>

<h2>The plan of record (July 2026 verdict)</h2>
<table>
<tr><th style="width:80px">Action</th><th>Detail</th></tr>
<tr class="act-sell"><td>SELL</td><td>Entire ~$$16 lot (≈2,500 sh) near $$13 — harvests ≈$$7,300 long-term tax loss. Sell <b>specific lots</b>, never default FIFO.</td></tr>
<tr class="act-sell"><td>SELL</td><td>~1,000 sh of the ~$$13 lot (tax-neutral) → total trim ≈70%, proceeds ≈$$45,700.</td></tr>
<tr class="act-hold"><td>KEEP</td><td>~1,500 sh runner. Stop: daily close &lt; $$9.80 → sell all, no exceptions. Trim ~500 sh at $$13.60, ~500 at $$15.50, exit at $$18.</td></tr>
<tr class="act-hold"><td>OPTION</td><td>Sell $$15-strike covered calls 1–2 mo out (IV rich; assignment = exit above blended basis).</td></tr>
<tr class="act-hold"><td>PARK</td><td>Proceeds → cash/T-bills; redeployment is a separate decision.</td></tr>
</table>

<h2>Probability map (July 2026 baseline)</h2>
<table>
<tr><th>Horizon</th><th>Bear · 30%</th><th>Base · 45%</th><th>Bull · 25%</th></tr>
<tr><td><b>2–8 weeks</b></td><td>Snap-back to $$9.84 / $$8–9 base</td><td class="base">Chop $$11–14 while RSI cools</td><td>Through $$13.59 → $$14–15 → ~$$18</td></tr>
<tr><td><b>12 months</b></td><td>$$6–8 (multiple compression)</td><td class="base">$$12–15 (grows into valuation)</td><td>$$17–20+ (re-rating persists)</td></tr>
</table>

<h2>Calendar</h2>
<table>
<tr><th style="width:150px">Date</th><th>Event</th><th>Watch</th></tr>
<tr><td class="num">$wash_row
<tr><td class="num">~Jul 24, 2026</td><td>Short-interest print</td><td>Still rising into strength = distribution confirmed</td></tr>
<tr><td class="num">Aug 14, 2026</td><td>Q2 13F deadline</td><td>Did active managers chase or trim? Fairfax follow-through?</td></tr>
<tr><td class="num">$earn_date ($earn_days)</td><td><b>Q2 FY27 earnings</b></td><td>QNX <i>royalty</i> revenue (not backlog) · Secure Comms/DND revenue · guidance held</td></tr>
</table>

<div class="footer">Auto-generated by tools/bb_monitor.py — alerts only, never trades. Research basis: two-session
multi-agent process (Bull/Bear debate + position-blind Fundamentals/Technicals/Flow/Industry team), citations in
stocks/blackberry/sources.md &amp; outlook.md. Not personalized financial advice; verify live quotes before orders.</div>
</div></body></html>
""")


def write_report(metrics, alerts, state, source):
    """Render the live HTML report — the FINAL-REPORT action plan fused with current data."""
    c = CONFIG
    shares, basis, avg = position()
    close = metrics["close"]
    pill = lambda cls, txt: f'<span class="pill {cls}">{txt}</span>'

    rows = []
    # hard stop
    fired = close < c["hard_stop"]
    rows.append(f"<tr><td>{pill('fired' if fired else 'armed', 'FIRED' if fired else 'ARMED')}</td>"
                f"<td>Hard stop — daily close &lt; ${c['hard_stop']:.2f} → sell all remaining</td>"
                f"<td class='num'>{(c['hard_stop'] / close - 1) * 100:+.1f}% away</td></tr>")
    # tranches
    for level, advice in c["tranche_levels"].items():
        done = f"{level:.2f}" in state["fired_tranches"]
        rows.append(f"<tr><td>{pill('fired' if done else 'armed', 'FIRED' if done else 'ARMED')}</td>"
                    f"<td>Tranche ${level:.2f} — {advice}</td>"
                    f"<td class='num'>{(level / close - 1) * 100:+.1f}% away</td></tr>")
    # trailing stop
    hi = state.get("trailing_high") or close
    dd = (hi - close) / hi * 100 if hi else 0.0
    t_cls = "fired" if dd >= c["trailing_stop_pct"] else ("watch" if dd >= c["trailing_stop_pct"] * 0.6 else "ok")
    rows.append(f"<tr><td>{pill(t_cls, 'FIRED' if t_cls == 'fired' else ('WATCH' if t_cls == 'watch' else 'OK'))}</td>"
                f"<td>Trailing stop — {c['trailing_stop_pct']:.0f}% off highest close since {c['trailing_start_date']}</td>"
                f"<td class='num'>{dd:.1f}% off ${hi:.2f} high</td></tr>")
    # exhaustion
    rsi_v = metrics["rsi"] if metrics["rsi"] != "" else 0
    hot = rsi_v > c["rsi_overbought"] and metrics["ext_vs_sma20_pct"] > c["sma_extension_pct"]
    rows.append(f"<tr><td>{pill('watch' if hot else 'ok', 'WATCH' if hot else 'OK')}</td>"
                f"<td>Momentum exhaustion — RSI &gt; {c['rsi_overbought']:.0f} and &gt; {c['sma_extension_pct']:.0f}% above SMA20</td>"
                f"<td class='num'>RSI {rsi_v} · {metrics['ext_vs_sma20_pct']:+.1f}% vs SMA20</td></tr>")

    # wash-sale calendar row + banner text
    if c["loss_sale_date"]:
        end = date.fromisoformat(c["loss_sale_date"]) + timedelta(days=c["wash_sale_days"])
        left = (end - date.today()).days
        wash_row = (f"{end} ({max(left, 0)}d left)</td><td>Wash-sale window ends</td>"
                    f"<td>Until then: buy NO BB in ANY account (incl. IRA/spouse)</td></tr>")
    else:
        wash_row = ("—</td><td>Wash-sale clock not started</td>"
                    "<td>Set CONFIG['loss_sale_date'] the day you sell at a loss</td></tr>")

    earn = date.fromisoformat(c["earnings_date"])
    earn_days = (earn - date.today()).days

    if alerts:
        alert_block = ("<div class='alerts'><b>⚠ TRIGGERS FIRED THIS CHECK:</b><br>"
                       + "<br>".join(alerts) + "</div>")
    else:
        alert_block = "<div class='quiet'>✓ No triggers fired this check — discipline intact, nothing to do.</div>"

    html = REPORT_TEMPLATE.substitute(
        stamp=datetime.now().strftime("%Y-%m-%d %H:%M"), source=source,
        bar_date=metrics["date"], alert_block=alert_block,
        price=f"{close:,.2f}", value=f"{metrics['value']:,.0f}",
        pnl=f"${metrics['pnl']:+,.0f}", pnl_pct=f"{metrics['pnl_pct']:+.1f}%",
        avg=f"{avg:.2f}", to_breakeven=f"{(avg / close - 1) * 100:+.1f}%",
        stop=f"{c['hard_stop']:.2f}", to_stop=f"{(c['hard_stop'] / close - 1) * 100:+.1f}%",
        rsi=f"{metrics['rsi']}", ext=f"{metrics['ext_vs_sma20_pct']:+.1f}%",
        sma20=f"{metrics['sma20']}", sma50=f"{metrics['sma50']}", sma200=f"{metrics['sma200']}",
        atr=f"{metrics['atr']}", trail_high=f"{hi:.2f}", trail_dd=f"{dd:.1f}%",
        trigger_rows="\n".join(rows), wash_row=wash_row,
        earn_date=str(earn), earn_days=f"{earn_days}d" if earn_days >= 0 else "past",
    )
    with open(c["html_report"], "w") as f:
        f.write(html)
    print(f"  Live report -> {c['html_report']}")


# ------------------------------ modes ----------------------------

def run_once(csv_path=None):
    df = add_indicators(fetch_history(CONFIG["ticker"], csv_path))
    state = load_state()
    alerts, metrics = evaluate(df, state)
    summary(metrics)
    dispatch(alerts)
    if not alerts:
        print("\n  No triggers fired. Holding pattern — discipline intact.")
    write_report(metrics, alerts, state,
                 f"offline CSV ({os.path.basename(csv_path)})" if csv_path else "yfinance (live/delayed)")
    metrics["run_at"] = datetime.now().isoformat(timespec="seconds")
    log_csv(metrics)
    save_state(state)


def market_open() -> bool:
    if ZoneInfo is None:
        return True
    now = datetime.now(ZoneInfo("America/New_York"))
    return (now.weekday() < 5
            and (now.hour, now.minute) >= (9, 30)
            and now.hour < 16)


def run_loop(minutes: int, csv_path=None):
    print(f"Looping every {minutes} min during US market hours. Ctrl-C to stop.")
    while True:
        if market_open():
            try:
                run_once(csv_path)
            except SystemExit as e:  # keep the loop alive through fetch failures
                print(f"  [check skipped: {e}]")
        else:
            print(f"  {datetime.now():%H:%M} market closed — sleeping.")
        time.sleep(minutes * 60)


def backtest(csv_path=None):
    """Replay ~12 months of daily bars; print every trigger that WOULD have fired."""
    df = add_indicators(fetch_history(CONFIG["ticker"], csv_path))
    df = df.tail(252)
    state = {"trailing_high": None, "fired_tranches": []}
    print(f"\nBACKTEST — {df.index[0].date()} .. {df.index[-1].date()} "
          f"({len(df)} sessions)\n" + "-" * 64)
    fired, prev_alerts = 0, set()
    for i in range(20, len(df)):  # need SMA20 warm-up
        alerts, _ = evaluate(df.iloc[: i + 1], state)
        # suppress date-relative rules in replay — they only make sense live
        alerts = [a for a in alerts if not a.startswith(("WASH-SALE", "EARNINGS"))]
        # edge-triggered: a condition that persists for weeks prints once, on entry
        new = [a for a in alerts if a.split(":")[0] not in prev_alerts]
        prev_alerts = {a.split(":")[0] for a in alerts}
        for a in new:
            print(f"  {df.index[i].date()}  ${df.iloc[i]['Close']:.2f}  {a}")
            fired += 1
    print("-" * 64)
    print(f"{fired} trigger(s) would have fired. "
          f"Sanity-check the dates against the chart before trusting levels.\n")


def main():
    p = argparse.ArgumentParser(description="BB position monitor (alerts only, never trades)")
    p.add_argument("--once", action="store_true", help="single check (default)")
    p.add_argument("--loop", type=int, metavar="MIN", help="re-check every MIN minutes in market hours")
    p.add_argument("--backtest", action="store_true", help="replay last 12 months of triggers")
    p.add_argument("--csv", metavar="FILE", help="offline OHLCV CSV instead of yfinance")
    args = p.parse_args()

    banner()
    if args.backtest:
        backtest(args.csv)
    elif args.loop:
        run_loop(args.loop, args.csv)
    else:
        run_once(args.csv)


if __name__ == "__main__":
    main()
