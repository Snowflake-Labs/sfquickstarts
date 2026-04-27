author: Szymon Rybka
id: setting-up-leads-notifications-in-slack
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/data-engineering
language: en
summary: How to use webhooks for export Snowflake Marketplace lead information.
environments: web
status: Archived 
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>

# Setting Up Leads Notifications in Slack
<!-- ------------------------ -->
## Overview 

This guide is designed for users who wish to automate the export of lead events from the Snowflake Marketplace and use them in an external system. As a practical example, we will demonstrate how to send new lead information as a Slack message using webhooks.

Throughout this process, we will leverage JavaScript procedures to properly format messages and serve as a solid starting point for further self-exploration.

By the end of this guide, you should be familiar with Snowflake listing events and you will learn ways how to integrate them with external services.
### Prerequisites
- Snowflake Account with the ability to create a Database, Notification, Serverless Task, Execute Task, and access to the `LISTING_EVENTS_DAILY` view in the `DATA_SHARING_USAGE` schema
- Intermediate knowledge of Snowflake to execute queries and understand the underlying data structure.
- Basic knowledge of `json` to understand the structure of the data being sent to the webhook.
- Basic knowledge of JavaScript.


### What You’ll Learn
- How to analyze Snowflake Marketplace lead events
- How to export lead data using Notifications
- How to send a Slack message using webhooks
- How to automate the process using Snowflake Tasks


