#!/usr/bin/env python3
"""
Snowflake Iceberg V3 Comprehensive Guide
Streaming Telemetry Simulator using Snowpipe Streaming SDK

This script simulates real-time vehicle telemetry data and streams it
directly into an Iceberg V3 table using Snowpipe Streaming.
"""

import os
import sys
import json
import time
import random
import signal
import uuid
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = SCRIPT_DIR.parent / 'config.env'

# Load configuration
if CONFIG_PATH.exists():
    load_dotenv(CONFIG_PATH)
else:
    # Try current directory as fallback
    load_dotenv('config.env')
    if not os.getenv('SNOWFLAKE_ACCOUNT'):
        print(f"ERROR: Could not find config.env at {CONFIG_PATH}")
        print("Make sure you've copied config.env.template to config.env and configured it.")
        sys.exit(1)

# Try to import Snowflake Ingest SDK
try:
    from snowflake.ingest import SimpleIngestManager
    from snowflake.ingest import StagedFile
    SNOWPIPE_AVAILABLE = True
except ImportError:
    SNOWPIPE_AVAILABLE = False
    print("Warning: snowflake-ingest not available. Using connector fallback.")

# Try to import Snowflake Connector
try:
    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas
    CONNECTOR_AVAILABLE = True
except ImportError:
    CONNECTOR_AVAILABLE = False

# Configuration
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'FLEET_ANALYTICS_DB')
SNOWFLAKE_SCHEMA = 'RAW'
SNOWFLAKE_TABLE = 'VEHICLE_TELEMETRY_STREAM'
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'FLEET_ANALYTICS_WH')
SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

# Validate required configuration
if not SNOWFLAKE_ACCOUNT or SNOWFLAKE_ACCOUNT == 'your_account_identifier':
    print("ERROR: SNOWFLAKE_ACCOUNT is not configured in config.env")
    print(f"Config file location: {CONFIG_PATH}")
    sys.exit(1)

if not SNOWFLAKE_USER or SNOWFLAKE_USER == 'your_username':
    print("ERROR: SNOWFLAKE_USER is not configured in config.env")
    print(f"Config file location: {CONFIG_PATH}")
    sys.exit(1)

# Streaming configuration
MAX_DURATION_SECONDS = int(os.getenv('STREAMING_DURATION', 300))  # 5 minutes max
VEHICLE_COUNT = int(os.getenv('STREAMING_VEHICLE_COUNT', 50))
EVENTS_PER_SECOND = float(os.getenv('STREAMING_EVENTS_PER_SECOND', 2))
BATCH_SIZE = 10

# External Lineage Configuration
# Simulates telemetry coming from an MQTT/IoT broker (realistic for vehicle fleets)
# Common platforms: AWS IoT Core, Azure IoT Hub, HiveMQ, EMQX
IOT_BROKER_NAMESPACE = os.getenv('IOT_BROKER_NAMESPACE', 'mqtt://fleet-iot-gateway.example.com')
IOT_SOURCE_NAME = os.getenv('IOT_SOURCE_NAME', 'Fleet Vehicle Telematics')
IOT_TOPIC_PATTERN = os.getenv('IOT_TOPIC_PATTERN', 'fleet/vehicles/+/telemetry')
ENABLE_EXTERNAL_LINEAGE = os.getenv('ENABLE_EXTERNAL_LINEAGE', 'true').lower() == 'true'

# Account URL for REST API (reuse from Spark config)
SNOWFLAKE_ACCOUNT_URL = os.getenv('SNOWFLAKE_ACCOUNT_URL', SNOWFLAKE_ACCOUNT)

