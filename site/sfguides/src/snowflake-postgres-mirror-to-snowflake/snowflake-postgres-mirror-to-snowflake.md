author: Elizabeth Christensen
id: snowflake-postgres-mirror-to-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to replicate Snowflake Postgres tables to Snowflake for analytics using a mirror
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Postgres

# Mirror Data from Snowflake Postgres to Snowflake
<!-- ------------------------ -->

>**Note:
>Postgres Mirror features are in preview and under rapid development. Some features may not be available.**<br>

If you have operational data in Snowflake Postgres, you can use **Postgres Mirror** to automatically replicate tables into Snowflake for analytics. Mirror uses change data capture (CDC) under the hood to keep Snowflake tables in sync with Postgres — no ETL pipelines, no external tooling, and no manual data movement.

In this quickstart, you will create an operational Postgres database with a simple IoT schema, set up Postgres Mirror to replicate those tables into Snowflake, and verify that new data flows through automatically.

### What You Will Build
- A Snowflake Postgres instance with an operational IoT database (devices, sensors, and readings)
- A Postgres Mirror that replicates selected tables into Snowflake on a schedule
- An end-to-end sync pipeline that picks up new rows automatically

### What You Will Learn
- How to create and connect to a Snowflake Postgres instance
- How to configure grants required for Postgres Mirror replication
- How to enable the required extensions (`pg_lake` and `snowflake_cdc`)
- How to create a mirror using SQL or the Snowflake UI
- How to verify data replication and monitor ongoing sync

### Prerequisites
- Access to a Snowflake account with Snowflake Postgres enabled
- A SQL client capable of connecting to Postgres (e.g., `psql`)

<!-- ------------------------ -->
## Create a Postgres Instance

Start by creating a new Snowflake Postgres instance. You will need the instance name in a later step when creating the mirror.

### Create the Instance
Create a new Snowflake Postgres instance from the Snowflake UI or SQL. If this is your first time, follow the [Getting Started with Snowflake Postgres](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/) guide for detailed instructions. Copy and save the **instance name** — you will need it when setting up the mirror.

### Connect to the Instance
Connect to your Snowflake Postgres instance using `psql` or your preferred SQL client:

```bash
psql postgres://<user>:<password>@<instance-host>:5432/postgres
```

### Existing instances

If you already have an instance created prior to the mirroring feature, you will need to do an instance refresh from the Postgres -- Manage options. 

<!-- ------------------------ -->
## Set Up Grants for Replication

Before creating a mirror, you need to grant the required permissions in Snowflake. This grant allow the Snowflake application to administer mirrors and access your Postgres instance.

Run the following in **Snowflake**:

```sql
GRANT USAGE ON POSTGRES INSTANCE "my-instance" TO APPLICATION snowflake;
```

Replace `"my-instance"` with the name of your Postgres instance.

<!-- ------------------------ -->
## Create Postgres Tables

Now switch to your **Postgres** connection. Create a simple IoT schema with three related tables: devices, sensors, and readings.

```sql
CREATE TABLE devices (
    device_id SERIAL PRIMARY KEY,
    device_name TEXT NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sensors (
    sensor_id SERIAL PRIMARY KEY,
    device_id INT REFERENCES devices(device_id),
    sensor_type TEXT NOT NULL, -- e.g., 'Temperature', 'Humidity'
    unit TEXT
);

CREATE TABLE readings (
    reading_id SERIAL PRIMARY KEY,
    sensor_id INT REFERENCES sensors(sensor_id),
    value NUMERIC(10, 2),
    ts TIMESTAMP DEFAULT NOW()
);
```

### Seed Sample Data
Populate the tables with sample IoT data — 5 devices, 2 sensors per device, and 485 sensor readings spread over the past several hours.

```sql
-- 2. Insert 5 Devices
INSERT INTO devices (device_name, location)
SELECT 
    'IoT-Gateway-' || i,
    CASE WHEN i % 2 = 0 THEN 'Warehouse-A' ELSE 'Loading-Dock' END
FROM generate_series(1, 5) AS i;

-- 3. Insert 10 Sensors (2 for each device)
INSERT INTO sensors (device_id, sensor_type, unit)
SELECT 
    d.device_id,
    s.type,
    CASE WHEN s.type = 'Temperature' THEN 'Celsius' ELSE 'Percent' END
FROM devices d
CROSS JOIN (SELECT unnest(ARRAY['Temperature', 'Humidity']) AS type) AS s;

-- 4. Insert 485 Readings
INSERT INTO readings (sensor_id, value, ts)
SELECT 
    (sample_id % 10) + 1, -- Cycles through the 10 sensors
    (random() * 40 + 10)::numeric(10,2), -- Generates a value between 10 and 50
    NOW() - (sample_id || ' minutes')::interval -- Offsets time into the past
FROM generate_series(1, 485) AS sample_id;
```

