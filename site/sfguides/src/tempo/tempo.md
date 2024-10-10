author: mando222
id: tempo
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

This guide will walk you through the process of setting up and using the TEMPO Native App in your Snowflake environment with provided sample data ([CIC Dataset](https://www.unb.ca/cic/datasets/ids-2017.html)).

The data that is provided comes from the Canadian Institute for Cybersecurity.  You can see the data set - and an explanation of the attacks discerned by Tempo [here](https://www.unb.ca/cic/datasets/ids-2017.html)

### What You’ll Learn 
- How to run Tempo on sample data ([CIC Dataset](https://www.unb.ca/cic/datasets/ids-2017.html))
- Optional - How to view the output in Splunk

### What You’ll Need 
- A [Snowflake](https://www.snowflake.com/login/) Account 
- Optional - A [Splunk](https://www.splunk.com/) Account or instance

### What You’ll Build 
- A working LogLM alerting dashboard

<!-- ------------------------ -->
## Install the TEMPO Native App
Duration: 2

1. Obtain the TEMPO Native App from the Snowflake Marketplace.
2. It is recommended that during installation you shorten the name to just TEMPO.  
  - To do so, examine Options for your installation before selecting Get
  - Where you see the extended name of the application, TEMPO - the first..., edit that to read just TEMPO
  - Once you have shortened the name - which will simplify management - please select Get
  - After you select Get the TEMPO app will be installed; you will also receive an email from Snowflake
3. After Tempo is installed, you will be prompted to select Configure
4. When you select Configure, you will be asked to grant the following permissions; please do so

GRANT CREATE COMPUTE POOL ON ACCOUNT TO APPLICATION TEMPO;
GRANT CREATE WAREHOUSE ON ACCOUNT TO APPLICATION TEMPO;

5. Continue to click through and Launch the app

At this point, you will be a Worksheet showing SHOW TABLES; you are now ready to use Tempo as explained below

The application comes with its own warehouse (TEMPO_WH) and compute pool (TEMPO_COMPUTE_POOL) with the following specs, which will be used for container services runs.

### TEMPO_WH
- **Type**: Snowpark Optimized
- **Size**: Medium
- **Auto Suspend**: 120 seconds
- **Auto Resume**: Enabled
- **Initial State**: Active

### TEMPO_COMPUTE_POOL
- **Node Configuration**:
  - **Minimum Nodes**: 1
  - **Maximum Nodes**: 1
- **Auto Suspend**: 360 seconds
- **Instance Family**: GPU_NV_S
- **Auto Resume**: Enabled
- **Initial State**: Active

<!-- ------------------------ -->
## Initialize the Application and Grant Permissions for Sample Data Access
Duration: 2

Starting on the same worksheet, you can now initialize Tempo:

```sql
CALL TEMPO.MANAGER.STARTUP();
```
<!-- ------------------------ -->

## Perform Inference 
Duration: 2

After a few minutes, Snowflake will be ready to perform inference. You are creating a Snowflake Job service, which are containers that run a specific image and terminate as soon as the run is completed. 

Once completed, we will use the `TEMPO.DETECTION` schema's stored procedure to perform inference on sample log data. These stored procedures take a job service name as the only parameter.  The demo data looks at logs for all Workstations and logs for all Webservers for a midsized company over several days.  This demo data was obtained from the Canadian Institute of Cybersecurity. In a live run each created procedure represents a call to the respective model type IE. workstation representing the model specialized for workstations, webservers for webservers and so on. 

When used for inference in your company, you would likely choose to execute each of these models as relevant logs are ingested. Tempo is modular in construction in order to minimize costs and compute time.  

Example:

```sql
CALL TEMPO.DETECTION.WORKSTATIONS('<job_service_name>');
```
`<job_service_name>`: the name of the run you want to perform (e.g., 'tempo_run_one', 'here_we_go')

or
```sql
CALL TEMPO.DETECTION.WEBSERVER('<job_service_name>');
```
After you run inference to find anomalies - or incidents - by looking at the Workstations or the Webserver, you will see a table with all the sequences the model has created.  Unlike many neural network based solutions, one strength of Tempo is that it preserves and shares relevant sequences for further analysis.  

If you order the rows by the Anomaly column, you will see that for Workstations you should see 11 anomalies and for Webserver you should see 3918 anomalies.  

Were this a production use case, you might want to augment these results with information from IP Info or threat intelligence, to look into the external IPs that are indicated to be part of likely security incidents.  

Some users have asked to see the entities that Tempo can discern.  Note that for larger environments it would be typical to have Tempo to discern many more types of entities.  You can ask Tempo to specifically learn the types of entities that are present in the log data provided using the following command:

```sql
CALL TEMPO.DETECTION.DEVICE_IDENTIFICATION('<job_service_name>');
```
At this point you have already seen the ability of DeepTempo to discern incidents in complex log data that traditional approaches are challenged to identify.  As you can see, the output from DeepTempo could be used in conjunction with other data sources that you possess about your organization.

<!-- ------------------------ -->

### Monitor Job Services

The TEMPO.DETECTION.WORKSTATION and ...WEBSERVER commands should execute in 3-4 minutes.  

If you decide to test the model on a larger dataset or otherwise would like to keep track of the execution of the inference on this sample data, you can check the status of Job services. 
As a reminder, job_service_name is the same job service name you assigned when you ran TEMPO.DETECTION.

```sql
CALL SYSTEM$GET_SERVICE_STATUS('DETECTION.<job_service_name>');
```

`<job_service_name>`: The name of the job service to check.

Example:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('DETECTION.WORKSTATION_RUN_ONE');
```
<!-- ------------------------ -->
## Viewing Results in Splunk
Duration: 5

This optional section guides you through setting up Splunk Enterprise to analyze the output from the Snowflake TEMPO project.  This step is optional and intended for Splunk users who want a visualization of the output.  For this demo we used a trial account on Splunk and we import the results of Tempo as CSV.  In a production use case, you will likely use the Snowflake Splunk connector, DBConnect, as explained in the Snowflake documentation [here]: (https://community.snowflake.com/s/article/Integrating-Snowflake-and-Splunk-with-DBConnect)

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

5. Save the Dashboard
   - After the dashboard is saved, you will now have to create a Tempo Splunk macro

7. Create a Tempo macro in Splunk
   - In splunk create a new Splunk macro by going to ```Settings``` > ```Advanced Search``` > ```+ Add New```
   - Keep Destination app as ```search```
   - Name the macro ```TempoDataLocation```
   - Define the macro as your Splunk path to Tempo's csv output. Will look something like this
   ```xml
   source="your-filename.csv" host="Your Name" sourcetype="csv"
   ```
   - You can leave the rest of the macro creation blank.
   - Save the macro

You should now be able to see the incidents - or anomalies - in your new dashboard.  This enables Security Operations teams to click through on the context provided by Tempo.  For example, you can see all transactions to and from a specific IP address, or across given ports, as a part of investigating the incidents that have been identified.

Note that as a default, only the incidents are uploaded.  Not also transferring and loading the entire dataset of logs simplifies the work of the Security Operator and also can translate into significant cost savings, as Splunk and most security operations solutions tend to charge by data ingested.  

### Important Notes
- Set strong passwords for all user accounts.
- Ensure sufficient disk space (minimum 10GB recommended).
- Keep your EC2 instance and Splunk Enterprise updated with the latest security patches.

### Troubleshooting
- If the script fails to find the Splunk tarball, confirm that it's in the correct directory.
- For user creation issues, check Splunk server logs and verify authentication credentials.

<!-- ------------------------ -->

### What You Learned
- How to run Tempo on Snowflake as a NativeApp
- How to monitor Tempo
- How to see incidents and relevant context identified by Tempo in Splunk

Congratulations, you just ran the world's first purpose-built LogLM available as a Snowflake NativeApp.  In the weeks to come DeepTempo will launch a range of additional easy-to-use options and extensions as NativeApps, including simplifying the use of your own data with Tempo and upgrades to the power of Tempo including scale-out multi-GPU usage.  

Please share your feedback, questions, and suggestions.  
