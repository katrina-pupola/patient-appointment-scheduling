"""Cost function f (lower is better).
Hard: overlapping visits (huge penalty).
Soft: time deviation, overtime, idle gaps, unscheduled patients.
Patient penalties are multiplied by the patient's weight."""
from .model import Instance, Solution, HORIZON

W_OVERLAP = 10_000
W_UNASSIGNED = 200
W_DEV = 1
W_OVERTIME = 20
W_IDLE = 2


def patient_cost(inst: Instance, p: int, value) -> float:
    """Cost of one patient: deviation + overtime, or penalty if unscheduled."""
    pat = inst.patients[p]
    if value is None:
        return W_UNASSIGNED * pat.weight
    d, s = value
    doc = inst.doctors[d]
    e = s + pat.duration
    overtime = max(0, doc.work_start - s) + max(0, e - doc.work_end)
    overtime = min(overtime, pat.duration)
    return W_DEV * pat.weight * abs(s - pat.preferred) + W_OVERTIME * overtime


def doctor_cost(sol: Solution, d: int) -> float:
    """Non-additive part of one doctor's day: overlaps (hard) and idle gaps."""
    pats = sol.by_doc[d]
    if not pats:
        return 0.0
    occ = [0] * HORIZON
    first, last = HORIZON, 0
    for p in pats:
        s = sol.assign[p][1]
        e = s + sol.inst.patients[p].duration
        first = min(first, s)
        last = max(last, e)
        for t in range(s, e):
            occ[t] += 1
    overlap = 0
    idle = 0
    for t in range(first, last):
        c = occ[t]
        if c == 0:
            idle += 1
        elif c > 1:
            overlap += c - 1
    return W_OVERLAP * overlap + W_IDLE * idle


def total_cost(sol: Solution) -> float:
    inst = sol.inst
    return (sum(patient_cost(inst, p, sol.assign[p]) for p in range(len(inst.patients)))
            + sum(doctor_cost(sol, d) for d in range(len(inst.doctors))))


def breakdown(sol: Solution) -> dict:
    """Readable decomposition of the cost (used in reports)."""
    inst = sol.inst
    res = {"overlap_slots": 0, "unassigned": 0, "unassigned_cost": 0.0,
           "deviation_cost": 0.0, "deviation_minutes_avg": 0.0,
           "overtime_slots": 0, "idle_slots": 0}
    devs = []
    for p in inst.patients:
        a = sol.assign[p.id]
        if a is None:
            res["unassigned"] += 1
            res["unassigned_cost"] += W_UNASSIGNED * p.weight
            continue
        d, s = a
        doc = inst.doctors[d]
        res["deviation_cost"] += W_DEV * p.weight * abs(s - p.preferred)
        devs.append(abs(s - p.preferred) * 15)
        e = s + p.duration
        res["overtime_slots"] += min(p.duration, max(0, doc.work_start - s) + max(0, e - doc.work_end))
    for d in range(len(inst.doctors)):
        c = doctor_cost(sol, d)
        res["overlap_slots"] += int(c // W_OVERLAP)
        res["idle_slots"] += int((c % W_OVERLAP) // W_IDLE)
    res["deviation_minutes_avg"] = sum(devs) / len(devs) if devs else 0.0
    res["total"] = total_cost(sol)
    return res
