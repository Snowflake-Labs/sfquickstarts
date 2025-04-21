author: jedify-team
id: jedify-native-app
summary: Learn how to set up and use Jedify's AI-powered analytics solution in Snowflake
categories: Data-Science, AI-ML
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: AI, Machine Learning, Analytics, Native App, Semantic Analysis

# Build and deploy Automated Semantic-Driven Insights with Jedify utilizing Snowflake and Cortex AI - Quickstart Guide
<!-- ------------------------ -->
## Overview 
Duration: 1

Jedify is a Snowflake Native App designed to deliver **Automated Semantic-Driven Insights** by leveraging AI-powered data processing. It helps businesses extract meaningful insights from structured, unstructured, contextual, and non contextual data without requiring complex queries or manual intervention. The app seamlessly integrates with Snowflake, enabling users to **accelerate decision-making, enhance analytics capabilities, and optimize data-driven workflows**.

### **Prerequisites**
<!-- ------------------------ -->
Before getting started, ensure you have the following:
<!-- ------------------------ -->
✅ **A Snowflake account** (Paid)
<!-- ------------------------ -->
✅ **Account Admin or appropriate permissions** to install Native Apps
<!-- ------------------------ -->
✅ **Cortex AI enabled** in your Snowflake region (if not please email [support@jedify.com](mailto:support@jedify.com) before progressing)
<!-- ------------------------ -->
✅ **Proper network configurations** to allow seamless API connections
<!-- ------------------------ -->
<!-- ------------------------ -->
### **What You Will Learn**
<!-- ------------------------ -->
✔️ Understand how to **deploy and configure** a Snowflake Native App
<!-- ------------------------ -->
✔️ Learn how **Jedify's AI-powered insights engine** works
<!-- ------------------------ -->
✔️ Explore **semantic evaluation** and its role in automated data analysis
<!-- ------------------------ -->
✔️ Gain expertise in **BI tool integration** for real-time insights
<!-- ------------------------ -->
✔️ Optimize data workflows by leveraging **AI-driven query recommendations**

<!-- ------------------------ -->
### **What You Will Build**
By following this guide, you will set up and deploy **Jedify's Snowflake Native App** within your Snowflake environment. This includes:
* Installing the Jedify app from the Snowflake Marketplace
* Connecting it to your Snowflake and other data sources
* A Semantic evaluation agent to asses whether the data provided will support achievig your desired goals
* Autonomous Semantic Fusion™
* Integrating AI-driven query assistance to enhance business intelligence and reporting

At the end of this process, you will have a fully operational **AI-powered analytics solution** that automatically interprets data and provides actionable insights.

<!-- ------------------------ -->
## Installing the Jedify Native App
Duration: 3

In this step, you'll install the Jedify Native App from the Snowflake Marketplace and configure initial settings.

