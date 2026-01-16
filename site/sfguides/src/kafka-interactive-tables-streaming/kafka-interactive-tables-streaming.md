author: Brian Hess
id: kafka-interactive-tables-streaming
language: en
summary: Learn how to use Snowflake's Interactive Tables and Interactive Warehouses with real-time data from Kafka using Snowpipe Streaming v2.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/snowflake-feature/snowpipe-streaming
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Real-Time Analytics with Kafka, Interactive Tables, and Snowpipe Streaming v2

## Overview

In this quickstart, you will learn how to build a real-time data pipeline that ingests IoT sensor data from Apache Kafka into Snowflake using the new Snowpipe Streaming v2 (High-Performance Architecture). You will then use Snowflake's Interactive Tables and Interactive Warehouses to achieve low-latency queries on this streaming data.

### What You'll Learn
- How to set up Apache Kafka locally using Docker with KRaft (no Zookeeper required)
- How to create Interactive Tables optimized for low-latency queries
- How to create and configure Interactive Warehouses
- How to configure the Snowflake Kafka Connector with Snowpipe Streaming v2 to stream data from Kafka into an Interactive Table
- How to query streaming data with sub-second latency

### What You'll Need
- A Snowflake account in AWS us-west-2 region (Interactive Tables are available in select regions)
- Docker Desktop installed on your machine
- Python 3.9 or later
- Basic knowledge of Kafka and SQL

### What You'll Build
- A local Kafka environment with Kafka Connect
- A data generator that produces simulated IoT sensor data
- An Interactive Table receiving real-time data via Snowpipe Streaming v2
- An Interactive Warehouse optimized for low-latency queries

### Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────────────┐
│  Python Data    │────▶│  Apache Kafka   │────▶│  Snowflake Kafka Connector      │
│  Generator      │     │  (KRaft Mode)   │     │  (Snowpipe Streaming v2)        │
└─────────────────┘     └─────────────────┘     └───────────────┬─────────────────┘
                                                                │
                                                                ▼
                        ┌─────────────────┐     ┌─────────────────────────────────┐
                        │  Interactive    │◀────│  Interactive Table              │
                        │  Warehouse      │     │  (SENSOR_DATA)                  │
                        │  (Low Latency)  │     │                                 │
                        └─────────────────┘     └─────────────────────────────────┘
```

## Prerequisites

### Verify Docker Installation

Open a terminal and verify Docker is installed:

```bash
docker --version
docker compose version
```

### Verify Python Installation

```bash
python3 --version
```

### Install Required Python Packages

```bash
pip install kafka-python confluent-kafka
```

### Clone or Download the Assets

Download the assets from this quickstart to a local directory from this [GitHub repository](https://github.com/Snowflake-Labs/sfguide-kafka-interactive-tables-streaming). 
The assets include:
- `docker-compose.yml` - Kafka cluster configuration
- `Dockerfile.connect` - Kafka Connect with Snowflake connector
- `generate_sensor_data.py` - Script to generate continuous sensor data
- `send_message.py` - Script to send a single message
- `INTERACTIVE_TABLES_SETUP.ipynb` - Snowflake notebook for setup

## Setup Snowflake Objects

Before we start the Kafka cluster, we need to create the necessary Snowflake objects and configure authentication. All SQL commands for Snowflake setup are in the **`INTERACTIVE_TABLES_SETUP.ipynb`** notebook.

### Import and Run the Setup Notebook

1. In Snowsight, click on **Projects** → **Notebooks**
2. Click the dropdown arrow next to **+ Notebook** and select **Import .ipynb file**
3. Upload the `INTERACTIVE_TABLES_SETUP.ipynb` file from the assets folder
4. Select **Run on container** for the runtime
5. Click **Create**

### What the Notebook Creates

The notebook will guide you through creating:

- **Database and Schema**: `KAFKA_INTERACTIVE.STREAMING`
- **Kafka Connector Role**: `KAFKA_CONNECTOR_ROLE` with necessary privileges
- **Kafka User**: `KAFKA_USER` for the Kafka connector (with RSA key pair authentication)
- **Interactive Table**: `SENSOR_DATA` with clustering on `device_id` and `timestamp`
- **Interactive Warehouse**: `SENSOR_IWH` for low-latency queries

### Generate RSA Key Pair

Before running the key pair authentication section of the notebook, generate an RSA key pair in your terminal:

```bash
# Generate private key (unencrypted for simplicity in this demo)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Display the public key (you'll need this for the notebook)
cat rsa_key.pub | grep -v "BEGIN\|END" | tr -d '\n'
```

Copy the public key content (without the `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----` lines) and paste it into the notebook when prompted.

### Run Setup Cells

Run the notebook cells in **Parts 1-7** to complete the Snowflake setup. The notebook includes detailed explanations for each step.

## Setup Local Kafka Environment

The assets folder contains the Docker configuration files needed to run Kafka locally.

### Understanding the Docker Files

**`docker-compose.yml`** - Defines two services:
- **kafka**: Confluent Platform Kafka 7.6.0 running in KRaft mode (no Zookeeper required). Exposes ports 9092 (internal) and 29092 (external/host access).
- **kafka-connect**: Kafka Connect with the Snowflake connector pre-installed. Exposes port 8083 for the REST API.

**`Dockerfile.connect`** - Builds a custom Kafka Connect image that includes:
- Snowflake Kafka Connector 4.0.0-rc6
- BouncyCastle FIPS libraries for cryptographic operations

### Prepare the Environment

Navigate to the assets directory and create the required directories:

```bash
cd assets
mkdir -p keys connect-config
```

### Copy Your Private Key

Copy the RSA private key you generated earlier to the keys directory:

```bash
cp rsa_key.p8 keys/
```

### Start Kafka Cluster

```bash
docker compose up -d
```

Wait for the services to be healthy:

```bash
docker compose ps
```

You should see both `kafka` and `kafka-connect` services running.

## Create Kafka Topic

### Create the Sensor Data Topic

Use the Kafka CLI tools inside the container to create a topic:

```bash
docker exec -it kafka kafka-topics --create \
  --topic sensor_data \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### Verify Topic Creation

