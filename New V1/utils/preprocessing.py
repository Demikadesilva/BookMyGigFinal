"""
Shared preprocessing utilities used across all models.
"""

import re
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler


# ── Text ─────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase, strip HTML/special chars, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML
    text = re.sub(r"[^a-z0-9\s'.,!?-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_text_length(series: pd.Series) -> pd.Series:
    return series.fillna("").apply(lambda x: len(str(x).split()))


# ── Encoding ──────────────────────────────────────────────────────────────────

def label_encode(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict]:
    encoders = {}
    df = df.copy()
    for col in columns:
        le = LabelEncoder()
        df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders


def one_hot_encode(df: pd.DataFrame, columns: list[str], drop_first: bool = True) -> pd.DataFrame:
    return pd.get_dummies(df, columns=columns, drop_first=drop_first)


# ── Normalisation ─────────────────────────────────────────────────────────────

def min_max_scale(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, MinMaxScaler]:
    scaler = MinMaxScaler()
    df = df.copy()
    df[columns] = scaler.fit_transform(df[columns].fillna(0))
    return df, scaler


def standard_scale(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
    scaler = StandardScaler()
    df = df.copy()
    df[columns] = scaler.fit_transform(df[columns].fillna(0))
    return df, scaler


# ── Missing Values ────────────────────────────────────────────────────────────

def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna("Unknown")
    return df


# ── Date Features ─────────────────────────────────────────────────────────────

def extract_datetime_features(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    dt = pd.to_datetime(df[col], errors="coerce")
    df[f"{col}_year"]        = dt.dt.year
    df[f"{col}_month"]       = dt.dt.month
    df[f"{col}_dayofweek"]   = dt.dt.dayofweek
    df[f"{col}_hour"]        = dt.dt.hour
    df[f"{col}_is_weekend"]  = (dt.dt.dayofweek >= 5).astype(int)
    df[f"{col}_quarter"]     = dt.dt.quarter
    return df
