import pandas as pd
import random
from faker import Faker

fake = Faker('en_GB')

# Configuration
NUM_RECORDS = 200 # Set this to 200 to get M101 to M300
START_ID = 101

locations = ['London', 'Manchester', 'Glasgow', 'Bristol', 'Birmingham', 'Edinburgh', 'Liverpool', 'Leeds', 'Brighton', 'Cardiff', 'Newcastle', 'Sheffield', 'Belfast']
types = ['Solo', 'Band', 'DJ', 'Duo', 'Trio', 'Quartet']
genres_pool = ['Indie', 'Pop', 'Jazz', 'Rock', 'Classical', 'DJ', 'Folk', 'Electronic', 'Soul', 'R&B', 'Blues', 'Acoustic', 'Hip-Hop', 'Country']

data = []

for i in range(NUM_RECORDS):
    musician_id = f"M{START_ID + i:03d}"
    
    m_type = random.choice(types)
    
    # Generate realistic names based on type
    if m_type == 'Solo':
        name = fake.name()
    elif m_type == 'DJ':
        name = f"DJ {fake.first_name()}"
    elif m_type == 'Duo':
        name = f"{fake.first_name()} & {fake.first_name()}"
    else:
        name = f"The {fake.word().capitalize()} {random.choice(['Boys', 'Strings', 'Cats', 'Echoes', 'Project', 'Band'])}"

    contact = f"booking@{name.replace(' ', '').replace('&', '').lower()}.co.uk"
    location = random.choice(locations)
    
    # Assign genres
    if m_type == 'DJ':
        genres = "DJ" if random.random() > 0.5 else "DJ, Electronic"
    elif m_type == 'Quartet' and random.random() > 0.4:
        genres = "Classical"
    else:
        num_genres = random.choices([1, 2], weights=[0.4, 0.6])[0]
        genres = ", ".join(random.sample(genres_pool, num_genres))

    # Calculate Experience and Price realistically
    # Include cold starts (0 years)
    experience = random.choices([0, random.randint(1, 20)], weights=[0.15, 0.85])[0]
    
    if experience == 0:
        base_price = random.randint(100, 150)
        social_links = False
    else:
        # Base price roughly correlates with experience and group size
        size_multiplier = 1 if m_type in ['Solo', 'DJ'] else 2 if m_type == 'Duo' else 3.5
        base_price = int(100 + (experience * 30 * size_multiplier) + random.randint(-50, 150))
        # Clamp between 100 and 2000
        base_price = max(100, min(2000, base_price))
        # Round to nearest 10
        base_price = round(base_price / 10) * 10
        social_links = True if random.random() > 0.1 else False # 90% have links if experienced

    data.append({
        'Musician_ID': musician_id,
        'Musician_Name': name,
        'Musician_Type': m_type,
        'Musician_Contact': contact,
        'Location': location,
        'Genres': genres,
        'Years_Experience': experience,
        'Base_Price': base_price,
        'Social_Links': social_links
    })

df = pd.DataFrame(data)

# Export to CSV (quoting genres properly)
df.to_csv('musicians_M101_to_M300.csv', index=False, quoting=1) # quoting=1 wraps strings with commas in quotes
print(f"Successfully generated {NUM_RECORDS} rows!")