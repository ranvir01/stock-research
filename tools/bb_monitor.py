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


# ------------------------------ modes ----------------------------

def run_once(csv_path=None):
    df = add_indicators(fetch_history(CONFIG["ticker"], csv_path))
    state = load_state()
    alerts, metrics = evaluate(df, state)
    summary(metrics)
    dispatch(alerts)
    if not alerts:
        print("\n  No triggers fired. Holding pattern — discipline intact.")
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
