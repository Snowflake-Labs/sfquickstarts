"""
Synthetic Data Generator for CC_DEMO - Schema-aligned version
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import snowflake.connector

np.random.seed(42)

connection_name = os.getenv("SNOWFLAKE_CONNECTION_NAME")
if not connection_name:
    raise ValueError("Set SNOWFLAKE_CONNECTION_NAME environment variable")

conn = snowflake.connector.connect(connection_name=connection_name)
cursor = conn.cursor()
cursor.execute("USE DATABASE CC_DEMO")
cursor.execute("USE WAREHOUSE CC_ML_WH")

NUM_CREATORS = 10_000
NUM_BRANDS = 1_000
NUM_EVENTS = 500_000
NUM_INTERACTIONS = 100_000
CATEGORIES = ['fashion', 'beauty', 'home', 'fitness', 'lifestyle', 'food', 'travel', 'tech']
PLATFORMS = ['instagram', 'tiktok', 'app', 'youtube']
EVENT_TYPES = ['click', 'view', 'purchase', 'share', 'save']
COUNTRIES = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'BR']

ARCHETYPES = {
    'POWER_PERFORMER': {'pct': 0.05, 'eng': (0.10, 0.15), 'followers': (1_000_000, 5_000_000), 'base_conv': 0.75},
    'RISING_STAR':     {'pct': 0.15, 'eng': (0.07, 0.11), 'followers': (100_000, 1_000_000),  'base_conv': 0.55},
    'STEADY_EARNER':   {'pct': 0.50, 'eng': (0.03, 0.07), 'followers': (50_000, 500_000),    'base_conv': 0.35},
    'LONG_TAIL':       {'pct': 0.30, 'eng': (0.01, 0.03), 'followers': (1_000, 100_000),     'base_conv': 0.15},
}

print("=" * 60)
print("CC_DEMO Synthetic Data Generation")
print("=" * 60)

# 1. CREATORS (schema: CREATOR_ID, CREATOR_NAME, CATEGORY, FOLLOWER_COUNT, COUNTRY, AVG_ENGAGEMENT, JOINED_DATE)
print("\n[1/4] Generating CREATORS...")
archetypes = np.random.choice(list(ARCHETYPES.keys()), size=NUM_CREATORS, p=[ARCHETYPES[a]['pct'] for a in ARCHETYPES])

creators = []
base_date = datetime.now() - timedelta(days=365)
for i, arch in enumerate(archetypes):
    cfg = ARCHETYPES[arch]
    creators.append({
        'CREATOR_ID': f'CR_{i:05d}',
        'CREATOR_NAME': f'Creator_{i}',
        'CATEGORY': str(np.random.choice(CATEGORIES)),
        'FOLLOWER_COUNT': int(np.random.uniform(*cfg['followers'])),
        'COUNTRY': str(np.random.choice(COUNTRIES)),
        'AVG_ENGAGEMENT': float(np.random.uniform(*cfg['eng'])),
        'JOINED_DATE': (base_date + timedelta(days=np.random.randint(365))).strftime('%Y-%m-%d'),
        'ARCHETYPE': arch,
    })

creators_df = pd.DataFrame(creators)
print(f"  Archetype distribution:\n{creators_df['ARCHETYPE'].value_counts().to_string()}")

cursor.execute("TRUNCATE TABLE IF EXISTS CC_DEMO.RAW.CREATORS")
vals = [(str(r['CREATOR_ID']), str(r['CREATOR_NAME']), str(r['CATEGORY']), 
         int(r['FOLLOWER_COUNT']), str(r['COUNTRY']), float(r['AVG_ENGAGEMENT']), str(r['JOINED_DATE']))
        for _, r in creators_df.iterrows()]
cursor.executemany("INSERT INTO CC_DEMO.RAW.CREATORS VALUES (%s,%s,%s,%s,%s,%s,%s)", vals)
conn.commit()
print(f"  [PASS] CREATORS: {NUM_CREATORS} rows")

# 2. BRANDS (schema: BRAND_ID, BRAND_NAME, CATEGORY, BUDGET_TIER)
print("\n[2/4] Generating BRANDS...")
budget_tiers = np.random.choice(['enterprise', 'high', 'medium', 'low'], size=NUM_BRANDS, p=[0.10, 0.25, 0.40, 0.25])
brands = [{'BRAND_ID': f'BRAND_{i:04d}', 'BRAND_NAME': f'Brand_{i}',
           'CATEGORY': str(np.random.choice(CATEGORIES)), 'BUDGET_TIER': str(tier)} 
          for i, tier in enumerate(budget_tiers)]
brands_df = pd.DataFrame(brands)
print(f"  Budget tier distribution:\n{brands_df['BUDGET_TIER'].value_counts().to_string()}")

cursor.execute("TRUNCATE TABLE IF EXISTS CC_DEMO.RAW.BRANDS")
vals = [(str(r['BRAND_ID']), str(r['BRAND_NAME']), str(r['CATEGORY']), str(r['BUDGET_TIER'])) for _, r in brands_df.iterrows()]
cursor.executemany("INSERT INTO CC_DEMO.RAW.BRANDS VALUES (%s,%s,%s,%s)", vals)
conn.commit()
print(f"  [PASS] BRANDS: {NUM_BRANDS} rows")

# 3. BEHAVIORAL_EVENTS (schema: EVENT_ID, CREATOR_ID, BRAND_ID, SESSION_ID, EVENT_TYPE, EVENT_DATE, EVENT_TIMESTAMP, GMV, CTR, ENGAGEMENT_SCORE, PLATFORM)
print("\n[3/4] Generating BEHAVIORAL_EVENTS (500K rows)...")
creator_lookup = creators_df.set_index('CREATOR_ID').to_dict('index')
archetype_weights = {'POWER_PERFORMER': 4, 'RISING_STAR': 3, 'STEADY_EARNER': 2, 'LONG_TAIL': 1}
creator_weights = np.array([archetype_weights[creator_lookup[c]['ARCHETYPE']] for c in creators_df['CREATOR_ID']])
creator_weights = creator_weights / creator_weights.sum()

base_ts = datetime.now() - timedelta(days=7)
events = []
for i in range(NUM_EVENTS):
    creator_id = str(np.random.choice(creators_df['CREATOR_ID'].values, p=creator_weights))
    creator = creator_lookup[creator_id]
    brand = brands_df.iloc[np.random.randint(NUM_BRANDS)]
    base_eng = creator['AVG_ENGAGEMENT']
    gmv_ranges = {'POWER_PERFORMER': (200, 500), 'RISING_STAR': (100, 300), 'STEADY_EARNER': (20, 100), 'LONG_TAIL': (0, 50)}
    ts = base_ts + timedelta(days=np.random.randint(7), hours=np.random.randint(24), minutes=np.random.randint(60))
    events.append({
        'EVENT_ID': f'EVT_{i:07d}',
        'CREATOR_ID': creator_id,
        'BRAND_ID': str(brand['BRAND_ID']),
        'SESSION_ID': f'SESS_{np.random.randint(100000):06d}',
        'EVENT_TYPE': str(np.random.choice(EVENT_TYPES, p=[0.3, 0.4, 0.1, 0.1, 0.1])),
        'EVENT_DATE': ts.strftime('%Y-%m-%d'),
        'EVENT_TIMESTAMP': ts.strftime('%Y-%m-%d %H:%M:%S'),
        'GMV': float(np.random.uniform(*gmv_ranges[creator['ARCHETYPE']]) if np.random.random() < 0.1 else 0),
        'CLICK_THROUGH_RATE': float(min(base_eng * np.random.uniform(0.8, 1.2), 1.0)),
        'ENGAGEMENT_SCORE': float(base_eng * np.random.uniform(0.8, 1.2)),
        'PLATFORM': str(np.random.choice(PLATFORMS)),
    })

events_df = pd.DataFrame(events)
cursor.execute("TRUNCATE TABLE IF EXISTS CC_DEMO.RAW.BEHAVIORAL_EVENTS")
batch_size = 10000
for start in range(0, len(events_df), batch_size):
    batch = events_df.iloc[start:start+batch_size]
    vals = [(str(r['EVENT_ID']), str(r['CREATOR_ID']), str(r['BRAND_ID']), str(r['SESSION_ID']), str(r['EVENT_TYPE']),
             str(r['EVENT_DATE']), str(r['EVENT_TIMESTAMP']), float(r['GMV']), float(r['CLICK_THROUGH_RATE']),
             float(r['ENGAGEMENT_SCORE']), str(r['PLATFORM'])) for _, r in batch.iterrows()]
    cursor.executemany("INSERT INTO CC_DEMO.RAW.BEHAVIORAL_EVENTS VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", vals)
    conn.commit()
    print(f"    {min(start+batch_size, NUM_EVENTS):,} / {NUM_EVENTS:,}")
print(f"  [PASS] BEHAVIORAL_EVENTS: {NUM_EVENTS} rows")

# 4. CREATOR_BRAND_INTERACTIONS (schema: INTERACTION_ID, CREATOR_ID, BRAND_ID, CAMPAIGN_ID, EVENT_TIMESTAMP, CONVERTED, MATCH_QUALITY)
print("\n[4/4] Generating CREATOR_BRAND_INTERACTIONS (100K rows)...")
interactions = []
for i in range(NUM_INTERACTIONS):
    creator_id = str(np.random.choice(creators_df['CREATOR_ID'].values, p=creator_weights))
    creator = creator_lookup[creator_id]
    brand = brands_df.iloc[np.random.randint(NUM_BRANDS)]
    base_conv = ARCHETYPES[creator['ARCHETYPE']]['base_conv']
    category_match = creator['CATEGORY'] == brand['CATEGORY']
    conv_prob = base_conv * (1.2 if category_match else 0.85) * np.random.uniform(0.7, 1.3)
    conv_prob = min(max(conv_prob, 0), 1)
    ts = base_ts + timedelta(days=np.random.randint(7), hours=np.random.randint(24), minutes=np.random.randint(60))
    interactions.append({
        'INTERACTION_ID': f'INT_{i:06d}',
        'CREATOR_ID': creator_id,
        'BRAND_ID': str(brand['BRAND_ID']),
        'CAMPAIGN_ID': f'CAMP_{np.random.randint(1000):04d}',
        'EVENT_TIMESTAMP': ts.strftime('%Y-%m-%d %H:%M:%S'),
        'CONVERTED': bool(np.random.random() < conv_prob),
        'MATCH_QUALITY': float(conv_prob),
    })

interactions_df = pd.DataFrame(interactions)
conv_rate = interactions_df['CONVERTED'].mean()
print(f"  Overall conversion rate: {conv_rate:.2%}")

cursor.execute("TRUNCATE TABLE IF EXISTS CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS")
batch_size = 10000
for start in range(0, len(interactions_df), batch_size):
    batch = interactions_df.iloc[start:start+batch_size]
    vals = [(str(r['INTERACTION_ID']), str(r['CREATOR_ID']), str(r['BRAND_ID']), str(r['CAMPAIGN_ID']),
             str(r['EVENT_TIMESTAMP']), bool(r['CONVERTED']), float(r['MATCH_QUALITY'])) for _, r in batch.iterrows()]
    cursor.executemany("INSERT INTO CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS VALUES (%s,%s,%s,%s,%s,%s,%s)", vals)
    conn.commit()
print(f"  [PASS] CREATOR_BRAND_INTERACTIONS: {NUM_INTERACTIONS} rows")

# Final validation
print("\n" + "=" * 60)
cursor.execute("""
SELECT 'RAW.CREATORS' AS TBL, COUNT(*) FROM CC_DEMO.RAW.CREATORS
UNION ALL SELECT 'RAW.BRANDS', COUNT(*) FROM CC_DEMO.RAW.BRANDS
UNION ALL SELECT 'RAW.BEHAVIORAL_EVENTS', COUNT(*) FROM CC_DEMO.RAW.BEHAVIORAL_EVENTS
UNION ALL SELECT 'RAW.CREATOR_BRAND_INTERACTIONS', COUNT(*) FROM CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,} rows")
cursor.close()
conn.close()
print("\n[COMPLETE]")
