"""Initial solution (Decreasing + Cheapest Insertion).
Hardest patients first; each goes to the free spot
that increases cost the least."""
from .model import Instance, Solution, HORIZON
from .cost import patient_cost, doctor_cost


def greedy(inst: Instance) -> Solution:
    sol = Solution(inst)
    order = sorted(inst.patients,
                   key=lambda p: (-p.weight, len(inst.qualified[p.id]), -p.duration))
    for pat in order:
        p = pat.id
        best_val, best_inc = None, patient_cost(inst, p, None)
        for d in inst.qualified[p]:
            base = doctor_cost(sol, d)
            busy = [False] * HORIZON
            for q in sol.by_doc[d]:
                s0 = sol.assign[q][1]
                for t in range(s0, s0 + inst.patients[q].duration):
                    busy[t] = True
            for s in range(0, HORIZON - pat.duration + 1):
                if any(busy[s:s + pat.duration]):
                    continue
                pc = patient_cost(inst, p, (d, s))
                if pc >= best_inc:
                    continue
                sol.set(p, (d, s))
                inc = pc + doctor_cost(sol, d) - base
                sol.set(p, None)
                if inc < best_inc:
                    best_val, best_inc = (d, s), inc
        sol.set(p, best_val)
    return sol
