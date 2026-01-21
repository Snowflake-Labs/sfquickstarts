author: Joviane Bellegarde
id: connectors-google-analytics-raw-data
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/snowflake-feature/connectors
language: en
summary: Ingest raw Google Analytics data into Snowflake with a native connector for custom marketing analytics and attribution modeling.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with the Snowflake Connector for Google Analytics
<!-- ------------------------ -->
## Overview

![assets/snowflake_connector_banner.png](assets/snowflake_connector_banner.png)

In this Quickstart, we will investigate how to use the Snowflake Connector for Google Analytics Raw Data to emulate data ingestion from Google Analytics to BigQuery into Snowflake.

### What You Will Build
- A BigQuery dataset with Google Analytics data.
- A Streamlit application to visualize the data.

### What You Will Learn
You will learn how to:
- Create a Google Analytics Project.
- Create a BigQuery dataset.
- Install and configure the Snowflake Connector for Google Analytics Raw Data.
- Visualize the BigQuery data in a Streamlit application.

### Prerequisites
- A [Google Account](https://accounts.google.com/signup/v2/webcreateaccount?hl=en&flowName=GlifWebSignIn&flowEntry=SignUp) to access [Google Analytics](https://analytics.google.com/) and [BigQuery](https://cloud.google.com/bigquery).
- Familiarity with basic Python and SQL.
- Familiarity with data science notebooks.
- Go to the [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) sign-up page and register for a free account. After registration, you will receive an email containing a link that will take you to Snowflake, where you can sign in.

<!-- ------------------------ -->
## Snowflake Environment

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface to create Snowflake objects (warehouse, database, schema, role).

#### Creating Objects and Loading Data
1. Navigate to Worksheets, click `+` in the top-right corner to create a new Worksheet, and choose **SQL Worksheet**.

2. Copy and paste the [setup script](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-connector-for-google-analytics/blob/main/scripts/setup.sql) code to create Snowflake objects (warehouse, database, schema) and click **Run All** at the top of the Worksheet.

<!-- ------------------------ -->
## Google Analytics

### Overview
In this section, we will create a Google Analytics Account and Property in Google Analytics.

#### Create Account

1. To create an Account, navigate to [Google Analytics](https://analytics.google.com/) and click on **Start measuring**.

![assets/welcome_to_analytics.png](assets/welcome_to_analytics.png)

2. Enter an account name such as **Snowflake Connector Account** and click **Next**.

![assets/create_account_page.png](assets/create_account_page.png)

3. Enter the **Property Name** as **Snowflake Connector Property** and click **Next**.

![assets/property.png](assets/property.png)

4. Select the industry category and business size and click **Next**.

![assets/business_description.png](assets/business_description.png)

5. Select the business objectives and click **Create**.

![assets/objectives.png](assets/objectives.png)

6. Accept the terms and conditions and click **I Accept**.

![assets/terms.png](assets/terms.png)


<!-- ------------------------ -->
## BigQuery

### Overview
In this section, we will create a BigQuery dataset and table to store Google Analytics data.

#### Create a BigQuery Project
1. Navigate to [Google Cloud Console](https://console.cloud.google.com/) and click on **Create or select a project** button to create a new project.

![assets/query_welcome.png](assets/query_welcome.png)

2. Select **New Project** then **No organization** and click **Create**.

![assets/new_project.png](assets/new_project.png)

3. In the popup notification window on the top right, click **SELECT PROJECT**.

![assets/notification.png](assets/notification.png)

4. The page will automatically load to the new project. Hover over the left sidebar to expand it and in the **Resources** section, click on **BigQuery**.

![assets/resources_bigquery.png](assets/resources_bigquery.png)

5. In the **Explorer**, enter `bigquery-` in the **Search BigQuery resources** box and toggle to **Search all projects**. Click on the star next to `bigquery-public-data` to star the dataset.

![assets/star_bigquery.png](assets/star_bigquery.png)

6. Click **X** in the **Search BigQuery resources** to view your project and the starred project.

![assets/starred_project.png](assets/starred_project.png)

7. Expand the **bigquery-public-data** dataset to view the datasets.

![assets/general_datasets.png](assets/general_datasets.png)

8. Scroll down to find and expand the `ga4_obfuscated_sample_ecommerce` dataset and select the only table that's in this dataset. It should start with `events_`. Click `COPY`.

![assets/copy_data.png](assets/copy_data.png)

9. Select **BROWSE**.

![assets/copy_table.png](assets/copy_table.png)

10. Select the project that was created earlier, **Snowflake Connector Project** in this example.

![assets/select_project.png](assets/select_project.png)

11. After clicking on the project, the **Dataset** and **Table** fields will be blank.

![assets/two_blanks.png](assets/two_blanks.png)

12. Click on the **Dataset** field and select **CREATE NEW DATASET** in the dropdown. 

![assets/create_new_dataset.png](assets/create_new_dataset.png)

13. Enter `analytics_20210131` and click **CREATE DATASET**.

![assets/dataset_id.png](assets/dataset_id.png)

14. Click on the **Table** field and enter `events_20210131` for the table name and click **COPY**.

![assets/copy_table_2.png](assets/copy_table_2.png)

15. Click **GO TO TABLE** on the toast that appears on the bottom of the page.

![assets/toast.png](assets/toast.png)

16. View the table by clicking **PREVIEW**.

![assets/preview_table.png](assets/preview_table.png)


<!-- ------------------------ -->
## Link Analytics

### Overview
In this section, we will link Google Analytics to BigQuery.

#### Link Google Analytics to BigQuery

1. Navigate to [Google Analytics](https://analytics.google.com/) and enter **BigQuery Links** in the search bar and select **BigQuery Links**.

![assets/search_bigquery.png](assets/search_bigquery.png)

2. Click the **Link** button.

![assets/link_button.png](assets/link_button.png)

3. Click on the **Choose a BigQuery project** button.

![assets/choose_project.png](assets/choose_project.png)

4. Select the BigQuery Project and click **Confirm**.

![assets/confirm_project.png](assets/confirm_project.png)

5. Click **Next** and select **Include advertising identifiers for mobile app streams**, **Streaming (best-effort)**, and **Daily**. Click **Next** again.

![assets/configure_link.png](assets/configure_link.png)

6. Click **Submit**.

![assets/submit_link.png](assets/submit_link.png)

7. A new link is created.

![assets/link_created.png](assets/link_created.png)


<!-- ------------------------ -->
## Service Account

### Overview
In this step, we will configure the OAuth Consent Screen.

#### Create Service Account Key
1. Navigate back to BigQuery and hover over the left sidebar to expand it and click on **APIs & Services** then **Credentials**.

![assets/credentials_1.png](assets/credentials_1.png)

2. Click on **Create Credentials** and select **Service account**.

![assets/credentials_to_service.png](assets/credentials_to_service.png)

3. Enter a **Service account name** such as **Connector Service Account** and click **CREATE AND CONTINUE**.

![assets/service_account_name.png](assets/service_account_name.png)

4. Add all 3 of these roles one at a time by clicking on the dropdown list to select a role, and then click **+ ADD ANOTHER ROLE** to add the next role then click DONE: **BigQuery Data Viewer**, **BigQuery Read Session User** and **BigQuery Job User**.

![assets/roles.png](assets/roles.png)

5. Click on the newly created service account and click on **ADD KEY** then **Create new key**.

![assets/created_service_account.png](assets/created_service_account.png)


![assets/create_new_key.png](assets/create_new_key.png)

6. Select **JSON** and click **CREATE**.

![assets/create_json.png](assets/create_json.png)

7. The JSON key file will be downloaded to your computer.

![assets/json_saved.png](assets/json_saved.png)

<!-- ------------------------ -->


## OAuth Configuration

### Overview
In this section, we will configure the OAuth Consent Screen.

#### Configure OAuth Consent Screen
1. Hover over the left sidebar to expand it and click on **APIs & Services** then **OAuth consent screen**.

![assets/navigate_to_oauth.png](assets/navigate_to_oauth.png)

2. Select **External** and click **CREATE**.

3. **Note** if you have the **GO TO NEW EXPERIENCE** button, click the button to proceed to the next step.

![assets/go_to_new_experience.png](assets/go_to_new_experience.png)

4. Navigate to **Clients** and click on **GET STARTED**.

![assets/get_started.png](assets/get_started.png)

5. Enter the App name as **Snowflake Connector for Google Analytics Raw Data** and click **NEXT**.

![assets/app_info_1.png](assets/app_info_1.png)

6. Click **External** and then **NEXT**.

![assets/external_audience.png](assets/external_audience.png)

7. Enter an email address (preferably the same one entered for the User Support Email) and click **NEXT**.

![assets/app_info_3.png](assets/app_info_3.png)

8. Select to Agree and click **CONTINUE**.

![assets/agree_and_continue.png](assets/agree_and_continue.png)

9. Click **CREATE**.

![assets/app_info_4.png](assets/app_info_4.png)

<!-- ------------------------ -->
## Enable API

### Overview
In this section, we will enable the Cloud Resource Manager API.

#### Cloud Resource Manager API
1. Inside BigQuery, enter **Cloud Resource Manager API** in the search bar and click on **Cloud Resource Manager API**.

![assets/search_cloud_resource_api.png](assets/search_cloud_resource_api.png)

2. Click **ENABLE**.

![assets/enable.png](assets/enable.png)


<!-- ------------------------ -->
## Connector

### Overview
In this section, we will install and configure the Snowflake Connector for Google Analytics Raw Data.

#### Clean Up Script
1. Navigate to the Snowflake Marketplace and type in **Snowflake Connector for Google Analytics Raw Data** and click on the Connector.

![assets/search_connector.png](assets/search_connector.png)

2. Click **GET** and then **GET** to install the Connector.

![assets/get.png](assets/get.png)

3. Click **Configure**.

![assets/configure_connector.png](assets/configure_connector.png)

4. Click **Mark all as done** and then click **Start configuration**.

![assets/connector_1.png](assets/connector_1.png)

5. Click **Configure**.

![assets/connector_2.png](assets/connector_2.png)

6. Upload the JSON file that was previously downloaded and upload it to this page and click **Connect**.

![assets/connector_3.png](assets/connector_3.png)

7. Click **Define data to sync**.

![assets/connector_4.png](assets/connector_4.png)

8. Select the data to sync and click **Start sync**.

![assets/start_sync.png](assets/start_sync.png)

9. When the data is syncing, the UI will indicate with **Last sync: x minutes ago**.

![assets/data_synced.png](assets/data_synced.png)

<!-- ------------------------ -->
## Notebook

### Overview
In this section, we will create a Snowflake Notebook to view the data: both the raw un-flattened and flattened data.

#### Create a Snowflake Notebook
1. Download the [Snowflake Notebook](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-connector-for-google-analytics/blob/main/notebooks/0_start_here.ipynb)
2. Navigate to Snowsight, make sure you're using the **ACCOUNTADMIN** role and go to **Projects** and **Notebooks**.
3. Click on the dropdown arrow portion of the `+ Notebook` button.
4. Click on `Import .ipynb file`.
5. A popup window will appear to upload the Notebook file.
6. In the **Name** section, name the Notebook, select **GOOGLE_ANALYTICS** for the database and **RAW_DATA** for the schema.
7. Select **GOOGLE_ANALYTICS_DS_WH** for the warehouse.
8. Click **Create**.
9. Click **Run all** to run the Notebook.

<!-- ------------------------ -->
## Streamlit

### Overview
In this section, we will create a Streamlit application to visualize the data.

#### Visualize Data
1. Copy the [Streamlit code](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-connector-for-google-analytics/blob/main/scripts/streamlit.py).
2. Navigate to Snowsight, make sure you're using the **ACCOUNTADMIN** role and go to **Projects** and **Streamlit**.
3. Click on the `+ Streamlit App` button.
4. In the **App title** section, name the app, select **GOOGLE_ANALYTICS** for the database and **RAW_DATA** for the schema.
5. Select **GOOGLE_ANALYTICS_DS_WH** for the warehouse.
6. Paste in the Streamlit code into the code editor and click **Run**.

<!-- ------------------------ -->
## Clean Up

### Overview
When you're finished with this Quickstart, you can clean up the objects created in Snowflake.

#### Clean Up Script
Navigate to the last cell in the Snowflake Notebook labeled **clean_up** to uncomment and run it to drop all objects created in this Quickstart.

<!-- ------------------------ -->
## Conclusion and Resources
### Congrats! You're reached the end of this Quickstart!

#### What You Learned
With the completion of this Quickstart, you have learned how to:
- Use the Snowflake Connector for Google Analytics Raw Data to ingest data from Google Analytics/BigQuery into Snowflake.
- Visualize the data in a Streamlit application.

#### Resources
- [Snowflake Connector for Google Analytics Raw Data](https://other-docs.snowflake.com/en/connectors/google/gard/gard-connector-about)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
