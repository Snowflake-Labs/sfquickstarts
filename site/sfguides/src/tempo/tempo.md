author: mando222
id: Tempo
summary: This is a guide on getting started with Tempo on Snowflake
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Security, LLGM, Intrusion Detection

# Getting Started with TEMPO (Using Sample Data)
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide will walk you through the process of setting up and using the TEMPO Native App in your Snowflake environment with provided sample data.

### What You’ll Learn 
- How to run Tempo on sample data.
- How to fine tune the model 
- How to view the output in Splunk

### What You’ll Need 
- A [SnowFlake](https://www.snowflake.com/login/) Account 
- A [Splunk](https://www.splunk.com/) Account or instance

### What You’ll Build 
- A working LLGM alerting dashboard

<!-- ------------------------ -->
## Install the TEMPO Native App
Duration: 2


1. Obtain the TEMPO native app from the Snowflake Marketplace.
2. Once installed, the app will be available for use in your Snowflake environment.
3. Grant the app privileges to create the required compute resources:

```sql
GRANT CREATE COMPUTE POOL ON ACCOUNT TO APPLICATION TEMPO;
GRANT CREATE WAREHOUSE ON ACCOUNT TO APPLICATION TEMPO;
GRANT EXECUTE TASK ON ACCOUNT TO APPLICATION TEMPO;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO APPLICATION TEMPO;
```

It’s recommended to create a dedicated warehouse for the application with the following properties:

```sql
CREATE WAREHOUSE <YOUR_WAREHOUSE_NAME> 
WAREHOUSE_TYPE = 'SNOWPARK-OPTIMIZED' 
WAREHOUSE_SIZE = 'LARGE' ; 

GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE_NAME> TO APPLICATION TEMPO;
```

The application comes with its own in-house warehouse (TEMPO_WH), which will be used for container services and live inference only.


<!-- ------------------------ -->
## Initialize the Application and Grant Permissions for Sample Data Acces
Duration: 2

Call the startup procedure to initialize the app:

```sql
CALL TEMPO.MANAGER.STARTUP();
```

Grant the TEMPO app the necessary permissions to access the sample data:

```sql
GRANT USAGE ON DATABASE tempo_sample TO APPLICATION TEMPO;
GRANT USAGE ON SCHEMA tempo_sample.inference_samples TO APPLICATION TEMPO;
GRANT USAGE ON SCHEMA tempo_sample.training_samples TO APPLICATION TEMPO;
GRANT SELECT ON ALL TABLES IN SCHEMA tempo_sample.inference_samples TO APPLICATION TEMPO;
GRANT SELECT ON ALL TABLES IN SCHEMA tempo_sample.training_samples TO APPLICATION TEMPO;
```

<!-- ------------------------ -->
## Perform Inference (TempoInference)
Duration: 2

Use the `TEMPOINFERENCE` stored procedure to perform inference on sample static log data. It takes the table's FQN (fully qualified name), a Boolean to control whether full logs or only anomalies are returned, and the log type, in this order.

```sql
CALL TEMPO.DETECTION.TEMPOINFERENCE('<TABLE_FQN>',<RETURN BOOLEAN>, '<LOG_TYPE>');
```

<TABLE_FQN>: The fully qualified name of the table for inference.

<RETURN BOOLEAN> : The Boolean value that determines if the whole table provided will be returned (True) or not (False).

<LOG_TYPE>: The type of log to use (e.g., 'workstation', 'webserver').

Example:

```sql
CALL TEMPO.DETECTION.TEMPOINFERENCE('tempo_sample.inference_samples.workstations_inference', True, 'workstation');

```sql
CALL TEMPO.DETECTION.TEMPOINFERENCE('tempo_sample.inference_samples.webservers_inference',False,'webserver');
```


<!-- ------------------------ -->
## Optional Step: Fine-Tuning Models
Duration: 2

If you need to adjust the models for better performance with your specific data patterns, you can use the fine-tuning feature. This step is optional and should be performed only if the default models don't meet your specific needs.

### Grant Permissions for Fine-Tuning

If you decide to fine-tune, you will be making use of the in-house compute pool with GPU access and the following configuration:

### Fine-Tune Models

The ideal fine-tuning sequence based on data availability is Device before Anomaly, so that the Anomaly model can use the Device outputs. To fine-tune the models, you would execute the following queries:

```sql
CALL TEMPO.FINE_TUNE.DEVICE_MODEL('<SERVICE_NAME>');
CALL TEMPO.FINE_TUNE.WORKSTATION_MODEL('<SERVICE_NAME>');
```

<SERVICE_NAME>: The tag attached to a snowflake container service for monitoring 

Example:

```sql
CALL TEMPO.FINE_TUNE.DEVICE_MODEL(‘first device model fine tuning’);
```

### Monitor Fine-Tuning Services

Check the status of fine-tuning services:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('<FINE_TUNE_SERVICE_NAME>');
```

<FINE_TUNE_SERVICE_NAME>: The name of the fine-tuning service to check.

Example:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('FINE_TUNE.sample_workstation');
```

Note: Fine-tuning can be a time-consuming process and may incur additional computational costs. Only proceed with fine-tuning if you have specific requirements that aren't met by the default models.

<!-- ------------------------ -->
## Live Inference
Duration: 2

### Setting Up Live Inference

To start live inference, you need to initialize the necessary components such as streams, tasks, and live update tables. Before that, you need to allow `change tracking` on the specific table you would like live inference on:

```sql
ALTER TABLE '<TABLE_NAME>' SET CHANGE_TRACKING = TRUE;
```

<TABLE_NAME>: The FQN of the table to enable change tracking.

### Start Live Inference

To start the live inference process, use the `START_LIVE_INFERENCE` procedure. This procedure sets up a data stream, creates a live updates table, and schedules a task that continuously monitors incoming data and applies the inference model.

```sql
CALL TEMPO.LIVE_INFERENCE.START_LIVE_INFERENCE('<TABLE_PATH>', '<MODEL_TYPE>', ‘<REFRESH_TIME>’);
```

<TABLE_PATH>: The fully qualified name of the table to monitor.

<MODEL_TYPE>: The type of model to apply for inference.

<REFRESH_TIME>: The required wait time after which the task would be called. It can be set to how often your source data updates (using CRON or Minutes)

Example:

```sql
CALL TEMPO.LIVE_INFERENCE.START_LIVE_INFERENCE('mydb.myschema.mytable', 'workstation', ‘1 M’);
```

### Monitor, Suspend, and Resume Task:

After creating a task, the task name should be visible in the Snowflake interface. 

- Monitoring tasks:
Now, you can select a task from there to check its activity and status, for example:

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => '<Task_name>'
));
```

<Task_name>: The name of the task used for live updates.

- Suspending Task:

Suspending the job allows you to make changes to the task's schedule, dependencies, or underlying queries securely and without affecting its execution. You can suspend a task.

```sql
ALTER TASK <Task_name> SUSPEND;
```

- Resuming tasks:
After making changes to the tasks, you can freely resume the task using:

```sql
ALTER TASK <Task_name> RESUME;
```

### Shutting Down Live Inference

When you need to stop live inference, use the `SHUTDOWN_LIVE_INFERENCE` procedure to safely terminate the process.

```sql
CALL TEMPO.LIVE_INFERENCE.SHUTDOWN_LIVE_INFERENCE('<TABLE_NAME>');
```

<TABLE_NAME>: The name of the table for which live inference should be shut down (not the FQN, just the table name).

Example:

```sql
CALL TEMPO.LIVE_INFERENCE.SHUTDOWN_LIVE_INFERENCE('mytable');
```

After live inference is set up, review the results stored in the live updates table. This table will contain the incoming data along with the model’s classification.

```sql
SELECT * FROM TEMPO.LIVE_INFERENCE.LIVE_UPDATES_ON_<TABLE_NAME>;
```

<TABLE_NAME>: The name of the table used for live updates.

Example:

```sql
SELECT * FROM TEMPO.LIVE_INFERENCE.LIVE_UPDATES_ON_mytable;
```

### Additional Notes

**Performance Considerations:** Live inference tasks can consume significant resources. Ensure that your Snowflake environment is properly scaled to handle the workload.

This guide uses sample data provided with TEMPO. For using your own data, please refer to the custom data guide.

<!-- ------------------------ -->
## Viewing Results in Splunk
Duration: 5

This section guides you through setting up Splunk Enterprise to view the output from the Snowflake TEMPO project.

### Prerequisites
- An Amazon EC2 instance running Amazon Linux or another compatible Linux distribution
- Root or sudo access
- Splunk Enterprise installer tarball (`.tgz` file)
- `anomaly_hub.xml` dashboard file

### Install Splunk Enterprise
Duration: 5

1. Clone the installation repository:
   ```bash
   git clone https://github.com/your-username/splunk-tempo-dashboard-installer.git
   cd splunk-tempo-dashboard-installer
   ```

2. Place the Splunk Enterprise tarball in the same directory as the script.

3. Edit the script to set your desired credentials:
   ```bash
   vi splunk_tempo_install.sh
   ```

4. Make the script executable and run it:
   ```bash
   chmod +x splunk_tempo_install.sh
   sudo ./splunk_tempo_install.sh
   ```

### Configure Splunk and Load Data
Duration: 3

1. Access Splunk at `http://your_ip:8000` and log in with the credentials you set.

2. Download the CSV file from the TEMPO Snowflake app output.

3. In Splunk, go to Settings > Add Data > Upload > select your CSV file.

4. Follow the prompts to load the CSV, using default options.

### Create the Dashboard
Duration: 2

1. After loading the CSV, click "Build Dashboards" > "Create New Dashboard".

2. Select "Classic Dashboard Builder" and create the dashboard.

3. In the dashboard editor, switch to "Source" view.

4. Copy the XML from `anomaly_hub.xml` and paste it into the Source view.

5. Update the CSV filename in the query:
   ```xml
   <query>source="your-filename.csv" host="Josiah" sourcetype="csv"
   | stats count as event_count</query>
   ```

6. Save the dashboard.

### Important Notes
- Set strong passwords for all user accounts.
- Ensure sufficient disk space (minimum 10GB recommended).
- Keep your EC2 instance and Splunk Enterprise updated with the latest security patches.

### Troubleshooting
- If the script fails to find the Splunk tarball, ensure it's in the correct directory.
- For user creation issues, check Splunk server logs and verify authentication credentials.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

Now it is time for you to try Tempo with your own data. The power is now at your fingertips to take on the future of security.


### What You Learned
- Completed setup of Tempo on SnowFlake
- Fine Tuned Tempo
- Ran Tempo on a sample dataset

