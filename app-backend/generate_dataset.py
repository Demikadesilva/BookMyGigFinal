import pandas as pd
import numpy as np
import random
from pathlib import Path
import uuid
import datetime

DATASET_DIR = Path("../Dataset")
DATASET_DIR.mkdir(exist_ok=True)

# Generate 2500 Musicians
musicians = []
musician_types = ["Band", "Solo Musician", "DJ", "Orchestra", "Singer"]
genres = ["Rock", "Pop", "Jazz", "Classical", "Hip Hop", "Electronic", "Country", "R&B"]
cities = ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool", "Edinburgh", "Bristol"]

for i in range(1, 2501):
    m_id = f"M{i:04d}"
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

df_musicians = pd.DataFrame(musicians)
df_musicians.to_csv(DATASET_DIR / "musicians.csv", index=False)
print(f"Generated {len(musicians)} musicians.")

# Generate Events
events = []
event_types = ["Wedding", "Corporate Event", "Private Party", "Festival", "Club Night", "Birthday"]
client_ids = [f"C{str(uuid.uuid4())[:8]}" for _ in range(1000)] # 1000 clients

for i in range(1, 5001):
    events.append({
        "Event_ID": f"E{i:05d}",
        "Client_ID": random.choice(client_ids),
        "City": random.choice(cities),
        "Date_Time": (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 365))).isoformat(),
        "Expected_Pax": random.randint(20, 1000),
        "Event_Type": random.choice(event_types),
        "Budget": round(random.uniform(500.0, 5000.0), 2)
    })

df_events = pd.DataFrame(events)
df_events.to_csv(DATASET_DIR / "events.csv", index=False)
print(f"Generated {len(events)} events.")

# Generate Bookings
bookings = []
for i in range(1, 5001):
    b_id = f"B{i:05d}"
    bookings.append({
        "Booking_ID": b_id,
        "Musician_ID": random.choice(musicians)["Musician_ID"],
        "Client_ID": random.choice(client_ids),
        "Event_ID": events[i-1]["Event_ID"], # One booking per event for simplicity
        "Date_Time": events[i-1]["Date_Time"],
        "Duration": random.randint(1, 8),
        "Price_Charged": round(random.uniform(200.0, 3000.0), 2),
        "Rating": random.choice([1, 2, 3, 4, 5, 5, 5, 4, 4]) # Weighted towards higher ratings
    })

df_bookings = pd.DataFrame(bookings)
df_bookings.to_csv(DATASET_DIR / "bookings.csv", index=False)
print(f"Generated {len(bookings)} bookings.")

# Generate Reviews
reviews = []
good_words = ["amazing", "great", "fantastic", "wonderful", "excellent", "loved it", "highly recommended"]
bad_words = ["terrible", "awful", "bad", "disappointing", "too loud", "late"]

for i, booking in enumerate(bookings):
    rating = booking["Rating"]
    if rating >= 4:
        text = f"The performance was {random.choice(good_words)}. We had a {random.choice(good_words)} time!"
    elif rating <= 2:
        text = f"It was fairly {random.choice(bad_words)}. Slightly {random.choice(bad_words)} experience."
    else:
        text = "It was okay, average performance."
        
    reviews.append({
        "Review_ID": f"R{i+1:05d}",
        "Booking_ID": booking["Booking_ID"],
        "Review_Text": text,
        "Rating": rating,
        "Created_At": datetime.datetime.now().isoformat()
    })

df_reviews = pd.DataFrame(reviews)
df_reviews.to_csv(DATASET_DIR / "reviews.csv", index=False)
print(f"Generated {len(reviews)} reviews.")

# Generate Social Metrics
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

df_socials = pd.DataFrame(socials)
df_socials.to_csv(DATASET_DIR / "social_media_metrics.csv", index=False)
print(f"Generated {len(socials)} social metrics.")

print("Finished generating all sample data CSVs!")
