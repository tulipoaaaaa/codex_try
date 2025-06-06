#!/usr/bin/env python3
"""
generate_synth.py
-----------------
Produce ND-JSON event streams that mimic Hyperliquid *allMids* price ticks
and *userFills* trade events.  Used by the test-harness and chaos-soak.

Features
~~~~~~~~
• Student-t return distribution (fatter tails than Gaussian).  
• Volatility regimes: normal, high-vol, flash-crash.  
• Optional ‘liquidity-thin’ mode (larger gaps + slippage).  
• Deterministic output via --seed.  
• Emits to stdout or --out file (gzip if .gz).  
Each line is a JSON dict with keys:
    { "ts": <epoch-ms>, "type": "mid"|"fill", ... }

Examples
~~~~~~~~
# 60-minute normal regime for BTC at 1 tick/second
python scripts/generate_synth.py --asset BTC --minutes 60 > btc_stream.ndjson

# High-vol, 10× speed replay, gzip output
python scripts/generate_synth.py --asset ETH --minutes 15 --vol high \
       --speed 10 --out eth_highvol.ndjson.gz
"""

from __future__ import annotations
import argparse, json, math, random, sys, time, gzip
from datetime import datetime, timedelta
from pathlib import Path
try:
    import numpy as np
except ImportError:
    np = None  # fall back to random.gauss if numpy missing

# ---------------------------- helpers --------------------------------- #

def _student_t(df: int, size: int):
    """Return Student-t random samples with df degrees of freedom."""
    if np:
        return np.random.standard_t(df, size)
    # fallback (slow) – Box-Muller on Gaussian then scale
    for _ in range(size):
        g = random.gauss(0, 1)
        yield g * math.sqrt(df / random.gammavariate(df / 2, 2))

def _price_series(start_px: float, seconds: int, vol: str, seed: int | None):
    if seed is not None:
        random.seed(seed)
        if np:
            np.random.seed(seed)

    df = 3 if vol == "flash" else 5
    sigma = 0.0005 if vol == "normal" else 0.002
    if vol == "high":
        sigma *= 3
    if vol == "flash":
        sigma *= 6
    rets = list(_student_t(df, seconds))
    prices = [start_px]
    for r in rets:
        prices.append(max(0.1, prices[-1] * (1 + r * sigma)))
    return prices[1:]  # drop initial

def _emit(out_fh, obj):
    out_fh.write(json.dumps(obj, separators=(",", ":")) + "\n")

# ---------------------------- main ------------------------------------ #

def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("--asset", default="BTC", help="Asset symbol")
    p.add_argument("--start", type=float, default=30_000.0, help="Start price")
    p.add_argument("--minutes", type=int, default=60, help="Duration in minutes")
    p.add_argument("--speed", type=int, default=1, help="Replay speed factor")
    p.add_argument("--vol", choices=["normal", "high", "flash"], default="normal")
    p.add_argument("--liq-thin", action="store_true", help="Emit larger slippage fills")
    p.add_argument("--seed", type=int, help="Deterministic RNG seed")
    p.add_argument("--out", help="Output file (defaults to stdout; .gz → gzip)")
    args = p.parse_args(argv)

    seconds = args.minutes * 60
    now_ms = int(time.time() * 1000)

    prices = _price_series(args.start, seconds, args.vol, args.seed)

    # open output target
    if args.out:
        fh = gzip.open(args.out, "wt") if args.out.endswith(".gz") else open(args.out, "w")
    else:
        fh = sys.stdout

    try:
        for i, px in enumerate(prices):
            ts = now_ms + i * 1000 // args.speed
            _emit(fh, {"ts": ts, "type": "mid", "coin": args.asset, "px": round(px, 2)})
            # every 15 ticks emit a synthetic fill
            if i % 15 == 0:
                sz = round(random.uniform(0.01, 0.2), 4)
                slip = px * (0.002 if args.liq_thin else 0.0004)
                fill_px = round(px + random.choice([-slip, slip]), 2)
                _emit(
                    fh,
                    {
                        "ts": ts,
                        "type": "fill",
                        "coin": args.asset,
                        "side": random.choice(["B", "S"]),
                        "px": fill_px,
                        "sz": sz,
                        "eventId": f"sim-{ts}-{i}",
                    },
                )
    finally:
        if fh is not sys.stdout:
            fh.close()

if __name__ == "__main__":
    main()