1. Go to the Snowflake App Marketplace and search for "Jedify"
2. Click 'Get' to start the installation process
3. Follow the on-screen instructions to grant necessary permissions
4. Generate a Jedify Access Key:
   * Visit [power.jedify.com](https://power.jedify.com) to create an account and obtain your API key
   * Once you create an account or log in (if you already have an account), create a new access key by entering a name and clicking "Create Key"
   * When your key is generated, copy the secret key value as it will only be shown once. Store this key securely as you'll need it to authenticate the Jedify Native App
> aside positive
> 
> Note that the API key setup may take a few seconds to complete.

5. In the Snowflake native app UI, click Onboarding to kick off the onboarding process

<!-- ------------------------ -->
## Granting permissions
Duration: 5

For Jedify to access your data and provide meaningful insights, you need to grant the necessary permissions.

1. As part of the onboarding flow, you'll be prompted to grant privileges to the Jedify application
2. If your organization uses a proxy server or firewall to control inbound traffic, you'll need to whitelist specific IP addresses

```sql
CREATE NETWORK RULE JEDIFY_ACCESS_RULE
MODE = INGRESS
TYPE = IPV4
VALUE_LIST = (
  '54.82.120.241/32',
  '54.221.135.9/32',
  '54.86.110.214/32',
  '54.226.185.100/32',
  '54.197.160.10/32',
  '174.129.63.235/32',
  '54.227.16.250/32',
  '18.234.244.111/32',
  '3.81.125.12/32',
  '54.144.62.191/32',
  '54.92.151.103/32',
  '18.208.133.145/32',
  '52.6.210.170/32'
);
```

3. Configure the application settings according to your specific requirements
4. Verify that all permissions are correctly applied before proceeding to the next step

> aside negative
> 
> Without proper permissions, Jedify won't be able to access your data sources, which will limit its functionality.


<!-- ------------------------ -->
## Connecting Data Sources
Duration: 5

In this step, you'll connect Jedify to your data sources to enable semantic analysis and insights generation.

Jedify's powerful semantic analysis works best when it has access to various data sources within your Snowflake environment. The platform can analyze:

* Structured data (tables and views)
* Unstructured data
* Contextual data
* Non-contextual data

To connect your data sources:

1. Select the databases, schemas, and tables you want to analyze
2. Jedify will automatically scan and index the connected data sources
3. You can review the data sources that have been connected and add additional ones as needed

<!-- ------------------------ -->
## Integrating with BI Tools
Duration: 10

Jedify integrates with your existing BI tools to enable model verification and learning from your analytics workflows.

Set up your BI connection by following these steps:

1. Navigate to the BI Connections section in the Jedify app
2. Select your BI system (Looker, Tableau, or Power BI)
3. Provide the necessary credentials: 

   * **Tableau:**
        - Server URL
        - User Email
        - Site name
        - Client ID
        - Secret ID
        - Secret value

   * **Looker:**
        - Base URL
        - Client ID
        - Client Secret

   * **Power BI:**
        - Currently in Alpha, please email [support@jedify.com](mailto:support@jedify.com) to get access
4. Test the connection to ensure it works properly
5. Save your configuration

Once connected, Jedify will:

* Observe queries and usage patterns to improve its semantic understanding
* Verify model predictions against actual BI usage
* Continuously refine its semantic models based on how your organization uses data
* Adapt its processing to your organization's unique analytical needs

This integration allows Jedify to learn from your team's analytical workflows, and improves the relevance and accuracy of its semantic processing.

<!-- ------------------------ -->
## Running the semantic evaluation
Duration: 5

The Semantic Evaluation reviews your entire setup and assesses whether the configuration completed so far will enable meaningful insights.


1. Jedify will comprehensively analyze:
   * Tables and views you've granted access to
   * BI tool connections (if established)
   * Data coverage across different domains
   * Potential gaps in your data ecosystem
2. Review the evaluation results:
   * Consider granting access to additional data sources
   * Review incomplete permissions
   * Consider connecting a BI Tool

> aside positive
> 
> The evaluation allows you to return to any step, ensuring you can address configuration issues before proceeding.

Jedify's Semantic Evaluation serves as a comprehensive health check that:

* Confirms proper access permissions are in place
* Verifies that connected data sources provide sufficient context
* Assesses the coverage and accuracy of the semantic model that will be built
* Identifies any missing connections or configuration steps

This evaluation ensures that your Jedify setup is optimized before proceeding to the Autonomous Semantic Fusion™ process, saving time and improving results.

<!-- ------------------------ -->
## Deploying as Autonomous Semantic Fusion™ Model
Duration: 2

After completing all previous steps, the deployment process will start by clicking the "Build" button:

1. This process occurs in the background and typically takes a couple of hours to complete
2. When the model is ready, you'll receive an email notification
3. Log in to [app.jedify.com](https://app.jedify.com) to view and interact with your model

The Autonomous Semantic Fusion™ model that Jedify builds for you enables:

* Interactive exploration through the Jedify web interface
* Custom Scenarios with Agentic AI for specific needs like reports and data processing

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 1

Jedify simplifies and enhances **data-driven decision-making** by automating complex analytics workflows. By integrating AI-powered semantic analysis with Snowflake's data ecosystem, businesses can **uncover deep insights, optimize operations, and reduce the manual effort required for data interpretation**.

**With Jedify, you can:**   
<!-- ------------------------ -->
✔️ **Extract insights** without writing SQL queries
<!-- ------------------------ -->
✔️ **Automate data analysis** using AI-powered evaluation
<!-- ------------------------ -->
✔️ **Improve BI reporting** with **semantic-driven** insights

### **What You Learned**
<!-- ------------------------ -->
By completing this guide, you have:
<!-- ------------------------ -->
🔹 Set up and configured **Jedify's Snowflake Native App**
<!-- ------------------------ -->
🔹 Learned how **semantic-driven AI** enhances analytics
<!-- ------------------------ -->
🔹 Integrated Jedify with **BI and reporting tools**
<!-- ------------------------ -->
🔹 Optimized data queries with **AI-driven recommendations**

### **Resources**
<!-- ------------------------ -->
For additional learning, check out these resources:
<!-- ------------------------ -->
📖 **Jedify Documentation** – [Jedify.com/documentation](https://jedify.com/documentation)
<!-- ------------------------ -->
📹 **Jedify Video Demos** – [Watch on YouTube](https://youtu.be/Ufiyg4gBYzQ?feature=shared)
<!-- ------------------------ -->
📄 **Snowflake Cortex AI Overview** – [Snowflake Docs](https://www.snowflake.com/en/product/features/cortex/)
<!-- ------------------------ -->
📚 **Jedify Blog** – [Jedify Blog](https://jedify.com/category/blog/)
