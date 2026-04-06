"""
BookMyGig — LLM-as-a-Judge Dataset Validation
===============================================
Uses gpt-5-chat via Azure OpenAI to evaluate dataset quality across four dimensions:
  1. Data Quality      — are values realistic and well-formed?
  2. Consistency       — do records agree with each other?
  3. Correctness       — are the semantics logically sound?
  4. Completeness      — are all required fields populated?

Each dimension is scored 0-10 with structured JSON feedback.

Setup:
  export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
  export AZURE_OPENAI_API_KEY="<your-key>"
  export AZURE_OPENAI_DEPLOYMENT="gpt-5-chat"    # or your deployment name

Run:
  python -m pipelines.llm_judge
  python -m pipelines.llm_judge --table reviews --samples 20
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    PROCESSED_DIR, RAW_DIR,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT,
    EVAL_REPORT_DIR, RANDOM_SEED,
)
from utils.logging_config import get_logger

log = get_logger("llm_judge", "llm_judge.log")


# ── data structures ───────────────────────────────────────────────────────────

@dataclass
class JudgementResult:
    table: str
    sample_index: int
    record_id: str
    quality_score: float        # 0-10
    consistency_score: float    # 0-10
    correctness_score: float    # 0-10
    completeness_score: float   # 0-10
    overall_score: float        # weighted average
    issues: list[str]
    suggestions: list[str]
    raw_response: str

    @property
    def pass_threshold(self) -> bool:
        return self.overall_score >= 7.0


# ── Azure OpenAI client ───────────────────────────────────────────────────────

def _get_client():
    """Return an AzureOpenAI client. Raises clear error if credentials missing."""
    try:
        from openai import AzureOpenAI
    except ImportError:
        raise ImportError("openai package not installed. Run: pip install openai>=1.0.0")

    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        raise EnvironmentError(
            "Azure OpenAI credentials not set.\n"
            "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
        )

    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


# ── prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert data quality auditor specialising in AI training datasets for
music booking platforms. Your task is to evaluate individual records from a synthetic dataset
called BookMyGig. You must assess each record across four dimensions and return a structured
JSON response.

Evaluation dimensions (score each 0-10):
  - quality:       Are values realistic, well-formatted, and plausible for a UK music booking platform?
  - consistency:   Do the values within the record agree with each other (e.g. price vs. experience vs. type)?
  - correctness:   Are the semantics logically sound (e.g. review sentiment matches rating)?
  - completeness:  Are all required fields populated with meaningful values?

Return ONLY valid JSON in this exact schema:
{
  "quality_score": <float 0-10>,
  "consistency_score": <float 0-10>,
  "correctness_score": <float 0-10>,
  "completeness_score": <float 0-10>,
  "issues": ["<issue 1>", "<issue 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"]
}

Be strict but fair. A perfect record scores 10 on all dimensions."""


def _build_user_prompt(table: str, record: dict) -> str:
    table_context = {
        "musicians": "This record represents a musician profile on a UK-based booking platform.",
        "clients":   "This record represents a client (individual, corporate, venue, or event planner) on a booking platform.",
        "events":    "This record represents an event that a client is organising and wants to book music for.",
        "bookings":  "This record represents a completed booking between a client and a musician for an event.",
        "reviews":   "This record represents a review left by a client after a booking. Crucially, the review text sentiment should match the numeric rating.",
        "social_media_metrics": "This record represents social media statistics for a musician on one platform.",
    }.get(table, f"This is a record from the {table} table.")

    record_json = json.dumps(record, indent=2, default=str)
    return (
        f"Table: {table}\n"
        f"Context: {table_context}\n\n"
        f"Record to evaluate:\n{record_json}\n\n"
        "Please evaluate this record and return your assessment as JSON."
    )


# ── LLM call with retry ───────────────────────────────────────────────────────

def _call_llm(client, prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.1,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            wait = 2 ** attempt
            log.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait}s…")
            time.sleep(wait)
    raise RuntimeError("LLM call failed after all retries")


def _parse_llm_response(raw: str) -> dict:
    try:
        data = json.loads(raw)
        return {
            "quality_score":     float(data.get("quality_score", 5.0)),
            "consistency_score": float(data.get("consistency_score", 5.0)),
            "correctness_score": float(data.get("correctness_score", 5.0)),
            "completeness_score":float(data.get("completeness_score", 5.0)),
            "issues":            data.get("issues", []),
            "suggestions":       data.get("suggestions", []),
        }
    except (json.JSONDecodeError, ValueError) as e:
        log.error(f"Failed to parse LLM response: {e}\nRaw: {raw[:200]}")
        return {
            "quality_score": 0.0, "consistency_score": 0.0,
            "correctness_score": 0.0, "completeness_score": 0.0,
            "issues": ["Parse error"], "suggestions": [],
        }


# ── main judge function ───────────────────────────────────────────────────────

