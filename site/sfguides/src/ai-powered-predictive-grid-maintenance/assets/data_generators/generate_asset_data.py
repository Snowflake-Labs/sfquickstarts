# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
AI-Driven Grid Reliability & Predictive Maintenance
Synthetic Data Generator

Purpose: Generate realistic synthetic data for transformer monitoring demo
- 100 substation transformers across Florida
- 6 months of hourly sensor readings
- Realistic degradation patterns with some failures
- Asset master data with geolocation
- Maintenance history
- Historical failure events

Author: Grid Reliability AI/ML Team
Date: 2025-11-15
Version: 1.0

Usage:
    python data_generator.py --output-dir ./generated_data --months 6 --assets 100
"""

import argparse
import json
import csv
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import uuid

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Florida counties and major substations
FLORIDA_LOCATIONS = [
    # County, City, Substation, Lat, Lon, Customers
    ("Miami-Dade", "Miami", "Downtown Miami SS", 25.7617, -80.1918, 15000),
    ("Miami-Dade", "Kendall", "Kendall SS", 25.6795, -80.3173, 12500),
    ("Broward", "Fort Lauderdale", "FTL North SS", 26.1224, -80.1373, 11000),
    ("Broward", "Pembroke Pines", "Pembroke SS", 26.0031, -80.2906, 9500),
    ("Palm Beach", "West Palm Beach", "WPB Central SS", 26.7153, -80.0534, 12500),
    ("Palm Beach", "Boca Raton", "Boca SS", 26.3683, -80.1289, 8500),
    ("Hillsborough", "Tampa", "Tampa East SS", 27.9506, -82.4572, 13000),
    ("Hillsborough", "Brandon", "Brandon SS", 27.9378, -82.2859, 7500),
    ("Orange", "Orlando", "Orlando Central SS", 28.5383, -81.3792, 14000),
    ("Orange", "Winter Park", "Winter Park SS", 28.6000, -81.3392, 6500),
    ("Duval", "Jacksonville", "Jacksonville East SS", 30.3322, -81.6557, 11500),
    ("Pinellas", "St. Petersburg", "St. Pete SS", 27.7676, -82.6403, 9000),
    ("Lee", "Fort Myers", "Fort Myers SS", 26.6406, -81.8723, 8000),
    ("Polk", "Lakeland", "Lakeland SS", 28.0395, -81.9498, 6000),
    ("Brevard", "Melbourne", "Melbourne SS", 28.0836, -80.6081, 7000),
]

# Transformer manufacturers and models
MANUFACTURERS = [
    ("ABB", ["TXP 25MVA", "TXP 50MVA", "DTR 25MVA"]),
    ("Siemens", ["GEAFOL 25MVA", "GEAFOL 50MVA"]),
    ("GE", ["Prolec 25MVA", "Prolec 50MVA"]),
    ("Schneider Electric", ["Minera 25MVA", "Minera 50MVA"]),
    ("Hitachi", ["ONAN 25MVA", "ONAF 50MVA"]),
]

# Failure types with typical progression patterns
FAILURE_PATTERNS = {
    "WINDING_FAIL": {
        "oil_temp_increase": 1.2,  # Multiplier
        "h2_increase": 50,  # ppm per week
        "load_sensitivity": 1.5,
        "duration_weeks": 3,
    },
    "BUSHING_FAULT": {
        "partial_discharge_increase": 100,  # pC per week
        "oil_temp_increase": 1.1,
        "duration_weeks": 4,
    },
    "OIL_LEAK": {
        "oil_level_drop": 0.05,  # 5% per week
        "load_temp_increase": 1.15,
        "duration_weeks": 6,
    },
    "TAP_CHANGER": {
        "acoustic_increase": 5,  # dB per week
        "vibration_increase": 0.5,  # mm/s per week
        "duration_weeks": 5,
    },
    "COOLING_FAIL": {
        "oil_temp_increase": 1.3,
        "winding_temp_increase": 1.4,
        "duration_weeks": 2,
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_asset_id(index: int) -> str:
    """Generate asset ID like T-SS047-001"""
    return f"T-SS{index:03d}-001"

def assign_location(index: int) -> Tuple:
    """Assign location to asset with some clustering"""
    loc = FLORIDA_LOCATIONS[index % len(FLORIDA_LOCATIONS)]
    # Add some geographic jitter for variety
    lat_jitter = np.random.normal(0, 0.05)
    lon_jitter = np.random.normal(0, 0.05)
    return (
        loc[0],  # County
        loc[1],  # City
        f"{loc[2]}-{index % 3 + 1}",  # Substation
        round(loc[3] + lat_jitter, 6),  # Lat
        round(loc[4] + lon_jitter, 6),  # Lon
        int(loc[5] * random.uniform(0.8, 1.2))  # Customers (with variation)
    )

def assign_manufacturer() -> Tuple[str, str]:
    """Randomly assign manufacturer and model"""
    mfg, models = random.choice(MANUFACTURERS)
    model = random.choice(models)
    return mfg, model

def calculate_baseline_params(capacity_mva: float, age_years: float, load_factor: float) -> Dict:
    """Calculate baseline sensor parameters for healthy transformer"""
    return {
        "oil_temp_base": 70 + age_years * 0.5 + load_factor * 15,
        "winding_temp_base": 85 + age_years * 0.8 + load_factor * 20,
        "load_current_base": capacity_mva * 1000 / 138 * load_factor,  # Assuming 138kV
        "vibration_base": 3.0 + age_years * 0.1,
        "acoustic_base": 60 + age_years * 0.5,
        "h2_base": 50 + age_years * 2,
        "co_base": 200 + age_years * 10,
        "co2_base": 1000 + age_years * 50,
        "ch4_base": 30 + age_years * 1,
    }

# =============================================================================
# ASSET MASTER DATA GENERATION
# =============================================================================

def generate_asset_master(num_assets: int = 100) -> pd.DataFrame:
    """Generate asset master data"""
    print(f"Generating asset master data for {num_assets} transformers...")
    
    assets = []
    for i in range(num_assets):
        asset_id = generate_asset_id(i)
        county, city, substation, lat, lon, customers = assign_location(i)
        mfg, model = assign_manufacturer()
        
        # Age: mostly 10-20 years, some newer, some older
        age_years = int(np.random.beta(2, 2) * 25 + 5)
        install_date = datetime.now() - timedelta(days=age_years * 365)
        
        # Capacity: 25 or 50 MVA
        capacity_mva = random.choice([25, 50])
        
        # Criticality based on customers affected
        criticality = min(100, int(50 + customers / 300))
        
        # Last maintenance: random within last 2 years
        last_maint_days = random.randint(30, 730)
        last_maint_date = datetime.now() - timedelta(days=last_maint_days)
        
        asset = {
            "ASSET_ID": asset_id,
            "ASSET_TYPE": "TRANSFORMER",
            "ASSET_SUBTYPE": "POWER_TRANSFORMER",
            "MANUFACTURER": mfg,
            "MODEL": model,
            "SERIAL_NUMBER": f"SN-{uuid.uuid4().hex[:12].upper()}",
            "INSTALL_DATE": install_date.strftime("%Y-%m-%d"),
            "EXPECTED_LIFE_YEARS": 25,
            "LOCATION_SUBSTATION": substation,
            "LOCATION_CITY": city,
            "LOCATION_COUNTY": county,
            "LOCATION_LAT": lat,
            "LOCATION_LON": lon,
            "VOLTAGE_RATING_KV": 138,
            "CAPACITY_MVA": capacity_mva,
            "CRITICALITY_SCORE": criticality,
            "CUSTOMERS_AFFECTED": customers,
            "REPLACEMENT_COST_USD": capacity_mva * 17000,  # ~$17k per MVA
            "LAST_MAINTENANCE_DATE": last_maint_date.strftime("%Y-%m-%d"),
            "STATUS": "ACTIVE",
        }
        assets.append(asset)
    
    df = pd.DataFrame(assets)
    print(f"Generated {len(df)} assets")
    return df

# =============================================================================
# SENSOR READINGS GENERATION
# =============================================================================

def generate_sensor_readings(
    assets_df: pd.DataFrame,
    months: int = 6,
    failure_rate: float = 0.10
) -> pd.DataFrame:
    """Generate hourly sensor readings with realistic patterns and failures"""
    print(f"Generating {months} months of hourly sensor readings...")
    
    start_date = datetime.now() - timedelta(days=months * 30)
    hours = months * 30 * 24
    
    # Select assets that will fail
    num_failures = int(len(assets_df) * failure_rate)
    failing_assets = assets_df.sample(n=num_failures)["ASSET_ID"].tolist()
    print(f"Simulating failures for {num_failures} assets: {failing_assets[:5]}...")
    
    all_readings = []
    
    for idx, asset in assets_df.iterrows():
        if idx % 10 == 0:
            print(f"  Processing asset {idx+1}/{len(assets_df)}...")
        
        asset_id = asset["ASSET_ID"]
        age_years = (datetime.now() - pd.to_datetime(asset["INSTALL_DATE"])).days / 365.25
        capacity_mva = asset["CAPACITY_MVA"]
        
        # Base load factor (with daily and seasonal variation)
        base_load_factor = np.random.uniform(0.60, 0.85)
        
        # Calculate baseline parameters
        baseline = calculate_baseline_params(capacity_mva, age_years, base_load_factor)
        
        # Determine if this asset will fail
        is_failing = asset_id in failing_assets
        if is_failing:
            failure_type = random.choice(list(FAILURE_PATTERNS.keys()))
            failure_pattern = FAILURE_PATTERNS[failure_type]
            failure_week = random.randint(int(hours / 168) - 8, int(hours / 168) - 1)  # Fail in last 8 weeks
        
        for hour in range(hours):
            timestamp = start_date + timedelta(hours=hour)
            
            # Time-based variations
            day_of_week = timestamp.weekday()
            hour_of_day = timestamp.hour
            month = timestamp.month
            
            # Load pattern: higher during business hours and summer
            hour_factor = 1.0 + 0.2 * np.sin((hour_of_day - 6) * np.pi / 12)
            weekday_factor = 1.1 if day_of_week < 5 else 0.9
            season_factor = 1.0 + 0.15 * np.sin((month - 1) * np.pi / 6)  # Peak in July
            
            load_factor = base_load_factor * hour_factor * weekday_factor * season_factor
            load_factor = np.clip(load_factor, 0.3, 0.95)
            
            # Ambient temperature (Florida climate)
            base_ambient = 25 + 5 * np.sin((month - 1) * np.pi / 6)  # Seasonal
            ambient_temp = base_ambient + np.random.normal(0, 2)
            
            # Calculate sensor readings
            oil_temp = baseline["oil_temp_base"] + load_factor * 10 + (ambient_temp - 25) * 0.5
            winding_temp = baseline["winding_temp_base"] + load_factor * 15 + (ambient_temp - 25) * 0.7
            load_current = baseline["load_current_base"] * load_factor
            
            # Apply failure pattern if applicable
            if is_failing:
                current_week = hour // 168
                weeks_to_failure = failure_week - current_week
                
                if 0 < weeks_to_failure <= failure_pattern["duration_weeks"]:
                    # Asset is degrading
                    degradation_factor = 1 - (weeks_to_failure / failure_pattern["duration_weeks"])
                    
                    if "oil_temp_increase" in failure_pattern:
                        oil_temp *= (1 + (failure_pattern["oil_temp_increase"] - 1) * degradation_factor)
                    if "h2_increase" in failure_pattern:
                        baseline["h2_base"] += failure_pattern["h2_increase"] * degradation_factor
                    if "partial_discharge_increase" in failure_pattern:
                        partial_discharge = 50 + failure_pattern["partial_discharge_increase"] * degradation_factor
                    if "acoustic_increase" in failure_pattern:
                        baseline["acoustic_base"] += failure_pattern["acoustic_increase"] * degradation_factor
            
            # Add noise to all readings
            reading = {
                "ASSET_ID": asset_id,
                "READING_TIMESTAMP": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "OIL_TEMPERATURE_C": round(oil_temp + np.random.normal(0, 1.5), 2),
                "WINDING_TEMPERATURE_C": round(winding_temp + np.random.normal(0, 2.0), 2),
                "LOAD_CURRENT_A": round(load_current + np.random.normal(0, 10), 2),
                "LOAD_VOLTAGE_KV": round(138 + np.random.normal(0, 1.5), 2),
                "AMBIENT_TEMP_C": round(ambient_temp, 2),
                "HUMIDITY_PCT": round(np.clip(70 + 15 * np.sin((month - 1) * np.pi / 6) + np.random.normal(0, 5), 0, 100), 2),
                "VIBRATION_MM_S": round(baseline["vibration_base"] + np.random.normal(0, 0.5), 4),
                "ACOUSTIC_DB": round(baseline["acoustic_base"] + np.random.normal(0, 2), 2),
                "DISSOLVED_H2_PPM": round(max(0, baseline["h2_base"] + np.random.normal(0, 10)), 2),
                "DISSOLVED_CO_PPM": round(max(0, baseline["co_base"] + np.random.normal(0, 20)), 2),
                "DISSOLVED_CO2_PPM": round(max(0, baseline["co2_base"] + np.random.normal(0, 50)), 2),
                "DISSOLVED_CH4_PPM": round(max(0, baseline["ch4_base"] + np.random.normal(0, 5)), 2),
                "BUSHING_TEMP_C": round(oil_temp - 5 + np.random.normal(0, 2), 2),
                "TAP_POSITION": random.randint(-8, 8),
                "PARTIAL_DISCHARGE_PC": round(max(0, 30 + np.random.exponential(20)), 2),
                "POWER_FACTOR": round(np.clip(0.85 + np.random.normal(0, 0.02), 0.7, 0.99), 4),
            }
            all_readings.append(reading)
    
    df = pd.DataFrame(all_readings)
    print(f"Generated {len(df):,} sensor readings")
    return df

# =============================================================================
# MAINTENANCE HISTORY GENERATION
# =============================================================================

def generate_maintenance_history(assets_df: pd.DataFrame, months: int = 6) -> pd.DataFrame:
    """Generate maintenance history records"""
    print("Generating maintenance history...")
    
    maintenance_records = []
    start_date = datetime.now() - timedelta(days=months * 30)
    
    for idx, asset in assets_df.iterrows():
        asset_id = asset["ASSET_ID"]
        
        # Each asset has 1-3 maintenance events in the period
        num_events = random.randint(1, 3)
        
        for i in range(num_events):
            maint_date = start_date + timedelta(days=random.randint(0, months * 30))
            
            maint_type = random.choice([
                "INSPECTION", "INSPECTION", "INSPECTION",  # More inspections
                "PREVENTIVE", "PREVENTIVE",
                "REPAIR", "REPLACEMENT"
            ])
            
            descriptions = {
                "INSPECTION": "Routine inspection and oil sampling",
                "PREVENTIVE": "Preventive maintenance including bushing cleaning and tap changer servicing",
                "REPAIR": "Corrective maintenance to address identified issues",
                "REPLACEMENT": "Component replacement",
            }
            
            costs = {
                "INSPECTION": (500, 2000),
                "PREVENTIVE": (5000, 15000),
                "REPAIR": (10000, 50000),
                "REPLACEMENT": (50000, 150000),
            }
            
            downtimes = {
                "INSPECTION": (0, 0.5),
                "PREVENTIVE": (2, 8),
                "REPAIR": (8, 24),
                "REPLACEMENT": (24, 72),
            }
            
            cost_range = costs[maint_type]
            downtime_range = downtimes[maint_type]
            
            record = {
                "MAINTENANCE_ID": f"WO-{maint_date.year}{maint_date.month:02d}-{uuid.uuid4().hex[:8].upper()}",
                "ASSET_ID": asset_id,
                "MAINTENANCE_DATE": maint_date.strftime("%Y-%m-%d"),
                "MAINTENANCE_TYPE": maint_type,
                "DESCRIPTION": descriptions[maint_type],
                "TECHNICIAN": f"TECH-{random.randint(100, 999)}",
                "COST_USD": round(random.uniform(*cost_range), 2),
                "DOWNTIME_HOURS": round(random.uniform(*downtime_range), 2),
                "OUTCOME": random.choice(["SUCCESS"] * 9 + ["PARTIAL"]),  # 90% success rate
            }
            maintenance_records.append(record)
    
    df = pd.DataFrame(maintenance_records)
    df = df.sort_values("MAINTENANCE_DATE")
    print(f"Generated {len(df)} maintenance records")
    return df

# =============================================================================
# FAILURE EVENTS GENERATION
# =============================================================================

def generate_failure_events(assets_df: pd.DataFrame, failure_rate: float = 0.10) -> pd.DataFrame:
    """Generate historical failure events"""
    print("Generating failure events...")
    
    num_failures = int(len(assets_df) * failure_rate)
    failing_assets = assets_df.sample(n=num_failures)
    
    failure_records = []
    
    for idx, asset in failing_assets.iterrows():
        asset_id = asset["ASSET_ID"]
        customers = asset["CUSTOMERS_AFFECTED"]
        
        failure_type = random.choice(list(FAILURE_PATTERNS.keys()))
        
        # Failure occurred in last 4 weeks
        failure_date = datetime.now() - timedelta(days=random.randint(1, 28))
        
        # Outage duration depends on failure type
        outage_hours = {
            "WINDING_FAIL": random.uniform(4, 8),
            "BUSHING_FAULT": random.uniform(2, 4),
            "OIL_LEAK": random.uniform(3, 6),
            "TAP_CHANGER": random.uniform(2, 5),
            "COOLING_FAIL": random.uniform(1, 3),
        }[failure_type]
        
        # Repair cost from reference data
        repair_costs = {
            "WINDING_FAIL": 425000,
            "BUSHING_FAULT": 85000,
            "OIL_LEAK": 45000,
            "TAP_CHANGER": 125000,
            "COOLING_FAIL": 35000,
        }
        
        record = {
            "EVENT_ID": f"FE-{failure_date.year}{failure_date.month:02d}-{uuid.uuid4().hex[:8].upper()}",
            "ASSET_ID": asset_id,
            "FAILURE_TIMESTAMP": failure_date.strftime("%Y-%m-%d %H:%M:%S"),
            "FAILURE_TYPE": failure_type,
            "ROOT_CAUSE": f"Detailed root cause analysis for {failure_type}",
            "CUSTOMERS_AFFECTED": customers,
            "OUTAGE_DURATION_HOURS": round(outage_hours, 2),
            "REPAIR_COST_USD": repair_costs[failure_type] * random.uniform(0.8, 1.2),
            "REPLACEMENT_FLAG": failure_type in ["WINDING_FAIL"],
            "PREVENTABLE_FLAG": True,
            "ADVANCED_WARNING_DAYS": random.randint(14, 30),
        }
        failure_records.append(record)
    
    df = pd.DataFrame(failure_records)
    df = df.sort_values("FAILURE_TIMESTAMP")
    print(f"Generated {len(df)} failure events")
    return df

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic grid reliability data")
    parser.add_argument("--output-dir", type=str, default="./generated_data",
                        help="Output directory for generated files")
    parser.add_argument("--months", type=int, default=6,
                        help="Months of historical data to generate")
    parser.add_argument("--assets", type=int, default=100,
                        help="Number of transformer assets to generate")
    parser.add_argument("--failure-rate", type=float, default=0.10,
                        help="Percentage of assets that will fail (0.0-1.0)")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("AI-Driven Grid Reliability - Data Generator")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  Assets: {args.assets}")
    print(f"  Timespan: {args.months} months")
    print(f"  Failure Rate: {args.failure_rate * 100}%")
    print(f"  Output Directory: {output_dir}")
    print("=" * 80)
    
    # Generate datasets
    print("\n1. Generating Asset Master Data...")
    assets_df = generate_asset_master(args.assets)
    assets_df.to_csv(output_dir / "asset_master.csv", index=False)
    print(f"   Saved to: {output_dir / 'asset_master.csv'}")
    
    print("\n2. Generating Sensor Readings...")
    readings_df = generate_sensor_readings(assets_df, args.months, args.failure_rate)
    
    # Save sensor readings in batches (for easier loading)
    batch_size = 100000
    num_batches = (len(readings_df) // batch_size) + 1
    
    for i in range(num_batches):
        batch = readings_df[i * batch_size:(i + 1) * batch_size]
        if len(batch) > 0:
            # Save as JSON for Snowpipe
            batch_file = output_dir / f"sensor_readings_batch_{i+1}.json"
            batch.to_json(batch_file, orient="records", lines=True)
            print(f"   Saved batch {i+1}/{num_batches}: {batch_file} ({len(batch):,} records)")
    
    print("\n3. Generating Maintenance History...")
    maintenance_df = generate_maintenance_history(assets_df, args.months)
    maintenance_df.to_csv(output_dir / "maintenance_history.csv", index=False)
    print(f"   Saved to: {output_dir / 'maintenance_history.csv'}")
    
    print("\n4. Generating Failure Events...")
    failures_df = generate_failure_events(assets_df, args.failure_rate)
    failures_df.to_csv(output_dir / "failure_events.csv", index=False)
    print(f"   Saved to: {output_dir / 'failure_events.csv'}")
    
    # Generate summary statistics
    print("\n" + "=" * 80)
    print("DATA GENERATION COMPLETE")
    print("=" * 80)
    print(f"Summary:")
    print(f"  Assets: {len(assets_df):,}")
    print(f"  Sensor Readings: {len(readings_df):,}")
    print(f"  Maintenance Records: {len(maintenance_df):,}")
    print(f"  Failure Events: {len(failures_df):,}")
    print(f"\nTotal file size: ~{sum(f.stat().st_size for f in output_dir.glob('*')) / 1024 / 1024:.1f} MB")
    
    # Print loading instructions
    print("\n" + "=" * 80)
    print("NEXT STEPS: Loading Data into Snowflake")
    print("=" * 80)
    print("""
1. Upload files to Snowflake stage:
   
   PUT file://{output_dir}/asset_master.csv @RAW.ASSET_DATA_STAGE AUTO_COMPRESS=TRUE;
   PUT file://{output_dir}/sensor_readings_batch_*.json @RAW.SENSOR_DATA_STAGE AUTO_COMPRESS=TRUE;
   PUT file://{output_dir}/maintenance_history.csv @RAW.MAINTENANCE_DATA_STAGE AUTO_COMPRESS=TRUE;

2. Load data into tables:
   
   COPY INTO RAW.ASSET_MASTER FROM @RAW.ASSET_DATA_STAGE 
   FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT') MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
   
   -- Sensor readings will auto-load via Snowpipe if configured
   -- Or manually: ALTER PIPE RAW.SENSOR_READINGS_PIPE REFRESH;

3. Verify data loaded:
   
   SELECT COUNT(*) FROM RAW.ASSET_MASTER;
   SELECT COUNT(*) FROM RAW.SENSOR_READINGS;
   SELECT COUNT(*) FROM RAW.MAINTENANCE_HISTORY;
""".format(output_dir=output_dir))
    
    print("=" * 80)

if __name__ == "__main__":
    main()


