"""
BookMyGig — Sentiment Analysis Model
======================================
Two-stage sentiment analysis:
  Stage 1: VADER (fast, rule-based baseline)
  Stage 2: DistilBERT (deep learning, fine-tuned on SST-2)
  Final:   Weighted blend (40% VADER + 60% BERT)

Output per review:
  - vader_score       : compound -1 to +1
  - bert_score        : probability of POSITIVE class
  - sentiment_score   : blended 0-1 score
  - sentiment_label   : POSITIVE / NEUTRAL / NEGATIVE
"""

from __future__ import annotations

import os
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

warnings.filterwarnings("ignore")

# ── lazy imports ──────────────────────────────────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_AVAILABLE = True
except ImportError:
    _VADER_AVAILABLE = False

try:
    from transformers import pipeline as hf_pipeline, AutoTokenizer, AutoModelForSequenceClassification
    _BERT_AVAILABLE = True
except ImportError:
    _BERT_AVAILABLE = False


VADER_WEIGHT = 0.40
BERT_WEIGHT  = 0.60
DISTILBERT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
MAX_LEN = 512


class SentimentModel:
    """Ensemble sentiment analyser: VADER + DistilBERT."""

    def __init__(
        self,
        vader_weight: float = VADER_WEIGHT,
        bert_weight:  float = BERT_WEIGHT,
        use_bert:     bool  = True,
        bert_batch_size: int = 32,
    ):
        self.vader_weight    = vader_weight
        self.bert_weight     = bert_weight
        self.use_bert        = use_bert and _BERT_AVAILABLE
        self.bert_batch_size = bert_batch_size
        self._vader = None
        self._bert  = None

    # ── setup ─────────────────────────────────────────────────────────────────

    def _load_vader(self):
        if not _VADER_AVAILABLE:
            raise ImportError("vaderSentiment not installed: pip install vaderSentiment")
        if self._vader is None:
            self._vader = SentimentIntensityAnalyzer()
        return self._vader

    def _load_bert(self):
        if not _BERT_AVAILABLE:
            raise ImportError("transformers not installed: pip install transformers torch")
        if self._bert is None:
            from config import SAVED_MODELS_DIR
            custom_model_path = SAVED_MODELS_DIR / "distilbert_finetuned"
            
            if custom_model_path.exists():
                print(f"Loading CUSTOM fine-tuned DistilBERT from {custom_model_path}...")
                model_to_load = str(custom_model_path)
            else:
                print("Custom model not found. Falling back to generic pre-trained model...")
                model_to_load = DISTILBERT_MODEL

            self._bert = hf_pipeline(
                "text-classification",
                model=model_to_load, 
                tokenizer=model_to_load,
                truncation=True,
                max_length=MAX_LEN,
                device=-1,   # CPU; set to 0 for GPU if you have one
            )
        return self._bert

    # ── scoring ───────────────────────────────────────────────────────────────

    def vader_score(self, text: str) -> float:
        """VADER compound score normalised to [0, 1]."""
        if not isinstance(text, str) or not text.strip():
            return 0.5
        vader = self._load_vader()
        compound = vader.polarity_scores(text)["compound"]  # -1 to +1
        return (compound + 1) / 2  # map to [0, 1]

    def bert_score(self, texts: list[str]) -> np.ndarray:
        """DistilBERT POSITIVE probability for a batch of texts. Returns array [0,1]."""
        bert = self._load_bert()
        scores = []
        for i in range(0, len(texts), self.bert_batch_size):
            batch = texts[i : i + self.bert_batch_size]
            results = bert(batch)
            for r in results:
                if r["label"] == "POSITIVE":
                    score = 0.6 + (r["score"] * 0.4)
                elif r["label"] == "NEGATIVE":
                    score = 0.4 - (r["score"] * 0.4)
                else:
                    score = 0.5
                scores.append(score)
        return np.array(scores)

    def predict(self, texts: list[str]) -> pd.DataFrame:
        """
        Run full ensemble prediction on a list of texts.
        Returns DataFrame with columns:
          vader_score, bert_score, sentiment_score, sentiment_label
        """
        if not texts:
            return pd.DataFrame(columns=["vader_score", "bert_score", "sentiment_score", "sentiment_label"])

        # VADER pass
        vader_scores = np.array([self.vader_score(t) for t in texts])

        # BERT pass (optional)
        if self.use_bert:
            bert_scores = self.bert_score(texts)
            blended = self.vader_weight * vader_scores + self.bert_weight * bert_scores
        else:
            bert_scores = np.full(len(texts), np.nan)
            blended = vader_scores

        labels = np.where(blended >= 0.6, "POSITIVE",
                          np.where(blended <= 0.4, "NEGATIVE", "NEUTRAL"))

        return pd.DataFrame({
            "vader_score":     np.round(vader_scores, 4),
            "bert_score":      np.round(bert_scores, 4),
            "sentiment_score": np.round(blended, 4),
            "sentiment_label": labels,
        })

    def predict_series(self, series: pd.Series) -> pd.DataFrame:
        return self.predict(series.fillna("").astype(str).tolist())

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "vader_weight": self.vader_weight,
            "bert_weight":  self.bert_weight,
            "use_bert":     self.use_bert,
            "bert_batch_size": self.bert_batch_size,
        }, path / "sentiment_config.joblib")

    @classmethod
    def load(cls, path: str | Path) -> "SentimentModel":
        path = Path(path)
        cfg = joblib.load(path / "sentiment_config.joblib")
        return cls(**cfg)
