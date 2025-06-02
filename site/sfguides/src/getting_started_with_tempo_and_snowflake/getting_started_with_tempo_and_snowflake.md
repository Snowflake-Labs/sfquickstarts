author: security_team
id: tempo_setup_and_user_guide
summary: Complete guide for setting up and using Tempo cybersecurity platform on Snowflake with Forensichat analysis capabilities
categories: Security
environments: web
status: Published
feedback link: https://github.com/DeepTempo/tempo-guides/issues
tags: Security, Deep Learning, Network Analysis, MITRE ATT&CK, Threat Detection

# Tempo Setup and User Guide
<!-- ------------------------ -->
## Overview
Duration: 3

Tempo is a modern cybersecurity solution that leverages deep learning for network threat detection. By moving beyond conventional rule-based approaches, Tempo offers a sophisticated and adaptable way to identify and respond to security events. Tempo uses a Deep Learning model that analyzes network and flow logs to detect various attacks, mapping them to MITRE ATT&CK for integration with your SIEM, SOC, and Threat Response systems.

This comprehensive guide covers both the initial setup of Tempo on Snowflake and how to effectively use the Forensichat analysis interface for cybersecurity investigations.

### What You'll Learn
- How to install and configure Tempo on Snowflake
- How to navigate the Tempo user interface
- How to perform forensic analysis using Forensichat
- How to interpret MITRE ATT&CK framework mappings
- How to configure data sources and settings

### What You'll Need
- A Snowflake account with appropriate permissions
- Network flow data with required features
- Basic understanding of network security concepts

### What You'll Build
- A fully functional threat detection and analysis platform

<!-- ------------------------ -->
## Finding and Installing Tempo
Duration: 4

### Accessing the Snowflake Marketplace

