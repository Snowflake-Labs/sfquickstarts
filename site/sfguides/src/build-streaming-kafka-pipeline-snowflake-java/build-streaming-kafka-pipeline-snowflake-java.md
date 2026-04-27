author: Vino Duraisamy, Praveen Gattu
id: build-streaming-kafka-pipeline-snowflake-java
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/ai
language: en
summary: Build a production-grade Kafka-to-Snowflake streaming pipeline using the Snowpipe Streaming Java SDK, then layer on ML forecasting and natural language analytics with Cortex Analyst.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues


# Build a Kafka-to-Snowflake Streaming Pipeline with the Java SDK
<!-- ------------------------ -->
## Overview

Most Kafka-to-Snowflake tutorials use a managed connector. This guide skips the connector and shows you how to build the consumer yourself using the [Snowpipe Streaming SDK](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview) — giving you full control over batching, error handling, retry logic, and offset tracking.

The use case: a telecom cell tower monitoring pipeline. A fake producer generates Call Detail Records (CDRs) into Kafka. A custom Java consumer reads them and streams each record directly into Snowflake using the Snowpipe Streaming SDK's `appendRow` API. Once data is flowing, you train three ML forecast models in pure SQL and create a Semantic View so you can ask questions like "Which towers will have the highest call drop rate this week?" in natural language.

### What You Will Learn

- How Snowpipe Streaming channels and offset tokens work
- How to map Kafka partitions to Snowflake channels with a `ConsumerRebalanceListener`
- How to commit Kafka offsets only after Snowflake confirms persistence
- How to handle retries, backpressure, and channel invalidation with production-grade error handling (exponential backoff, HTTP 409 channel reopening, fail-fast on auth errors)
- Best practices for writing robust Snowpipe Streaming consumers: channel-per-partition mapping, durable offset commits, and graceful error recovery
- How to train `SNOWFLAKE.ML.FORECAST` models in SQL
- How to create a Semantic View and query it with Cortex Analyst
- How to automate the entire pipeline with Cortex Code skills

### What You Will Build

- A multi-threaded Java consumer that streams CDRs from Kafka into Snowflake
- An interactive fake producer for generating test CDR data
- Three ML forecast models for tower analytics
- A Semantic View with natural language query support via Cortex Analyst

### What is Cortex Code?

Cortex Code is Snowflake's CLI-based AI coding assistant. It understands Snowflake APIs, SQL, and Java and can execute multi-step workflows through skills. This guide includes a Cortex Code skill that automates the entire pipeline setup — from Kafka startup to ML forecasting — with a single prompt. You can follow the manual steps below to learn how everything works, then use the skill to replicate (or extend) the pipeline instantly.

### Prerequisites

- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with `ACCOUNTADMIN` privileges
- Java 17 or higher
- Maven 3.8 or higher
- Homebrew (macOS) for running Kafka locally, or an existing Kafka broker
- OpenSSL (included on macOS and most Linux distributions)
- Basic familiarity with Java and SQL

> **Prefer the fast path?** If you have [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) installed, skip ahead to [Automate With Cortex Code](#automate-with-cortex-code) and type `CDR demo`. It handles Kafka setup, Snowflake objects, config, build, and ML forecasting automatically.

<!-- ------------------------ -->
## Automate With Cortex Code

Everything you do manually in this guide can be fully automated with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) — Snowflake's CLI-based AI coding assistant. A Cortex Code skill bundled with the demo repo handles the entire pipeline for you, from Kafka topic creation to ML forecast results.

### Install the Skill

