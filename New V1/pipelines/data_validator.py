"""
BookMyGig — Statistical Data Validation Pipeline
=================================================
Validates the cleaned datasets against a schema of rules.
Produces a structured validation report (JSON + console).

Run:  python -m pipelines.data_validator
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, EVAL_REPORT_DIR
from utils.logging_config import get_logger

log = get_logger("data_validator", "data_validator.log")


# ── data structures ───────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    severity: str      # "error" | "warning" | "info"
    table: str
    column: str
    rule: str
    message: str
    count: int = 0


@dataclass
class TableValidationResult:
    table_name: str
    row_count: int
    column_count: int
    issues: list[ValidationIssue] = field(default_factory=list)
    score: float = 100.0   # 0-100 quality score

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)
        penalty = {"error": 10, "warning": 3, "info": 0.5}.get(issue.severity, 0)
        self.score = max(0.0, self.score - penalty)


@dataclass
class ValidationReport:
    generated_at: str
    tables: list[TableValidationResult] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        if not self.tables:
            return 0.0
        return round(sum(t.score for t in self.tables) / len(self.tables), 2)

    @property
    def total_errors(self) -> int:
        return sum(1 for t in self.tables for i in t.issues if i.severity == "error")

    @property
    def total_warnings(self) -> int:
        return sum(1 for t in self.tables for i in t.issues if i.severity == "warning")


# ── rule helpers ──────────────────────────────────────────────────────────────

def _check_no_nulls(result: TableValidationResult, df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col not in df.columns:
            result.add_issue(ValidationIssue("error", result.table_name, col, "column_exists", f"Column '{col}' is missing"))
            continue
        null_count = df[col].isnull().sum()
        if null_count > 0:
            result.add_issue(ValidationIssue("error", result.table_name, col, "no_nulls", f"{null_count} null values found", null_count))


def _check_unique(result: TableValidationResult, df: pd.DataFrame, col: str) -> None:
    dupes = df[col].duplicated().sum()
    if dupes > 0:
        result.add_issue(ValidationIssue("error", result.table_name, col, "unique", f"{dupes} duplicate values found", dupes))


def _check_range(result: TableValidationResult, df: pd.DataFrame, col: str, lo: float, hi: float) -> None:
    if col not in df.columns:
        return
    out = ((df[col] < lo) | (df[col] > hi)).sum()
    if out > 0:
        result.add_issue(ValidationIssue("warning", result.table_name, col, "range_check", f"{out} values outside [{lo}, {hi}]", int(out)))


def _check_allowed_values(result: TableValidationResult, df: pd.DataFrame, col: str, allowed: set) -> None:
    if col not in df.columns:
        return
    bad = (~df[col].isin(allowed)).sum()
    if bad > 0:
        result.add_issue(ValidationIssue("error", result.table_name, col, "allowed_values", f"{bad} values not in {allowed}", int(bad)))


def _check_distribution(result: TableValidationResult, df: pd.DataFrame, col: str, expected_min_unique: int) -> None:
    if col not in df.columns:
        return
    unique_count = df[col].nunique()
    if unique_count < expected_min_unique:
        result.add_issue(ValidationIssue("warning", result.table_name, col, "diversity",
                                         f"Only {unique_count} unique values (expected >= {expected_min_unique})"))


def _check_min_rows(result: TableValidationResult, df: pd.DataFrame, min_rows: int) -> None:
    if len(df) < min_rows:
        result.add_issue(ValidationIssue("error", result.table_name, "*", "min_rows",
                                         f"Table has {len(df)} rows, expected >= {min_rows}", len(df)))


# ── per-table validators ──────────────────────────────────────────────────────

def validate_musicians(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("musicians", len(df), len(df.columns))
    _check_min_rows(r, df, 200)
    _check_no_nulls(r, df, ["Musician_ID", "Musician_Name", "Musician_Type", "Location", "Years_Experience", "Base_Price"])
    _check_unique(r, df, "Musician_ID")
    _check_allowed_values(r, df, "Musician_Type", {"Solo", "Band", "DJ", "Duo", "Trio", "Quartet"})
    _check_range(r, df, "Years_Experience", 0, 50)
    _check_range(r, df, "Base_Price", 50, 5000)
    _check_distribution(r, df, "Location", 8)
    _check_distribution(r, df, "Musician_Type", 4)

    # cold-start ratio check
    cold_ratio = (df["Years_Experience"] == 0).mean()
    if cold_ratio > 0.3:
        r.add_issue(ValidationIssue("warning", "musicians", "Years_Experience", "cold_start_ratio",
                                    f"Cold-start ratio {cold_ratio:.1%} seems high"))

    return r


def validate_clients(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("clients", len(df), len(df.columns))
    _check_min_rows(r, df, 100)
    _check_no_nulls(r, df, ["Client_ID", "Client_Name", "Client_Type"])
    _check_unique(r, df, "Client_ID")
    _check_allowed_values(r, df, "Client_Type", {"Individual", "Corporate", "Venue", "Event Planner"})
    _check_distribution(r, df, "Client_Type", 3)
    return r


def validate_events(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("events", len(df), len(df.columns))
    _check_min_rows(r, df, 300)
    _check_no_nulls(r, df, ["Event_ID", "Client_ID", "City", "Date_Time", "Expected_Pax", "Event_Type", "Budget"])
    _check_unique(r, df, "Event_ID")
    _check_range(r, df, "Expected_Pax", 1, 2000)
    _check_range(r, df, "Budget", 100, 500_000)
    _check_distribution(r, df, "Event_Type", 5)
    _check_distribution(r, df, "City", 6)
    return r


def validate_bookings(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("bookings", len(df), len(df.columns))
    _check_min_rows(r, df, 200)
    _check_no_nulls(r, df, ["Booking_ID", "Musician_ID", "Client_ID", "Event_ID", "Duration", "Price_Charged", "Rating"])
    _check_unique(r, df, "Booking_ID")
    _check_range(r, df, "Rating", 1, 5)
    _check_range(r, df, "Duration", 1, 12)
    _check_range(r, df, "Price_Charged", 50, 100_000)

    # rating distribution check
    rating_counts = df["Rating"].value_counts(normalize=True)
    if rating_counts.get(5, 0) > 0.80:
        r.add_issue(ValidationIssue("warning", "bookings", "Rating", "rating_skew",
                                    "More than 80% of ratings are 5-star — possible unrealistic skew"))
    return r


def validate_reviews(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("reviews", len(df), len(df.columns))
    _check_min_rows(r, df, 200)
    _check_no_nulls(r, df, ["Review_ID", "Booking_ID", "Review_Text", "Rating"])
    _check_unique(r, df, "Review_ID")
    _check_range(r, df, "Rating", 1, 5)

    # text length check
    df["_len"] = df["Review_Text"].astype(str).str.split().str.len()
    short = (df["_len"] < 5).sum()
    if short > 0:
        r.add_issue(ValidationIssue("warning", "reviews", "Review_Text", "min_length",
                                    f"{short} reviews are very short (< 5 words)", int(short)))

    # review diversity (not all identical)
    dup_text = df["Review_Text"].duplicated().sum()
    dup_ratio = dup_text / len(df)
    if dup_ratio > 0.5:
        r.add_issue(ValidationIssue("error", "reviews", "Review_Text", "text_diversity",
                                    f"{dup_ratio:.1%} of reviews are duplicates — dataset needs more variety"))

    return r


def validate_social_metrics(df: pd.DataFrame) -> TableValidationResult:
    r = TableValidationResult("social_media_metrics", len(df), len(df.columns))
    _check_min_rows(r, df, 500)
    _check_no_nulls(r, df, ["Musician_ID", "Platform", "Followers", "Likes", "Views", "Date_Collected"])
    _check_allowed_values(r, df, "Platform", {"Instagram", "TikTok", "YouTube"})
    _check_range(r, df, "Followers", 0, 100_000_000)
    _check_range(r, df, "Views", 0, 1_000_000_000)
    return r


# ── cross-table checks ────────────────────────────────────────────────────────

def validate_referential_integrity(
    musicians, clients, events, bookings, reviews, social
) -> list[ValidationIssue]:
    issues = []
    m_ids = set(musicians["Musician_ID"])
    c_ids = set(clients["Client_ID"])
    e_ids = set(events["Event_ID"])
    b_ids = set(bookings["Booking_ID"])

    orphan_bk_m = (~bookings["Musician_ID"].isin(m_ids)).sum()
    if orphan_bk_m:
        issues.append(ValidationIssue("error", "bookings", "Musician_ID", "ref_integrity",
                                      f"{orphan_bk_m} bookings reference unknown musicians", int(orphan_bk_m)))

    orphan_bk_e = (~bookings["Event_ID"].isin(e_ids)).sum()
    if orphan_bk_e:
        issues.append(ValidationIssue("error", "bookings", "Event_ID", "ref_integrity",
                                      f"{orphan_bk_e} bookings reference unknown events", int(orphan_bk_e)))

    orphan_rv = (~reviews["Booking_ID"].isin(b_ids)).sum()
    if orphan_rv:
        issues.append(ValidationIssue("error", "reviews", "Booking_ID", "ref_integrity",
                                      f"{orphan_rv} reviews reference unknown bookings", int(orphan_rv)))

    orphan_sc = (~social["Musician_ID"].isin(m_ids)).sum()
    if orphan_sc:
        issues.append(ValidationIssue("error", "social_media_metrics", "Musician_ID", "ref_integrity",
                                      f"{orphan_sc} social records reference unknown musicians", int(orphan_sc)))

    return issues


# ── main ──────────────────────────────────────────────────────────────────────

def run_validation_pipeline(
    cleaned_dir: Path = PROCESSED_DIR,
) -> ValidationReport:
    log.info("=" * 60)
    log.info("BookMyGig — Statistical Data Validation Pipeline")
    log.info("=" * 60)

    def load(name: str) -> pd.DataFrame:
        path = cleaned_dir / f"{name}_clean.csv"
        if not path.exists():
            log.warning(f"{path} not found — falling back to raw")
            from config import RAW_DIR
            path = RAW_DIR / f"{name}.csv"
        return pd.read_csv(path)

    musicians = load("musicians")
    clients   = load("clients")
    events    = load("events")
    bookings  = load("bookings")
    reviews   = load("reviews")
    social    = load("social_media_metrics")

    report = ValidationReport(generated_at=datetime.now().isoformat())

    report.tables.append(validate_musicians(musicians))
    report.tables.append(validate_clients(clients))
    report.tables.append(validate_events(events))
    report.tables.append(validate_bookings(bookings))
    report.tables.append(validate_reviews(reviews))
    report.tables.append(validate_social_metrics(social))

    # cross-table
    ri_issues = validate_referential_integrity(musicians, clients, events, bookings, reviews, social)
    for issue in ri_issues:
        tbl = next((t for t in report.tables if t.table_name == issue.table), None)
        if tbl:
            tbl.add_issue(issue)

    # ── print summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  DATA VALIDATION REPORT — {report.generated_at[:19]}")
    print("=" * 70)
    print(f"  Overall Quality Score : {report.overall_score:>6.1f} / 100")
    print(f"  Total Errors          : {report.total_errors}")
    print(f"  Total Warnings        : {report.total_warnings}")
    print("-" * 70)

    for t in report.tables:
        status = "PASS" if t.score >= 80 else ("WARN" if t.score >= 60 else "FAIL")
        print(f"  [{status}] {t.table_name:30s} rows={t.row_count:>5,}  score={t.score:>5.1f}")
        for issue in t.issues:
            icon = {"error": "[E]", "warning": "[W]", "info": "[I]"}.get(issue.severity, "[?]")
            print(f"        {icon} [{issue.rule}] {issue.message}")

    print("=" * 70 + "\n")

    # ── save JSON report ──────────────────────────────────────────────────────
    report_path = EVAL_REPORT_DIR / "validation_report.json"

    def _serial(obj):
        if isinstance(obj, ValidationIssue):
            return asdict(obj)
        if isinstance(obj, TableValidationResult):
            return {
                "table_name": obj.table_name,
                "row_count": obj.row_count,
                "column_count": obj.column_count,
                "score": obj.score,
                "issues": [asdict(i) for i in obj.issues],
            }
        return str(obj)

    with open(report_path, "w") as f:
        json.dump(
            {
                "generated_at": report.generated_at,
                "overall_score": report.overall_score,
                "total_errors": report.total_errors,
                "total_warnings": report.total_warnings,
                "tables": [_serial(t) for t in report.tables],
            },
            f,
            indent=2,
            default=str,
        )
    log.info(f"Validation report saved → {report_path}")
    return report


if __name__ == "__main__":
    run_validation_pipeline()
