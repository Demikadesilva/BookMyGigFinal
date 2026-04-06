import pandas as pd
import random
from datetime import datetime, timedelta

# Configuration
NUM_RECORDS = 300 # Change to 200 if you want to strictly cap at E200
START_ID = 1

cities = ['London', 'Manchester', 'Glasgow', 'Bristol', 'Birmingham', 'Edinburgh', 'Liverpool', 'Leeds', 'Brighton', 'Cardiff', 'Newcastle']

# Simulating the Venues from previous dataset (they book frequent pub gigs)
venue_clients = ['C002', 'C006', 'C010', 'C014', 'C018', 'C022', 'C026', 'C029', 'C033', 'C037', 'C041', 'C045', 'C049', 'C053']
event_planners_and_corporate = [f"C{str(i).zfill(3)}" for i in range(1, 101) if f"C{str(i).zfill(3)}" not in venue_clients]

# Seasonality Weights by Month (1-12)
# Order: [Wedding, Birthday, Pub Gig, Corporate, Festival]
seasonality_weights = {
    1:  [0.05, 0.20, 0.50, 0.25, 0.00], # Jan: Low weddings, high pubs/corporate kickoffs
    2:  [0.05, 0.25, 0.50, 0.20, 0.00], # Feb
    3:  [0.10, 0.20, 0.45, 0.25, 0.00], # Mar
    4:  [0.20, 0.15, 0.45, 0.20, 0.00], # Apr: Spring weddings start
    5:  [0.35, 0.10, 0.35, 0.15, 0.05], # May: Wedding season kicks in
    6:  [0.40, 0.10, 0.25, 0.10, 0.15], # Jun: Summer weddings + Festivals
    7:  [0.45, 0.10, 0.20, 0.05, 0.20], # Jul: Peak Summer
    8:  [0.45, 0.10, 0.20, 0.05, 0.20], # Aug
    9:  [0.25, 0.15, 0.35, 0.20, 0.05], # Sep: Autumn corporate starts
    10: [0.15, 0.15, 0.40, 0.30, 0.00], # Oct
    11: [0.05, 0.15, 0.35, 0.45, 0.00], # Nov: Corporate holiday prep
    12: [0.05, 0.10, 0.35, 0.50, 0.00], # Dec: Peak Corporate parties
}

data = []

# Generate a random datetime within a specific month
def get_random_date(year, month):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    random_days = random.randint(0, (end_date - start_date).days)
    
    # Push Pub Gigs and Weddings to weekends mostly
    date = start_date + timedelta(days=random_days)
    hour = random.choice([12, 13, 14, 15, 18, 19, 20, 21, 22])
    minute = random.choice([0, 30])
    
    return date.replace(hour=hour, minute=minute)

for i in range(NUM_RECORDS):
    event_id = f"E{START_ID + i:03d}"
    
    # Pick a random month to simulate full year distribution evenly
    month = random.randint(1, 12)
    event_date = get_random_date(2025, month)
    
    # Pick Event Type based on Seasonality Weights
    event_type = random.choices(
        ['Wedding', 'Birthday', 'Pub Gig', 'Corporate', 'Festival'], 
        weights=seasonality_weights[month]
    )[0]
    
    # Assign Client ID, Pax, and Budget based on Event Type
    if event_type == 'Pub Gig':
        client_id = random.choice(venue_clients) # Venues book pub gigs
        pax = random.randint(50, 300)
        budget = pax * random.uniform(2.5, 5.0) # Lower per head budget
    elif event_type == 'Festival':
        client_id = random.choice(event_planners_and_corporate)
        pax = random.randint(500, 1000)
        budget = pax * random.uniform(15.0, 25.0)
    elif event_type == 'Wedding':
        client_id = random.choice(event_planners_and_corporate)
        pax = random.randint(80, 250)
        budget = pax * random.uniform(15.0, 35.0)
    elif event_type == 'Corporate':
        client_id = random.choice(event_planners_and_corporate)
        pax = random.randint(100, 600)
        budget = pax * random.uniform(12.0, 30.0)
    else: # Birthday
        client_id = random.choice(event_planners_and_corporate)
        pax = random.randint(20, 80)
        budget = pax * random.uniform(8.0, 15.0)

    # Format Date and Round Budget
    date_str = event_date.strftime('%Y-%m-%d %H:%M')
    budget = round(budget / 50) * 50 # Round to nearest 50 for realistic figures

    data.append({
        'Event_ID': event_id,
        'Client_ID': client_id,
        'City': random.choice(cities),
        'Date_Time': date_str,
        'Expected_Pax': pax,
        'Event_Type': event_type,
        'Budget': budget
    })

# Create DataFrame and Export
df = pd.DataFrame(data)
df = df.sort_values(by='Date_Time') # Chronological order makes sense for events
df.to_csv('events_dataset.csv', index=False)
print(f"Successfully generated {NUM_RECORDS} seasonal events!")