```bash
docker exec -it kafka kafka-topics --describe \
  --topic sensor_data \
  --bootstrap-server localhost:9092
```

You should see output showing the topic with 3 partitions. The output will look something like this:
```bash
Topic: sensor_data	TopicId: h4tQAyduQm-TD6L4qyLOew	PartitionCount: 3	ReplicationFactor: 1	Configs:
	Topic: sensor_data	Partition: 0	Leader: 1	Replicas: 1	Isr: 1
	Topic: sensor_data	Partition: 1	Leader: 1	Replicas: 1	Isr: 1
	Topic: sensor_data	Partition: 2	Leader: 1	Replicas: 1	Isr: 1
```

## Configure Kafka Connect for Snowpipe Streaming v2

### Set Environment Variables

Set your Snowflake account identifier as an environment variable. This is the part before `.snowflakecomputing.com` (e.g., `xyz12345` or `someorg-someacctname`):

```bash
export SNOWFLAKE_ACCOUNT="your-account-identifier"
```

### Deploy the Snowflake Connector

Create the connector using the Kafka Connect REST API:

```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "snowflake-sensor-data",
    "config": {
        "connector.class": "com.snowflake.kafka.connector.SnowflakeStreamingSinkConnector",
        "tasks.max": "3",
        "topics": "sensor_data",
        "snowflake.url.name": "'"${SNOWFLAKE_ACCOUNT}"'.snowflakecomputing.com",
        "snowflake.user.name": "KAFKA_USER",
        "snowflake.private.key": "'$(grep -v "BEGIN\|END" keys/rsa_key.p8 | tr -d '\n')'",
        "snowflake.database.name": "KAFKA_INTERACTIVE",
        "snowflake.schema.name": "STREAMING",
        "snowflake.role.name": "KAFKA_CONNECTOR_ROLE",
        "snowflake.ingestion.method": "SNOWPIPE_STREAMING",
        "snowflake.enable.schematization": "TRUE",
        "snowflake.topic2table.map": "sensor_data:SENSOR_DATA",
        "key.converter": "org.apache.kafka.connect.storage.StringConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "false",
        "buffer.flush.time": "10",
        "buffer.count.records": "10000",
        "buffer.size.bytes": "20000000",
        "errors.tolerance": "all",
        "errors.log.enable": "true",
        "snowflake.streaming.enable.altering.target.pipes.tables": "false",
        "snowflake.streaming.v2.enabled": "true"
    }
}'
```

### Verify Connector Status

Check that the connector is running:

