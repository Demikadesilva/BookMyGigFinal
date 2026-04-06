"""
BookMyGig — Data Cleaning Pipeline
====================================
Cleans and validates the 6 raw CSV datasets:
  musicians, clients, events, bookings, reviews, social_media_metrics

Run:  python -m pipelines.data_cleaner
"""

import re
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    MUSICIANS_CSV, CLIENTS_CSV, EVENTS_CSV,
    BOOKINGS_CSV, REVIEWS_CSV, SOCIAL_METRICS_CSV,
    PROCESSED_DIR, RANDOM_SEED,
)
from utils.logging_config import get_logger

log = get_logger("data_cleaner", "data_cleaner.log")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def _report(df: pd.DataFrame, name: str, original_len: int) -> None:
    dropped = original_len - len(df)
    log.info(f"{name:30s} | rows: {len(df):>5,} | dropped: {dropped:>4,}")


def _strip_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all string columns."""
    for col in df.select_dtypes("object").columns:
        df[col] = df[col].str.strip()
    return df


# ── individual cleaners ───────────────────────────────────────────────────────

def clean_musicians(path=MUSICIANS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    # ID format
    df = df[df["Musician_ID"].str.match(r"^M\d{3,}$", na=False)]

    # required fields
    df = df.dropna(subset=["Musician_Name", "Musician_Type", "Location"])

    # valid types
    valid_types = {"Solo", "Band", "DJ", "Duo", "Trio", "Quartet"}
    df = df[df["Musician_Type"].isin(valid_types)]

    # numeric sanity
    df["Years_Experience"] = pd.to_numeric(df["Years_Experience"], errors="coerce").fillna(0).clip(0, 50).astype(int)
    df["Base_Price"]       = pd.to_numeric(df["Base_Price"],       errors="coerce").fillna(df["Base_Price"].median() if "Base_Price" in df else 300)
    df["Base_Price"]       = df["Base_Price"].clip(50, 5000).round(-1)  # round to 10

    # boolean
    df["Social_Links"] = df["Social_Links"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(False)

    # duplicate IDs
    df = df.drop_duplicates(subset="Musician_ID")

    # clean contact email (basic check)
    df["Musician_Contact"] = df["Musician_Contact"].str.lower()

    _report(df, "musicians", orig)
    return df.reset_index(drop=True)


def clean_clients(path=CLIENTS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    df = df[df["Client_ID"].str.match(r"^C\d{3,}$", na=False)]
    df = df.dropna(subset=["Client_Name", "Client_Type"])
    valid_types = {"Individual", "Corporate", "Venue", "Event Planner"}
    df = df[df["Client_Type"].isin(valid_types)]
    df = df.drop_duplicates(subset="Client_ID")

    _report(df, "clients", orig)
    return df.reset_index(drop=True)


def clean_events(path=EVENTS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    df = df[df["Event_ID"].str.match(r"^E\d{3,}$", na=False)]
    df = df.dropna(subset=["Event_ID", "Client_ID", "City", "Date_Time", "Event_Type"])

    df["Date_Time"]    = pd.to_datetime(df["Date_Time"], errors="coerce")
    df = df.dropna(subset=["Date_Time"])

    df["Expected_Pax"] = pd.to_numeric(df["Expected_Pax"], errors="coerce").fillna(50).clip(1, 2000).astype(int)
    df["Budget"]       = pd.to_numeric(df["Budget"], errors="coerce").clip(100, 500_000)
    df["Budget"]       = df["Budget"].fillna(df["Budget"].median())

    valid_event_types = {
        "Wedding", "Corporate", "Birthday", "Pub Gig", "Festival",
        "Private Party", "Concert", "Charity Gala", "University Ball",
        "Awards Night", "Product Launch", "Bar Mitzvah",
    }
    df["Event_Type"] = df["Event_Type"].apply(
        lambda x: x if x in valid_event_types else "Private Party"
    )

    df = df.drop_duplicates(subset="Event_ID")
    df["Date_Time"] = df["Date_Time"].dt.strftime("%Y-%m-%d %H:%M")

    _report(df, "events", orig)
    return df.reset_index(drop=True)


def clean_bookings(path=BOOKINGS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    df = df[df["Booking_ID"].str.match(r"^B\d{3,}$", na=False)]
    df = df.dropna(subset=["Booking_ID", "Musician_ID", "Client_ID", "Event_ID"])

    df["Duration"]      = pd.to_numeric(df["Duration"],      errors="coerce").clip(1, 12).fillna(2).astype(int)
    df["Price_Charged"] = pd.to_numeric(df["Price_Charged"], errors="coerce").clip(50, 50_000)
    df["Rating"]        = pd.to_numeric(df["Rating"],        errors="coerce").clip(1, 5).round().astype("Int64")

    df = df.dropna(subset=["Rating", "Price_Charged"])
    df = df.drop_duplicates(subset="Booking_ID")

    _report(df, "bookings", orig)
    return df.reset_index(drop=True)


def clean_reviews(path=REVIEWS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    df = df[df["Review_ID"].str.match(r"^R\d{3,}$", na=False)]
    df = df.dropna(subset=["Review_ID", "Booking_ID", "Review_Text"])

    # remove empty / very short reviews
    df["Review_Text"] = df["Review_Text"].astype(str)
    df = df[df["Review_Text"].str.split().str.len() >= 3]

    df["Rating"]     = pd.to_numeric(df["Rating"], errors="coerce").clip(1, 5).round().astype("Int64")
    df["Created_At"] = pd.to_datetime(df["Created_At"], errors="coerce").dt.strftime("%Y-%m-%d")

    df = df.dropna(subset=["Rating", "Created_At"])
    df = df.drop_duplicates(subset="Review_ID")

    # truncate excessively long reviews (> 500 words)
    df["Review_Text"] = df["Review_Text"].apply(
        lambda x: " ".join(str(x).split()[:500])
    )

    _report(df, "reviews", orig)
    return df.reset_index(drop=True)


def clean_social_metrics(path=SOCIAL_METRICS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    orig = len(df)
    df = _strip_df(df)

    df = df.dropna(subset=["Musician_ID", "Platform"])
    valid_platforms = {"Instagram", "TikTok", "YouTube"}
    df = df[df["Platform"].isin(valid_platforms)]

    for col in ["Followers", "Likes", "Views"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").clip(0).fillna(0).astype(int)

    df["Date_Collected"] = pd.to_datetime(df["Date_Collected"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["Date_Collected"])

    # remove duplicate musician+platform+date combinations (keep latest)
    df = df.sort_values("Date_Collected", ascending=False)
    df = df.drop_duplicates(subset=["Musician_ID", "Platform", "Date_Collected"])

    _report(df, "social_media_metrics", orig)
    return df.reset_index(drop=True)


# ── cross-table referential integrity ─────────────────────────────────────────

def enforce_referential_integrity(
    musicians, clients, events, bookings, reviews, social
) -> tuple:
    """Remove orphan records that reference non-existent parent records."""

    m_ids  = set(musicians["Musician_ID"])
    c_ids  = set(clients["Client_ID"])
    e_ids  = set(events["Event_ID"])
    b_ids  = set(bookings["Booking_ID"])

    # events must reference valid clients
    before = len(events)
    events = events[events["Client_ID"].isin(c_ids)]
    log.info(f"events after ref-integrity: {len(events)} (dropped {before - len(events)} orphan client refs)")

    # bookings must reference valid musicians, clients, events
    before = len(bookings)
    bookings = bookings[
        bookings["Musician_ID"].isin(m_ids) &
        bookings["Client_ID"].isin(c_ids) &
        bookings["Event_ID"].isin(e_ids)
    ]
    log.info(f"bookings after ref-integrity: {len(bookings)} (dropped {before - len(bookings)})")

    # reviews must reference valid bookings
    b_ids = set(bookings["Booking_ID"])
    before = len(reviews)
    reviews = reviews[reviews["Booking_ID"].isin(b_ids)]
    log.info(f"reviews after ref-integrity: {len(reviews)} (dropped {before - len(reviews)})")

    # social must reference valid musicians
    before = len(social)
    social = social[social["Musician_ID"].isin(m_ids)]
    log.info(f"social_metrics after ref-integrity: {len(social)} (dropped {before - len(social)})")

    return musicians, clients, events, bookings, reviews, social


# ── save ──────────────────────────────────────────────────────────────────────

def save_cleaned(df: pd.DataFrame, filename: str) -> None:
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    log.info(f"Saved → {path}")


# ── main ──────────────────────────────────────────────────────────────────────

def run_cleaning_pipeline() -> dict[str, pd.DataFrame]:
    log.info("=" * 60)
    log.info("BookMyGig — Data Cleaning Pipeline")
    log.info("=" * 60)

    musicians = clean_musicians()
    clients   = clean_clients()
    events    = clean_events()
    bookings  = clean_bookings()
    reviews   = clean_reviews()
    social    = clean_social_metrics()

    musicians, clients, events, bookings, reviews, social = enforce_referential_integrity(
        musicians, clients, events, bookings, reviews, social
    )

    save_cleaned(musicians, "musicians_clean.csv")
    save_cleaned(clients,   "clients_clean.csv")
    save_cleaned(events,    "events_clean.csv")
    save_cleaned(bookings,  "bookings_clean.csv")
    save_cleaned(reviews,   "reviews_clean.csv")
    save_cleaned(social,    "social_media_metrics_clean.csv")

    log.info("Cleaning pipeline complete.")
    return {
        "musicians": musicians, "clients": clients, "events": events,
        "bookings": bookings, "reviews": reviews, "social": social,
    }


if __name__ == "__main__":
    run_cleaning_pipeline()
