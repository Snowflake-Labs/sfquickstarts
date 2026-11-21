#!/usr/bin/env python3
"""
Get Started with Snowflake-Managed Iceberg Tables
Streaming Telemetry Simulator

Simulates real-time vehicle telemetry data and inserts it into
a Snowflake-managed Iceberg table.
"""

import os
import sys
import json
import time
import random
import signal
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = SCRIPT_DIR / 'config.env'

if CONFIG_PATH.exists():
    load_dotenv(CONFIG_PATH)
else:
    load_dotenv('config.env')

try:
    import snowflake.connector
except ImportError:
    print("ERROR: snowflake-connector-python is not installed.")
    print("Run: pip install snowflake-connector-python")
    sys.exit(1)

# Configuration
SNOWFLAKE_CONNECTION = os.getenv('SNOWFLAKE_CONNECTION', 'default')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'FLEET_DB')
SNOWFLAKE_SCHEMA = 'RAW'
SNOWFLAKE_TABLE = 'VEHICLE_TELEMETRY_STREAM'

MAX_DURATION_SECONDS = int(os.getenv('STREAMING_DURATION', 300))
VEHICLE_COUNT = int(os.getenv('STREAMING_VEHICLE_COUNT', 50))
EVENTS_PER_SECOND = float(os.getenv('STREAMING_EVENTS_PER_SECOND', 2))
BATCH_SIZE = 10

running = True