In the Snowflake Marketplace, you can find the Tempo app or directly access it [here](https://app.snowflake.com/marketplace/listing/GZTYZOYXHP3/deeptempo-cybersecurity-tempo).

### Prerequisites for Deployment

Before installing Tempo, ensure you have:
- Grant Tempo necessary permissions including creating warehouses and compute pools
- Configure proper database access
- Verify sufficient storage and compute resources

### Selecting Storage for Your Data

If you want to run Tempo on your own data, follow these steps to select the correct storage before launching the app:

1. Click the **Add** button next to the **on Incident Inference Logs** section
2. In the popup window, click **+Select Data**
3. From the dropdown menu, find and select the appropriate table containing your network flow data
4. Click **Save** to confirm your selection

**Note:** If you would like to use demo data for testing purposes, you can skip this step and proceed with the default configuration.

Once Tempo is successfully installed and running, a management interface launches which will help you monitor and interact with the system.

<!-- ------------------------ -->
## User Interface Navigation
Duration: 2

### Main Navigation Menu

The Tempo interface includes several main sections accessible from the navigation menu on the left side:

- **Home**: Dashboard with overview and welcome information
- **Data Sources**: Configure and manage data input sources
- **Threat Overview**: High-level analysis of your network security posture
- **Forensic Analysis**: Detailed investigation capabilities using Forensichat
- **Deep Investigation**: Advanced analysis of specific threats and sequences
- **Settings**: System configuration and user preferences

### Accessing the Interface

To access and use Tempo:

1. Navigate to the Tempo app in your Snowflake instance, typically found under Data Products > Apps > Tempo
2. The Tempo interface will load, displaying the available features and navigation options
3. Use the left navigation menu to move between different analysis sections

<!-- ------------------------ -->
## Executing Procedures Through the UI
Duration: 5

The Tempo interface enables users to run predefined procedures directly from the UI instead of using Snowflake worksheets.

### Important Configuration Notes

**⚠️ Critical Information:**
- **Inference Procedures** (Incident Classification, MITRE Classification) will default to demo data tables unless you explicitly configure which table to target under Reference Pages
- **Performance Evaluation** and **Model Fine-Tuning** require you to explicitly set the target evaluation or tuning table on the reference page—they have no demo defaults
- Ensure you have selected or created the correct source tables before executing procedures, or the command will fail

### Step-by-Step Procedure Execution

1. **Select Your Procedure**
   - Click the **Select Procedure** dropdown menu
   - Choose the desired command from options like "Investigate Sequence 🔎", "Incident Classification 🛡️", etc.

2. **Enter Required Parameters (if applicable)**
   - For **Investigate Sequence 🔎**: Enter the 29-character NetFlow Sequence ID in the text field and press Enter
   - For **Incident Classification 🛡️**: Use the **Include MITRE Classification** toggle to enable or disable ATT&CK framework mapping

3. **Execute the Command**
   - Click **Execute Command** to launch the selected procedure
   - The button will be disabled until all required inputs are valid or until the run is completed

4. **Monitor Execution Status**
   - Watch the status indicator above the Execute button:
     - ⏳ **Running** (auto-polls every 5 seconds)
     - ✅ **Completed**
     - ❌ **Failed**

5. **View Results**
   - Once completed, scroll down to see the output table for your selected procedure:
     - **Investigate Sequence**: Shows raw NetFlow rows and related events
     - **Incident/MITRE Classification**: Displays inference logs with threat classifications
     - **Performance Evaluation**: Lists recent performance metrics and accuracy scores
     - **Model Fine-Tuning**: Returns a summary message with tuning results

<!-- ------------------------ -->
## Threat Overview Analysis
Duration: 4

### MITRE ATT&CK Framework Distribution

The Threat Overview section provides a comprehensive view of your network security status through MITRE ATT&CK framework mapping. Tempo automatically categorizes detected threats into the following phases:

- **Initial Access**: Events indicating initial compromise attempts
- **Collection**: Data gathering activities by potential attackers
- **Impact**: Actions aimed at manipulation, interruption, or destruction of systems
- **Credential Access**: Attempts to steal user credentials or authentication tokens
- **Privilege Escalation**: Efforts to gain higher-level permissions within systems
- **Discovery**: Network and system reconnaissance activities
- **Exfiltration**: Data theft and unauthorized data transfer attempts
- **Lateral Movement**: Movement between systems within the network
- **Reconnaissance**: Information gathering activities about targets

### Network Security Metrics

The overview dashboard displays key metrics including:
- Unique IP Connections detected
- Total Network Events processed
- Potential Anomalies identified
- Distribution of MITRE ATT&CK tactics observed

<!-- ------------------------ -->
## Forensic Analysis with Forensichat
Duration: 6

### Using the Forensic Analysis Assistant

Forensichat is Tempo's AI-powered analysis assistant that enables natural language interaction with your security data for advanced forensic investigations.

### Creating and Executing Queries

1. **Access the Query Interface**
   - Navigate to the Forensic Analysis section
   - Locate the query input field

2. **Enter Natural Language Queries**
   - Type questions in plain English, such as:
     - `Show me top 10 similar events to sequence id 982b5a35-d289-46f7-8adb-6aea0936b1c2`
     - `Find all connections from suspicious IP addresses`
     - `What are the most common attack patterns in the last 24 hours?`

3. **Analyze Query Results**
   - Results are displayed in table format showing:
     - Sequence IDs for event correlation
     - Source and destination IP addresses
     - Data transfer volumes (forward and backward bytes)
     - MITRE ATT&CK classifications
     - Timestamp information

### Forensic Insights and Similarity Analysis

Tempo provides insights based on similarity search in high-dimensional embeddings constructed from your network logs. For any suspicious sequence, you can:

- View similar events to identify patterns and potential attack campaigns
- Correlate events across different time periods
- Analyze traffic flows between specific IP addresses
- Investigate data transfer patterns that may indicate exfiltration

### Detailed Network Forensics

The Forensic Analysis section allows for in-depth investigation of network activities:

1. **Filter by Network Parameters**
   - Select source and destination IPs to filter events
   - Choose specific time ranges for analysis
   - Filter by ports or protocols

2. **Analyze Connection Statistics**
   - View total connections between endpoints
   - Examine forward and backward byte transfers
   - Analyze packet counts and flow durations

3. **MITRE ATT&CK Phase Analysis**
   - View distribution of attack phases for specific connections
   - Examine detailed occurrences of each attack technique
   - Identify predominant tactics used in network communications

<!-- ------------------------ -->
## Deep Investigation Capabilities
Duration: 3

### Advanced Threat Analysis

The Deep Investigation section provides detailed forensic analysis capabilities for specific security incidents:

1. **Sequence-Based Investigation**
   - Analyze specific NetFlow sequences flagged as suspicious
   - View complete event timelines and related activities
   - Correlate events across multiple network segments

2. **Connection-Specific Analysis**
   - Focus investigation on particular communication paths
   - Examine detailed statistics about data transferred
   - Identify attack techniques used in specific connections

3. **Pattern Recognition**
   - Leverage deep learning embeddings to find similar attack patterns
   - Identify potential attack campaigns spanning multiple incidents
   - Correlate seemingly unrelated security events

<!-- ------------------------ -->
## Settings and Configuration
Duration: 3

### Filtering and Display Options

Tempo provides customizable filtering options to tailor forensic investigations to specific analytical needs:

| Toggle Setting | Description |
|----------------|-------------|
| **Ignore Unclassified MITRE Tactics** | Hides events that could not be mapped to any MITRE ATT&CK tactic, enabling focus on recognized adversarial behavior patterns |
| **Ignore Benign Network Flows** | Excludes network flows flagged as benign or normal, reducing noise and helping isolate potentially suspicious traffic |
| **Ignore Anomalous Flows** | Removes network flows labeled as anomalous, useful when focusing only on confirmed patterns or known behavior baselines |
| **Ignore Unclassified Events** | Filters out events that were not categorized during the detection pipeline, simplifying the visual workspace |

### Data Source Configuration

Configure your data sources to ensure optimal analysis:

1. **Access Data Sources Section**
   - Navigate to Data Sources from the main menu
   - Review current data source configurations

2. **Verify Data Format Requirements**
   - Ensure your dataset includes all required features
   - Validate timestamp formats and data types
   - Check for proper labeling if using supervised learning

<!-- ------------------------ -->
## Required Data Features
Duration: 2

Your dataset must include the following features for proper analysis:

| Feature | Description | Example |
|---------|-------------|---------|
| timestamp | String datetime when flow started | "2017-03-07 08:55:58" |
| flow_dur | The duration of the flow in seconds | 120.5 |
| src_ip | Unique identifier of the source device | "192.168.1.100" |
| dest_ip | Unique identifier of the destination device | "10.0.0.50" |
| src_port | Source port number | 443 |
| dest_port | Destination port number | 80 |
| fwd_bytes | Payload bytes sent from source to destination | 2048 |
| bwd_bytes | Payload bytes sent from destination to source | 1024 |
| total_fwd_pkts | Packets sent from source to destination | 15 |
| total_bwd_pkts | Packets sent from destination to source | 12 |
| label | Indicates if flow is suspicious (1) or normal (0) | 0 or 1 |

**Compatible Data Sources:**
These features can be exported from network monitoring tools such as NetFlow, Wireshark, Zeek, SolarWinds, or AWS/GCP Flow logs.

<!-- ------------------------ -->
## Troubleshooting
Duration: 2

### Common Issues and Solutions

If you encounter issues with Tempo:

1. **System Status Verification**
   - Check the System Status page to ensure all components are online
   - Verify that compute pools are active and accessible

2. **Data Source Problems**
   - Verify data source configurations are correct
   - Ensure required data features are present and properly formatted
   - Check that timestamps are in the correct format

3. **Snowflake Resource Issues**
   - Check warehouse and compute pool status using `SHOW COMPUTE POOLS IN ACCOUNT;`
   - Verify that resources have sufficient capacity for your data volume
   - Ensure auto-suspend and auto-resume settings are configured appropriately

4. **Permission and Access Issues**
   - Verify that all necessary permissions are properly configured
   - Check that the management console is accessible via the Streamlit dashboard
   - Ensure database access permissions are granted correctly

5. **Performance Issues**
   - Monitor resource utilization during analysis
   - Consider scaling compute resources for large datasets
   - Verify that data is properly indexed for optimal query performance

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 1

### Conclusion

You have successfully learned how to set up and use Tempo, a cutting-edge cybersecurity platform that leverages deep learning for advanced threat detection and forensic analysis. With Forensichat's natural language interface and comprehensive MITRE ATT&CK framework integration, you now have powerful tools for identifying and investigating network security incidents.

### What You Learned
- How to install and configure Tempo on Snowflake
- How to navigate the Tempo user interface effectively
- How to perform forensic analysis using natural language queries
- How to interpret MITRE ATT&CK framework mappings
- How to configure settings and data sources for optimal analysis

### Additional Resources

For more information and assistance:
- **Snowflake Marketplace**: [Tempo App](https://app.snowflake.com/marketplace/listing/GZTYZOYXHP3/deeptempo-cybersecurity-tempo)
- **MITRE ATT&CK Framework**: [attack.mitre.org](https://attack.mitre.org/)
- **Technical Support**: [support@deeptempo.ai](mailto:support@deeptempo.ai)
- **Documentation**: Check the Tempo app documentation within Snowflake for additional technical details