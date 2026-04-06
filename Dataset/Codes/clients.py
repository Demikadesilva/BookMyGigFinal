import pandas as pd
import random
from faker import Faker

# Initialize Faker with UK locale
fake = Faker('en_GB')

# Configuration
NUM_RECORDS = 300

client_types = ['Individual', 'Corporate', 'Venue', 'Event Planner']
# Realistic distribution: 40% individuals, 25% venues, 20% corporate, 15% event planners
type_weights = [0.40, 0.20, 0.25, 0.15] 

data = []

for i in range(NUM_RECORDS):
    client_id = f"C{i+1:03d}"
    c_type = random.choices(client_types, weights=type_weights)[0]
    
    # Generate realistic names and contact info based on Client_Type
    if c_type == 'Individual':
        first_name = fake.first_name()
        last_name = fake.last_name()
        name = f"{first_name} {last_name}"
        domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])
        contact = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{domain}"
        
    elif c_type == 'Corporate':
        company_name = fake.company()
        name = company_name
        clean_name = company_name.split()[0].replace(',', '').replace("'", "").lower()
        domain = f"{clean_name}.co.uk"
        prefix = random.choice(['events', 'hr', 'social', 'admin'])
        contact = f"{prefix}@{domain}"
        
    elif c_type == 'Venue':
        pub_name = fake.street_name().split()[0]
        suffix = random.choice(['Pub', 'Tavern', 'Inn', 'Bar', 'Club', 'Academy'])
        name = f"The {pub_name} {suffix}"
        clean_name = pub_name.lower()
        domain = f"{clean_name}{suffix.lower()}.co.uk"
        prefix = random.choice(['bookings', 'manager', 'music', 'live', 'gigs'])
        contact = f"{prefix}@{domain}"
        
    else: # Event Planner
        agency_name = fake.last_name()
        suffix = random.choice(['Events', 'Weddings', 'Planners', 'Occasions'])
        name = f"{agency_name} {suffix}"
        clean_name = agency_name.lower()
        domain = f"{clean_name}{suffix.lower()}.uk"
        prefix = random.choice(['hello', 'info', 'team', 'contact'])
        contact = f"{prefix}@{domain}"

    data.append({
        'Client_ID': client_id,
        'Client_Name': name,
        'Client_Type': c_type,
        'Client_Contact': contact
    })

# Create DataFrame
df = pd.DataFrame(data)

# Export to CSV
df.to_csv('clients_dataset.csv', index=False)
print(f"Successfully generated {NUM_RECORDS} rows in clients_dataset_300.csv!")