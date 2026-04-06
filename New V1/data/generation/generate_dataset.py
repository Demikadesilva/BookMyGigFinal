"""
BookMyGig - Comprehensive Dataset Generation Script
=====================================================
Generates production-quality synthetic datasets for:
  - Musicians       (500 records, M001-M500)
  - Clients         (300 records, C001-C300)
  - Events          (800 records, E001-E800)
  - Bookings        (600 records, B001-B600)
  - Reviews         (600 records, R001-R600)  ← varied sentiment incl. 1-2-3 star
  - Social Metrics  (1,500 records, 500 musicians × 3 platforms)

Run:  python generate_dataset.py
Output: ../raw/*.csv
"""

import csv
import math
import os
import random
from datetime import datetime, timedelta

# ── reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)

# ── output directory ─────────────────────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

# ── shared look-up tables ─────────────────────────────────────────────────────
UK_CITIES = [
    "London", "Manchester", "Glasgow", "Bristol", "Birmingham",
    "Edinburgh", "Liverpool", "Leeds", "Brighton", "Cardiff",
    "Newcastle", "Sheffield", "Belfast", "Oxford", "Cambridge",
    "Nottingham", "Leicester", "Reading", "Southampton", "York",
]

MUSICIAN_TYPES = ["Solo", "Band", "DJ", "Duo", "Trio", "Quartet"]

GENRES_POOL = [
    "Indie", "Pop", "Jazz", "Rock", "Classical", "Folk",
    "Electronic", "Soul", "R&B", "Blues", "Acoustic",
    "Hip-Hop", "Country", "Funk", "Reggae", "Gospel",
]

EVENT_TYPES = [
    "Wedding", "Corporate", "Birthday", "Pub Gig", "Festival",
    "Private Party", "Concert", "Charity Gala", "University Ball",
    "Awards Night", "Product Launch", "Bar Mitzvah",
]

CLIENT_TYPES = ["Individual", "Corporate", "Venue", "Event Planner"]

PLATFORMS = ["Instagram", "TikTok", "YouTube"]

# ── name pools ────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "James", "Oliver", "Harry", "Jack", "George", "Noah", "Charlie", "Jacob",
    "Alfie", "Freddie", "Poppy", "Emily", "Olivia", "Sophie", "Lily", "Amelia",
    "Jessica", "Ella", "Grace", "Mia", "Emma", "Hannah", "Isabella", "Chloe",
    "Liam", "Ethan", "Mason", "Aiden", "Lucas", "Dylan", "Ryan", "Nathan",
    "Zara", "Leah", "Naomi", "Priya", "Aisha", "Sofia", "Clara", "Diana",
    "Tom", "Sam", "Alex", "Jordan", "Morgan", "Taylor", "Casey", "Jamie",
    "Leon", "Marcus", "Oscar", "Finn", "Hugo", "Rory", "Sean", "Callum",
    "Megan", "Rachel", "Laura", "Sarah", "Kate", "Amy", "Anna", "Beth",
]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Evans",
    "Wilson", "Thomas", "Roberts", "Johnson", "Lewis", "Walker", "Robinson",
    "White", "Thompson", "Martin", "Harris", "Clark", "Young", "Hall",
    "Allen", "Scott", "Wright", "Mitchell", "Turner", "Hill", "Green",
    "Baker", "Adams", "Nelson", "Carter", "Parker", "Collins", "Stewart",
    "Morris", "Reed", "Cook", "Bailey", "Bell", "Cooper", "Rogers",
    "Richardson", "Cox", "Howard", "Ward", "Phillips", "Campbell", "Shaw",
]

BAND_WORDS = [
    "Midnight", "Velvet", "Neon", "Electric", "Silver", "Golden", "Crystal",
    "Cosmic", "Thunder", "Ember", "Royal", "Scarlet", "Violet", "Arctic",
    "Broken", "Rising", "Falling", "Burning", "Dancing", "Echoing",
]

BAND_SUFFIXES = [
    "Echoes", "Strings", "Lights", "Dreams", "Beats", "Souls", "Waves",
    "Project", "Band", "Collective", "Sound", "Orchestra", "Ensemble",
    "Junction", "Revival", "Riot", "Union", "Circuit", "Society",
]

COMPANY_WORDS = [
    "Smith", "Taylor", "Johnson", "Williams", "Brown", "Davies", "Evans",
    "Harrison", "Burton", "Mitchell", "Clarke", "Fletcher", "Graham",
    "Hartley", "Lawson", "Maxwell", "Preston", "Stanley", "Thornton",
]

