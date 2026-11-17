import sys
from pathlib import Path

import numpy as np
import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from perfreport import excel, metrics  # noqa: E402
from generate_sample_data import simulate  # noqa: E402


@pytest.fixture(scope="module")
def ds():
    exams, items, responses = simulate(n_learners=20, n_exams=5, items_per_exam=60, seed=1)
    return metrics.Dataset(exams, items, responses)


def test_scores_are_percentages(ds):
    s = metrics.exam_scores(ds)
    assert s["score"].between(0, 100).all()
    assert s["percentile"].between(0, 100).all()


def test_z_scores_centered_per_exam(ds):
    s = metrics.exam_scores(ds)
    assert np.allclose(s.groupby("exam_id")["z"].mean(), 0, atol=1e-9)


def test_trend_labels(ds):
    t = metrics.trend(metrics.exam_scores(ds))
    assert set(t["trend"].dropna().unique()) <= {"declining", "stable", "improving"}


def test_domain_gap_definition(ds):
    d = metrics.domain_performance(ds)
    assert np.allclose(d["gap"], d["score"] - d["cohort"])


def test_weak_areas_sorted(ds):
    lid = ds.responses["learner_id"].iloc[0]
    w = metrics.weak_areas(ds, lid, top=5, min_items=3)
    assert len(w) <= 5
    assert w["priority"].is_monotonic_decreasing


def test_learner_workbook_has_sheets(ds, tmp_path):
    lid = ds.responses["learner_id"].iloc[0]
    p = excel.learner_workbook(ds, lid, tmp_path / "r.xlsx")
    wb = load_workbook(p)
    assert wb.sheetnames == ["Summary", "Trajectory", "Domains", "Competencies", "Priorities"]


def test_cohort_workbook(ds, tmp_path):
    p = excel.cohort_workbook(ds, tmp_path / "c.xlsx")
    ws = load_workbook(p)["Cohort overview"]
    assert ws.max_row == ds.responses["learner_id"].nunique() + 1
