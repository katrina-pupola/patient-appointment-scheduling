"""Simulated Annealing (lecture slide 13).
Accept better moves always, worse ones with probability exp(-delta/t).
t0 set automatically, then t = alpha * t until t < t_min.
hill_climbing() is the same with t = 0 (slide 11)."""
import math
import random
import time

from .model import Solution
from .cost import total_cost
from .moves import random_move, apply_with_delta, undo_move, specialty_groups


def calibrate_t0(sol: Solution, rng, groups, p0=0.5, samples=300) -> float:
    worse = []
    for _ in range(samples):
        mv = random_move(sol, rng, groups)
        if mv is None:
            continue
        delta, undo = apply_with_delta(sol, mv)
        undo_move(sol, undo)
        if 0 < delta < 5000:          # ignore hard-constraint violations
            worse.append(delta)
    if not worse:
        return 1.0
    avg = sum(worse) / len(worse)
    return -avg / math.log(p0)


def simulated_annealing(start: Solution, seed=0, alpha=0.95, iters_per_temp=None,
                        t_min=0.05, p0=0.5, time_limit=None, trace=False):
    rng = random.Random(seed)
    inst = start.inst
    groups = specialty_groups(inst)
    cur = start.copy()
    cur_cost = total_cost(cur)
    best, best_cost = cur.copy(), cur_cost
    if iters_per_temp is None:
        iters_per_temp = 50 * len(inst.patients)
    t = calibrate_t0(cur, rng, groups, p0)
    t0 = t
    history = []
    t_start = time.perf_counter()
    it = 0
    while t > t_min:
        for _ in range(iters_per_temp):
            mv = random_move(cur, rng, groups)
            if mv is None:
                continue
            it += 1
            delta, undo = apply_with_delta(cur, mv)
            if delta <= 0 or rng.random() < math.exp(-delta / t):
                cur_cost += delta
                if cur_cost < best_cost - 1e-9:
                    best, best_cost = cur.copy(), cur_cost
            else:
                undo_move(cur, undo)
        if trace:
            history.append((it, t, cur_cost, best_cost))
        t *= alpha
        if time_limit and time.perf_counter() - t_start > time_limit:
            break
    return best, best_cost, {"iterations": it, "t0": t0, "history": history}


def hill_climbing(start: Solution, seed=0, max_iters=100_000, patience=None):
    """Accept only non-worsening moves (t[k] = 0). Stops after max_iters or
    after `patience` consecutive moves without improvement."""
    rng = random.Random(seed)
    inst = start.inst
    groups = specialty_groups(inst)
    cur = start.copy()
    cur_cost = total_cost(cur)
    if patience is None:
        patience = 20 * len(inst.patients)
    since_improve = 0
    it = 0
    while it < max_iters and since_improve < patience:
        mv = random_move(cur, rng, groups)
        if mv is None:
            continue
        it += 1
        delta, undo = apply_with_delta(cur, mv)
        if delta <= 0:
            cur_cost += delta
            since_improve = 0 if delta < 0 else since_improve + 1
        else:
            undo_move(cur, undo)
            since_improve += 1
    return cur, cur_cost, {"iterations": it}
