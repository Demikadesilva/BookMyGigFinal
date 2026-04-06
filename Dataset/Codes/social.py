import pandas as pd
import random

# Configuration
NUM_MUSICIANS = 200
START_ID = 1
PLATFORMS = ['Instagram', 'TikTok', 'YouTube']
DATE_COLLECTED = '2026-02-24'

data = []

for i in range(NUM_MUSICIANS):
    musician_id = f"M{START_ID + i:03d}"
    
    # Determine a base "popularity tier" for this musician so their metrics scale somewhat logically across platforms
    # 60% small/local (100-10k), 30% mid-tier (10k-100k), 10% established (100k-500k)
    tier = random.choices(['small', 'mid', 'established'], weights=[0.6, 0.3, 0.1])[0]
    
    for platform in PLATFORMS:
        # Generate followers based on tier and platform nuances
        if tier == 'small':
            followers = random.randint(100, 10000)
        elif tier == 'mid':
            followers = random.randint(10000, 100000)
        else:
            followers = random.randint(100000, 500000)
            
        # Add platform-specific noise (e.g., DJs might blow up on TikTok, Classical on YouTube)
        # We'll apply a random multiplier between 0.5 and 1.5 to keep it organic
        followers = int(followers * random.uniform(0.5, 1.5))
        followers = max(100, min(followers, 500000)) # Clamp bounds
        
        # Calculate realistically scaled Engagement
        if platform == 'TikTok':
            # TikTok has high views relative to followers, and high likes relative to views
            views = int(followers * random.uniform(5.0, 50.0))
            likes = int(views * random.uniform(0.1, 0.25))
        elif platform == 'Instagram':
            # IG has moderate reach, decent like ratio
            views = int(followers * random.uniform(2.0, 15.0))
            likes = int(views * random.uniform(0.05, 0.20))
        else: # YouTube
            # YouTube views are usually cumulative, subscribers are harder to get
            views = int(followers * random.uniform(10.0, 100.0))
            likes = int(views * random.uniform(0.02, 0.10))

        data.append({
            'Musician_ID': musician_id,
            'Platform': platform,
            'Followers': followers,
            'Likes': likes,
            'Views': views,
            'Date_Collected': DATE_COLLECTED
        })

df = pd.DataFrame(data)

# Export to CSV
df.to_csv('social_media_metrics.csv', index=False)
print(f"Successfully generated {len(data)} rows for {NUM_MUSICIANS} musicians!")