### Verify the Data
Confirm the data was inserted:

```sql
select COUNT(*) from readings;
```

You should see 485 rows.

<!-- ------------------------ -->
## Enable Extensions and Create the Mirror

### Enable Extensions
Install `pg_lake` and `snowflake_cdc` on your Postgres instance. These extensions provide the change data capture and object storage capabilities that Postgres Mirror relies on.

```sql
CREATE EXTENSION snowflake_cdc CASCADE;
```

### Create the Mirror via SQL
You can create a mirror using the `snowflake.postgres.create_mirror` procedure. This tells Snowflake which Postgres tables to replicate and how often to sync.

> **Note:** The target database in Snowflake must not already exist — the mirror will create it automatically.

```sql
CALL snowflake.postgres.create_mirror(
    mirror_name         => 'orders_mirror',
    postgres_instance   => 'mirror-test-sql',
    postgres_database   => 'postgres',
    target_database     => 'POSTGRESMIRRORTOSNOWFLAKE',
    postgres_tables     => ['public.devices', 'public.sensors', 'public.readings'],
    postgres_schemas    => NULL,
    refresh_interval    => '1 minute'
);
```

Replace `postgres_instance` with your instance. Mirror name and target database are names you choose. 

### Create the Mirror via UI
You can also create a mirror from the Snowflake UI. Navigate to your Postgres instance and select **Manage** to configure mirroring.

![Postgres Mirror Creation Screen](assets/postgres-mirror-creation-screen.png)

There is also a Mirroring tab on the Postgres landing page . This may take a few minutes to refresh after your initial mirror creation, you can do a hard refresh.

<!-- ------------------------ -->
## Confirm Data in Snowflake

Once the mirror is created and the initial sync completes, switch to **Snowflake** and verify that the data has arrived.

```sql
SELECT COUNT(*) FROM POSTGRESMIRRORTOSNOWFLAKE.PUBLIC.READINGS;
```

You should see 485 rows, matching the count from Postgres.

<!-- ------------------------ -->
## Add More Data and Monitor Sync

Now test that ongoing changes replicate automatically. Switch back to **Postgres** and insert 500 additional readings with varied sensor data spread over the last 24 hours.

```sql
-- Insert 500 additional readings with varied logic
INSERT INTO readings (sensor_id, value, ts)
SELECT 
    s.sensor_id,
    CASE 
        WHEN s.sensor_type = 'Temperature' THEN (20 + (random() * 15))::numeric(10,2) -- Temp: 20-35°C
        ELSE (40 + (random() * 50))::numeric(10,2)                                -- Humidity: 40-90%
    END as value,
    -- Spreads the data over the last 24 hours
    NOW() - (random() * (24 * 60) * '1 minute'::interval) as ts
FROM sensors s
CROSS JOIN generate_series(1, 50) -- 10 sensors * 50 iterations = 500 rows
ORDER BY random();
```

### Verify in Postgres
Confirm the new total in Postgres:

```sql
select COUNT(*) from readings;
```

You should see 985 rows (485 original + 500 new).

### Verify in Snowflake
Wait about a minute for the mirror to sync, then check the count in Snowflake:

```sql
SELECT COUNT(*) FROM POSTGRESMIRRORTOSNOWFLAKE.PUBLIC.READINGS;
```

The count should match 985. From this point on, any inserts, updates, or deletes in Postgres will automatically replicate to Snowflake on the configured refresh interval.

<!-- ------------------------ -->
## Conclusion and Resources

### Congratulations!
You have successfully set up Postgres Mirror to replicate operational data from Snowflake Postgres into Snowflake — with no external ETL pipeline required. New changes in Postgres are automatically captured and synced on a schedule.

### What You Learned
- How to create a Snowflake Postgres instance and connect to it
- How to configure the grants required for Postgres Mirror
- How to enable the `pg_lake` and `snowflake_cdc` extensions
- How to create a mirror using SQL or the Snowflake UI
- How to verify initial replication and monitor ongoing sync

### Related Resources
- [Getting Started with Snowflake Postgres](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/)
- [pg_lake for Snowflake Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake)
- [Introducing pg_lake: Integrate Your Data Lakehouse with Postgres](https://www.snowflake.com/en/engineering-blog/pg-lake-postgres-lakehouse-integration/) (blog)