VENUE_NAMES = [
    "The Grand Hall", "The Crown", "The Empire", "The Academy",
    "The Forum", "The Palladium", "The Arches", "The Warehouse",
    "The Loft", "The Lounge", "The Terrace", "The Pavilion",
    "The Castle", "The Manor", "The Barn", "The Rooftop",
    "The Social", "The Junction", "The Hub", "The Atrium",
]

DOMAIN_SUFFIXES = [".co.uk", ".com", ".org.uk", ".net"]

# ── helpers ───────────────────────────────────────────────────────────────────

def rnd_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rnd_email(prefix: str) -> str:
    clean = prefix.lower().replace(" ", ".").replace("&", "").replace("'", "")
    domain = random.choice(["gmail", "yahoo", "hotmail", "outlook", "musicnet.uk", "freemail.com"])
    suffix = random.choice([".co.uk", ".com"])
    return f"{clean}@{domain}{suffix}"


def rnd_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def write_csv(filename: str, rows: list[dict], fieldnames: list[str]) -> None:
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  ✓  {filename:35s} → {len(rows):>5,} rows")


# ── 1. MUSICIANS (500) ────────────────────────────────────────────────────────

def generate_musicians(n: int = 500) -> list[dict]:
    rows = []
    used_names = set()

    for i in range(1, n + 1):
        mid = f"M{i:03d}"
        m_type = random.choice(MUSICIAN_TYPES)

        # unique name
        for _ in range(50):
            if m_type == "Solo":
                name = rnd_name()
            elif m_type == "DJ":
                name = f"DJ {random.choice(FIRST_NAMES)}"
            elif m_type == "Duo":
                n1, n2 = random.choice(FIRST_NAMES), random.choice(FIRST_NAMES)
                name = f"{n1} & {n2}"
            else:
                word = random.choice(BAND_WORDS)
                suffix = random.choice(BAND_SUFFIXES)
                name = f"The {word} {suffix}"
            if name not in used_names:
                used_names.add(name)
                break

        # genres
        if m_type == "DJ":
            genres = "DJ" if random.random() > 0.5 else "DJ, Electronic"
        elif m_type == "Quartet" and random.random() > 0.35:
            genres = "Classical"
        else:
            k = random.choices([1, 2, 3], weights=[0.35, 0.45, 0.20])[0]
            genres = ", ".join(random.sample(GENRES_POOL, k))

        # cold-start: ~12% have 0 years experience
        is_cold = random.random() < 0.12
        experience = 0 if is_cold else random.randint(1, 25)

        if is_cold:
            base_price = random.randint(80, 150)
            has_links = False
        else:
            size_mult = {
                "Solo": 1.0, "DJ": 1.1, "Duo": 1.8,
                "Trio": 2.5, "Band": 3.0, "Quartet": 4.0,
            }.get(m_type, 1.0)
            base_price = int(80 + experience * 28 * size_mult + random.randint(-60, 200))
            base_price = max(80, min(3500, round(base_price / 10) * 10))
            has_links = random.random() > 0.08

        contact = f"booking@{name.lower().replace(' ', '').replace('&', '').replace('.', '')[:20]}.co.uk"
        location = random.choice(UK_CITIES)

        rows.append({
            "Musician_ID": mid,
            "Musician_Name": name,
            "Musician_Type": m_type,
            "Musician_Contact": contact,
            "Location": location,
            "Genres": genres,
            "Years_Experience": experience,
            "Base_Price": base_price,
            "Social_Links": has_links,
        })
    return rows


# ── 2. CLIENTS (300) ──────────────────────────────────────────────────────────

def generate_clients(n: int = 300) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        cid = f"C{i:03d}"
        c_type = random.choice(CLIENT_TYPES)

        if c_type == "Individual":
            name = rnd_name()
            contact = rnd_email(name)
        elif c_type == "Corporate":
            w1, w2 = random.choice(COMPANY_WORDS), random.choice(COMPANY_WORDS)
            name = f"{w1} & {w2} Ltd" if random.random() > 0.4 else f"{w1} Group"
            contact = f"events@{w1.lower()}{w2.lower()}.co.uk"
        elif c_type == "Venue":
            name = random.choice(VENUE_NAMES)
            clean = name.lower().replace("the ", "").replace(" ", "")
            contact = f"bookings@{clean}.co.uk"
        else:  # Event Planner
            planner = rnd_name()
            name = f"{planner} Events"
            contact = rnd_email(name)

        rows.append({
            "Client_ID": cid,
            "Client_Name": name,
            "Client_Type": c_type,
            "Client_Contact": contact,
        })
    return rows


