"""Generate a synthetic cohort taking a series of mock exams (no real data).

Each learner has a latent general ability, a learner-specific profile across
domains and an individual growth rate. Exams differ in overall difficulty.
Responses are drawn from a logistic model, producing realistic trajectories,
plateaus and weak areas.

Outputs (in --out):
    exams.csv      exam_id, date, label
    items.csv      exam_id, item_id, domain, topic, competency
    responses.csv  learner_id, exam_id, item_id, correct (0/1)
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

FRAMEWORK = {
    "Internal Medicine": ["Cardiology", "Endocrinology", "Infectious Diseases", "Nephrology", "Pulmonology"],
    "Surgery": ["Trauma", "Acute Abdomen", "Perioperative Care", "Vascular Surgery"],
    "Pediatrics": ["Neonatology", "Growth & Development", "Pediatric Infections", "Immunization"],
    "Obstetrics & Gynecology": ["Prenatal Care", "Labor & Delivery", "Gynecologic Oncology", "Family Planning"],
    "Public Health": ["Epidemiology", "Primary Care", "Health Policy", "Preventive Medicine"],
}
COMPETENCIES = ["Diagnosis", "Management", "Prevention", "Clinical Reasoning"]


def simulate(n_learners: int = 50, n_exams: int = 7, items_per_exam: int = 100,
             seed: int = 2026):
    rng = np.random.default_rng(seed)
    domains = list(FRAMEWORK)
    learners = [f"L{i:03d}" for i in range(1, n_learners + 1)]

    ability = rng.normal(0, 0.8, n_learners)
    profile = rng.normal(0, 0.45, (n_learners, len(domains)))
    growth = rng.normal(0.08, 0.06, n_learners)
    exam_shift = rng.normal(0, 0.25, n_exams)

    start = date(2026, 2, 1)
    exams = pd.DataFrame({
        "exam_id": [f"E{e + 1}" for e in range(n_exams)],
        "date": [(start + timedelta(days=30 * e)).isoformat() for e in range(n_exams)],
        "label": [f"Mock exam {e + 1}" for e in range(n_exams)],
    })

    item_rows, resp_rows = [], []
    weights = np.array([0.24, 0.20, 0.20, 0.18, 0.18])
    for e, exam_id in enumerate(exams["exam_id"]):
        dom_idx = rng.choice(len(domains), items_per_exam, p=weights)
        diff = rng.normal(exam_shift[e], 0.9, items_per_exam)
        for k in range(items_per_exam):
            dom = domains[dom_idx[k]]
            item_rows.append({
                "exam_id": exam_id,
                "item_id": f"{exam_id}-Q{k + 1:03d}",
                "domain": dom,
                "topic": rng.choice(FRAMEWORK[dom]),
                "competency": rng.choice(COMPETENCIES),
            })
        theta = (ability[:, None] + profile[:, dom_idx] + growth[:, None] * e)
        p = 1 / (1 + np.exp(-(theta - diff[None, :])))
        correct = (rng.random(p.shape) < p).astype(int)
        for i, lid in enumerate(learners):
            # ~3% of learners miss a given exam
            if rng.random() < 0.03 and e > 0:
                continue
            for k in range(items_per_exam):
                resp_rows.append((lid, exam_id, f"{exam_id}-Q{k + 1:03d}", int(correct[i, k])))

    items = pd.DataFrame(item_rows)
    responses = pd.DataFrame(resp_rows, columns=["learner_id", "exam_id", "item_id", "correct"])
    return exams, items, responses


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--learners", type=int, default=50)
    ap.add_argument("--exams", type=int, default=7)
    ap.add_argument("--items", type=int, default=100)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=str(Path(__file__).parent / "data"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exams, items, responses = simulate(a.learners, a.exams, a.items, a.seed)
    exams.to_csv(out / "exams.csv", index=False)
    items.to_csv(out / "items.csv", index=False)
    responses.to_csv(out / "responses.csv", index=False)
    print(f"{responses['learner_id'].nunique()} learners · {len(exams)} exams · "
          f"{len(responses):,} responses -> {out}")


if __name__ == "__main__":
    main()