def judge_table(
    table: str,
    df: pd.DataFrame,
    id_col: str,
    n_samples: int = 30,
    delay_seconds: float = 0.5,
) -> list[JudgementResult]:
    """Run LLM-as-a-judge on `n_samples` random rows of `df`."""

    client = _get_client()

    sample = df.sample(min(n_samples, len(df)), random_state=RANDOM_SEED).reset_index(drop=True)
    results = []

    log.info(f"Judging {len(sample)} samples from [{table}] …")

    for idx, row in sample.iterrows():
        record = row.to_dict()
        record_id = str(record.get(id_col, idx))

        prompt = _build_user_prompt(table, record)
        raw = _call_llm(client, prompt)
        parsed = _parse_llm_response(raw)

        # weighted overall score: correctness weighted highest for reviews
        weights = (
            {"quality": 0.2, "consistency": 0.2, "correctness": 0.4, "completeness": 0.2}
            if table == "reviews"
            else {"quality": 0.25, "consistency": 0.25, "correctness": 0.25, "completeness": 0.25}
        )
        overall = (
            parsed["quality_score"]      * weights["quality"]
            + parsed["consistency_score"]  * weights["consistency"]
            + parsed["correctness_score"]  * weights["correctness"]
            + parsed["completeness_score"] * weights["completeness"]
        )

        result = JudgementResult(
            table=table,
            sample_index=int(idx),
            record_id=record_id,
            quality_score=parsed["quality_score"],
            consistency_score=parsed["consistency_score"],
            correctness_score=parsed["correctness_score"],
            completeness_score=parsed["completeness_score"],
            overall_score=round(overall, 2),
            issues=parsed["issues"],
            suggestions=parsed["suggestions"],
            raw_response=raw,
        )
        results.append(result)

        status = "PASS" if result.pass_threshold else "FAIL"
        log.info(
            f"  [{status}] {record_id:10s} | "
            f"Q={parsed['quality_score']:.1f} "
            f"C={parsed['consistency_score']:.1f} "
            f"Cor={parsed['correctness_score']:.1f} "
            f"Comp={parsed['completeness_score']:.1f} "
            f"→ {overall:.2f}"
        )

        if parsed["issues"]:
            for issue in parsed["issues"]:
                log.debug(f"    Issue: {issue}")

        time.sleep(delay_seconds)

    return results


# ── aggregate report ──────────────────────────────────────────────────────────

def print_judge_summary(all_results: list[JudgementResult]) -> None:
    if not all_results:
        print("No results to summarise.")
        return

    tables = sorted(set(r.table for r in all_results))

    print("\n" + "=" * 75)
    print("  LLM-AS-A-JUDGE VALIDATION REPORT")
    print("=" * 75)
    print(f"  {'Table':<30} {'N':>4} {'Quality':>8} {'Consist':>8} {'Correct':>8} {'Complete':>9} {'Overall':>8} {'Pass%':>7}")
    print("-" * 75)

    for tbl in tables:
        rs = [r for r in all_results if r.table == tbl]
        avg = lambda attr: sum(getattr(r, attr) for r in rs) / len(rs)
        pass_pct = sum(1 for r in rs if r.pass_threshold) / len(rs) * 100

        print(
            f"  {tbl:<30} {len(rs):>4} "
            f"{avg('quality_score'):>8.2f} "
            f"{avg('consistency_score'):>8.2f} "
            f"{avg('correctness_score'):>8.2f} "
            f"{avg('completeness_score'):>9.2f} "
            f"{avg('overall_score'):>8.2f} "
            f"{pass_pct:>6.1f}%"
        )

    overall = sum(r.overall_score for r in all_results) / len(all_results)
    pass_total = sum(1 for r in all_results if r.pass_threshold) / len(all_results) * 100
    print("-" * 75)
    print(f"  {'TOTAL':<30} {len(all_results):>4} {'':>8} {'':>8} {'':>8} {'':>9} {overall:>8.2f} {pass_total:>6.1f}%")
    print("=" * 75 + "\n")


def save_judge_report(all_results: list[JudgementResult], path: Path | None = None) -> Path:
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EVAL_REPORT_DIR / f"llm_judge_report_{ts}.json"

    data = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(all_results),
        "overall_avg_score": round(sum(r.overall_score for r in all_results) / max(len(all_results), 1), 3),
        "pass_rate": round(sum(1 for r in all_results if r.pass_threshold) / max(len(all_results), 1), 3),
        "results": [asdict(r) for r in all_results],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    log.info(f"Judge report saved → {path}")
    return path


# ── CLI entry point ───────────────────────────────────────────────────────────

TABLE_CONFIG = {
    "musicians":           ("Musician_ID",  20),
    "clients":             ("Client_ID",    15),
    "events":              ("Event_ID",     15),
    "bookings":            ("Booking_ID",   20),
    "reviews":             ("Review_ID",    25),
    "social_media_metrics":("Musician_ID",  15),
}


def _load_table(table: str) -> pd.DataFrame:
    clean_path = PROCESSED_DIR / f"{table}_clean.csv"
    raw_path   = RAW_DIR / f"{table}.csv"
    path = clean_path if clean_path.exists() else raw_path
    log.info(f"Loading {table} from {path}")
    return pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="BookMyGig LLM-as-a-Judge validator")
    parser.add_argument("--table",   default="all",  help="Table name or 'all'")
    parser.add_argument("--samples", type=int, default=None, help="Samples per table (overrides default)")
    parser.add_argument("--delay",   type=float, default=0.5, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    tables_to_run = list(TABLE_CONFIG.keys()) if args.table == "all" else [args.table]
    all_results: list[JudgementResult] = []

    for table in tables_to_run:
        if table not in TABLE_CONFIG:
            log.warning(f"Unknown table '{table}' — skipping")
            continue

        id_col, default_samples = TABLE_CONFIG[table]
        n = args.samples if args.samples else default_samples

        df = _load_table(table)
        results = judge_table(table, df, id_col, n_samples=n, delay_seconds=args.delay)
        all_results.extend(results)

    print_judge_summary(all_results)
    save_judge_report(all_results)


if __name__ == "__main__":
    main()
