"""Branch & Bound for tiny instances only (finds the true optimum).
Places patients one by one, cuts branches that can't beat the best."""
import time
from .model import Instance, Solution, HORIZON
from .cost import patient_cost, total_cost


def branch_and_bound(inst: Instance, upper_bound: float = float("inf"),
                     incumbent: Solution | None = None, time_limit: float = 600.0):
    order = sorted(inst.patients,
                   key=lambda p: (-p.weight, len(inst.qualified[p.id]), -p.duration))
    order = [p.id for p in order]
    n = len(order)
    busy = [[False] * HORIZON for _ in inst.doctors]
    sol = Solution(inst)
    best = {"cost": upper_bound, "sol": incumbent.copy() if incumbent else None}
    nodes = [0]
    t0 = time.perf_counter()
    timed_out = [False]

    def candidates(p):
        pat = inst.patients[p]
        cands = [(patient_cost(inst, p, None), None)]
        for d in inst.qualified[p]:
            b = busy[d]
            for s in range(0, HORIZON - pat.duration + 1):
                if not any(b[s:s + pat.duration]):
                    cands.append((patient_cost(inst, p, (d, s)), (d, s)))
        cands.sort(key=lambda x: x[0])
        return cands

    def dfs(k, partial):
        nodes[0] += 1
        if nodes[0] % 20000 == 0 and time.perf_counter() - t0 > time_limit:
            timed_out[0] = True
        if timed_out[0]:
            return
        if k == n:
            c = total_cost(sol)              # adds the (non-additive) idle part
            if c < best["cost"] - 1e-9:
                best["cost"], best["sol"] = c, sol.copy()
            return
        p = order[k]
        dur = inst.patients[p].duration
        for c, val in candidates(p):
            if partial + c >= best["cost"] - 1e-9:
                break
            sol.set(p, val)
            if val is not None:
                d, s = val
                for t in range(s, s + dur):
                    busy[d][t] = True
            dfs(k + 1, partial + c)
            if val is not None:
                for t in range(s, s + dur):
                    busy[d][t] = False
            sol.set(p, None)

    dfs(0, 0.0)
    return best["sol"], best["cost"], {
        "nodes": nodes[0], "optimal": not timed_out[0],
        "time": time.perf_counter() - t0}
