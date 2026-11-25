#!/usr/bin/env python3
"""Control-band check for one production metric (playbook Stage 6, "Closing the loop on metrics").

  control-band.py SERIES [--metric NAME] [--window-days 30] [--higher-is-worse | --lower-is-worse]

SERIES: a CSV (time,value per line, ISO time) or a JSON list of {"time": ..., "value": ...}, hourly
readings, oldest first. The band is the mean and sigma of the window before the latest reading.
Prints one JSON object: metric, latest, mean, sigma, z, band (normal | 1σ | 2σ | 3σ), action:
  1σ  log only (noise alone puts about four readings a day there)
  2σ  investigate (a person looks)
  3σ  act: run /ship-maintain with this JSON to draft an intent for triage
Exit code: 0 normal or 1σ, 10 for 2σ, 20 for 3σ, so a scheduled job can branch on it.
Read-only: it never changes monitoring, deploys or rolls back. No third-party packages.
"""
import argparse, csv, json, statistics, sys
from datetime import datetime, timedelta, timezone


def load(path):
    if path.endswith(".json"):
        rows = [(r["time"], float(r["value"])) for r in json.load(open(path, encoding="utf-8"))]
    else:
        rows = [(r[0], float(r[1])) for r in csv.reader(open(path, encoding="utf-8")) if r and r[0][:1].isdigit()]
    out = []
    for t, v in rows:
        d = datetime.fromisoformat(t.strip().replace("Z", "+00:00"))
        out.append((d if d.tzinfo else d.replace(tzinfo=timezone.utc), v))   # naive times are read as UTC
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("series"); ap.add_argument("--metric", default="metric")
    ap.add_argument("--window-days", type=int, default=30)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--higher-is-worse", action="store_true", default=True)
    g.add_argument("--lower-is-worse", action="store_true")
    a = ap.parse_args()
    rows = load(a.series)
    if not rows:
        sys.exit("control-band: no readings")
    t_last, v_last = rows[-1]
    window = [v for t, v in rows[:-1] if t >= t_last - timedelta(days=a.window_days)]
    if len(window) < 48:
        sys.exit(f"control-band: need at least 48 readings in the last {a.window_days} days, found {len(window)}")
    mean = statistics.mean(window)
    # a flat series has sigma 0; floor it so a tiny change is not read as 3σ
    sigma = max(statistics.pstdev(window), abs(mean) * 0.01, 1e-9)
    z = (v_last - mean) / sigma
    worse = -z if a.lower_is_worse else z
    band = "3σ" if worse >= 3 else "2σ" if worse >= 2 else "1σ" if worse >= 1 else "normal"
    action = {"3σ": "act: /ship-maintain with this JSON", "2σ": "investigate", "1σ": "log only", "normal": "none"}[band]
    print(json.dumps({"metric": a.metric, "time": t_last.isoformat(), "latest": v_last, "mean": round(mean, 4),
                      "sigma": round(sigma, 4), "z": round(z, 2), "band": band, "action": action,
                      "window_readings": len(window)}, ensure_ascii=False))
    sys.exit({"3σ": 20, "2σ": 10}.get(band, 0))


if __name__ == "__main__":
    main()