# ── 3. EVENTS (800) ───────────────────────────────────────────────────────────

def generate_events(clients: list[dict], n: int = 800) -> list[dict]:
    rows = []
    client_ids = [c["Client_ID"] for c in clients]
    start_dt = datetime(2024, 6, 1, 12, 0)
    end_dt   = datetime(2026, 6, 1, 23, 0)

    for i in range(1, n + 1):
        eid = f"E{i:03d}"
        cid = random.choice(client_ids)
        city = random.choice(UK_CITIES)
        etype = random.choice(EVENT_TYPES)
        pax = random.randint(20, 600)

        # budget scales with pax and event type
        budget_per_head = {
            "Wedding": random.uniform(15, 40),
            "Corporate": random.uniform(20, 60),
            "Festival": random.uniform(5, 20),
            "University Ball": random.uniform(10, 25),
            "Awards Night": random.uniform(25, 70),
            "Charity Gala": random.uniform(20, 50),
            "Product Launch": random.uniform(30, 80),
            "Concert": random.uniform(10, 30),
            "Birthday": random.uniform(5, 15),
            "Pub Gig": random.uniform(2, 8),
            "Private Party": random.uniform(8, 20),
            "Bar Mitzvah": random.uniform(20, 45),
        }.get(etype, random.uniform(5, 25))

        budget = int(pax * budget_per_head)
        budget = max(200, round(budget / 50) * 50)

        # time slots: evenings / weekends more common
        hour = random.choices(
            [13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
            weights=[3, 3, 4, 5, 8, 10, 12, 14, 12, 9],
        )[0]
        minute = random.choice([0, 30])
        ev_date = rnd_date(start_dt, end_dt).replace(hour=hour, minute=minute)

        rows.append({
            "Event_ID": eid,
            "Client_ID": cid,
            "City": city,
            "Date_Time": fmt_dt(ev_date),
            "Expected_Pax": pax,
            "Event_Type": etype,
            "Budget": budget,
        })
    return rows


# ── 4. BOOKINGS (600) ─────────────────────────────────────────────────────────

def generate_bookings(
    musicians: list[dict],
    clients: list[dict],
    events: list[dict],
    n: int = 600,
) -> list[dict]:
    rows = []
    m_lookup = {m["Musician_ID"]: m for m in musicians}
    event_ids = [e["Event_ID"] for e in events]
    client_ids = [c["Client_ID"] for c in clients]

    # each event used at most once for a booking slot
    used_events = set()

    for i in range(1, n + 1):
        bid = f"B{i:03d}"

        # pick an unused event (or reuse if exhausted)
        for _ in range(50):
            eid = random.choice(event_ids)
            if eid not in used_events:
                used_events.add(eid)
                break

        # pick a musician (prefer experienced ones – weighted)
        m = random.choices(
            musicians,
            weights=[max(1, m["Years_Experience"] + 2) for m in musicians],
        )[0]
        mid = m["Musician_ID"]
        cid = random.choice(client_ids)

        duration = random.choices([1, 2, 3, 4, 5, 6], weights=[5, 20, 35, 25, 10, 5])[0]

        # price charged = base_price * duration * small multiplier (demand / event type)
        base = m_lookup[mid]["Base_Price"]
        multiplier = random.uniform(0.9, 2.2)
        price_charged = int(base * duration * multiplier)
        price_charged = max(100, round(price_charged / 10) * 10)

        # rating slightly correlated with experience
        exp = m_lookup[mid]["Years_Experience"]
        if exp == 0:
            rating = random.choices([1, 2, 3, 4, 5], weights=[10, 15, 30, 30, 15])[0]
        elif exp < 5:
            rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25])[0]
        else:
            rating = random.choices([1, 2, 3, 4, 5], weights=[2, 5, 10, 30, 53])[0]

        # booking date = event date (use a representative date)
        ev_date_str = next(
            (e["Date_Time"] for e in events if e["Event_ID"] == eid),
            "2025-06-01 19:00",
        )

        rows.append({
            "Booking_ID": bid,
            "Musician_ID": mid,
            "Client_ID": cid,
            "Event_ID": eid,
            "Date_Time": ev_date_str,
            "Duration": duration,
            "Price_Charged": price_charged,
            "Rating": rating,
        })
    return rows


