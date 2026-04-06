import pandas as pd
import numpy as np
import random
from pathlib import Path
import uuid
import datetime
import os
import sys

# Change working directory so models can be imported
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database import engine, Base, SessionLocal
from models.musician import Musician
from models.event import Event
from models.booking import Booking
from models.review import Review
from models.social_metric import SocialMetric
from sqlalchemy.orm import Session

# Recreate tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

DATASET_DIR = Path("../Dataset")
DATASET_DIR.mkdir(exist_ok=True)

# Generate 2500 Musicians
musicians = []
musician_types = ["Band", "Solo Musician", "DJ", "Orchestra", "Singer"]
genres = ["Rock", "Pop", "Jazz", "Classical", "Hip Hop", "Electronic", "Country", "R&B"]
cities = ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool", "Edinburgh", "Bristol"]

for i in range(1, 2501):
    m_id = f"M{i:05d}"
    musicians.append({
        "Musician_ID": m_id,
        "Musician_Name": f"Artist {i}",
        "Musician_Type": random.choice(musician_types),
        "Musician_Contact": f"contact{i}@example.com",
        "Location": random.choice(cities),
        "Genres": ", ".join(random.sample(genres, k=random.randint(1, 3))),
        "Years_Experience": random.randint(1, 20),
        "Base_Price": round(random.uniform(100.0, 2000.0), 2),
        "Social_Links": str(random.choice([True, False]))
    })

# Events, Bookings, Reviews ... (omitted CSV writing to save time, directly injecting)

events = []
client_ids = [f"C{str(uuid.uuid4())[:8]}" for _ in range(1000)]
event_types = ["Wedding", "Corporate Event", "Private Party", "Festival", "Club Night", "Birthday"]

for i in range(1, 5001):
    events.append({
        "Event_ID": f"E{i:06d}",
        "Client_ID": random.choice(client_ids),
        "City": random.choice(cities),
        "Date_Time": (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 365))).isoformat(),
        "Expected_Pax": random.randint(20, 1000),
        "Event_Type": random.choice(event_types),
        "Budget": round(random.uniform(500.0, 5000.0), 2)
    })

bookings = []
for i in range(1, 5001):
    b_id = f"B{i:06d}"
    bookings.append({
        "Booking_ID": b_id,
        "Musician_ID": random.choice(musicians)["Musician_ID"],
        "Client_ID": events[i-1]["Client_ID"],
        "Event_ID": events[i-1]["Event_ID"],
        "Date_Time": events[i-1]["Date_Time"],
        "Duration": random.randint(1, 8),
        "Price_Charged": round(random.uniform(200.0, 3000.0), 2),
        "Rating": random.choice([1, 2, 3, 4, 5, 5, 5, 4, 4])
    })

reviews = []
good_words = ["amazing", "great", "fantastic", "wonderful", "excellent"]
bad_words = ["terrible", "awful", "bad", "disappointing"]

for i, booking in enumerate(bookings):
    rating = booking["Rating"]
    if rating >= 4:
        text = f"The performance was {random.choice(good_words)}!"
        score, label = 0.8, "POSITIVE"
    elif rating <= 2:
        text = f"It was fairly {random.choice(bad_words)}."
        score, label = -0.5, "NEGATIVE"
    else:
        text = "It was okay, average performance."
        score, label = 0.0, "NEUTRAL"
        
    reviews.append({
        "Review_ID": f"R{i+1:06d}",
        "Booking_ID": booking["Booking_ID"],
        "Review_Text": text,
        "Rating": rating,
        "Created_At": datetime.datetime.now().isoformat(),
        "sentiment_score": score,
        "sentiment_label": label,
        "vader_score": score,
        "bert_score": score,
        "is_anomaly": False,
        "anomaly_score": random.uniform(-0.1, 0.5)
    })

socials = []
platforms = ["Instagram", "Twitter", "Facebook", "TikTok"]
for m in musicians:
    if str(m["Social_Links"]) == "True":
        socials.append({
            "Musician_ID": m["Musician_ID"],
            "Platform": random.choice(platforms),
            "Followers": random.randint(100, 50000),
            "Likes": random.randint(50, 100000),
            "Views": random.randint(100, 200000),
            "Date_Collected": datetime.datetime.now().isoformat()
        })

print("Saving models to DB...")
db = SessionLocal()
try:
    for m in musicians:
        db.add(Musician(
            musician_id=m["Musician_ID"],
            name=m["Musician_Name"],
            musician_type=m["Musician_Type"],
            contact=m["Musician_Contact"],
            location=m["Location"],
            genres=m["Genres"],
            years_experience=m["Years_Experience"],
            base_price=m["Base_Price"],
            has_social_links=m["Social_Links"] == "True"
        ))
    db.commit()
    print("Musicians added!")

    for e in events:
        db.add(Event(
            event_id=e["Event_ID"],
            client_id=e["Client_ID"],
            city=e["City"],
            date_time=e["Date_Time"],
            expected_pax=e["Expected_Pax"],
            event_type=e["Event_Type"],
            budget=e["Budget"]
        ))
    db.commit()
    print("Events added!")

    for b in bookings:
        db.add(Booking(
            booking_id=b["Booking_ID"],
            musician_id=b["Musician_ID"],
            client_id=b["Client_ID"],
            event_id=b["Event_ID"],
            date_time=b["Date_Time"],
            duration=b["Duration"],
            price_charged=b["Price_Charged"],
            rating=b["Rating"]
        ))
    db.commit()
    print("Bookings added!")

    for r in reviews:
        db.add(Review(
            review_id=r["Review_ID"],
            booking_id=r["Booking_ID"],
            review_text=r["Review_Text"],
            rating=r["Rating"],
            created_at=r["Created_At"],
            sentiment_score=r["sentiment_score"],
            sentiment_label=r["sentiment_label"],
            vader_score=r["vader_score"],
            bert_score=r["bert_score"],
            is_anomaly=r["is_anomaly"],
            anomaly_score=r["anomaly_score"]
        ))
    db.commit()
    print("Reviews added!")

    for s in socials:
        db.add(SocialMetric(
            musician_id=s["Musician_ID"],
            platform=s["Platform"],
            followers=s["Followers"],
            likes=s["Likes"],
            views=s["Views"],
            date_collected=s["Date_Collected"]
        ))
    db.commit()
    print("Socials added!")

    print("Success! Generated database with 2500 dummy musicians and relations.")
except Exception as err:
    db.rollback()
    print(f"Error: {err}")
finally:
    db.close()
