import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

EVAL_DIR = Path(__file__).parent
REPORTS_DIR = EVAL_DIR / "reports"
CHARTS_DIR = EVAL_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def plot_pricing_comparison():
    report_path = REPORTS_DIR / "pricing_evaluation.json"
    if not report_path.exists():
        print("Pricing report not found. Run evaluate_pricing.py first.")
        return

    with open(report_path, "r") as f:
        data = json.load(f)

    models = data.get("models", {})
    if not models: return

    model_names = list(models.keys())
    rmse_vals = [models[m].get("RMSE", 0) for m in model_names]
    mae_vals = [models[m].get("MAE", 0) for m in model_names]

    x = np.arange(len(model_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, rmse_vals, width, label='RMSE (£)', color='#2c3e50')
    ax.bar(x + width/2, mae_vals, width, label='MAE (£)', color='#e74c3c')

    ax.set_ylabel('Error in £ (Lower is better)')
    ax.set_title('Pricing Model Comparison: Ridge vs LightGBM')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    save_path = CHARTS_DIR / 'pricing_comparison_chart.png'
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Created: {save_path.name}")


def plot_sentiment_comparison():
    """
    Automatically reads the sentiment JSON and plots VADER vs DistilBERT.
    """
    report_path = REPORTS_DIR / "sentiment_evaluation.json"
    if not report_path.exists():
        print("Sentiment report not found. Run evaluate_sentiment.py first.")
        return

    with open(report_path, "r") as f:
        data = json.load(f)

    models = data.get("models", {})
    if "VADER" not in models or "DistilBERT" not in models:
        print("Model specific data not found in sentiment json.")
        return

    vader = models["VADER"]
    bert = models["DistilBERT"]

    vader_scores = [vader["accuracy"], vader["precision"], vader["recall"], vader["f1_score"]]
    bert_scores = [bert["accuracy"], bert["precision"], bert["recall"], bert["f1_score"]]
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    
    bars1 = ax.bar(x - width/2, vader_scores, width, label='VADER (Baseline)', color='#e74c3c')
    bars2 = ax.bar(x + width/2, bert_scores, width, label='DistilBERT (Advanced)', color='#2ecc71')

    ax.set_ylabel('Score (0 to 1)')
    ax.set_title('Sentiment Analysis Model Comparison: VADER vs DistilBERT')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.1)
    ax.legend(loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for bars in [bars1, bars2]:
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval:.3f}', ha='center', fontsize=9)

    save_path = CHARTS_DIR / 'sentiment_comparison_chart.png'
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Created: {save_path.name}")


def plot_recommendation_metrics():
    report_path = REPORTS_DIR / "recommendation_evaluation.json"
    if not report_path.exists():
        print("Recommendation report not found. Run evaluate_recommendation.py first.")
        return

    with open(report_path, "r") as f:
        data = json.load(f)

    k = data.get('k', 10)
    metrics = [f'Precision@{k}', f'Recall@{k}', f'NDCG@{k}', 'MAP']
    scores = [
        data.get('precision_at_k', 0),
        data.get('recall_at_k', 0),
        data.get('ndcg_at_k', 0),
        data.get('map', 0)
    ]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(metrics, scores, color='#16a085')
    
    plt.ylim(0, max(scores) + 0.1 if scores else 1.0)
    plt.ylabel('Score')
    plt.title('Hybrid Recommendation System Metrics')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.01, round(yval, 4), ha='center')

    save_path = CHARTS_DIR / 'recommendation_metrics_chart.png'
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Created: {save_path.name}")

def plot_anomaly_metrics():
    """
    Reads the anomaly_evaluation.json report and plots 
    Precision, Recall, F1, and ROC-AUC against the synthetic ground truth.
    """
    report_path = REPORTS_DIR / "anomaly_evaluation.json"
    if not report_path.exists():
        print("Anomaly report not found. Run evaluate_anomaly.py first.")
        return

    with open(report_path, "r") as f:
        data = json.load(f)

    gt_metrics = data.get("vs_synthetic_gt", {})
    if not gt_metrics:
        print("No ground truth metrics found in anomaly JSON.")
        return

    metrics = ['Precision', 'Recall', 'F1-Score', 'ROC-AUC']
    scores = [
        gt_metrics.get('precision', 0),
        gt_metrics.get('recall', 0),
        gt_metrics.get('f1', 0),
        gt_metrics.get('roc_auc', 0)
    ]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(metrics, scores, color=['#e67e22', '#d35400', '#f39c12', '#c0392b'])
    
    plt.ylim(0, 1.1)
    plt.ylabel('Score (0 to 1)')
    plt.title('Isolation Forest: Anomaly Detection Performance')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.4f}", ha='center')

    save_path = CHARTS_DIR / 'anomaly_metrics_chart.png'
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" Created: {save_path.name}")


if __name__ == "__main__":
    print("Generating Result Charts...")
    plot_pricing_comparison()
    plot_sentiment_comparison()
    plot_recommendation_metrics()
    plot_anomaly_metrics()
    print(f"\nAll charts have been saved to: {CHARTS_DIR}")