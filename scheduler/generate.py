"""Random but reproducible test-instance generator."""
import random
from .model import Doctor, Patient, Instance

SPECIALTIES = ["gimenes_arsts", "kardiologs", "neirologs", "dermatologs", "pediatrs"]
SPEC_PROB = [0.40, 0.20, 0.15, 0.15, 0.10]
# working windows in slots (0 = 08:00, 40 = 18:00)
WINDOWS = [(0, 24), (8, 32), (16, 40), (0, 32), (8, 40), (4, 28)]


def generate(name: str, n_doctors: int, n_patients: int, seed: int) -> Instance:
    rng = random.Random(seed)
    doctors = []
    for d in range(n_doctors):
        # make sure every specialty is covered by someone
        main = SPECIALTIES[d % len(SPECIALTIES)] if d < len(SPECIALTIES) else \
            rng.choices(SPECIALTIES, SPEC_PROB)[0]
        specs = [main]
        if rng.random() < 0.35:
            extra = rng.choice([s for s in SPECIALTIES if s != main])
            specs.append(extra)
        ws, we = rng.choice(WINDOWS)
        doctors.append(Doctor(d, f"Arsts_{d + 1}", specs, ws, we))
    available = sorted({s for d in doctors for s in d.specialties})
    probs = [SPEC_PROB[SPECIALTIES.index(s)] for s in available]

    patients = []
    for p in range(n_patients):
        urgency = rng.choices([1, 2, 3], [0.6, 0.3, 0.1])[0]
        spec = rng.choices(available, probs)[0]
        age = rng.randint(1, 17) if spec == "pediatrs" else rng.randint(18, 95)
        duration = rng.choices([1, 2, 3, 4], [0.30, 0.40, 0.20, 0.10])[0]
        if urgency == 3:
            preferred = rng.randint(0, 8)            # urgent: as early as possible
        else:
            preferred = rng.randint(0, 40 - duration)
        patients.append(Patient(p, age, urgency, spec, duration, preferred))
    return Instance(name, doctors, patients)


# (name, doctors, patients, seed) - from tiny (exactly solvable) to large
SUITE = [
    ("T1_2d_6p", 2, 6, 1),
    ("T2_2d_8p", 2, 8, 2),
    ("T3_3d_10p", 3, 10, 3),
    ("S1_5d_30p", 5, 30, 4),
    ("M1_8d_70p", 8, 70, 5),
    ("M2_8d_110p", 8, 110, 6),     # overloaded: demand > capacity
    ("L1_15d_150p", 15, 150, 7),
    ("L2_25d_300p", 25, 300, 8),
]

if __name__ == "__main__":
    import os
    os.makedirs("instances", exist_ok=True)
    for name, d, p, seed in SUITE:
        generate(name, d, p, seed).save(f"instances/{name}.json")
        print("saved", name)
