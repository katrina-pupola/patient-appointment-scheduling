"""Solve one instance and print the schedule.
Usage: python main.py instances/S1_5d_30p.json"""
import argparse
import time

from scheduler.model import Instance
from scheduler.construct import greedy
from scheduler.cost import total_cost, breakdown
from scheduler.sa import simulated_annealing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--alpha", type=float, default=0.95)
    args = ap.parse_args()

    inst = Instance.load(args.instance)
    t = time.perf_counter()
    start = greedy(inst)
    print(f"Greedy start: f = {total_cost(start):.1f}")
    best, cost, info = simulated_annealing(start, seed=args.seed, alpha=args.alpha)
    print(f"Simulated annealing: f = {cost:.1f}  ({info['iterations']} iterations, "
          f"{time.perf_counter() - t:.2f} s, t0 = {info['t0']:.2f})")
    print(breakdown(best))
    print()
    print(f"{'pac.':>4} {'specialitāte':<14} {'st.':>3} {'vec.':>4}  {'ārsts':<9} {'laiks':<13} vēlamais")
    for r in sorted(best.to_table(), key=lambda r: (r["doctor"] or "~", r["start"] or "")):
        when = "NEIEPLĀNOTS" if r["doctor"] is None else f"{r['start']}-{r['end']}"
        print(f"{r['patient']:>4} {r['specialty']:<14} {r['urgency']:>3} {r['age']:>4}  "
              f"{r['doctor'] or '-':<9} {when:<13} {r['preferred']}")


if __name__ == "__main__":
    main()
