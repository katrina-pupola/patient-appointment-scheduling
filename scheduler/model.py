"""Domain: doctors, patients and a solution.
Time is in 15-min slots: 0 = 08:00, 40 = 18:00, 48 = 20:00 (overtime only)."""
from __future__ import annotations
import json
from dataclasses import dataclass, field

SLOT_MIN = 15
DAY_START_H = 8
HORIZON = 48

URGENCY_WEIGHT = {1: 1.0, 2: 3.0, 3: 10.0}   # 1=planned, 2=soon, 3=urgent


def slot_to_clock(s: int) -> str:
    m = DAY_START_H * 60 + s * SLOT_MIN
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass
class Doctor:
    id: int
    name: str
    specialties: list[str]
    work_start: int          # first working slot (inclusive)
    work_end: int            # end of working time (exclusive)


@dataclass
class Patient:
    id: int
    age: int
    urgency: int             # 1..3
    specialty: str           # required specialty
    duration: int            # in slots
    preferred: int           # preferred start slot
    weight: float = 0.0      # importance, derived from urgency and age

    def __post_init__(self):
        age_factor = 1.5 if (self.age < 7 or self.age >= 75) else 1.0
        self.weight = URGENCY_WEIGHT[self.urgency] * age_factor


@dataclass
class Instance:
    name: str
    doctors: list[Doctor]
    patients: list[Patient]
    qualified: dict[int, list[int]] = field(default_factory=dict)  # patient -> doctor ids

    def __post_init__(self):
        self.qualified = {
            p.id: [d.id for d in self.doctors if p.specialty in d.specialties]
            for p in self.patients
        }

    @staticmethod
    def load(path: str) -> "Instance":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return Instance(
            name=data["name"],
            doctors=[Doctor(**d) for d in data["doctors"]],
            patients=[Patient(**{k: v for k, v in p.items() if k != "weight"})
                      for p in data["patients"]],
        )

    def save(self, path: str) -> None:
        data = {
            "name": self.name,
            "slot_minutes": SLOT_MIN,
            "horizon_slots": HORIZON,
            "doctors": [d.__dict__ for d in self.doctors],
            "patients": [{k: v for k, v in p.__dict__.items() if k != "weight"}
                         for p in self.patients],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)


class Solution:
    """assign[p] = (doctor, start_slot) or None if not scheduled.
    by_doc[d] = patients of doctor d (for fast cost updates)."""

    def __init__(self, inst: Instance):
        self.inst = inst
        self.assign: list[tuple[int, int] | None] = [None] * len(inst.patients)
        self.by_doc: list[set[int]] = [set() for _ in inst.doctors]

    def set(self, p: int, value: tuple[int, int] | None) -> None:
        old = self.assign[p]
        if old is not None:
            self.by_doc[old[0]].discard(p)
        self.assign[p] = value
        if value is not None:
            self.by_doc[value[0]].add(p)

    def copy(self) -> "Solution":
        s = Solution.__new__(Solution)
        s.inst = self.inst
        s.assign = list(self.assign)
        s.by_doc = [set(x) for x in self.by_doc]
        return s

    def to_table(self) -> list[dict]:
        rows = []
        for p in self.inst.patients:
            a = self.assign[p.id]
            rows.append({
                "patient": p.id, "specialty": p.specialty, "urgency": p.urgency,
                "age": p.age,
                "doctor": None if a is None else self.inst.doctors[a[0]].name,
                "start": None if a is None else slot_to_clock(a[1]),
                "end": None if a is None else slot_to_clock(a[1] + p.duration),
                "preferred": slot_to_clock(p.preferred),
            })
        return rows
