"""Static figures (PNG) for slides, reports and the README."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import metrics  # noqa: E402


def cohort_heatmap(ds: metrics.Dataset, path, max_learners: int = 30):
    ov = metrics.cohort_overview(ds)
    doms = sorted(ds.items["domain"].unique())
    m = ov[doms].head(max_learners)
    fig, ax = plt.subplots(figsize=(7, 0.26 * len(m) + 1.6))
    im = ax.imshow(m.to_numpy(), cmap="RdYlGn", vmin=30, vmax=80, aspect="auto")
    ax.set_xticks(range(len(doms)), [d.replace(" & ", " &\n") for d in doms], fontsize=8)
    ax.set_yticks(range(len(m)), m.index, fontsize=7)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m.iat[i, j]:.0f}", ha="center", va="center", fontsize=6.5)
    ax.set_title("Cohort heatmap · % correct by domain (sorted by mean score)", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def learner_trajectory(ds: metrics.Dataset, learner_id: str, path):
    s = metrics.exam_scores(ds)
    band = s.groupby("exam_order")["score"].quantile([0.25, 0.5, 0.75]).unstack()
    me = s[s["learner_id"] == learner_id]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.fill_between(band.index, band[0.25], band[0.75], color="#1f6feb", alpha=0.15, label="cohort IQR")
    ax.plot(band.index, band[0.5], color="#1f6feb", lw=1, ls="--", label="cohort median")
    ax.plot(me["exam_order"], me["score"], marker="o", color="#cf222e", lw=2, label=learner_id)
    ax.set_xticks(band.index, [f"E{i}" for i in band.index])
    ax.set_ylim(0, 100)
    ax.set_ylabel("% correct")
    ax.set_title(f"Trajectory of {learner_id} across mock exams")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def domain_radar(ds: metrics.Dataset, learner_id: str, path):
    d = metrics.domain_performance(ds)
    d = d[d["learner_id"] == learner_id].sort_values("domain")
    labels = d["domain"].tolist()
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    ang += ang[:1]
    me = d["score"].tolist() + d["score"].tolist()[:1]
    co = d["cohort"].tolist() + d["cohort"].tolist()[:1]
    fig, ax = plt.subplots(figsize=(4.6, 4.6), subplot_kw={"polar": True})
    ax.plot(ang, co, color="#1f6feb", lw=1, ls="--", label="cohort")
    ax.plot(ang, me, color="#cf222e", lw=2, label=learner_id)
    ax.fill(ang, me, color="#cf222e", alpha=0.15)
    ax.set_xticks(ang[:-1], [lbl.replace(" & ", " &\n") for lbl in labels], fontsize=8)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", bbox_to_anchor=(1.25, -0.1), frameon=False, fontsize=8)
    ax.set_title("Domain profile (% correct)", fontsize=10)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
