"""Neighbourhood moves:
SHIFT    - move a visit 1-4 slots earlier/later
REASSIGN - new doctor and time for a patient
SWAP     - two same-specialty patients swap places
UNASSIGN - remove a patient from the schedule
Only changed patients/doctors are re-evaluated (delta)."""
import random
from .model import Solution, HORIZON
from .cost import patient_cost, doctor_cost

MOVE_PROBS = (("SHIFT", 0.40), ("REASSIGN", 0.35), ("SWAP", 0.20), ("UNASSIGN", 0.05))


class Move:
    __slots__ = ("changes",)

    def __init__(self, changes):
        self.changes = changes          # list of (patient, new_value)


def _clamp_start(s, dur):
    return max(0, min(HORIZON - dur, s))


def random_move(sol: Solution, rng: random.Random, by_spec: dict) -> Move | None:
    inst = sol.inst
    n = len(inst.patients)
    r = rng.random()
    acc = 0.0
    kind = "SHIFT"
    for k, pr in MOVE_PROBS:
        acc += pr
        if r < acc:
            kind = k
            break

    if kind == "SHIFT":
        p = rng.randrange(n)
        a = sol.assign[p]
        if a is None:
            kind = "REASSIGN"
        else:
            delta = rng.choice((-4, -3, -2, -1, 1, 2, 3, 4))
            s = _clamp_start(a[1] + delta, inst.patients[p].duration)
            if s == a[1]:
                return None
            return Move([(p, (a[0], s))])

    if kind == "REASSIGN":
        p = rng.randrange(n)
        pat = inst.patients[p]
        docs = inst.qualified[p]
        if not docs:
            return None
        d = rng.choice(docs)
        if rng.random() < 0.7:
            s = pat.preferred + rng.randint(-8, 8)
        else:
            s = rng.randrange(HORIZON)
        s = _clamp_start(s, pat.duration)
        if sol.assign[p] == (d, s):
            return None
        return Move([(p, (d, s))])

    if kind == "SWAP":
        p = rng.randrange(n)
        group = by_spec[inst.patients[p].specialty]
        if len(group) < 2:
            return None
        q = rng.choice(group)
        a, b = sol.assign[p], sol.assign[q]
        if p == q or a == b:
            return None
        # keep each visit inside the horizon after the swap
        na = None if b is None else (b[0], _clamp_start(b[1], inst.patients[p].duration))
        nb = None if a is None else (a[0], _clamp_start(a[1], inst.patients[q].duration))
        return Move([(p, na), (q, nb)])

    # UNASSIGN
    p = rng.randrange(n)
    if sol.assign[p] is None:
        return None
    return Move([(p, None)])


def apply_with_delta(sol: Solution, move: Move) -> tuple[float, list]:
    """Apply the move in place and return (delta_cost, undo_info)."""
    inst = sol.inst
    docs = set()
    for p, v in move.changes:
        if sol.assign[p] is not None:
            docs.add(sol.assign[p][0])
        if v is not None:
            docs.add(v[0])
    before = sum(doctor_cost(sol, d) for d in docs)
    before += sum(patient_cost(inst, p, sol.assign[p]) for p, _ in move.changes)
    undo = [(p, sol.assign[p]) for p, _ in move.changes]
    for p, v in move.changes:
        sol.set(p, v)
    after = sum(doctor_cost(sol, d) for d in docs)
    after += sum(patient_cost(inst, p, sol.assign[p]) for p, _ in move.changes)
    return after - before, undo


def undo_move(sol: Solution, undo: list) -> None:
    for p, v in reversed(undo):
        sol.set(p, v)


def specialty_groups(inst) -> dict:
    groups: dict[str, list[int]] = {}
    for p in inst.patients:
        groups.setdefault(p.specialty, []).append(p.id)
    return groups