# ── 5. REVIEWS (600) ─────────────────────────────────────────────────────────

# Rich, varied review templates keyed by star rating
REVIEW_TEMPLATES = {
    5: [
        "Absolutely sensational performance — the crowd was completely blown away from the first song to the last. {positive_detail} Cannot recommend highly enough!",
        "Outstanding! {positive_detail} The energy was infectious and everyone had an incredible time. Will definitely book again.",
        "Best booking decision we ever made. {positive_detail} Professionalism from start to finish. Five stars without hesitation.",
        "Exceptional talent. {positive_detail} They had the whole room on their feet within minutes. Truly memorable.",
        "Wow. Just wow. {positive_detail} If I could give six stars I would. Guests are still talking about it.",
        "Perfect in every way. {positive_detail} Arrived early, set up quickly, and delivered a flawless set. 10/10.",
        "{positive_detail} We had very high expectations and they exceeded every single one. Absolutely brilliant.",
        "Fantastic night! {positive_detail} The musician was warm, engaging, and incredibly talented. Couldn't be happier.",
        "What an incredible evening. {positive_detail} The setlist was perfectly curated for our audience. Highly recommended!",
        "Superb performance from start to finish. {positive_detail} The guests couldn't stop complimenting the entertainment.",
    ],
    4: [
        "Really great performance overall. {positive_detail} Minor technical hiccup at the start but they handled it gracefully. Would book again.",
        "Very enjoyable night. {positive_detail} The sound balance could have been slightly better, but the talent speaks for itself.",
        "{positive_detail} A solid, professional performance. Guests were happy and dancing all night. Recommended.",
        "Excellent entertainment! {positive_detail} Ran about 10 minutes over time but nobody was complaining. Great value.",
        "Good performance and good attitude. {positive_detail} Would appreciate a slightly more varied setlist next time.",
        "Very impressed overall. {positive_detail} Communication beforehand was quick and clear. Performance delivered as promised.",
        "High-quality entertainment. {positive_detail} Everything ran smoothly and the crowd response was fantastic.",
        "{positive_detail} Delivered a strong set with real energy. A small issue with the monitor mix, but nothing that affected the show significantly.",
        "Enjoyed the performance very much. {positive_detail} Would rate 5 stars if setup time had been shorter. Still highly recommended.",
        "Great experience. {positive_detail} They were accommodating with our song requests and the vibe was spot on.",
    ],
    3: [
        "Decent performance but not quite what we expected. {mixed_detail} Guests seemed to enjoy it though.",
        "Average overall. {mixed_detail} The talent is clearly there but the energy felt inconsistent throughout the evening.",
        "{mixed_detail} Some songs were great, others fell flat. I think a different setlist would have worked better for our audience.",
        "Hit and miss. {mixed_detail} Good at times, but struggled to keep momentum after the break.",
        "Okay performance for the price point. {mixed_detail} Wouldn't rush to rebook but wouldn't discourage others either.",
        "{mixed_detail} Communication was slow before the event and the performance itself was middle-of-the-road.",
        "Mixed feelings. Started really strongly then seemed to lose the room halfway through. {mixed_detail}",
        "Not bad, not great. {mixed_detail} If they tightened up the transitions between songs it would make a big difference.",
        "Some guests enjoyed it, others were less enthused. {mixed_detail} Largely delivered what was advertised, I suppose.",
        "Fairly good but room for improvement. {mixed_detail} Worth trying if the budget is tight, but there are better options.",
    ],
    2: [
        "Disappointing experience unfortunately. {negative_detail} We expected much better based on the profile.",
        "Not up to the standard we needed for our event. {negative_detail} Guests noticed and commented on it.",
        "{negative_detail} Arrived late and the performance was below par. Wouldn't recommend for a formal event.",
        "Let down overall. {negative_detail} The booking process was fine but the actual performance missed the mark.",
        "Below expectations I'm afraid. {negative_detail} Sound issues throughout that were never properly resolved.",
        "Struggled to connect with the audience. {negative_detail} The energy just wasn't there on the night.",
        "{negative_detail} Several guests left before the set finished. Not the outcome we were hoping for.",
        "Communication was poor and the performance reflected that. {negative_detail} Would not rebook.",
        "Unfortunately a disappointing night. {negative_detail} I hope this was an off night for them, but we can't take that risk again.",
        "Regret this booking. {negative_detail} Have had far better experiences with other performers at similar price points.",
    ],
    1: [
        "Terrible experience. {negative_detail} Asked for a refund and will be leaving reviews everywhere.",
        "Absolutely appalling. {negative_detail} Do not book under any circumstances.",
        "{negative_detail} Ruined what should have been a special occasion. Completely unprofessional.",
        "Worst booking I have ever made. {negative_detail} The 'performance' was embarrassing for everyone.",
        "Complete no-show for 40 minutes, then a shambolic performance. {negative_detail} Avoid.",
        "{negative_detail} We ended up playing a Spotify playlist for our guests. A total waste of money.",
        "Disgusting level of professionalism. {negative_detail} Will be pursuing this through the platform dispute process.",
        "Genuinely shocking. {negative_detail} I have been attending events for 20 years and this was the worst entertainment I have ever witnessed.",
        "One star is being generous. {negative_detail} Everything that could go wrong did go wrong.",
        "Stay away. {negative_detail} Not a single positive thing to say about the experience.",
    ],
}

