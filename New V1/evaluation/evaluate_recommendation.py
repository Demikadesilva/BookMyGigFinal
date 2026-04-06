"""
BookMyGig — Recommendation System Evaluation
=============================================
Metrics: Precision@K, Recall@K, NDCG@K, MAP, Coverage, Novelty

Run:  python -m evaluation.evaluate_recommendation
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, MUSICIANS_CSV, BOOKINGS_CSV, SAVED_MODELS_DIR, EVAL_REPORT_DIR, RANDOM_SEED
from models.recommendation_model import HybridRecommender
from utils.logging_config import get_logger

log = get_logger("eval_recommendation", "eval_recommendation.log")


def dcg_at_k(relevant: list, k: int) -> float:
    """Discounted Cumulative Gain."""
    relevance = [1 if item in relevant else 0 for item in relevant[:k]]
    return sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevance))


def ndcg_at_k(recommended: list, relevant: list, k: int) -> float:
    actual_dcg = dcg_at_k(recommended[:k], k)
    ideal = sorted([1] * len(relevant) + [0] * max(0, k - len(relevant)), reverse=True)
    ideal_dcg = sum(rel / np.log2(idx + 2) for idx, rel in enumerate(ideal[:k]))
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def evaluate(k: int = 10) -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Recommendation System Evaluation")
    log.info("=" * 60)

    # Load recommender
    rec_path = SAVED_MODELS_DIR / "recommendation"
    if not rec_path.exists():
        log.warning("Recommender not found — training now...")
        from training.train_recommendation import run
        run()

    recommender = HybridRecommender.load(rec_path)

    # Load bookings
    bk_path = PROCESSED_DIR / "bookings_clean.csv"
    bookings = pd.read_csv(bk_path if bk_path.exists() else BOOKINGS_CSV)

    # Build ground truth: for each client, all musicians they rated 4+
    ground_truth = (
        bookings[bookings["Rating"] >= 4]
        .groupby("Client_ID")["Musician_ID"]
        .apply(list)
        .to_dict()
    )

    item_counts = bookings["Musician_ID"].value_counts().to_dict()
    total_interactions = len(bookings)

    # Evaluate on clients with history
    warm_clients = [
        cid for cid, hist in ground_truth.items()
        if len(hist) >= 2
    ]

    if not warm_clients:
        log.warning("No warm clients found for evaluation")
        return {}

    sample = warm_clients[:min(100, len(warm_clients))]

    precisions, recalls, ndcgs, aps, novelty_scores = [], [], [], [], []
    all_recommended = set()

    for cid in sample:
        relevant  = ground_truth.get(cid, [])
        # exclude last booking (leave-one-out)
        holdout   = relevant[-1]
        train_rel = relevant[:-1]

        try:
            recs = recommender.recommend(client_id=cid, exclude_ids=train_rel)
            rec_ids = recs["Musician_ID"].tolist()
        except Exception:
            continue

        all_recommended.update(rec_ids)
        hits = [m for m in rec_ids[:k] if m == holdout]

        p = len(hits) / k
        r = len(hits) / max(1, 1)  # only 1 holdout item
        n = ndcg_at_k(rec_ids, [holdout], k)

        # AP
        ap = sum(
            (len([m for m in rec_ids[:j+1] if m == holdout]) / (j + 1))
            for j, m in enumerate(rec_ids[:k])
            if m == holdout
        ) / max(1, 1)

        rec_novelty = [
            -np.log2(item_counts.get(m, 1) / total_interactions)
            for m in rec_ids[:k]
        ]
        novelty_scores.append(np.mean(rec_novelty))

        precisions.append(p)
        recalls.append(r)
        ndcgs.append(n)
        aps.append(ap)

    n_musicians = len(recommender._musicians)
    coverage = len(all_recommended) / n_musicians if n_musicians else 0

    metrics = {
        "k": k,
        "evaluated_clients":  len(sample),
        "precision_at_k":    round(np.mean(precisions), 4),
        "recall_at_k":       round(np.mean(recalls), 4),
        "ndcg_at_k":         round(np.mean(ndcgs), 4),
        "map":               round(np.mean(aps), 4),
        "catalog_coverage":  round(coverage, 4),
        "map":               round(np.mean(aps), 4),
        "catalog_coverage":  round(coverage, 4),
        "novelty":           round(np.mean(novelty_scores), 4)
    }

    print("\n" + "=" * 60)
    print(f"  RECOMMENDATION EVALUATION RESULTS (K={k})")
    print("=" * 60)
    print(f"  Evaluated clients  : {len(sample)}")
    print(f"  Precision@{k}       : {metrics['precision_at_k']:.4f}")
    print(f"  Recall@{k}          : {metrics['recall_at_k']:.4f}")
    print(f"  NDCG@{k}            : {metrics['ndcg_at_k']:.4f}")
    print(f"  MAP                : {metrics['map']:.4f}")
    print(f"  Catalog Coverage   : {metrics['catalog_coverage']:.4f}")
    print(f"  Novelty            : {metrics['novelty']:.4f}")
    print("=" * 60 + "\n")
    

    report_path = EVAL_REPORT_DIR / "recommendation_evaluation.json"
    with open(report_path, "w") as fp:
        json.dump(metrics, fp, indent=2)
    log.info(f"Report saved → {report_path}")

    return metrics


if __name__ == "__main__":
    evaluate()
