"""Formatted Excel workbooks (one per learner + a cohort overview)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import metrics

HEADER = PatternFill("solid", fgColor="1F3A5F")
HFONT = Font(color="FFFFFF", bold=True)
TITLE = Font(size=16, bold=True, color="1F3A5F")


def _write_table(ws, df: pd.DataFrame, start_row: int = 1, start_col: int = 1, number_format="0.0"):
    for j, col in enumerate(df.columns):
        c = ws.cell(row=start_row, column=start_col + j, value=str(col))
        c.fill, c.font = HEADER, HFONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            if hasattr(v, "item"):
                v = v.item()
            c = ws.cell(row=start_row + i, column=start_col + j, value=v)
            if isinstance(v, float):
                c.number_format = number_format
    for j, col in enumerate(df.columns):
        width = max(len(str(col)), *(len(str(x)) for x in df.iloc[:, j].head(200))) + 2
        ws.column_dimensions[get_column_letter(start_col + j)].width = min(max(width, 9), 40)
    return start_row + len(df)


def learner_workbook(ds: metrics.Dataset, learner_id: str, path: str | Path) -> Path:
    scores = metrics.exam_scores(ds)
    mine = scores[scores["learner_id"] == learner_id]
    cohort_mean = scores.groupby("exam_id")["score"].mean().rename("cohort_mean")
    traj = mine.merge(cohort_mean, on="exam_id")[["exam_id", "score", "cohort_mean", "percentile"]]
    traj = traj.merge(ds.exams[["exam_id", "label", "date"]], on="exam_id")
    traj = traj[["label", "date", "score", "cohort_mean", "percentile"]]
    tr = metrics.trend(scores).loc[learner_id]
    dom = metrics.domain_performance(ds)
    dom = dom[dom["learner_id"] == learner_id][["domain", "n_items", "score", "cohort", "gap"]]
    comp = metrics.domain_performance(ds, "competency")
    comp = comp[comp["learner_id"] == learner_id][["competency", "n_items", "score", "cohort", "gap"]]
    weak = metrics.weak_areas(ds, learner_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws["A1"], ws["A1"].font = f"Performance report · {learner_id}", TITLE
    kpis = [
        ("Exams taken", int(tr["exams_taken"])),
        ("Mean score (%)", round(float(tr["mean_score"]), 1)),
        ("Last score (%)", round(float(tr["last_score"]), 1)),
        ("Trend vs cohort", str(tr["trend"])),
        ("Top priority topic", weak["topic"].iloc[0] if len(weak) else "—"),
    ]
    for i, (k, v) in enumerate(kpis, start=3):
        ws.cell(row=i, column=1, value=k).font = Font(bold=True)
        ws.cell(row=i, column=2, value=v)
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 24, 28
    ws.cell(row=10, column=1, value="How to read this report").font = Font(bold=True)
    notes = [
        "Trajectory: your score in each mock exam next to the cohort mean.",
        "Domains / Competencies: your % correct vs the cohort; negative gap = below the cohort.",
        "Priorities: topics ranked by distance to the 60% target, gap to the cohort and exam weight.",
    ]
    for i, n in enumerate(notes, start=11):
        ws.cell(row=i, column=1, value=f"• {n}")

    ws2 = wb.create_sheet("Trajectory")
    end = _write_table(ws2, traj)
    ch = LineChart()
    ch.title, ch.y_axis.title, ch.height, ch.width = "Score by mock exam (%)", "% correct", 8, 16
    ch.add_data(Reference(ws2, min_col=3, max_col=4, min_row=1, max_row=end), titles_from_data=True)
    ch.set_categories(Reference(ws2, min_col=1, min_row=2, max_row=end))
    ch.y_axis.scaling.min, ch.y_axis.scaling.max = 0, 100
    ws2.add_chart(ch, "H2")

    ws3 = wb.create_sheet("Domains")
    end = _write_table(ws3, dom)
    bc = BarChart()
    bc.type, bc.title, bc.height, bc.width = "bar", "Domain score vs cohort (%)", 8, 16
    bc.add_data(Reference(ws3, min_col=3, max_col=4, min_row=1, max_row=end), titles_from_data=True)
    bc.set_categories(Reference(ws3, min_col=1, min_row=2, max_row=end))
    ws3.add_chart(bc, "H2")
    ws3.conditional_formatting.add(f"E2:E{end}", ColorScaleRule(
        start_type="num", start_value=-15, start_color="F8696B",
        mid_type="num", mid_value=0, mid_color="FFFFFF",
        end_type="num", end_value=15, end_color="63BE7B"))

    ws4 = wb.create_sheet("Competencies")
    end = _write_table(ws4, comp)
    ws4.conditional_formatting.add(f"C2:C{end}", DataBarRule(
        start_type="num", start_value=0, end_type="num", end_value=100, color="5B9BD5"))

    ws5 = wb.create_sheet("Priorities")
    _write_table(ws5, weak)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def cohort_workbook(ds: metrics.Dataset, path: str | Path) -> Path:
    ov = metrics.cohort_overview(ds).reset_index()
    ov["trend"] = ov["trend"].astype(str)
    wb = Workbook()
    ws = wb.active
    ws.title = "Cohort overview"
    end = _write_table(ws, ov)
    domain_cols = [c for c in ov.columns if c in metrics.domain_performance(ds)["domain"].unique()]
    for c in domain_cols:
        col = get_column_letter(list(ov.columns).index(c) + 1)
        ws.conditional_formatting.add(f"{col}2:{col}{end}", ColorScaleRule(
            start_type="num", start_value=30, start_color="F8696B",
            mid_type="num", mid_value=55, mid_color="FFEB84",
            end_type="num", end_value=80, end_color="63BE7B"))
    ws.freeze_panes = "B2"

    scores = metrics.exam_scores(ds)
    by_exam = scores.groupby("exam_id")["score"].describe()[["count", "mean", "std", "min", "50%", "max"]]
    by_exam = by_exam.rename(columns={"50%": "median"}).reset_index()
    ws2 = wb.create_sheet("By exam")
    _write_table(ws2, by_exam)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