def signal_handler(sig, frame):
    global running
    print("\n\nShutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@dataclass
class VehicleState:
    vehicle_id: str
    latitude: float
    longitude: float
    speed_mph: float
    heading: float
    engine_rpm: int
    engine_temp_f: int
    oil_pressure_psi: float
    fuel_level_pct: float
    check_engine: bool
    hard_accelerations: int
    hard_brakes: int
    region: str


def create_vehicle_fleet(count):
    regions = [
        ("Pacific Northwest", 47.6, -122.3),
        ("California", 34.0, -118.2),
        ("Mountain West", 39.7, -104.9),
        ("Midwest", 41.8, -87.6),
        ("Northeast", 40.7, -74.0),
    ]
    vehicles = []
    for i in range(count):
        region_name, base_lat, base_lon = regions[i % len(regions)]
        vehicles.append(VehicleState(
            vehicle_id=f"VH-{i:04d}",
            latitude=base_lat + random.uniform(-0.5, 0.5),
            longitude=base_lon + random.uniform(-0.5, 0.5),
            speed_mph=random.uniform(0, 65),
            heading=random.uniform(0, 360),
            engine_rpm=random.randint(800, 3500),
            engine_temp_f=random.randint(180, 210),
            oil_pressure_psi=random.uniform(30, 50),
            fuel_level_pct=random.uniform(20, 100),
            check_engine=random.random() < 0.05,
            hard_accelerations=0,
            hard_brakes=0,
            region=region_name,
        ))
    return vehicles


def update_vehicle_state(v):
    speed_change = random.uniform(-10, 10)
    v.speed_mph = max(0, min(95, v.speed_mph + speed_change))

    movement = v.speed_mph * 0.00001
    v.latitude += movement * random.uniform(-0.5, 1)
    v.longitude += movement * random.uniform(-1, 0.5)

    if random.random() < 0.1:
        v.heading = (v.heading + random.uniform(-45, 45)) % 360

    v.engine_rpm = max(600, min(6000, v.engine_rpm + random.randint(-300, 300)))
    v.engine_temp_f = max(160, min(250, v.engine_temp_f + random.randint(-3, 5)))
    v.oil_pressure_psi = max(20, min(60, v.oil_pressure_psi + random.uniform(-2, 2)))
    v.fuel_level_pct = max(0, v.fuel_level_pct - v.speed_mph * 0.001 - random.uniform(0, 0.01))

    if abs(speed_change) > 8:
        if speed_change > 0:
            v.hard_accelerations += 1
        else:
            v.hard_brakes += 1

    if random.random() < 0.001:
        v.check_engine = not v.check_engine

    return v


def generate_telemetry_event(v):
    now = datetime.now(timezone.utc)
    telemetry_data = {
        "location": {"lat": round(v.latitude, 6), "lon": round(v.longitude, 6)},
        "speed_mph": round(v.speed_mph, 1),
        "heading": round(v.heading, 1),
        "engine": {
            "rpm": v.engine_rpm,
            "temperature_f": v.engine_temp_f,
            "oil_pressure_psi": round(v.oil_pressure_psi, 1),
            "fuel_level_pct": round(v.fuel_level_pct, 1),
        },
        "diagnostics": {
            "check_engine": v.check_engine,
            "codes": ["P0300"] if v.check_engine else [],
        },
        "driver_behavior": {
            "hard_acceleration_count": v.hard_accelerations,
            "hard_brake_count": v.hard_brakes,
        },
        "metadata": {
            "region": v.region,
            "timestamp_utc": now.isoformat(),
        },
    }
    return {
        "VEHICLE_ID": v.vehicle_id,
        "EVENT_TIMESTAMP": now.strftime("%Y-%m-%d %H:%M:%S.%f"),
        "TELEMETRY_DATA": json.dumps(telemetry_data),
    }


def create_connection():
    print(f"Connecting to Snowflake (connection: {SNOWFLAKE_CONNECTION})...")
    pat = os.getenv('SNOWFLAKE_PAT')

    conn_params = {
        'connection_name': SNOWFLAKE_CONNECTION,
        'database': SNOWFLAKE_DATABASE,
        'schema': SNOWFLAKE_SCHEMA,
    }

    if pat:
        conn_params['password'] = pat
        print("  Using PAT authentication")
    else:
        print("  Using connection defaults from ~/.snowflake/config.toml")

    conn = snowflake.connector.connect(**conn_params)
    print("  Connected!")
    return conn


def stream_batch(cursor, events):
    for event in events:
        cursor.execute(
            f"""
            INSERT INTO {SNOWFLAKE_TABLE} (VEHICLE_ID, EVENT_TIMESTAMP, TELEMETRY_DATA)
            SELECT %s, %s::TIMESTAMP_NTZ, PARSE_JSON(%s)
            """,
            (event["VEHICLE_ID"], event["EVENT_TIMESTAMP"], event["TELEMETRY_DATA"]),
        )


def main():
    global running

    print("=" * 60)
    print("Snowflake-Managed Iceberg Tables — Streaming Simulator")
    print("=" * 60)
    print(f"Connection: {SNOWFLAKE_CONNECTION}")
    print(f"Database:   {SNOWFLAKE_DATABASE}")
    print(f"Table:      {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")
    print(f"Vehicles:   {VEHICLE_COUNT}")
    print(f"Rate:       {EVENTS_PER_SECOND} events/sec")
    print(f"Duration:   {MAX_DURATION_SECONDS} seconds")
    print("-" * 60)
    print("Press Ctrl+C to stop")
    print("-" * 60)

    conn = create_connection()
    cursor = conn.cursor()

    print(f"\nInitializing {VEHICLE_COUNT} vehicles...")
    vehicles = create_vehicle_fleet(VEHICLE_COUNT)
    print("Fleet ready!\n")

    start_time = time.time()
    total_events = 0
    batch = []

    try:
        while running and (time.time() - start_time) < MAX_DURATION_SECONDS:
            selected = random.sample(vehicles, min(BATCH_SIZE, len(vehicles)))
            for v in selected:
                v = update_vehicle_state(v)
                batch.append(generate_telemetry_event(v))

            if len(batch) >= BATCH_SIZE:
                try:
                    stream_batch(cursor, batch)
                    conn.commit()
                    total_events += len(batch)

                    elapsed = time.time() - start_time
                    rate = total_events / elapsed if elapsed > 0 else 0
                    print(
                        f"\rEvents: {total_events:,} | Rate: {rate:.1f}/sec | Elapsed: {elapsed:.0f}s",
                        end="",
                        flush=True,
                    )
                    batch = []
                except Exception as e:
                    print(f"\nError: {e}")

            time.sleep(1 / EVENTS_PER_SECOND)
    except KeyboardInterrupt:
        pass

    cursor.close()
    conn.close()

    elapsed = time.time() - start_time
    print(f"\n\n{'=' * 60}")
    print("Streaming complete!")
    print(f"{'=' * 60}")
    print(f"Total events: {total_events:,}")
    print(f"Duration:     {elapsed:.1f}s")
    if elapsed > 0:
        print(f"Avg rate:     {total_events / elapsed:.1f} events/sec")
    print(f"\nQuery your data:")
    print(f"  SELECT * FROM {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE} LIMIT 10;")


if __name__ == "__main__":
    main()