### What You’ll Need
- A Snowflake account [trial account](https://signup.snowflake.com/?utm_cta=quickstarts_) or access to an existing account with access to:
  - `LISTING_EVENTS_DAILY` view in the `DATA_SHARING_USAGE` schema for getting new leads data
  - `CREATE INTEGRATION` privilege on Account. For notification creation.
- Slack Account with the ability to create a new channel and add a webhook integration.

### What You’ll Build 
- Serverless Task that runs every day and sends a message to Slack with the new leads from the Snowflake Marketplace.

<!-- ------------------------ -->
## Introduction To LISTING_EVENTS_DAILY view

To retrieve lead information, we will need to use the `LISTING_EVENTS_DAILY` view in the `DATA_SHARING_USAGE` schema. It lets you query the daily history of consumer activity on listings for the Snowflake Marketplace and data exchanges.

### Event Attributes of Interest

Each event has a set of attributes that we will focus on, specifically those related to leads. The relevant attributes are:

Lead Data:
- `CONSUMER_EMAIL` - Email address for the consumer account (if available).
- `CONSUMER_METADATA` - Other information included by the consumer when the event happened, such as their name or the reason for using a free email address.
- `CONSUMER_ACCOUNT_NAME` - Name of the consumer account.
- `CONSUMER_ORGANIZATION` - Organization name of the consumer account.

Lead Tiering:
- `LISTING_NAME` - Identifier of the listing.
- `LISTING_DISPLAY_NAME` - Display name of the listing.

Attributes that will help us set up automation:
- `LISTING_GLOBAL_NAME` - Global name of the listing. Unique for each listing and is used to create the listing URL.
- `EVENT_DATE` - Date of the event.
- `EVENT_TYPE` - Type of event

We need to determine which events are considered significant. `EVENT_TYPE` attribute will be the suitable attribute for filtering. In this document, the following values are proposed for this attribute:

- `GET` - Consumer creates a database for a free listing, or installs a Snowflake Native App.
- `REQUEST` - Consumer requests a limited trial listing or a free listing in a region where the data is not yet available.
- `TRIAL` - Consumer creates a trial database or installs a trial Snowflake Native App.
- `PURCHASE` - Consumer agrees to be invoiced when paid data in a paid listing is queried.
- `CANCEL PURCHASE` - Consumer decides to stop using the paid data in a paid listing.

The full list of events, along with descriptions, can be found here: [Snowflake Events Documentation](https://docs.snowflake.com/en/sql-reference/data-sharing-usage/listing-events-daily).

As a result, we can build the following query:

```snowflake
SELECT
    event_date,
    event_type,
    listing_global_name,
    listing_display_name,
    consumer_account_name,
    consumer_organization,
    consumer_name,
    CONSUMER_EMAIL,
    CONSUMER_METADATA:first_name as CONSUMER_FIRST_NAME,
    CONSUMER_METADATA:last_name as CONSUMER_LAST_NAME,
FROM
    snowflake.data_sharing_usage.listing_events_daily
WHERE
    event_type IN ('PURCHASE', 'CANCEL PURCHASE', 'GET', 'REQUEST', 'TRIAL');
```

> aside positive
> 
> **Note:** we applied dereferencing here by creating a separate alias for the customer's first name and last name. This will make it easier for us to format the proper message later.

<!-- ------------------------ -->
## Create new Notification Integration

The next step is to create a `NOTIFICATION INTEGRATION`. This document is based on official documentation for setting this up: [Snowflake Notification Integration Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration-webhooks).

Create a Slack webhook using a [guide](https://api.slack.com/messaging/webhooks).

- As output, you need a webhook URL: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`
- the webhook URL contains the secret `T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX` we should protect for this purpose, we will place it in a separate `SECRET` object

Let's create a new database to store all newly created objects.

```snowflake
CREATE DATABASE LEADS_NOTIFICATIONS;
```

Execute the following statement to create a `SECRET` object for the secret T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX that appears in the URL

```snowflake
CREATE OR REPLACE SECRET my_slack_webhook_secret
  TYPE = GENERIC_STRING
  SECRET_STRING = 'T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX';
```

Execute the following statement to create a notification integration for this webhook:

```snowflake
CREATE OR REPLACE NOTIFICATION INTEGRATION my_slack_webhook_int
  TYPE=WEBHOOK
  ENABLED=TRUE
  WEBHOOK_URL='https://hooks.slack.com/services/SNOWFLAKE_WEBHOOK_SECRET'
  WEBHOOK_SECRET=my_secrets_db.my_secrets_schema.my_slack_webhook_secret
  WEBHOOK_BODY_TEMPLATE='{"text": "SNOWFLAKE_WEBHOOK_MESSAGE"}'
  WEBHOOK_HEADERS=('Content-Type'='application/json');
```

You can test the functionality of this notification by executing the following code:

```snowflake
CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
  SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
    SNOWFLAKE.NOTIFICATION.SANITIZE_WEBHOOK_CONTENT('my message')
  ),
  SNOWFLAKE.NOTIFICATION.INTEGRATION('my_slack_webhook_int')
);
```

As a result, the notification should be added to the sending queue and shortly after, Slack should notify us about the new message.

![Slack screen with new new message](assets/slack_message.png)

<!-- ------------------------ -->
## Sending Only New Events

Since we plan to trigger our integration daily, we need to ensure that the same event is not sent twice. To achieve this, I suggest creating a table to track the leads that have already been sent. This table will serve as a log to keep a record of all sent events, allowing us to check for duplicates and prevent sending the same event multiple times.

```snowflake
CREATE TABLE IF NOT EXISTS leads_notification_history
(
    notification_time TIMESTAMP_TZ,
    event_id          STRING
);
```

The `event_id` will be a combination of the following fields:  `event_date`, `event_type`, `listing_global_name`, `consumer_account_name`, and `consumer_organization`. We will store the sent leads in this table.
In the next part, we will create a procedure that will add sent events to this table.

With this in place, we can also enhance the original query for return events whose `event_id` is not found in the `leads_notification_history` table as follows:

```snowflake
SELECT
    event_date,
    event_type,
    listing_global_name,
    listing_display_name,
    consumer_account_name,
    consumer_organization,
    consumer_name,
    CONSUMER_EMAIL,
    CONSUMER_METADATA:first_name as CONSUMER_FIRST_NAME,
        CONSUMER_METADATA:last_name as CONSUMER_LAST_NAME,
FROM
    snowflake.data_sharing_usage.listing_events_daily
WHERE
    CONCAT(event_date, event_type, listing_global_name, consumer_account_name, consumer_organization) NOT IN (
        SELECT
            event_id
        FROM
            leads_notification_history
        WHERE
            notification_time >= DATEADD('day', -4, CURRENT_DATE())
    )
  AND event_type IN ('PURCHASE', 'CANCEL PURCHASE', 'GET', 'REQUEST', 'TRIAL')
  AND exchange_name = 'SNOWFLAKE_DATA_MARKETPLACE'
  AND event_date >= DATEADD('day', -2, CURRENT_DATE())
ORDER BY
    event_date DESC;
```

Two new conditions in this query are worth noting:
- `exchange_name`: This limits the query to the official Snowflake Marketplace.
- `event_date`: Restricts the query to the last two days. These two days are a safe assumption if we plan to run the query once a day, adding a buffer in case the query is not run at the exact same time daily.

> aside positive
>
> **Note:** You can also use other fields if, e.g. If you do not want to send multiple leads with the same email use only the `CONSUMER_EMAIL` field. However, remember to also change this in the rest of the code.


<!-- ------------------------ -->
## Parsing events in JavaScript

Since we assume these steps will be performed quite frequently, I recommend creating an appropriate procedure right away. We decided to write it in **JavaScript**, but the choice of programming language is not essential.

First, we’ll create an empty procedure definition:

```snowflake
create or replace procedure get_events_and_send_notification_for_new_leads()
    returns VARCHAR
    language javascript
as
$$
// Enter javascript code here
$$;
```

In the next part, we will write individual JavaScript functions that will later be incorporated into this procedure.

You can run It by executing the following query:

```snowflake
CALL get_events_and_send_notification_for_new_leads();
```
Result:
```
get_events_and_send_notification_for_new_leads
SUCCESS
```

Now, let’s go through some necessary functions.

### Execute SQL Util
I prepared a useful helper function to avoid code duplication and make it easier to execute SQL commands from JavaScript. This function will be used in other functions later on.

```javascript
function exec(cmd, binds) {
    return snowflake.execute({
		sqlText: cmd,
		binds: binds
	});
}
```

### Find new events

This function contains the SQL query we prepared earlier. It fetches new lead events that have yet to be processed.

```javascript
function findNewEvents() {
    return exec(`
        SELECT
           event_date,
           event_type,
           listing_global_name,
           listing_display_name,
           consumer_account_name,
           consumer_organization,
           consumer_name,
           CONSUMER_EMAIL,
           CONSUMER_METADATA:first_name as CONSUMER_FIRST_NAME,
           CONSUMER_METADATA:last_name as CONSUMER_LAST_NAME,
        FROM
            snowflake.data_sharing_usage.listing_events_daily
        WHERE
            CONCAT( event_date, event_type, listing_global_name, consumer_account_name, consumer_organization) NOT IN (
                    SELECT
                        event_id
                    FROM
                        leads_notification_history
                    WHERE
                        notification_time >= DATEADD('day', -4, CURRENT_DATE())
            )
            AND event_type IN ('PURCHASE', 'CANCEL PURCHASE', 'GET', 'REQUEST', 'TRIAL')
            AND exchange_name = 'SNOWFLAKE_DATA_MARKETPLACE'
            AND event_date >= DATEADD('day', -2, CURRENT_DATE())
        ORDER BY
        event_date DESC;`
    );
}
```
Since we are only interested in new events, the query filters data from the last two days using the condition:

```snowflake
AND event_date >= DATEADD('day', -2, CURRENT_DATE())
```
However, it might be useful to temporarily include historical events for testing purposes. To achieve this, you can remove the date condition so that older events are also considered during testing.

### Processing Lead

Here’s how you can implement a function to process leads. This part will vary depending on the requirements of the system to which you want to send it.

```javascript
function build_json_payload(eventsResultSet) {
    let company_name = eventsResultSet.getColumnValue("CONSUMER_NAME");
    let organization_name = eventsResultSet.getColumnValue("CONSUMER_ORGANIZATION");
    let listing_name = eventsResultSet.getColumnValue("LISTING_DISPLAY_NAME");
    let listing_global_id = eventsResultSet.getColumnValue("LISTING_GLOBAL_NAME");
    let account_name = eventsResultSet.getColumnValue("CONSUMER_ACCOUNT_NAME");
    let consumer_email = eventsResultSet.getColumnValue("CONSUMER_EMAIL");
    let consumer_firstName = eventsResultSet.getColumnValue("CONSUMER_FIRST_NAME");
    let consumer_lastName = eventsResultSet.getColumnValue("CONSUMER_LAST_NAME");
    let payload = {
        "listing_display_name": listing_name,
        "organization_name": organization_name,
        "account_name": account_name,
        "listing_global_id": listing_global_id,
        "consumer_email": consumer_email,
        "consumer_firstName": consumer_firstName,
        "consumer_lastName": consumer_lastName,
        "company_name": company_name
    }
    return Object.entries(payload)
        .map(([key, value]) => `${key} - ${value}`)
        .join(" ");
}
```
> aside positive
>
>  **Note:** Integration with Slack requires a message in text form. If you are considering integrating with another system this function is a perfect start for preparing proper payload.

To integrate this into your overall process, you can call the `build_json_payload` function after fetching and processing new leads. E.g.:

```javascript
let resultSet = findNewEvents();
const results = [];
while (resultSet.next()) {
 results.push(build_json_payload(resultSet))
}
return results;
```

> aside positive
>
>  **Note:**  At this point we decided to process messages one by one using a while loop. If you plan to integrate with a system that allows you to accept multiple leads at once, you will need to modify this part and accordingly update `build_json_payload` to support multiple values.

```javascript
let resultSet = findNewEvents();
const results = [];
while (resultSet.next()) {
 results.push(resultSet)
}
return build_json_payload(results);
```

### Sending the Notification

The `sendNotification` function is responsible for sending the JSON payload to the pre-configured notification integration. The function uses Snowflake's `system$send_snowflake_notification` to send the payload to the specified integration. Here's the complete code:

```javascript
function sendNotification(payload) {
    exec(`call system$send_snowflake_notification(
        SNOWFLAKE.NOTIFICATION.APPLICATION_JSON(?),
        SNOWFLAKE.NOTIFICATION.INTEGRATION('my_slack_webhook_int'))`,
        [payload]);
}
```

The function takes a single argument, `payload`, which is the JSON object that contains the details of the new lead (built by the `build_json_payload` function).

`SNOWFLAKE.NOTIFICATION.INTEGRATION('my_slack_webhook_int')` specifies the notification integration that you set up earlier (in this case, `my_slack_webhook_int`).

### Updating processed leads table

Once new leads have been processed and notifications sent, we need to save them in the `leads_notification_history` table to prevent them from being sent again.
Here’s the function that inserts the processed leads into this history table:

```javascript
function insertSentEventsToHistory(eventsResultSet) {
      let event_date = eventsResultSet.getColumnValue("EVENT_DATE");
      let event_type = eventsResultSet.getColumnValue("EVENT_TYPE");
      let listing_global_name = eventsResultSet.getColumnValue("LISTING_GLOBAL_NAME");
      let consumer_account_name = eventsResultSet.getColumnValue("CONSUMER_ACCOUNT_NAME");
      let consumer_organization = eventsResultSet.getColumnValue("CONSUMER_ORGANIZATION");
          
      exec(`
        INSERT INTO
          leads_notification_history (notification_time, event_id)
        SELECT
          CURRENT_TIMESTAMP(), CONCAT(TO_DATE(:1), :2, :3, :4, :5);
        `, [event_date.toISOString(), event_type, listing_global_name, consumer_account_name, consumer_organization]);
    }
```

### Procedure Logic
Below is a concept of how procedure `get_events_and_send_notification_for_new_leads` could look like:

```javascript
let resultSet = findNewEvents();
if (resultSet.getRowCount() == 0) {
    return "SUCCESS: No new data for new leads, skip execution";
}

let sentNotificationsCount = 0;

while (resultSet.next()) {
    try {
        // Build payload for current lead and send notification
        let payload = build_json_payload(resultSet);

        // Send notification with the built payload
        sendNotification(payload);

        // Insert the processed lead into the history table
        insertSentEventsToHistory(resultSet);

        // Increment the counter of successfully sent notifications
        sentNotificationsCount++;
    } catch (err) {
        // Return the error if any issues occur during the process
        return `ERROR: ${err}`;
    }
}

// Return the final result based on the count of sent notifications
if (sentNotificationsCount == 0) {
    return "FAILURE: No notifications sent";
} else {
    return `SUCCESS: New Leads Processed and Notified: ${sentNotificationsCount}`;
}
```

### Final Code
Here’s the final implementation of the procedure `get_events_and_send_notification_for_new_leads`, incorporating all the previous functions you've built:

```snowflake
create or replace procedure get_events_and_send_notification_for_new_leads()
    returns VARCHAR
    language javascript
as
$$
    let resultSet = findNewEvents();
    if (resultSet.getRowCount() == 0) {
      return "SUCCESS: No new data for new leads, skip execution";
    }

    let sentNotificationsCount = 0;

    while (resultSet.next()) {
      try {
        // Build payload for current lead and send notification
        let payload = build_json_payload(resultSet);
        
        // Send notification with the built payload
        sendNotification(payload);

        // Insert the processed lead into the history table
        insertSentEventsToHistory(resultSet);

        // Increment the counter of successfully sent notifications
        sentNotificationsCount++;
      } catch (err) {
        // Return the error if any issues occur during the process
        return `ERROR: ${err}`;
      }
    }

    // Return the final result based on the count of sent notifications
    if (sentNotificationsCount == 0) {
        return "FAILURE: No notifications sent";
    } else {
        return `SUCCESS: New Leads Processed and Notified: ${sentNotificationsCount}`;
}

    function findNewEvents() {
      return exec(`
        SELECT
           event_date,
           event_type,
           listing_global_name,
           listing_display_name,
           consumer_account_name,
           consumer_organization,
           consumer_name,
           CONSUMER_EMAIL,
           CONSUMER_METADATA:first_name as CONSUMER_FIRST_NAME,
           CONSUMER_METADATA:last_name as CONSUMER_LAST_NAME,
        FROM
            snowflake.data_sharing_usage.listing_events_daily
        WHERE
            TRUE
            AND CONCAT(event_date, event_type, listing_global_name, consumer_account_name, consumer_organization) NOT IN (
                SELECT
                    event_id
                FROM
                    leads_notification_history
                WHERE
                    notification_time >= DATEADD('day', -4, CURRENT_DATE())
            )
            AND event_type IN ('PURCHASE', 'CANCEL PURCHASE', 'GET', 'REQUEST', 'TRIAL')
            AND exchange_name = 'SNOWFLAKE_DATA_MARKETPLACE'
           -- AND event_date >= DATEADD('day', -2, CURRENT_DATE())
        ORDER BY
            event_date DESC;`);
    }

function build_json_payload(eventsResultSet) {
      let company_name = eventsResultSet.getColumnValue("CONSUMER_NAME");
      let organization_name = eventsResultSet.getColumnValue("CONSUMER_ORGANIZATION");
      let listing_name = eventsResultSet.getColumnValue("LISTING_DISPLAY_NAME");
      let listing_global_id = eventsResultSet.getColumnValue("LISTING_GLOBAL_NAME");
      let account_name = eventsResultSet.getColumnValue("CONSUMER_ACCOUNT_NAME");
      let consumer_email = eventsResultSet.getColumnValue("CONSUMER_EMAIL");
      let consumer_firstName = eventsResultSet.getColumnValue("CONSUMER_FIRST_NAME");
      let consumer_lastName = eventsResultSet.getColumnValue("CONSUMER_LAST_NAME");
    let payload = {
        "listing_display_name": listing_name,
        "organization_name": organization_name,
        "account_name": account_name,
        "listing_global_id": listing_global_id,
        "consumer_email": consumer_email,
        "consumer_firstName": consumer_firstName,
        "consumer_lastName": consumer_lastName,
        "company_name": company_name
      }
     
      return Object.entries(payload)
            .map(([key, value]) => `${key} - ${value}`)
            .join(" ");
      }

    function sendNotification(payload) {
        exec(`call system$send_snowflake_notification(
        SNOWFLAKE.NOTIFICATION.APPLICATION_JSON(?),
        SNOWFLAKE.NOTIFICATION.INTEGRATION('my_slack_webhook_int'))`,
          [payload]);
    }

    function insertSentEventsToHistory(eventsResultSet) {
      let event_date = eventsResultSet.getColumnValue("EVENT_DATE");
      let event_type = eventsResultSet.getColumnValue("EVENT_TYPE");
      let listing_global_name = eventsResultSet.getColumnValue("LISTING_GLOBAL_NAME");
      let consumer_account_name = eventsResultSet.getColumnValue("CONSUMER_ACCOUNT_NAME");
      let consumer_organization = eventsResultSet.getColumnValue("CONSUMER_ORGANIZATION");
          
      exec(`
        INSERT INTO
          leads_notification_history (notification_time, notification_type, event_id)
        SELECT
          CURRENT_TIMESTAMP(), CONCAT(TO_DATE(:1), :2, :3, :4, :5);
        `, [event_date.toISOString(), event_type, listing_global_name, consumer_account_name, consumer_organization]);
    }
    
    function exec(cmd, binds) {
      return snowflake.execute({
        sqlText: cmd,
        binds: binds
      });
    }
$$;
```
You can execute the procedure by calling it:

```snowflake
CALL get_events_and_send_notification_for_new_leads();
```
To check the status of notifications you can call:

```snowflake
SELECT * FROM TABLE(INFORMATION_SCHEMA.NOTIFICATION_HISTORY());
```

<!-- ------------------------ -->
## Automating Lead Notifications

The solution described above enables easy lead processing and notifications but still requires manual execution. To streamline this, we can automate the process by creating a Snowflake Task. A task can be scheduled to automatically run the `get_events_and_send_notification_for_new_leads` procedure at specified intervals without manual intervention.

Here’s how you can create a Snowflake Task to automate the execution of the procedure.

```snowflake
CREATE OR REPLACE TASK lead_notification_task
    SCHEDULE = 'USING CRON 0 12 * * * UTC' -- Runs daily at 12:00 UTC
    SERVERLESS_TASK_MAX_STATEMENT_SIZE='MEDIUM' 
    COMMENT = 'Task to automate the sending of new lead notifications'
AS
    CALL get_events_and_send_notification_for_new_leads();
```

Once the task is created, you need to **activate** it to start running on the specified schedule:

```snowflake
ALTER TASK lead_notification_task RESUME;
```

To monitor the status of the task or check if it has run successfully, you can query the task history:

```snowflake
SHOW TASKS LIKE 'LEAD_NOTIFICATION_TASK';
```

You can manually trigger a single run of a task:

```snowflake
EXECUTE TASK LEAD_NOTIFICATION_TASK;
```

If you ever need to delete the task, you can do so with the following command:

```snowflake
DROP TASK IF EXISTS LEAD_NOTIFICATION_TASK;
```

> aside positive
>
> **Note:** Ensure that the task has the necessary access to both the database and the `leads_notification_history` table.

For more details on how to create and manage tasks in Snowflake, you can visit the official documentation: [Snowflake Task Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-task).

<!-- ------------------------ -->
## Calculating the Cost of the Solution
Before implementing the automated lead notification solution, it’s important to understand the potential costs involved. Snowflake charges for both compute resources (warehouses) and data storage. The main factors influencing the cost of this solution are:
- Warehouse Usage: The task uses the designated warehouse each time it runs. The cost will depend on how long the warehouse is active during each execution and its size.
- Storage Costs: The task processes leads, which are stored in the leads_notification_history table. The amount of data stored will depend on the number of leads and the data retention period.

<!-- ------------------------ -->
## Conclusion and Resources

### Conclusion

In this guide, we walked through the process of setting up a notification integration to send lead information from the Snowflake Marketplace to Slack. We used a JavaScript procedure to format the messages and created a task to automate the process. This solution can be easily customized to integrate with other systems or to process different types of events.

### Possible Improvements
Some additional steps that could further enhance this solution include:
- **Check whether the notification was sent** and further mark the leads as sent based on this.

### What You Learned
- How to analyze Snowflake Marketplace lead events
- How to export lead data using Notifications
- How to send a Slack message using webhooks
- How to automate the process using Snowflake Tasks

### Related Resources
- [Snowflake Notification Integration Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration-webhooks)
