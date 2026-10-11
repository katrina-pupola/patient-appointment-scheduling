"""Runs all experiments and writes results/ (CSV tables, JSON, plots).

Usage:  python run_experiments.py            (full run, ~15-20 min on 2 cores)
        python run_experiments.py --quick    (fewer runs, for a quick check)
"""
import csv
import json
import os
import statistics
import sys
import time
from multiprocessing import Pool

from scheduler.model import Instance
from scheduler.construct import greedy
from scheduler.cost import total_cost, breakdown
from scheduler.sa import simulated_annealing, hill_climbing
from scheduler.exact import branch_and_bound
from scheduler.generate import SUITE

QUICK = "--quick" in sys.argv
RUNS = 3 if QUICK else 10
EXACT_LIMIT = 30 if QUICK else 600
os.makedirs("results", exist_ok=True)


def load(name):
    return Instance.load(f"instances/{name}.json")


def job(args):
    kind, name, seed, extra = args
    inst = load(name)
    t = time.perf_counter()
    g = greedy(inst)
    g_time = time.perf_counter() - t
    if kind == "greedy":
        return kind, name, seed, extra, total_cost(g), g_time, breakdown(g)
    t = time.perf_counter()
    if kind == "hc":
        sol, c, _ = hill_climbing(g, seed=seed, max_iters=10**7)
    elif kind == "sa":
        sol, c, _ = simulated_annealing(g, seed=seed, alpha=extra)
    elif kind == "exact":
        # upper bound from one SA run, then Branch & Bound
        s0, c0, _ = simulated_annealing(g, seed=0)
        sol, c, info = branch_and_bound(inst, c0 + 1e-6, s0, EXACT_LIMIT)
        return kind, name, seed, info["optimal"], c, time.perf_counter() - t, info["nodes"]
    return kind, name, seed, extra, c, time.perf_counter() - t + g_time, breakdown(sol)


def main():
    names = [s[0] for s in SUITE]
    jobs = []
    for n in names:
        if n.startswith("T"):
            jobs.append(("exact", n, 0, None))
    for n in names:
        jobs.append(("greedy", n, 0, None))
        runs = RUNS if not n.startswith("L2") else max(3, RUNS // 2)
        for s in range(runs):
            jobs.append(("hc", n, s, None))
            jobs.append(("sa", n, s, 0.95))
        if not n.startswith("T"):
            jobs.append(("sa_long", n, 999, 0.99))
    # parameter study on M1: cooling factor alpha
    for a in (0.80, 0.90, 0.99):
        for s in range(3):
            jobs.append(("alpha", "M1_8d_70p", s, a))

    def norm(j):
        k, n, s, e = j
        return ("sa" if k in ("sa_long", "alpha") else k, n, s, e), k

    mapped = [norm(j) for j in jobs]
    t0 = time.perf_counter()
    with Pool(2) as pool:
        out = pool.map(job, [m[0] for m in mapped], chunksize=1)
    print(f"all jobs done in {time.perf_counter() - t0:.0f}s")

    raw = []
    for (_, label), r in zip(mapped, out):
        kind, name, seed, extra, cost, secs, info = r
        raw.append({"label": label, "instance": name, "seed": seed, "extra": extra,
                    "cost": cost, "time": secs, "info": info})
    with open("results/raw_results.json", "w") as f:
        json.dump(raw, f, indent=1)

    # reference value per instance: proven optimum, or best ever found
    ref, ref_type = {}, {}
    for n in names:
        vals = [r["cost"] for r in raw if r["instance"] == n]
        ref[n] = min(vals)
        ex = [r for r in raw if r["instance"] == n and r["label"] == "exact"]
        ref_type[n] = "optimums" if ex and ex[0]["extra"] else "labākais zināmais"

    rows = []
    for n in names:
        inst = load(n)
        def stats(label):
            rs = [r for r in raw if r["instance"] == n and r["label"] == label]
            cs = [r["cost"] for r in rs]
            ts = [r["time"] for r in rs]
            return cs, ts
        g, gt = stats("greedy")
        h, ht = stats("hc")
        s, st = stats("sa")
        gap = lambda c: 100 * (c - ref[n]) / ref[n] if ref[n] else 0.0
        ex = [r for r in raw if r["instance"] == n and r["label"] == "exact"]
        rows.append({
            "instance": n, "doctors": len(inst.doctors), "patients": len(inst.patients),
            "reference": round(ref[n], 1), "reference_type": ref_type[n],
            "exact_time_s": round(ex[0]["time"], 1) if ex else "",
            "greedy_cost": round(g[0], 1), "greedy_gap_%": round(gap(g[0]), 1),
            "greedy_time_s": round(gt[0], 3),
            "hc_avg": round(statistics.mean(h), 1), "hc_gap_avg_%": round(gap(statistics.mean(h)), 1),
            "hc_time_s": round(statistics.mean(ht), 2),
            "sa_best": round(min(s), 1), "sa_avg": round(statistics.mean(s), 1),
            "sa_std": round(statistics.pstdev(s), 1),
            "sa_gap_best_%": round(gap(min(s)), 1), "sa_gap_avg_%": round(gap(statistics.mean(s)), 1),
            "sa_time_s": round(statistics.mean(st), 2), "sa_runs": len(s),
        })
    with open("results/summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    alpha_rows = []
    for a in (0.80, 0.90, 0.95, 0.99):
        rs = [r for r in raw if r["instance"] == "M1_8d_70p" and
              ((r["label"] == "alpha" and r["extra"] == a) or
               (a == 0.95 and r["label"] == "sa" and r["seed"] < 3))]
        alpha_rows.append({"alpha": a, "avg_cost": round(statistics.mean(r["cost"] for r in rs), 1),
                           "avg_time_s": round(statistics.mean(r["time"] for r in rs), 2),
                           "gap_%": round(100 * (statistics.mean(r["cost"] for r in rs) - ref["M1_8d_70p"]) / ref["M1_8d_70p"], 1)})
    with open("results/alpha_study.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(alpha_rows[0].keys()))
        w.writeheader()
        w.writerows(alpha_rows)

    for r in rows:
        print(r)
    for r in alpha_rows:
        print(r)


if __name__ == "__main__":
    main()
