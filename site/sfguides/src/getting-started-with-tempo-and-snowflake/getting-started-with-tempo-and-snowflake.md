author: mando222
id: getting-started-with-tempo-and-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: This is a guide on getting started with Tempo on Snowflake 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with TEMPO and Snowflake
<!-- ------------------------ -->
## Overview 

Tempo is the first CyberSecurity solution based on a LogLM, or Log Language Model invented by DeepTempo.  These models are similar to their more familiar cousins, LLMs such as Anthropic's Claude and LLama. Like LLMs, LogLMs are Foundation Models that apply their understanding across very different environments and in response to differing inputs. However, Tempo was pre-trained using enormous quantities of logs. Tempo is focused on the pattern of events, including relative and absolute time. Tempo has been shown to be extremely accurate, with a low false positive and false negative rate.

This guide will walk you through the process of setting up and using the TEMPO Native App in your Snowflake environment with provided sample data ([CIC Dataset](https://www.unb.ca/cic/datasets/ids-2017.html)).

The data that is provided comes from the Canadian Institute for Cybersecurity.  You can see the data set - and an explanation of the attacks discerned by Tempo [here](https://www.unb.ca/cic/datasets/ids-2017.html)

### What You’ll Learn 
- How to run Tempo on sample data ([CIC Dataset](https://www.unb.ca/cic/datasets/ids-2017.html))
- How to check to see if Tempo is accurate in flagging attacks
- Optional - How to view the output in Splunk

### What You’ll Need 
- A [Snowflake](/login/) Account 
- Optional - A [Splunk](https://www.splunk.com/) Account or instance

### What You’ll Build 
- A working LogLM alerting dashboard

<!-- ------------------------ -->
## Install the TEMPO Native App

1. Find The App

In the Snowflake app Marketplace you can find the Tempo app or simply click [Here](https://app.snowflake.com/marketplace/listing/GZTYZOYXHP3).  

2. If you are running on your own data you will have the select the storage before clicking the launch app button in the deployment phase.
To select your table please click `add` next to the `on Incident Inference Logs` section. In the popup after clicking the `add` button click the `+Select Data` button and find the table you want to use on the dropdown.  Select it and click `Save`.

Note: If you are running with the demo data simply skip this step and continue. 

3. Snowflake will require you to grant permissions to run this app.  For a smooth experience make sure you do this in the initial setup though the Snowflake UI.

4. Go to the `Projects>Worksheets` console in Snowflake. Here you should see a `+` sign in the top right corner of the screen.  We will use this to create our own worksheets. Go ahead and click it now. 

5. From the top of the worksheet there should be a dropdown called `Select Databases`.  This is what you will use to attach our database to this worksheet.  If you are using demo data select the option with TEMPO at the beginning of it's name.

### The default resources created by the tempo app are as follows. 

#### TEMPO_WH
- **Type**: Snowpark Optimized
- **Size**: Medium
- **Auto Suspend**: 120 seconds
- **Auto Resume**: Enabled
- **Initial State**: Active

#### TEMPO_COMPUTE_POOL
- **Node Configuration**:
  - **Minimum Nodes**: 1
  - **Maximum Nodes**: 1
- **Auto Suspend**: 360 seconds
- **Instance Family**: GPU_NV_S
- **Auto Resume**: Enabled
- **Initial State**: Active

<!-- ------------------------ -->
## Start the app

In the new worksheet we now need to setup our procedures. We will start with initializing the container resources. Throughout this guide we will provide you with statements to run.  Please add them to the sheet. You can do these one by one or add them all to a single worksheet.

1. Initialize Application Resources
```sql
CALL management.create_resources();
```

Purpose: Initializes the application by loading required model weights and configurations
Required Permissions: Warehouse, compute pool, and task management access

It is recommended that you run this command prior to running the sheet as a whole.  It can take some time for the resources to spin up.  If you are the account admin you can monitor resources using `SHOW COMPUTE POOLS IN ACCOUNT;`. Once the compute pools are idle you may continue with the rest of the worksheet.

<!-- ------------------------ -->
## Run Static Inference

```sql
CALL static_detection.inference('your_service_name');
```
Parameters:
- `your_service_name`: Name of the service to analyze (string).  This is set by you and should be unique to each run.
Purpose: Executes inference on specified service data

If you want to use the demo feel free to name it something like `demorun` for the `your_service_name`.

<!-- ------------------------ -->
## Deep Dive Analysis in Snowflake

```sql
CALL inspect.deepdive(sequence_id);
```
Parameters:
- `sequence_id`: Identifier of the sequence to analyze (integer). This ID can be used down the road if any anomalies are detected to run deeper investigation on suspicious interactions. 
Purpose: Investigates specific sequences flagged as anomalies

Note: If running on demo data lets use 2 as the id (valid IDs 1-1200)

The results will be collections of related events making up Suspicious and Anomalous activities.  These are the events your security team would want verify as actuall intrusion events.

<!-- ------------------------ -->
## Viewing Results in Splunk

This optional section guides you through setting up Splunk Enterprise to analyze the output from the Snowflake TEMPO project.  This step is optional and intended for Splunk users who want a visualization of the output.  For this demo we used a trial account on Splunk and we import the results of Tempo as CSV.  In a production use case, you will likely use the Snowflake Splunk connector, DBConnect, as explained in the Snowflake documentation [here]: (https://community.snowflake.com/s/article/Integrating-Snowflake-and-Splunk-with-DBConnect)

### Prerequisites
- An Amazon EC2 instance running Amazon Linux or another compatible Linux distribution
- Root or sudo access
- Splunk Enterprise installer tarball (`.tgz` file)
- `anomaly_hub.xml` dashboard file

### Install Splunk Enterprise

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

1. Access Splunk at `http://your_ip:8000` and log in with the credentials you set.

2. Download the CSV file from the TEMPO Snowflake app output.

3. In Splunk, go to Settings > Add Data > Upload > select your CSV file.

4. Follow the prompts to load the CSV, using default options.

### Create the Dashboard

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
## Conclusion And Resources

### Conclusion

Congratulations, you just ran the world's first purpose-built LogLM available as a Snowflake NativeApp.  In the weeks to come DeepTempo will launch a range of additional easy-to-use options and extensions as NativeApps, including tooling to simplify the process of using your own data with Tempo and upgrades to the power of Tempo including scale out multi-GPU usage. 

### What You Learned
- How to run Tempo on Snowflake as a NativeApp
- How to monitor Tempo
- How to see incidents and relevant context identified by Tempo in Splunk

### Resources


To try the app please follow [This Link](https://app.snowflake.com/marketplace/listing/GZTYZOYXHNX/deeptempo-cybersecurity-tempo-cybersecurity-incident-identification-via-deep-learning?search=tempo)
[Snowflake Native Apps ](/en/data-cloud/workloads/applications/native-apps/) 