The skill lives in the [snowpipe-streaming-sdk-examples](https://github.com/snowflakedb/snowpipe-streaming-sdk-examples) repository. Clone the repo and copy the skill into your Cortex Code skills folder:

```bash
git clone https://github.com/snowflakedb/snowpipe-streaming-sdk-examples.git
mkdir -p ~/.snowflake/cortex/skills
cp -r snowpipe-streaming-sdk-examples/custom-kafka-consumer/.cortex/skills/custom-kafka-consumer \
      ~/.snowflake/cortex/skills/
```

The skill is automatically discovered by Cortex Code on the next session. Skills are loaded from `~/.snowflake/cortex/skills/` globally — the skill directory itself can live anywhere. However, **start Cortex Code from the `custom-kafka-consumer` project root** so the skill can work with the project files, run Maven builds, and locate the Kafka scripts it needs.

### Available Triggers

| Trigger Phrase | What It Does |
|---|---|
| `CDR demo` | Runs the full pipeline end-to-end |
| `kafka snowflake` | Same — sets up Kafka, Snowflake objects, config, and starts the pipeline |
| `kafka to snowflake` | Same — useful if you describe the goal naturally |
| `custom consumer` | Steps through the consumer setup interactively |
| `snowpipe streaming kafka` | Same — SDK-focused framing |

### Example Prompts

Start a Cortex Code session in the `custom-kafka-consumer` directory and try any of these:

```
CDR demo
```

```
kafka to snowflake
```

```
set up the kafka consumer and stream some CDR data
```

```
run the streaming ingest kafka demo
```

Each prompt confirms your intent before creating any resources and asks for your preferences (database name, schema, topic, etc.).

### What Gets Automated

Here is how the skill maps to the steps you complete manually in this guide:

| Manual Step | What the Skill Does |
|---|---|
| Install and start Kafka | Checks if Kafka is installed, starts broker, creates topic with 3 partitions |
| Create Snowflake Objects | Executes `CREATE DATABASE`, `SCHEMA`, and `CALL_DETAIL_RECORDS` table |
| Configure properties files | Prompts for your values and writes both `.properties` files |
| Build the project | Runs `mvn clean compile` and handles Java/Maven version errors |
| Run consumer + producer | Opens instructions for both terminals, starts streaming at 20 rec/sec |
| Verify data | Runs `SELECT COUNT(*)` and a sample query to confirm records arrived |
| Train ML Forecast models | Creates aggregation views and trains `tower_drop_forecast` model |
| Identify at-risk towers | Runs the maintenance recommendation query and surfaces CRITICAL towers |

The following sections walk through each of these steps manually. The manual walkthrough is intentional — it explains how every part of the pipeline works so you can customize, debug, and extend it. The skill automates these exact steps, but reading through them once gives you the understanding you need to troubleshoot or adapt the pipeline for your own use case.

<!-- ------------------------ -->
## Set Up Snowflake

### Create Database Objects

Connect to your Snowflake account and run the following SQL to create the database, schema, and landing table for CDR records.

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS CDR_STREAMING_DB;
CREATE SCHEMA IF NOT EXISTS CDR_STREAMING_DB.TELECOM;

CREATE TABLE IF NOT EXISTS CDR_STREAMING_DB.TELECOM.CALL_DETAIL_RECORDS (
    RECORD_ID         NUMBER,
    CALLER_NUMBER     VARCHAR,
    CALLEE_NUMBER     VARCHAR,
    CALL_TYPE         VARCHAR,   -- VOICE, SMS, DATA, MMS, VOICEMAIL
    NETWORK_TYPE      VARCHAR,   -- 4G, 5G, 3G, WIFI, ROAMING
    CALL_DISPOSITION  VARCHAR,   -- ANSWERED, NO_ANSWER, BUSY, FAILED, DROPPED
    DURATION_SECONDS  NUMBER,
    DATA_USAGE_MB     NUMBER,
    AREA_CODE         VARCHAR,
    CELL_TOWER        VARCHAR,   -- e.g. LAX-001, NYC-010
    PLAN              VARCHAR,   -- BASIC, STANDARD, PREMIUM, UNLIMITED, PREPAID
    EVENT_TIMESTAMP   TIMESTAMP_NTZ,
    INGEST_TIMESTAMP  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

### Configure RSA Key-Pair Authentication

The Snowpipe Streaming SDK uses JWT for authentication. Generate an RSA key pair and register the public key with your user.

```bash
# Generate private key (2048-bit, PKCS8 format)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Extract public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Print public key content (strip header/footer for Snowflake)
cat rsa_key.pub
```

Register the public key in Snowflake:

```sql
ALTER USER <your_username> SET RSA_PUBLIC_KEY='<paste_public_key_content_here>';

-- Verify it was set
DESCRIBE USER <your_username>;
```

> **Security note**: Never commit `rsa_key.p8` or `profile.json` to version control. The repo's `.gitignore` already excludes `profile.json`.

### Create profile.json

Create `profile.json` in the project root with your Snowflake credentials:

```json
{
  "url": "https://<account_identifier>.snowflakecomputing.com",
  "account": "<account_identifier>",
  "user": "<your_username>",
  "role": "ACCOUNTADMIN",
  "warehouse": "COMPUTE_WH",
  "private_key": "<contents_of_rsa_key.p8_without_header_footer>"
}
```

Replace the `private_key` value with the raw base64 content of your `rsa_key.p8` file (everything between `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`).

<!-- ------------------------ -->
## Clone and Build

### Clone the Repository

```bash
git clone https://github.com/snowflakedb/snowpipe-streaming-sdk-examples.git
cd snowpipe-streaming-sdk-examples/custom-kafka-consumer
```

### Understand the Project Structure

```
custom-kafka-consumer/
├── consumer-config.properties   # Kafka + Snowflake target config
├── producer-config.properties   # Kafka broker + tuning config
├── profile.json                 # Snowflake credentials (gitignored)
├── pom.xml
└── src/main/java/com/snowflake/streaming/
    ├── consumer/
    │   ├── Main.java              # Entry point, launches N consumer threads
    │   ├── CustomKafkaConsumer.java  # Core consumer logic
    │   └── Config.java            # Loads consumer-config.properties
    └── producer/
        ├── FakeKafkaWriter.java   # Interactive CDR generator
        └── Config.java            # Loads producer-config.properties
```

The key dependency is the Snowpipe Streaming SDK v2:

```xml
<dependency>
    <groupId>com.snowflake</groupId>
    <artifactId>snowpipe-streaming</artifactId>
    <version>1.3.0</version>
</dependency>
```

### Configure the Consumer

Edit `consumer-config.properties`:

```properties
# Kafka
kafka.bootstrap.servers=localhost:9092
kafka.topic=cdr-topic
kafka.group.id=cdr-consumer-group
kafka.poll.duration.ms=1000

# Snowflake channel prefix
snowflake.channel.name=CDR_CHANNEL
snowflake.database=CDR_STREAMING_DB
snowflake.schema=TELECOM
snowflake.table=CALL_DETAIL_RECORDS

# Path to Snowflake profile JSON
snowflake.profile.path=profile.json

# Consumer tuning
max.rows.per.append=100
consumer.thread.count=3
```

### Build

```bash
mvn clean compile
```

<!-- ------------------------ -->
## Start Kafka

Install and start a local Kafka broker with Homebrew. If you have an existing broker, skip to [Set Up the Topic](#set-up-the-topic).

```bash
brew install kafka
brew services start kafka
```

### Set Up the Topic

Create a topic with 3 partitions (matching `consumer.thread.count=3`):

```bash
kafka-topics.sh --create \
  --topic cdr-topic \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092
```

Verify:

```bash
kafka-topics.sh --describe --topic cdr-topic --bootstrap-server localhost:9092
```

<!-- ------------------------ -->
## How the Consumer Works

Before running, it helps to understand the three core patterns in `CustomKafkaConsumer.java`.

### 1:1 Partition-to-Channel Mapping

Each Kafka partition maps to exactly one Snowflake channel. The `ConsumerRebalanceListener` manages this lifecycle — opening channels when partitions are assigned and closing them on revoke:

```java
consumer.subscribe(List.of(kafkaTopicName), new ConsumerRebalanceListener() {
    @Override
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        for (TopicPartition tp : partitions) {
            String channelName = sfChannelPrefix + "_P" + tp.partition();
            OpenChannelResult result = sfClient.openChannel(channelName);
            SnowflakeStreamingIngestChannel channel = result.getChannel();
            partitionChannels.put(tp.partition(), channel);

            // Resume from where Snowflake last confirmed
            String lastToken = channel.getLatestCommittedOffsetToken();
            if (lastToken != null) {
                long offset = Long.parseLong(lastToken);
                consumer.seek(tp, offset + 1);
            }
        }
    }

    @Override
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        for (TopicPartition tp : partitions) {
            SnowflakeStreamingIngestChannel channel = partitionChannels.remove(tp.partition());
            if (channel != null && !channel.isClosed()) {
                channel.close(true, Duration.ofSeconds(30));
            }
        }
    }
});
```

On startup or rebalance, the consumer calls `getLatestCommittedOffsetToken()` on the channel. If Snowflake already persisted some records from a previous run, it seeks Kafka forward to `lastToken + 1` — preventing duplicate ingestion.

### Smart Offset Commits

Kafka offsets are committed **only after Snowflake confirms** the records are persisted:

```java
private void commitKafkaOffsetsAfterSnowflakeConfirm() {
    Map<TopicPartition, OffsetAndMetadata> toCommit = new HashMap<>();
    for (Map.Entry<Integer, SnowflakeStreamingIngestChannel> entry : partitionChannels.entrySet()) {
        int partition = entry.getKey();
        SnowflakeStreamingIngestChannel channel = entry.getValue();
        String token = channel.getLatestCommittedOffsetToken();
        if (token != null && !token.equals(lastCommittedTokens.get(partition))) {
            long offset = Long.parseLong(token);
            toCommit.put(new TopicPartition(kafkaTopicName, partition),
                         new OffsetAndMetadata(offset + 1));
            lastCommittedTokens.put(partition, token);
        }
    }
    if (!toCommit.isEmpty()) {
        consumer.commitSync(toCommit);
    }
}
```

This is what gives the pipeline exactly-once delivery semantics from Kafka's perspective.

### Retry Logic

The consumer handles transient errors with exponential backoff and jitter:

| HTTP Status | Behavior |
|-------------|----------|
| 401 / 403 | Fail-fast — authorization issue, no retry |
| 409 | Channel invalidated — reopen and continue |
| 429 / 5xx | Exponential backoff with jitter, no retry limit |
| 408 | Retryable, up to 10 attempts |

<!-- ------------------------ -->
## Run the Pipeline

Open two terminal windows.

### Terminal 1 — Start the Consumer

```bash
cd snowpipe-streaming-sdk-examples/custom-kafka-consumer
mvn compile exec:java -Dexec.mainClass="com.snowflake.streaming.consumer.Main"
```

You should see logs like:

```
INFO  Main - Starting 3 consumer thread(s). Topic=cdr-topic, Group=cdr-consumer-group
INFO  CustomKafkaConsumer - Opened channel 'CDR_CHANNEL_P0' for partition 0. Last committed offset: null
INFO  CustomKafkaConsumer - Opened channel 'CDR_CHANNEL_P1' for partition 1. Last committed offset: null
INFO  CustomKafkaConsumer - Opened channel 'CDR_CHANNEL_P2' for partition 2. Last committed offset: null
```

### Terminal 2 — Start the Producer

```bash
cd snowpipe-streaming-sdk-examples/custom-kafka-consumer
mvn compile exec:java -Dexec.mainClass="com.snowflake.streaming.producer.FakeKafkaWriter"
```

You will see an interactive menu:

```
=== Fake Kafka Writer — Mobile CDR Generator ===
  Topic: cdr-topic

Commands:
  1 | single             Send one call record
  2 | burst [count]      Send a burst of CDRs (default 100)
  3 | stream [rps]       Continuous CDR stream (default 10/sec, Enter to stop)
  4 | malformed          Send malformed JSON messages
  5 | nulls              Send CDRs with null / missing fields
  6 | custom [json]      Send a custom JSON payload
```

Send a burst of 500 records to start:

```
> burst 500
Sent 500 CDRs in 312 ms (1603 rec/sec)
```

Then start a continuous stream at 20 records/sec:

```
> stream 20
Streaming CDRs at ~20 rec/sec. Press Enter to stop...
```

### Verify Data in Snowflake

While the stream is running, check the table in Snowflake:

```sql
SELECT COUNT(*) FROM CDR_STREAMING_DB.TELECOM.CALL_DETAIL_RECORDS;

SELECT CELL_TOWER, CALL_DISPOSITION, COUNT(*) AS RECORD_COUNT
FROM CDR_STREAMING_DB.TELECOM.CALL_DETAIL_RECORDS
GROUP BY 1, 2
ORDER BY 1, 2;
```

Records should be appearing within a few seconds of being produced.

### Test Fault Tolerance

Stop the consumer (`Ctrl+C`), send more records from the producer, then restart the consumer. Observe in the logs:

```
INFO  CustomKafkaConsumer - Opened channel 'CDR_CHANNEL_P0'. Last committed offset: 499
INFO  CustomKafkaConsumer - Seeked partition 0 to offset 500
```

The consumer resumes exactly where it left off — no data loss, no duplicates.

<!-- ------------------------ -->
## Train ML Forecast Models

With CDR data flowing, you can train forecast models directly in Snowflake SQL. No Python, no external ML platform.

Snowflake ML `FORECAST` is a supervised time-series model that predicts future values from historical data. You train it with a query that returns `(timestamp, value)` — or `(timestamp, group, value)` for multi-series forecasts.

### Create Training Views

First, aggregate CDR data into daily metrics per tower:

```sql
USE DATABASE CDR_STREAMING_DB;
USE SCHEMA TELECOM;

-- Daily call volume per tower
CREATE OR REPLACE VIEW V_DAILY_CALL_VOLUME AS
SELECT
    DATE_TRUNC('DAY', EVENT_TIMESTAMP)::TIMESTAMP_NTZ AS EVENT_DATE,
    CELL_TOWER,
    COUNT(*) AS CALL_COUNT
FROM CALL_DETAIL_RECORDS
WHERE EVENT_TIMESTAMP IS NOT NULL
GROUP BY 1, 2;

-- Daily call drop rate per tower
CREATE OR REPLACE VIEW V_DAILY_CALL_DROP_RATE AS
SELECT
    DATE_TRUNC('DAY', EVENT_TIMESTAMP)::TIMESTAMP_NTZ AS EVENT_DATE,
    CELL_TOWER,
    ROUND(
        SUM(CASE WHEN CALL_DISPOSITION = 'DROPPED' THEN 1 ELSE 0 END)::FLOAT
        / NULLIF(COUNT(*), 0),
        4
    ) AS DROP_RATE
FROM CALL_DETAIL_RECORDS
WHERE EVENT_TIMESTAMP IS NOT NULL
GROUP BY 1, 2;

-- Daily data usage per tower (sum of DATA call durations as proxy for MB)
CREATE OR REPLACE VIEW V_DAILY_DATA_USAGE AS
SELECT
    DATE_TRUNC('DAY', EVENT_TIMESTAMP)::TIMESTAMP_NTZ AS EVENT_DATE,
    CELL_TOWER,
    SUM(COALESCE(DATA_USAGE_MB, 0)) AS TOTAL_DATA_MB
FROM CALL_DETAIL_RECORDS
WHERE EVENT_TIMESTAMP IS NOT NULL
  AND CALL_TYPE = 'DATA'
GROUP BY 1, 2;
```

### Train the Forecast Models

```sql
-- Model 1: Call volume forecast
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST CALL_VOLUME_FORECAST(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'V_DAILY_CALL_VOLUME'),
    SERIES_COLNAME => 'CELL_TOWER',
    TIMESTAMP_COLNAME => 'EVENT_DATE',
    TARGET_COLNAME => 'CALL_COUNT'
);

-- Model 2: Call drop rate forecast
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST CALL_DROP_RATE_FORECAST(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'V_DAILY_CALL_DROP_RATE'),
    SERIES_COLNAME => 'CELL_TOWER',
    TIMESTAMP_COLNAME => 'EVENT_DATE',
    TARGET_COLNAME => 'DROP_RATE'
);

-- Model 3: Data usage forecast
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST DATA_USAGE_FORECAST(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'V_DAILY_DATA_USAGE'),
    SERIES_COLNAME => 'CELL_TOWER',
    TIMESTAMP_COLNAME => 'EVENT_DATE',
    TARGET_COLNAME => 'TOTAL_DATA_MB'
);
```

Training runs asynchronously. Each `CREATE` statement completes when the model is ready.

### Generate Forecasts

Generate predictions for the next 7 days:

```sql
-- Forecast call volume for next 7 days
CALL CALL_VOLUME_FORECAST!FORECAST(
    FORECASTING_PERIODS => 7,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

-- Forecast call drop rates
CALL CALL_DROP_RATE_FORECAST!FORECAST(
    FORECASTING_PERIODS => 7,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

-- Forecast data usage
CALL DATA_USAGE_FORECAST!FORECAST(
    FORECASTING_PERIODS => 7,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);
```

Each call returns a result set with columns: `SERIES`, `TS`, `FORECAST`, `LOWER_BOUND`, `UPPER_BOUND`.

### Save Forecast Results

Save the predictions to tables for downstream analysis:

```sql
CREATE OR REPLACE TABLE CALL_VOLUME_PREDICTIONS AS
    SELECT * FROM TABLE(
        CALL_VOLUME_FORECAST!FORECAST(FORECASTING_PERIODS => 7)
    );

CREATE OR REPLACE TABLE CALL_DROP_RATE_PREDICTIONS AS
    SELECT * FROM TABLE(
        CALL_DROP_RATE_FORECAST!FORECAST(FORECASTING_PERIODS => 7)
    );

CREATE OR REPLACE TABLE DATA_USAGE_PREDICTIONS AS
    SELECT * FROM TABLE(
        DATA_USAGE_FORECAST!FORECAST(FORECASTING_PERIODS => 7)
    );
```

### Identify At-Risk Towers

Find towers with the highest predicted call drop rates:

```sql
SELECT
    SERIES AS CELL_TOWER,
    ROUND(AVG(FORECAST), 4) AS AVG_PREDICTED_DROP_RATE,
    ROUND(MAX(FORECAST), 4) AS PEAK_PREDICTED_DROP_RATE,
    COUNT(*) AS FORECAST_DAYS
FROM CALL_DROP_RATE_PREDICTIONS
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```

<!-- ------------------------ -->
## Query with Cortex Analyst

A Semantic View lets you describe your data in business terms so [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/overview) can translate natural language questions into SQL.

### Create the Semantic View

```sql
CREATE OR REPLACE SEMANTIC VIEW CDR_STREAMING_DB.TELECOM.TOWER_ANALYTICS_SV
  TABLES (
    CDR_STREAMING_DB.TELECOM.CALL_DETAIL_RECORDS AS CDR
      PRIMARY KEY (RECORD_ID)
      WITH SYNONYMS ('call records', 'CDR', 'call data'),
    CDR_STREAMING_DB.TELECOM.CALL_DROP_RATE_PREDICTIONS AS DROP_FORECAST
      WITH SYNONYMS ('drop rate forecast', 'predicted drop rates'),
    CDR_STREAMING_DB.TELECOM.CALL_VOLUME_PREDICTIONS AS VOLUME_FORECAST
      WITH SYNONYMS ('call volume forecast', 'predicted call volumes'),
    CDR_STREAMING_DB.TELECOM.DATA_USAGE_PREDICTIONS AS USAGE_FORECAST
      WITH SYNONYMS ('data usage forecast', 'predicted data usage')
  )
  RELATIONSHIPS (
    DROP_FORECAST (SERIES) REFERENCES CDR (CELL_TOWER),
    VOLUME_FORECAST (SERIES) REFERENCES CDR (CELL_TOWER),
    USAGE_FORECAST (SERIES) REFERENCES CDR (CELL_TOWER)
  )
  FACTS (
    CDR.DURATION_SECONDS WITH SYNONYMS ('call duration', 'duration in seconds'),
    CDR.DATA_USAGE_MB WITH SYNONYMS ('data usage', 'megabytes used'),
    DROP_FORECAST.FORECAST AS PREDICTED_DROP_RATE
      WITH SYNONYMS ('predicted drop rate', 'forecasted call drops'),
    VOLUME_FORECAST.FORECAST AS PREDICTED_CALL_VOLUME
      WITH SYNONYMS ('predicted call volume', 'forecasted call count'),
    USAGE_FORECAST.FORECAST AS PREDICTED_DATA_USAGE_MB
      WITH SYNONYMS ('predicted data usage', 'forecasted bandwidth')
  )
  DIMENSIONS (
    CDR.CELL_TOWER WITH SYNONYMS ('tower', 'cell tower', 'tower ID'),
    CDR.CALL_TYPE WITH SYNONYMS ('type of call'),
    CDR.NETWORK_TYPE WITH SYNONYMS ('network', '4G', '5G'),
    CDR.CALL_DISPOSITION WITH SYNONYMS ('call result', 'dropped', 'answered'),
    CDR.AREA_CODE WITH SYNONYMS ('area', 'region'),
    CDR.PLAN WITH SYNONYMS ('subscriber plan', 'service plan'),
    CDR.EVENT_TIMESTAMP WITH SYNONYMS ('call time', 'when')
  )
  METRICS (
    METRIC TOTAL_CALLS AS COUNT(CDR.RECORD_ID)
      WITH SYNONYMS ('total calls', 'call count'),
    METRIC CALL_DROP_RATE AS
      SUM(CASE WHEN CDR.CALL_DISPOSITION = 'DROPPED' THEN 1 ELSE 0 END)::FLOAT
      / NULLIF(COUNT(CDR.RECORD_ID), 0)
      WITH SYNONYMS ('drop rate', 'percentage dropped'),
    METRIC AVG_CALL_DURATION AS AVG(CDR.DURATION_SECONDS)
      WITH SYNONYMS ('average duration', 'mean call length'),
    METRIC TOTAL_DATA_USAGE_MB AS SUM(CDR.DATA_USAGE_MB)
      WITH SYNONYMS ('total data usage', 'total MB')
  );
```

### Use Cortex Analyst in Snowsight

1. In Snowsight, navigate to **AI & ML** > **Cortex Analyst**
2. Select the semantic view `CDR_STREAMING_DB.TELECOM.TOWER_ANALYTICS_SV`
3. Ask questions in natural language:

```
What cell towers will have the highest call drop rate in the next 7 days?

Which towers are most at risk and need maintenance?

What is the forecasted data usage per tower this week?

Show me call volume by network type for the LAX towers.

Which plan type has the most dropped calls?
```

Cortex Analyst translates each question into SQL against the semantic view and returns both the query and the results.

### Use Cortex Analyst via API

You can also query programmatically with the REST API:

```bash
curl -X POST \
  "https://<account_identifier>.snowflakecomputing.com/api/v2/cortex/analyst/message" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Which towers will have the highest call drop rate this week?"
          }
        ]
      }
    ],
    "semantic_view": "CDR_STREAMING_DB.TELECOM.TOWER_ANALYTICS_SV"
  }'
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a production-grade Kafka-to-Snowflake streaming pipeline using the Java SDK, with ML forecasting and natural language analytics on top.

You went from raw Kafka records to a queryable AI-powered analytics layer — all within Snowflake, without any external ML infrastructure.

### What You Learned

- How to map Kafka partitions to Snowflake channels using a `ConsumerRebalanceListener`
- How offset tokens enable resume-without-loss semantics across consumer restarts
- How to implement retry logic with exponential backoff for Snowpipe Streaming errors
- How to train multi-series ML forecast models in pure SQL with `SNOWFLAKE.ML.FORECAST`
- How to create a Semantic View and use Cortex Analyst for natural language queries

### Related Resources

Documentation:
- [Snowpipe Streaming Overview](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)
- [Snowpipe Streaming Java SDK Reference](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-java-sdk)
- [SNOWFLAKE.ML.FORECAST](https://docs.snowflake.com/en/user-guide/ml-functions/forecasting)
- [Cortex Analyst Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/overview)
- [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)

Source Code:
- [custom-kafka-consumer on GitHub](https://github.com/snowflakedb/snowpipe-streaming-sdk-examples/tree/main/custom-kafka-consumer)

Related Guides:
- [Getting Started with Snowpipe Streaming high-performance architecture and Cortex Code](https://quickstarts.snowflake.com/guide/getting-started-with-snowpipe-streaming-v2)
- [Getting Started with Snowpipe Streaming on AWS MSK](https://quickstarts.snowflake.com/guide/getting-started-with-snowpipe-streaming-aws-msk)
