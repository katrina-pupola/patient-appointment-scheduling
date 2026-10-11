"""Draw the convergence chart and the schedule chart (M1)."""
import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scheduler.model import Instance, slot_to_clock
from scheduler.construct import greedy
from scheduler.cost import total_cost
from scheduler.sa import simulated_annealing

os.makedirs("results", exist_ok=True)
inst = Instance.load("instances/M1_8d_70p.json")
g = greedy(inst)
best, best_cost, info = simulated_annealing(g, seed=1, trace=True)
it = [h[0] for h in info["history"]]

fig, ax1 = plt.subplots(figsize=(7, 3.2))
ax1.plot(it, [h[2] for h in info["history"]], color="#E8562A", lw=1, label="pašreizējais f(i)")
ax1.plot(it, [h[3] for h in info["history"]], color="#1D4F8A", lw=2, label="labākais f(best)")
ax1.axhline(total_cost(g), color="gray", ls="--", lw=1, label="sākotnējais risinājums")
ax1.set_xlabel("iterācija")
ax1.set_ylabel("izmaksas f")
ax1.set_yscale("log")
ax2 = ax1.twinx()
ax2.plot(it, [h[1] for h in info["history"]], color="#7AA95C", lw=1, ls=":", label="temperatūra t")
ax2.set_ylabel("temperatūra t")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper right")
ax1.set_title("Simulated Annealing konverģence (M1: 8 ārsti, 70 pacienti)", fontsize=10)
fig.tight_layout()
fig.savefig("results/convergence_M1.png", dpi=200)

# Gantt chart of the final schedule
colors = {1: "#9BC3E6", 2: "#F5B041", 3: "#E74C3C"}
fig, ax = plt.subplots(figsize=(7, 3.5))
for d in inst.doctors:
    ax.barh(d.id, d.work_end - d.work_start, left=d.work_start, color="#EEEEEE",
            edgecolor="#BBBBBB", height=0.8)
for p in inst.patients:
    a = best.assign[p.id]
    if a is None:
        continue
    ax.barh(a[0], p.duration, left=a[1], color=colors[p.urgency], edgecolor="black",
            height=0.6, lw=0.5)
ax.set_yticks([d.id for d in inst.doctors])
ax.set_yticklabels([f"{d.name} ({'/'.join(s[:4] for s in d.specialties)})" for d in inst.doctors],
                   fontsize=7)
ticks = list(range(0, 49, 8))
ax.set_xticks(ticks)
ax.set_xticklabels([slot_to_clock(t) for t in ticks], fontsize=8)
ax.invert_yaxis()
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#EEEEEE", label="darba laiks")] +
          [Patch(color=c, label=f"steidzamība {u}") for u, c in colors.items()],
          fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False)
ax.set_title(f"Iegūtais grafiks M1 (f = {best_cost:.1f})", fontsize=10)
fig.tight_layout()
fig.savefig("results/schedule_M1.png", dpi=200)

with open("results/schedule_M1.csv", "w", newline="", encoding="utf-8") as f:
    rows = best.to_table()
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("figures written; M1 cost", best_cost)
