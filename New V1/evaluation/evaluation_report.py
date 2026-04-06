"""
BookMyGig — Comprehensive Evaluation Report Generator
======================================================
Aggregates all model evaluation results into one JSON + printed report.

Run:  python -m evaluation.evaluation_report
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EVAL_REPORT_DIR
from utils.logging_config import get_logger

log = get_logger("eval_report", "eval_report.log")


def load_report(name: str) -> dict:
    path = EVAL_REPORT_DIR / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"status": "not_found", "path": str(path)}


def generate_report() -> dict:
    log.info("Generating comprehensive evaluation report...")

    reports = {
        "sentiment":       load_report("sentiment_evaluation"),
        "anomaly":         load_report("anomaly_evaluation"),
        "recommendation":  load_report("recommendation_evaluation"),
        "pricing":         load_report("pricing_evaluation"),
        "validation":      load_report("validation_report"),
        "llm_judge":       {},  # populated if exists
    }

    # find latest llm_judge report
    llm_reports = sorted(EVAL_REPORT_DIR.glob("llm_judge_report_*.json"), reverse=True)
    if llm_reports:
        with open(llm_reports[0]) as f:
            reports["llm_judge"] = json.load(f)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "reports": reports,
        "headline_metrics": {},
    }

    # Extract headline numbers
    hm = summary["headline_metrics"]
    if "accuracy" in reports["sentiment"]:
        hm["sentiment_accuracy"]    = reports["sentiment"]["accuracy"]
        hm["sentiment_f1"]          = reports["sentiment"].get("f1_score")
    if "flagged_pct" in reports["anomaly"]:
        hm["anomaly_flagged_pct"]   = reports["anomaly"]["flagged_pct"]
    if "ndcg_at_k" in reports["recommendation"]:
        hm["rec_ndcg_at_10"]        = reports["recommendation"]["ndcg_at_k"]
        hm["rec_precision_at_10"]   = reports["recommendation"]["precision_at_k"]
    if "models" in reports["pricing"]:
        lgb = reports["pricing"]["models"].get("LightGBM", {})
        hm["pricing_rmse_lgb"]      = lgb.get("RMSE")
        hm["pricing_r2_lgb"]        = lgb.get("R2")
    if "overall_score" in reports["validation"]:
        hm["data_quality_score"]    = reports["validation"]["overall_score"]
    if "overall_avg_score" in reports.get("llm_judge", {}):
        hm["llm_judge_avg_score"]   = reports["llm_judge"]["overall_avg_score"]

    # Print consolidated summary
    print("\n" + "=" * 75)
    print("  BOOKMYGIG AI — COMPREHENSIVE EVALUATION REPORT")
    print(f"  Generated: {summary['generated_at'][:19]}")
    print("=" * 75)

    for metric, value in hm.items():
        if value is not None:
            print(f"  {metric:<35} : {value}")

    print("\n  Model Evaluation Details:")
    if "accuracy" in reports["sentiment"]:
        print(f"    Sentiment  | Accuracy={reports['sentiment']['accuracy']:.4f}  F1={reports['sentiment'].get('f1_score',0):.4f}")
    if "flagged_pct" in reports["anomaly"]:
        print(f"    Anomaly    | Flagged={reports['anomaly']['flagged_pct']:.1f}%  ROC-AUC={reports['anomaly'].get('vs_synthetic_gt',{}).get('roc_auc',0):.4f}")
    if "ndcg_at_k" in reports["recommendation"]:
        r = reports["recommendation"]
        print(f"    Recommender| NDCG@10={r['ndcg_at_k']:.4f}  MAP={r.get('map',0):.4f}  Coverage={r.get('catalog_coverage',0):.2%}")
    if "models" in reports["pricing"]:
        lgb = reports["pricing"]["models"].get("LightGBM", {})
        print(f"    Pricing    | RMSE=£{lgb.get('RMSE','?')}  MAE=£{lgb.get('MAE','?')}  R²={lgb.get('R2','?')}")
    if "overall_score" in reports["validation"]:
        print(f"    Data       | Quality Score={reports['validation']['overall_score']:.1f}/100")

    print("=" * 75 + "\n")

    # Save
    out_path = EVAL_REPORT_DIR / "comprehensive_evaluation_report.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Comprehensive report saved → {out_path}")
    return summary


if __name__ == "__main__":
    generate_report()