POSITIVE_DETAILS = [
    "Arrived a full hour early and set up without any fuss.",
    "The sound quality was absolutely crystal clear all night.",
    "Crowd engagement was phenomenal — they read the room perfectly.",
    "Incredibly professional attitude from enquiry through to pack-down.",
    "Played three of our requested songs and arranged them beautifully.",
    "The lighting rig they brought added a whole new dimension to the venue.",
    "They interacted warmly with guests of all ages and backgrounds.",
    "Perfectly punctual, impeccably presented, and artistically superb.",
    "We were blown away by how well they adapted to different audience moods.",
    "Every single technical element was handled with care and expertise.",
    "The vocalist has an exceptional range and genuine stage presence.",
    "They stayed thirty minutes over schedule — for free — because the crowd demanded it.",
    "Seamlessly transitioned between genres to keep all demographics happy.",
    "Their original material was a real talking point among our guests.",
    "The acoustic set during dinner was the perfect touch of elegance.",
]

MIXED_DETAILS = [
    "Sound check took longer than expected but the performance itself was reasonable.",
    "Some technical issues in the first half, though they rallied well after the break.",
    "The setlist skewed older than we requested, which divided the crowd a little.",
    "Good talent but the pacing felt uneven — big peaks and then lulls.",
    "They were a few minutes late arriving but made up for it with a decent set.",
    "The volume levels were a bit inconsistent, though nothing that ruined the night.",
    "Communication before the event took a while, but they delivered on the day.",
    "Some songs resonated really well, but others seemed rehearsed rather than felt.",
    "The energy picked up significantly in the second set — wish the first had matched it.",
    "A solid performance, though it felt like they were playing it safe creatively.",
]

NEGATIVE_DETAILS = [
    "Arrived 45 minutes late with no apology or explanation.",
    "Sound quality was poor throughout — muffled and unbalanced.",
    "Barely interacted with the audience and seemed disengaged.",
    "Ignored our pre-agreed setlist and played entirely different material.",
    "Multiple equipment failures that were never properly resolved.",
    "Had to be asked repeatedly to adjust the volume to an acceptable level.",
    "The performance lasted only 40 minutes despite booking a two-hour slot.",
    "Attitude was rude and dismissive when guests made requests.",
    "Did not honour the agreed performance schedule or break structure.",
    "Quality was drastically below what the demo videos suggested.",
]


def build_review_text(rating: int) -> str:
    if rating == 5:
        template = random.choice(REVIEW_TEMPLATES[5])
        detail = random.choice(POSITIVE_DETAILS)
        return template.replace("{positive_detail}", detail)
    elif rating == 4:
        template = random.choice(REVIEW_TEMPLATES[4])
        detail = random.choice(POSITIVE_DETAILS)
        return template.replace("{positive_detail}", detail)
    elif rating == 3:
        template = random.choice(REVIEW_TEMPLATES[3])
        detail = random.choice(MIXED_DETAILS)
        return template.replace("{mixed_detail}", detail)
    elif rating == 2:
        template = random.choice(REVIEW_TEMPLATES[2])
        detail = random.choice(NEGATIVE_DETAILS)
        return template.replace("{negative_detail}", detail)
    else:
        template = random.choice(REVIEW_TEMPLATES[1])
        detail = random.choice(NEGATIVE_DETAILS)
        return template.replace("{negative_detail}", detail)