```bash
curl -s http://localhost:8083/connectors/snowflake-sensor-data/status | python3 -m json.tool
```

You should see output similar to:

```json
{
    "name": "snowflake-sensor-data",
    "connector": {
        "state": "RUNNING",
        "worker_id": "kafka-connect:8083"
    },
    "tasks": [
        {
            "id": 0,
            "state": "RUNNING",
            "worker_id": "kafka-connect:8083"
        },
        {
            "id": 1,
            "state": "RUNNING",
            "worker_id": "kafka-connect:8083"
        },
        {
            "id": 2,
            "state": "RUNNING",
            "worker_id": "kafka-connect:8083"
        }
    ],
    "type": "sink"
}
```

All tasks should show `"state": "RUNNING"`.

### Troubleshooting

If the connector fails, check the logs:

```bash
docker logs kafka-connect 2>&1 | grep -i snowflake | tail -50
```

Common issues:
- **Authentication errors**: Verify the RSA key pair is correctly configured
- **Permission errors**: Ensure the KAFKA_CONNECTOR_ROLE has all necessary privileges
- **Network errors**: Verify your Snowflake account URL is correct

## Start Streaming Data

Now let's start generating sensor data and watch it flow into Snowflake.

### Python Data Generator Scripts

The assets include two Python scripts for sending data to Kafka:

- **`send_message.py`** - Sends a single sensor reading to Kafka. Accepts a JSON string as a command-line argument.
- **`generate_sensor_data.py`** - Generates random IoT sensor data continuously at a configurable rate. Simulates 20 devices across 5 buildings with 5 sensor types (temperature, humidity, pressure, CO2, and light).

### Test with a Single Message

First, send a single sensor reading to verify end-to-end connectivity:

```bash
python send_message.py '{"device_id": "DEVICE_001", "sensor_type": "temperature", "value": 23.5, "unit": "celsius", "timestamp": "2024-01-15T10:30:00Z", "location": {"building": "HQ", "floor": 2, "zone": "A"}}'
```

You should see output confirming the message was sent:

```
Message sent successfully!
  Topic: sensor_data
  Partition: 1
  Offset: 0
```

### Verify Data in Snowflake

Go back to the **`INTERACTIVE_TABLES_SETUP.ipynb`** notebook in Snowsight and run the cells in **Part 8: Querying Streaming Data**. The first query should show your test message:

```sql
USE WAREHOUSE SENSOR_IWH;

SELECT * FROM SENSOR_DATA;
```

You should see one row with your test data (it may take 5-10 seconds for the data to appear due to Snowpipe Streaming latency).

### Generate Continuous Data

Now start the data generator to send continuous sensor data. The script accepts the following arguments:

- `--duration, -d`: Duration to run in minutes (default: 1)
- `--rate, -r`: Messages per second (default: 10)

Start generating 10 messages per second for 2 minutes:

```bash
python generate_sensor_data.py --duration 2 --rate 10
```

You'll see output like:

```
Starting data generation:
  Duration: 2.0 minute(s)
  Rate: 10 messages/second
  Topic: sensor_data
Press Ctrl+C to stop early

Messages sent: 1,200 | Elapsed: 120.0s | Rate: 10.0 msg/s

Generation complete!
  Total messages sent: 1,200
  Total time: 120.0 seconds
  Average rate: 10.0 messages/second
```

### Monitor Data Flow

While the generator is running, you can monitor:

**Kafka topic offsets:**
```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group connect-snowflake-sensor-data
```

Example output:
```
GROUP                          TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
connect-snowflake-sensor-data  sensor_data     0          412             412             0
connect-snowflake-sensor-data  sensor_data     1          398             398             0
connect-snowflake-sensor-data  sensor_data     2          390             390             0
```

**Connector status:**
```bash
curl -s http://localhost:8083/connectors/snowflake-sensor-data/status | python3 -m json.tool
```

Example output:
```json
{
    "name": "snowflake-sensor-data",
    "connector": {
        "state": "RUNNING",
        "worker_id": "kafka-connect:8083"
    },
    "tasks": [
        {"id": 0, "state": "RUNNING", "worker_id": "kafka-connect:8083"},
        {"id": 1, "state": "RUNNING", "worker_id": "kafka-connect:8083"},
        {"id": 2, "state": "RUNNING", "worker_id": "kafka-connect:8083"}
    ],
    "type": "sink"
}
```

