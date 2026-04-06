"""
BookMyGig — Hybrid Recommendation System
==========================================
Combines:
  1. Content-Based Filtering (CBF) — TF-IDF cosine similarity on musician profiles
  2. Collaborative Filtering (CF)  — Truncated SVD matrix factorisation
  3. Sentiment Intelligence        — Boosts scores by musician sentiment score
  4. Cold-Start Strategy           — Pure CBF for new users; gradual shift to hybrid

Hybrid score = alpha * CF + (1-alpha) * CBF, then * (1 + beta * sentiment)
  alpha = min(interaction_count / 10, ALPHA_MAX) → 0 for cold users, up to 0.7
  beta  = 0.20 (sentiment boost weight)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize


ALPHA_MAX   = 0.70
BETA        = 0.20
SVD_COMPONENTS = 25
TOP_N       = 10
TFIDF_MAX_FEATURES = 5000


class HybridRecommender:
    """Cold-start-aware hybrid recommender for BookMyGig."""

    def __init__(
        self,
        alpha_max:      float = ALPHA_MAX,
        beta:           float = BETA,
        svd_components: int   = SVD_COMPONENTS,
        top_n:          int   = TOP_N,
        random_state:   int   = 42,
    ):
        self.alpha_max      = alpha_max
        self.beta           = beta
        self.svd_components = svd_components
        self.top_n          = top_n
        self.random_state   = random_state

        self._tfidf      = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES, ngram_range=(1, 2))
        self._svd        = TruncatedSVD(n_components=svd_components, random_state=random_state)
        self._tfidf_mat  = None   # musician × feature matrix
        self._user_item  = None   # client × musician rating matrix
        self._cf_preds   = None   # predicted ratings DataFrame
        self._musicians  = None   # musician metadata DataFrame
        self.is_fitted   = False

    # ── feature building ──────────────────────────────────────────────────────

    @staticmethod
    def _build_musician_profile(df: pd.DataFrame) -> pd.Series:
        """Concatenate text features for each musician."""
        return (
            df["Musician_Type"].fillna("") + " "
            + df["Genres"].fillna("") + " "
            + df["Location"].fillna("") + " "
            + df["Years_Experience"].fillna(0).astype(str) + "yr "
        )

    # ── fitting ───────────────────────────────────────────────────────────────

    def fit(
        self,
        musicians: pd.DataFrame,
        bookings:  pd.DataFrame,
        sentiment_scores: pd.Series | None = None,
    ) -> "HybridRecommender":
        """
        Parameters
        ----------
        musicians       : musicians DataFrame with Musician_ID column
        bookings        : bookings DataFrame with Client_ID, Musician_ID, Rating
        sentiment_scores: Series indexed by Musician_ID with avg sentiment (0-1)
        """
        self._musicians = musicians.copy().set_index("Musician_ID")

        # ── CBF: TF-IDF ───────────────────────────────────────────────────────
        profiles = self._build_musician_profile(musicians)
        self._tfidf_mat = self._tfidf.fit_transform(profiles)

        # attach sentiment scores to musician metadata
        if sentiment_scores is not None:
            self._musicians["avg_sentiment"] = sentiment_scores
        else:
            self._musicians["avg_sentiment"] = 0.5

        # ── CF: Truncated SVD ─────────────────────────────────────────────────
        pivot = (
            bookings.pivot_table(
                index="Client_ID", columns="Musician_ID", values="Rating", aggfunc="mean"
            )
            .fillna(0)
        )
        self._user_item = pivot

        mat = pivot.values
        latent = self._svd.fit_transform(mat)
        reconstructed = latent @ self._svd.components_
        self._cf_preds = pd.DataFrame(
            reconstructed, index=pivot.index, columns=pivot.columns
        )

        self.is_fitted = True
        return self

    # ── recommendation ────────────────────────────────────────────────────────

    def _alpha(self, client_id: str) -> float:
        """Adaptive alpha based on user history."""
        if self._user_item is None or client_id not in self._user_item.index:
            return 0.0
        rated = (self._user_item.loc[client_id] > 0).sum()
        return min(rated / 10, self.alpha_max)

    def _cbf_scores(self, query_musician_id: str | None, genres: str | None, location: str | None) -> pd.Series:
        """Content-based scores relative to a query profile."""
        if query_musician_id and query_musician_id in self._musicians.index:
            idx = list(self._musicians.index).index(query_musician_id)
            query_vec = self._tfidf_mat[idx]
        else:
            # build query from free-text preferences
            query_text = f"{genres or ''} {location or ''}".strip() or "pop"
            query_vec  = self._tfidf.transform([query_text])

        sims = cosine_similarity(query_vec, self._tfidf_mat).flatten()
        return pd.Series(sims, index=self._musicians.index)

    def recommend(
        self,
        client_id: str | None = None,
        genres: str | None = None,
        location: str | None = None,
        query_musician_id: str | None = None,
        exclude_ids: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Returns top-N musicians as DataFrame:
          Musician_ID, Musician_Name, final_score, cbf_score, cf_score, sentiment_boost
        """
        if not self.is_fitted:
            raise RuntimeError("Recommender not fitted — call fit() first")

        alpha = self._alpha(client_id) if client_id else 0.0

        # CBF scores
        cbf = self._cbf_scores(query_musician_id, genres, location)

        # CF scores (for this client)
        if alpha > 0 and client_id in self._cf_preds.index:
            cf_raw = self._cf_preds.loc[client_id]
            cf_raw = cf_raw.reindex(cbf.index).fillna(0)
            cf_norm = (cf_raw - cf_raw.min()) / (cf_raw.max() - cf_raw.min() + 1e-8)
        else:
            cf_norm = pd.Series(0.0, index=cbf.index)

        hybrid = alpha * cf_norm + (1 - alpha) * cbf

        # Sentiment boost
        sent = self._musicians.get("avg_sentiment", pd.Series(0.5, index=self._musicians.index))
        hybrid = hybrid * (1 + self.beta * sent.reindex(cbf.index).fillna(0.5))

        # Build result
        result = pd.DataFrame({
            "Musician_ID":    hybrid.index,
            "final_score":    hybrid.values,
            "cbf_score":      cbf.reindex(hybrid.index).values,
            "cf_score":       cf_norm.reindex(hybrid.index).values,
            "sentiment_boost": sent.reindex(hybrid.index).fillna(0.5).values,
        })
        result = result.merge(
            self._musicians[["Musician_Name", "Musician_Type", "Genres", "Location", "Base_Price"]].reset_index(),
            on="Musician_ID", how="left",
        )

        if exclude_ids:
            result = result[~result["Musician_ID"].isin(exclude_ids)]

        return result.sort_values("final_score", ascending=False).head(self.top_n).reset_index(drop=True)

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._tfidf,      path / "tfidf_vectorizer.joblib")
        joblib.dump(self._tfidf_mat,  path / "tfidf_matrix.joblib")
        joblib.dump(self._svd,        path / "svd_model.joblib")
        joblib.dump(self._user_item,  path / "user_item_matrix.joblib")
        joblib.dump(self._cf_preds,   path / "cf_predictions.joblib")
        joblib.dump(self._musicians,  path / "musicians_index.joblib")
        joblib.dump({
            "alpha_max": self.alpha_max, "beta": self.beta,
            "svd_components": self.svd_components, "top_n": self.top_n,
            "random_state": self.random_state,
        }, path / "recommender_config.joblib")

    @classmethod
    def load(cls, path: str | Path) -> "HybridRecommender":
        path = Path(path)
        cfg = joblib.load(path / "recommender_config.joblib")
        obj = cls(**cfg)
        obj._tfidf     = joblib.load(path / "tfidf_vectorizer.joblib")
        obj._tfidf_mat = joblib.load(path / "tfidf_matrix.joblib")
        obj._svd       = joblib.load(path / "svd_model.joblib")
        obj._user_item = joblib.load(path / "user_item_matrix.joblib")
        obj._cf_preds  = joblib.load(path / "cf_predictions.joblib")
        obj._musicians = joblib.load(path / "musicians_index.joblib")
        obj.is_fitted  = True
        return obj
