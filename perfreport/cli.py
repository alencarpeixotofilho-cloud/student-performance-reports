"""Build every learner workbook plus the cohort overview.

    python -m perfreport --input examples/data --output out/
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import excel, figures, metrics


def build(input_dir: str, output_dir: str, with_figures: bool = True) -> int:
    ds = metrics.load(input_dir)
    out = Path(output_dir)
    learners = sorted(ds.responses["learner_id"].unique())
    for lid in learners:
        excel.learner_workbook(ds, lid, out / "learners" / f"report_{lid}.xlsx")
        if with_figures:
            figures.learner_trajectory(ds, lid, out / "learners" / f"trajectory_{lid}.png")
    excel.cohort_workbook(ds, out / "cohort_overview.xlsx")
    if with_figures:
        figures.cohort_heatmap(ds, out / "cohort_heatmap.png")
    return len(learners)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Individual and cohort performance reports.")
    ap.add_argument("--input", required=True, help="folder with exams.csv, items.csv, responses.csv")
    ap.add_argument("--output", default="out", help="output folder")
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)
    n = build(a.input, a.output, not a.no_figures)
    print(f"Built {n} learner workbooks + cohort overview in {a.output}")


if __name__ == "__main__":
    main()
