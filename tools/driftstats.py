#!/usr/bin/env python3
"""Rate summary and covariate correlations for a clock-drift archive.

Reproduces the numbers docs/clock-drift.md quotes per harvest, from the
archive image rather than by hand:

    driftstats.py hist.bin --arm 2 --drop-first --interval 43200
    driftstats.py hist.bin --arm 0                # the pre-experiment subset

Rate = total drift / total window (window-weighted); +-N% = widest single
deviation from it. Records with a window under DRIFT_MIN_WINDOW_S (6h) are
dropped, as on the device. Per-window covariates come from the same record
(boot/refresh deltas, mean ambient) plus the hourly rows the window covers
(intra-hour spread = mean of max-min). Correlations are Pearson unless
labelled; partials are first-order. Needs numpy (system python3 has it).
"""

import argparse
import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import history  # noqa: E402

MIN_WINDOW_S = 6 * 3600


def select(arc, arm, drop_first, since=None):
    rows = list(history._drift_rows(arc.drifts))
    if arm is not None:
        rows = [r for r in rows if r[10] == arm]
    if since:
        rows = [r for r in rows if r[0] >= since]
    if drop_first:
        rows = rows[1:]
    rows = [r for r in rows if r[2] >= MIN_WINDOW_S]
    return rows


def covariates(rows, hourly):
    t0 = rows[0][0]
    out = []
    for r in rows:
        sync, drift_s, win, ppm, amb, _, _, db, _, dr, _ = r
        days = win / 86400.0
        t = dt.datetime.strptime(sync, "%Y-%m-%d %H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc).timestamp()
        hrs = [h for h in hourly if t - win < h[0] <= t]
        spread = np.mean([h[2] - h[1] for h in hrs]) if hrs else np.nan
        e0 = dt.datetime.strptime(t0, "%Y-%m-%d %H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc).timestamp()
        out.append(dict(drift_s=drift_s, window_s=win, ppm=ppm,
                        wakes=db / days if db != "" else np.nan,
                        refreshes=dr / days if dr != "" else np.nan,
                        ambient=amb if amb != "" else np.nan, spread=spread,
                        window_d=days, elapsed_d=(t - e0) / 86400.0))
    return out


def pearson(x, y):
    m = ~(np.isnan(x) | np.isnan(y))
    return float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 2 else np.nan


def rank(x):
    order = np.argsort(x)
    r = np.empty(len(x))
    r[order] = np.arange(len(x), dtype=float)
    # average ties
    for v in np.unique(x):
        m = x == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def partial(rxy, rxz, ryz):
    return (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("image")
    ap.add_argument("--arm", type=int, help="keep only records with this arm byte")
    ap.add_argument("--drop-first", action="store_true",
                    help="drop the first selected record (reflash-straddled)")
    ap.add_argument("--since", help="keep records synced at/after this ISO date")
    ap.add_argument("--interval", type=int,
                    help="pinned resync interval in s; counts failed attempts")
    a = ap.parse_args()

    with open(a.image, "rb") as f:
        arc = history.Archive(f.read())
    rows = select(arc, a.arm, a.drop_first, a.since)
    if not rows:
        sys.exit("no records selected")
    hourly = [(ts, mn / 10.0, mx / 10.0) for ts, mn, mx, _ in arc.hourly
              if mn != history.HOURLY_NO_DATA]
    cov = covariates(rows, hourly)

    drift = sum(c["drift_s"] for c in cov)
    win = sum(c["window_s"] for c in cov)
    rate = drift / win * 1e6
    ppm = np.array([c["ppm"] for c in cov], float)
    widest = np.max(np.abs(ppm - rate)) / abs(rate) * 100
    print(f"n={len(cov)}  observed {win/86400:.2f}d  drift {drift:+.0f}s  "
          f"rate {rate:+.1f}ppm  range {ppm.min():+.0f}..{ppm.max():+.0f}  "
          f"+-{widest:.1f}%  sd {ppm.std():.1f}ppm")
    if a.interval:
        fails = sum(round(c["window_s"] / a.interval) - 1 for c in cov)
        print(f"failed attempts {fails} across {len(cov)} successes "
              f"(windows {min(c['window_s'] for c in cov)/3600:.1f}.."
              f"{max(c['window_s'] for c in cov)/3600:.1f}h vs {a.interval/3600:.0f}h)")
    half = len(cov) // 2
    for name, part in (("first half", cov[:half]), ("second half", cov[half:])):
        d = sum(c["drift_s"] for c in part); w = sum(c["window_s"] for c in part)
        print(f"  {name}: {d/w*1e6:+.0f}ppm over {len(part)}")
    el = np.array([c["elapsed_d"] for c in cov])
    slope = np.polyfit(el, ppm, 1)[0]
    print(f"  slope vs elapsed {slope:+.1f}ppm/day")

    keys = ["wakes", "refreshes", "ambient", "spread", "window_d", "elapsed_d"]
    X = {k: np.array([c[k] for c in cov], float) for k in keys}
    print(f"\n{'covariate':<10} {'min':>8} {'max':>8} {'r':>7} {'rho':>7}")
    for k in keys:
        x = X[k]
        print(f"{k:<10} {np.nanmin(x):8.2f} {np.nanmax(x):8.2f} "
              f"{pearson(x, ppm):+7.3f} {pearson(rank(x), rank(ppm)):+7.3f}")

    ra, rs, rw = (pearson(X["ambient"], ppm), pearson(X["spread"], ppm),
                  pearson(X["wakes"], ppm))
    r_as, r_aw = pearson(X["ambient"], X["spread"]), pearson(X["ambient"], X["wakes"])
    print(f"\nr(ambient,spread) {r_as:+.3f}   r(ambient,wakes) {r_aw:+.3f}")
    print(f"partial spread|ambient  {partial(rs, r_as, ra):+.3f}")
    print(f"partial ambient|spread  {partial(ra, r_as, rs):+.3f}")
    print(f"partial wakes|ambient   {partial(rw, r_aw, ra):+.3f}")


if __name__ == "__main__":
    main()