## Query Data with Interactive Warehouse

Now let's query the data using the Interactive Warehouse for low-latency results.

### Switch to Interactive Warehouse

In Snowsight or the notebook, run:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE KAFKA_INTERACTIVE;
USE SCHEMA STREAMING;

-- Switch to the Interactive Warehouse
USE WAREHOUSE SENSOR_IWH;
```

### Query Recent Sensor Data

```sql
-- Get the most recent readings
SELECT 
    device_id,
    sensor_type,
    value,
    unit,
    timestamp,
    location:building::STRING as building,
    location:floor::INTEGER as floor,
    location:zone::STRING as zone
FROM SENSOR_DATA
WHERE timestamp >= DATEADD(minute, -5, CURRENT_TIMESTAMP())
ORDER BY timestamp DESC
LIMIT 100;
```

### Aggregate Queries

```sql
-- Average readings by sensor type in last minute
SELECT 
    sensor_type,
    COUNT(*) as reading_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value
FROM SENSOR_DATA
WHERE timestamp >= DATEADD(minute, -1, CURRENT_TIMESTAMP())
GROUP BY sensor_type
ORDER BY reading_count DESC;
```

### Device Activity Dashboard Query

```sql
-- Active devices in last 30 seconds
SELECT 
    device_id,
    COUNT(*) as readings,
    MAX(timestamp) as last_reading
FROM SENSOR_DATA
WHERE timestamp >= DATEADD(second, -30, CURRENT_TIMESTAMP())
GROUP BY device_id
ORDER BY readings DESC;
```

### Compare Query Performance

Notice how queries on the Interactive Warehouse complete quickly (typically under 1 second) even while data is actively streaming in.

## Monitor and Observe

### View Streaming Channel Status

In Snowflake, you can monitor the Snowpipe Streaming channels:

```sql
SHOW CHANNELS IN SCHEMA KAFKA_INTERACTIVE.STREAMING;
```

### Check Default Pipe

With Snowpipe Streaming v2, a default pipe is automatically created:

```sql
SHOW PIPES IN SCHEMA KAFKA_INTERACTIVE.STREAMING;
```

### View Recent Ingestion Metrics

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    DATE_RANGE_START => DATEADD(hour, -1, CURRENT_TIMESTAMP()),
    DATE_RANGE_END => CURRENT_TIMESTAMP()
));
```

### Monitor Table Growth

```sql
-- Check table size and row count
SELECT 
    TABLE_NAME,
    ROW_COUNT,
    BYTES,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'SENSOR_DATA';
```

## Cleanup

When you're done with the demo, clean up the resources.

### Stop the Data Generator

Press `Ctrl+C` in the terminal where the generator is running.

### Remove Kafka Connector

```bash
curl -X DELETE http://localhost:8083/connectors/snowflake-sensor-data
```

### Stop Kafka Cluster

```bash
docker compose down -v
```

### Clean Up Snowflake Objects

Go back to the **`INTERACTIVE_TABLES_SETUP.ipynb`** notebook in Snowsight and run the cleanup cells in **Part 9: Cleanup**. This will drop all the Snowflake objects created during the demo.

## Conclusion and Resources

Congratulations! You've successfully built a real-time data pipeline using:

- **Apache Kafka** with KRaft mode (no Zookeeper)
- **Snowflake Kafka Connector** with Snowpipe Streaming v2
- **Interactive Tables** optimized for low-latency queries
- **Interactive Warehouses** providing sub-second query response

### What You Learned

- Setting up Kafka locally with Docker using the modern KRaft consensus protocol
- Configuring the Snowflake Kafka Connector for high-performance streaming
- Creating and configuring Interactive Tables and Interactive Warehouses
- Building Python data generators for IoT simulation
- Querying streaming data with consistent low latency

### Key Takeaways

1. **Snowpipe Streaming v2** provides near real-time data ingestion (5-10 second latency)
2. **Interactive Tables** are optimized for simple, selective queries with low latency
3. **Interactive Warehouses** never auto-suspend and provide consistent performance
4. The combination enables real-time dashboards and operational analytics

### Resources

- [Interactive Tables Documentation](https://docs.snowflake.com/en/user-guide/interactive)
- [Snowpipe Streaming High-Performance Architecture](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Snowflake Kafka Connector](https://docs.snowflake.com/en/user-guide/kafka-connector)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