def generate_reviews(bookings: list[dict]) -> list[dict]:
    """One review per booking (600 reviews)."""
    rows = []
    for i, b in enumerate(bookings, start=1):
        rid = f"R{i:03d}"
        rating = b["Rating"]

        # ~8% chance of fake/anomalous review: text sentiment contradicts rating
        is_fake = random.random() < 0.08
        if is_fake:
            fake_text_rating = 5 if rating <= 2 else 1  # reverse sentiment
            review_text = build_review_text(fake_text_rating)
        else:
            review_text = build_review_text(rating)

        # review posted 2-14 days after the booking date
        try:
            booking_dt = datetime.strptime(b["Date_Time"], "%Y-%m-%d %H:%M")
        except ValueError:
            booking_dt = datetime(2025, 6, 1)
        created = booking_dt + timedelta(days=random.randint(2, 14))

        rows.append({
            "Review_ID": rid,
            "Booking_ID": b["Booking_ID"],
            "Review_Text": review_text,
            "Rating": rating,
            "Created_At": created.strftime("%Y-%m-%d"),
        })
    return rows


# ── 6. SOCIAL MEDIA METRICS (1,500 rows) ─────────────────────────────────────

def generate_social_metrics(musicians: list[dict]) -> list[dict]:
    rows = []
    collection_dates = [
        datetime(2025, 6, 1),
        datetime(2025, 9, 1),
        datetime(2025, 12, 1),
        datetime(2026, 3, 1),
    ]

    for m in musicians:
        exp = m["Years_Experience"]
        base_followers = int(200 + exp * 600 + random.randint(-100, 2000))
        has_links = m["Social_Links"]

        if not has_links:
            # cold-start / no social presence → minimal metrics
            base_followers = random.randint(0, 500)

        collect_date = random.choice(collection_dates)

        for platform in PLATFORMS:
            pf_mult = {"Instagram": 1.0, "TikTok": 1.8, "YouTube": 0.7}.get(platform, 1.0)

            followers = max(0, int(base_followers * pf_mult * random.uniform(0.6, 1.5)))
            likes     = max(0, int(followers * random.uniform(0.3, 2.5)))
            views     = max(0, int(followers * random.uniform(5, 60)))

            # viral spike for some TikTok accounts
            if platform == "TikTok" and random.random() < 0.12:
                views = int(views * random.uniform(10, 50))

            rows.append({
                "Musician_ID": m["Musician_ID"],
                "Platform": platform,
                "Followers": followers,
                "Likes": likes,
                "Views": views,
                "Date_Collected": collect_date.strftime("%Y-%m-%d"),
            })
    return rows


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   BookMyGig — Comprehensive Dataset Generator        ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    print("Generating tables…")

    musicians = generate_musicians(500)
    clients   = generate_clients(300)
    events    = generate_events(clients, 800)
    bookings  = generate_bookings(musicians, clients, events, 600)
    reviews   = generate_reviews(bookings)
    social    = generate_social_metrics(musicians)

    print("\nWriting CSV files…")
    write_csv("musicians.csv",           musicians, ["Musician_ID","Musician_Name","Musician_Type","Musician_Contact","Location","Genres","Years_Experience","Base_Price","Social_Links"])
    write_csv("clients.csv",             clients,   ["Client_ID","Client_Name","Client_Type","Client_Contact"])
    write_csv("events.csv",              events,    ["Event_ID","Client_ID","City","Date_Time","Expected_Pax","Event_Type","Budget"])
    write_csv("bookings.csv",            bookings,  ["Booking_ID","Musician_ID","Client_ID","Event_ID","Date_Time","Duration","Price_Charged","Rating"])
    write_csv("reviews.csv",             reviews,   ["Review_ID","Booking_ID","Review_Text","Rating","Created_At"])
    write_csv("social_media_metrics.csv",social,    ["Musician_ID","Platform","Followers","Likes","Views","Date_Collected"])

    total = sum([len(musicians), len(clients), len(events), len(bookings), len(reviews), len(social)])
    print(f"\n✅  All datasets generated — {total:,} total records across 6 tables.")
    print(f"    Output directory: {os.path.abspath(OUT_DIR)}\n")

    # print rating distribution for sanity check
    from collections import Counter
    rating_dist = Counter(b["Rating"] for b in bookings)
    print("Rating distribution in bookings:")
    for r in sorted(rating_dist):
        bar = "█" * int(rating_dist[r] / 3)
        print(f"  {r}★  {bar}  ({rating_dist[r]})")
    print()


if __name__ == "__main__":
    main()
