"""Learner- and cohort-level performance indicators."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Dataset:
    exams: pd.DataFrame
    items: pd.DataFrame
    responses: pd.DataFrame

    @property
    def long(self) -> pd.DataFrame:
        """Responses joined with item metadata and exam order."""
        order = {e: i + 1 for i, e in enumerate(self.exams["exam_id"])}
        df = self.responses.merge(self.items, on=["exam_id", "item_id"], how="left")
        df["exam_order"] = df["exam_id"].map(order)
        return df


def load(folder: str | Path) -> Dataset:
    folder = Path(folder)
    return Dataset(
        exams=pd.read_csv(folder / "exams.csv"),
        items=pd.read_csv(folder / "items.csv"),
        responses=pd.read_csv(folder / "responses.csv"),
    )


def exam_scores(ds: Dataset) -> pd.DataFrame:
    """Percent correct per learner x exam, plus the cohort percentile rank."""
    df = ds.long.groupby(["learner_id", "exam_id", "exam_order"])["correct"].mean().mul(100)
    df = df.rename("score").reset_index()
    df["percentile"] = df.groupby("exam_id")["score"].rank(pct=True).mul(100).round(0)
    df["z"] = df.groupby("exam_id")["score"].transform(lambda s: (s - s.mean()) / s.std(ddof=0))
    return df.sort_values(["learner_id", "exam_order"])


def trend(scores: pd.DataFrame) -> pd.DataFrame:
    """Linear trend of standardized score (z) per learner: slope per exam.

    Using z instead of raw % removes differences in exam difficulty, so the
    slope reflects movement *relative to the cohort*.
    """
    rows = []
    for lid, g in scores.groupby("learner_id"):
        if len(g) >= 3:
            slope = float(np.polyfit(g["exam_order"], g["z"], 1)[0])
        else:
            slope = np.nan
        rows.append({"learner_id": lid, "z_slope": slope,
                     "last_score": float(g["score"].iloc[-1]),
                     "mean_score": float(g["score"].mean()),
                     "exams_taken": int(len(g))})
    out = pd.DataFrame(rows).set_index("learner_id")
    out["trend"] = pd.cut(out["z_slope"], [-np.inf, -0.08, 0.08, np.inf],
                          labels=["declining", "stable", "improving"])
    return out


def domain_performance(ds: Dataset, level: str = "domain") -> pd.DataFrame:
    """Percent correct per learner x ``level`` (domain, topic or competency),
    with the cohort mean and the learner's gap to the cohort."""
    df = ds.long
    learner = df.groupby(["learner_id", level])["correct"].agg(["mean", "size"])
    learner.columns = ["score", "n_items"]
    learner["score"] *= 100
    cohort = df.groupby(level)["correct"].mean().mul(100).rename("cohort")
    out = learner.reset_index().merge(cohort, on=level)
    out["gap"] = out["score"] - out["cohort"]
    return out


def weak_areas(ds: Dataset, learner_id: str, top: int = 5, min_items: int = 8,
               target: float = 60.0) -> pd.DataFrame:
    """Rank topics where the learner should focus.

    Priority combines (i) distance below the target score, (ii) gap to the
    cohort and (iii) how much the topic weighs in the exams (share of items).
    """
    topics = domain_performance(ds, "topic")
    weight = ds.items["topic"].value_counts(normalize=True).rename("weight")
    t = topics[topics["learner_id"] == learner_id].merge(weight, left_on="topic", right_index=True)
    t = t[t["n_items"] >= min_items].copy()
    t["below_target"] = (target - t["score"]).clip(lower=0)
    t["priority"] = (t["below_target"] + (-t["gap"]).clip(lower=0)) * (1 + 10 * t["weight"])
    dom = ds.items.drop_duplicates("topic").set_index("topic")["domain"]
    t["domain"] = t["topic"].map(dom)
    t = t.sort_values("priority", ascending=False).head(top)
    return t[["domain", "topic", "n_items", "score", "cohort", "gap", "priority"]].reset_index(drop=True)


def cohort_overview(ds: Dataset) -> pd.DataFrame:
    """One row per learner: mean, last score, trend and domain scores."""
    scores = exam_scores(ds)
    tr = trend(scores)
    dom = domain_performance(ds).pivot(index="learner_id", columns="domain", values="score")
    out = tr.join(dom.round(1))
    out["risk"] = np.where((out["last_score"] < 50) | (out["trend"] == "declining"), "attention", "")
    return out.sort_values("mean_score", ascending=False)