# PAT for REST API authentication (same token used for streaming)
SNOWFLAKE_PAT = os.getenv('SNOWFLAKE_ACCOUNTADMIN_TOKEN', '')

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle interrupt signal for graceful shutdown."""
    global running
    print("\n\nReceived interrupt signal. Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def send_external_lineage(conn, total_events: int, start_time: datetime, end_time: datetime):
    """
    Send OpenLineage event to Snowflake's External Lineage endpoint.
    
    This establishes lineage showing data flow from the IoT/MQTT broker 
    (where vehicles publish telemetry) to the Snowflake Iceberg table.
    
    See: https://docs.snowflake.com/en/user-guide/external-lineage
    """
    if not ENABLE_EXTERNAL_LINEAGE:
        return
    
    # Check if PAT is configured (required for REST API)
    if not SNOWFLAKE_PAT:
        print("\nNote: SNOWFLAKE_ACCOUNTADMIN_TOKEN not set in config.env. Skipping lineage registration.")
        return
    
    # Build lineage endpoint URL using configured account URL
    # Keep dashes as-is for the standard REST API (unlike Iceberg catalog which needs underscores)
    account_url = SNOWFLAKE_ACCOUNT_URL.lower()
    lineage_endpoint = f"https://{account_url}.snowflakecomputing.com/api/v2/lineage/external-lineage"
    
    # Build the OpenLineage COMPLETE event
    # Input: MQTT/IoT broker topic where vehicles publish telemetry
    # Output: Snowflake Iceberg table
    lineage_event = {
        "eventType": "COMPLETE",
        "eventTime": end_time.isoformat(),
        "job": {
            "namespace": "snowflake-streaming",
            "name": "fleet-telemetry-ingest"
        },
        "run": {
            "runId": str(uuid.uuid4()),
            "facets": {
                "processing_engine": {
                    "_producer": "https://github.com/snowflakedb/snowpipe-streaming",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ProcessingEngineRunFacet.json",
                    "name": "Snowpipe Streaming Python SDK",
                    "version": "1.0"
                }
            }
        },
        "producer": "https://github.com/snowflakedb/snowpipe-streaming",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json",
        "inputs": [
            {
                "namespace": IOT_BROKER_NAMESPACE,
                "name": IOT_SOURCE_NAME,
                "facets": {
                    "datasetType": {
                        "datasetType": "IoT Telemetry Stream"
                    },
                    "documentation": {
                        "_producer": "https://github.com/snowflakedb/snowpipe-streaming",
                        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationDatasetFacet.json",
                        "description": f"Vehicle telemetry from MQTT topic: {IOT_TOPIC_PATTERN}. Vehicles publish GPS, engine metrics, and driver behavior data via cellular telematics units."
                    },
                    "dataSource": {
                        "_producer": "https://github.com/snowflakedb/snowpipe-streaming",
                        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DataSourceDatasetFacet.json",
                        "name": IOT_SOURCE_NAME,
                        "uri": f"{IOT_BROKER_NAMESPACE}/{IOT_TOPIC_PATTERN}"
                    }
                }
            }
        ],
        "outputs": [
            {
                "namespace": f"snowflake://{SNOWFLAKE_ACCOUNT}",
                "name": f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}",
                "facets": {
                    "datasetType": {
                        "datasetType": "ICEBERG TABLE"
                    },
                    "outputStatistics": {
                        "_producer": "https://github.com/snowflakedb/snowpipe-streaming",
                        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/OutputStatisticsOutputDatasetFacet.json",
                        "rowCount": total_events,
                        "size": total_events * 500  # Approximate bytes per event
                    }
                }
            }
        ]
    }
    
    # Send to Snowflake External Lineage endpoint
    # Using PAT (Programmatic Access Token) for authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SNOWFLAKE_PAT}",
        "Accept": "application/json",
        "User-Agent": "FleetTelemetryStreamer/1.0",
        "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"
    }
    
    try:
        response = requests.post(
            lineage_endpoint,
            headers=headers,
            json=lineage_event,
            timeout=30
        )
        
        if response.status_code in (200, 201, 202):
            print(f"\n✓ External lineage registered: {IOT_SOURCE_NAME} → {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")
            print("  View in Snowsight: Catalog » Database Explorer » Select table » Lineage tab")
        elif response.status_code == 403:
            print(f"\nNote: External lineage not registered (missing INGEST LINEAGE privilege)")
            print("  To enable, run as ACCOUNTADMIN:")
            print("    GRANT INGEST LINEAGE ON ACCOUNT TO ROLE ACCOUNTADMIN;")
        else:
            print(f"\nNote: Lineage registration returned status {response.status_code}: {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        print(f"\nNote: Could not send lineage event: {e}")


@dataclass
class VehicleState:
    """Tracks the current state of a simulated vehicle."""
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
    tire_pressure_warning: bool
    hard_accelerations: int
    hard_brakes: int
    sharp_turns: int
    region: str


def create_vehicle_fleet(count: int) -> list[VehicleState]:
    """Create a fleet of vehicles with initial states."""
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
        vehicle = VehicleState(
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
            tire_pressure_warning=random.random() < 0.03,
            hard_accelerations=0,
            hard_brakes=0,
            sharp_turns=0,
            region=region_name
        )
        vehicles.append(vehicle)
    
    return vehicles


def update_vehicle_state(vehicle: VehicleState) -> VehicleState:
    """Simulate changes in vehicle state."""
    # Update speed (with some randomness)
    speed_change = random.uniform(-10, 10)
    vehicle.speed_mph = max(0, min(95, vehicle.speed_mph + speed_change))
    
    # Update position based on speed and heading
    movement = vehicle.speed_mph * 0.00001  # Simplified movement
    vehicle.latitude += movement * random.uniform(-0.5, 1)
    vehicle.longitude += movement * random.uniform(-1, 0.5)
    
    # Update heading with occasional turns
    if random.random() < 0.1:
        heading_change = random.uniform(-45, 45)
        vehicle.heading = (vehicle.heading + heading_change) % 360
        if abs(heading_change) > 30:
            vehicle.sharp_turns += 1
    
    # Update engine metrics
    vehicle.engine_rpm = max(600, min(6000, vehicle.engine_rpm + random.randint(-300, 300)))
    vehicle.engine_temp_f = max(160, min(250, vehicle.engine_temp_f + random.randint(-3, 5)))
    vehicle.oil_pressure_psi = max(20, min(60, vehicle.oil_pressure_psi + random.uniform(-2, 2)))
    
    # Fuel consumption
    fuel_consumption = vehicle.speed_mph * 0.001 + random.uniform(0, 0.01)
    vehicle.fuel_level_pct = max(0, vehicle.fuel_level_pct - fuel_consumption)
    
    # Driver behavior events
    if abs(speed_change) > 8:
        if speed_change > 0:
            vehicle.hard_accelerations += 1
        else:
            vehicle.hard_brakes += 1
    
    # Random diagnostic events
    if random.random() < 0.001:
        vehicle.check_engine = not vehicle.check_engine
    if random.random() < 0.002:
        vehicle.tire_pressure_warning = not vehicle.tire_pressure_warning
    
    return vehicle


def generate_telemetry_event(vehicle: VehicleState) -> dict:
    """Generate a telemetry event for a vehicle."""
    now = datetime.now(timezone.utc)
    
    # Create the VARIANT payload
    telemetry_data = {
        "location": {
            "lat": round(vehicle.latitude, 6),
            "lon": round(vehicle.longitude, 6)
        },
        "speed_mph": round(vehicle.speed_mph, 1),
        "heading": round(vehicle.heading, 1),
        "engine": {
            "rpm": vehicle.engine_rpm,
            "temperature_f": vehicle.engine_temp_f,
            "oil_pressure_psi": round(vehicle.oil_pressure_psi, 1),
            "fuel_level_pct": round(vehicle.fuel_level_pct, 1)
        },
        "diagnostics": {
            "check_engine": vehicle.check_engine,
            "tire_pressure_warning": vehicle.tire_pressure_warning,
            "codes": ["P0300"] if vehicle.check_engine else []
        },
        "driver_behavior": {
            "hard_acceleration_count": vehicle.hard_accelerations,
            "hard_brake_count": vehicle.hard_brakes,
            "sharp_turn_count": vehicle.sharp_turns
        },
        "metadata": {
            "region": vehicle.region,
            "timestamp_utc": now.isoformat(),
            "firmware_version": "2.4.1"
        }
    }
    
    return {
        "VEHICLE_ID": vehicle.vehicle_id,
        "EVENT_TIMESTAMP": now.strftime("%Y-%m-%d %H:%M:%S.%f"),
        "TELEMETRY_DATA": json.dumps(telemetry_data)
    }


def create_connection():
    """Create a Snowflake connection (reused for all operations)."""
    print("Connecting to Snowflake...")
    
    # Check for authenticator and password in config
    authenticator = os.getenv('SNOWFLAKE_AUTHENTICATOR', 'externalbrowser')
    password = os.getenv('SNOWFLAKE_ACCOUNTADMIN_TOKEN')
    
    conn_params = {
        'account': SNOWFLAKE_ACCOUNT,
        'user': SNOWFLAKE_USER,
        'database': SNOWFLAKE_DATABASE,
        'schema': SNOWFLAKE_SCHEMA,
        'warehouse': SNOWFLAKE_WAREHOUSE,
        'role': SNOWFLAKE_ROLE,
    }
    
    # If password/PAT is provided, use password auth
    if password:
        conn_params['password'] = password
        if authenticator and authenticator != 'externalbrowser':
            conn_params['authenticator'] = authenticator
        print("Using password/token authentication")
    else:
        conn_params['authenticator'] = authenticator
        print(f"Using authenticator: {authenticator}")
    
    conn = snowflake.connector.connect(**conn_params)
    print("Connected!")
    return conn


def stream_batch(cursor, events: list[dict]):
    """Insert a batch of events using an existing cursor."""
    for event in events:
        cursor.execute(
            f"""
            INSERT INTO {SNOWFLAKE_TABLE} (VEHICLE_ID, EVENT_TIMESTAMP, TELEMETRY_DATA)
            SELECT 
                %s,
                %s::TIMESTAMP_NTZ,
                PARSE_JSON(%s)
            """,
            (event["VEHICLE_ID"], event["EVENT_TIMESTAMP"], event["TELEMETRY_DATA"])
        )


def main():
    """Main function to run the streaming simulation."""
    global running
    
    print("=" * 60)
    print("Snowflake Iceberg V3 - Streaming Telemetry Simulator")
    print("=" * 60)
    print(f"Account: {SNOWFLAKE_ACCOUNT}")
    print(f"Database: {SNOWFLAKE_DATABASE}")
    print(f"Table: {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")
    print(f"Vehicles: {VEHICLE_COUNT}")
    print(f"Events/second: {EVENTS_PER_SECOND}")
    print(f"Max duration: {MAX_DURATION_SECONDS} seconds")
    print("-" * 60)
    print("Press Ctrl+C to stop streaming")
    print("-" * 60)
    
    if not CONNECTOR_AVAILABLE:
        print("ERROR: snowflake-connector-python is not installed.")
        print("Please run: pip install snowflake-connector-python")
        sys.exit(1)
    
    # Create a single connection (reused for all batches)
    conn = create_connection()
    cursor = conn.cursor()
    
    # Create vehicle fleet
    print(f"\nInitializing {VEHICLE_COUNT} vehicles...")
    vehicles = create_vehicle_fleet(VEHICLE_COUNT)
    print("Fleet initialized!")
    
    # Streaming loop
    start_time = time.time()
    total_events = 0
    batch = []
    
    print("\nStarting streaming...\n")
    
    try:
        while running and (time.time() - start_time) < MAX_DURATION_SECONDS:
            # Select random vehicles to generate events
            selected_vehicles = random.sample(vehicles, min(BATCH_SIZE, len(vehicles)))
            
            for vehicle in selected_vehicles:
                # Update vehicle state
                vehicle = update_vehicle_state(vehicle)
                
                # Generate event
                event = generate_telemetry_event(vehicle)
                batch.append(event)
            
            # Send batch when full
            if len(batch) >= BATCH_SIZE:
                try:
                    stream_batch(cursor, batch)
                    conn.commit()
                    total_events += len(batch)
                    
                    # Progress indicator
                    elapsed = time.time() - start_time
                    rate = total_events / elapsed if elapsed > 0 else 0
                    print(f"\rEvents streamed: {total_events:,} | "
                          f"Rate: {rate:.1f}/sec | "
                          f"Elapsed: {elapsed:.0f}s", end="", flush=True)
                    
                    batch = []
                except Exception as e:
                    print(f"\nError streaming batch: {e}")
                    # Keep trying
            
            # Control rate
            time.sleep(1 / EVENTS_PER_SECOND)
    
    except KeyboardInterrupt:
        pass
    
    # Capture end time for lineage
    stream_end_time = datetime.now(timezone.utc)
    stream_start_time = datetime.fromtimestamp(start_time, tz=timezone.utc)
    
    # Send external lineage event (before closing connection)
    if total_events > 0:
        send_external_lineage(conn, total_events, stream_start_time, stream_end_time)
    
    # Clean up connection
    cursor.close()
    conn.close()
    
    # Final stats
    elapsed = time.time() - start_time
    print(f"\n\n{'=' * 60}")
    print("Streaming Complete!")
    print(f"{'=' * 60}")
    print(f"Total events streamed: {total_events:,}")
    print(f"Total time: {elapsed:.1f} seconds")
    if elapsed > 0:
        print(f"Average rate: {total_events / elapsed:.1f} events/second")
    print(f"\nQuery your data:")
    print(f"  SELECT * FROM {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE} LIMIT 10;")
    print(f"\nView lineage in Snowsight:")
    print(f"  Catalog » Database Explorer » {SNOWFLAKE_DATABASE} » {SNOWFLAKE_SCHEMA} » {SNOWFLAKE_TABLE} » Lineage tab")


if __name__ == "__main__":
    main()
