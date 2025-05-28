author: Ian Maier
id: build_an_offsite_commerce_media_network_on_snowflake
summary: Build a commerce media platform for audience curation, offsite activation, and closed-loop measurement.
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Marketing
environments: dais <!--- What is the correct environment for the DAIS hands-on lab? -->
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Marketing, Partners, Media, Hightouch, Retail, Commerce

# Build an Offsite Commerce Media Network on Snowflake with Hightouch & The Trade Desk
<!-- ------------------------ -->
## Overview 
Duration: 1

In this guide you will learn how to transform your existing Snowflake investment into a user-friendly platform that a non-technical commerce media team can use to curate custom audiences, activate and share them with their advertising partners, and provide closed-loop attribution.

### Business Scenario
We are building a Travel Media Network for a global luxury hospitality conglomerate called Altuva, which owns multiple hotel brands with millions of  visitors annually. We are partnering with a high-end Consumer Packaged Goods company called Omnira, which sells luxury snacks, beverages, and health & wellness amenities within most of Altuva's hotels. Omnira has approached us with a specific campaign idea: they want to promote their chocolate truffles to your hotel visitors in the 30 days before their arrival to influence more in-hotel consumption.

Our task is to build a platform that our non-techincal media team can use to create a highly customized audience, share the audience with Omnira, and provide them with the data & reporting to attribute the ads they run to in-hotel purchases.

### Prerequisites
- N/A

### What You’ll Learn 
- How to enrich Snowflake with UID2s using the Native App for privacy-safe activation and measurement.
- How to build a visual audience builder on top of Snowflake using Hightouch.
- How to activate audiences on The Trade Desk using Hightouch, for both managed service and self-service campaign execution.
- How to send offline conversion events from Snowflake to The Trade Desk using Hightouch.
- How to execute The Trade Desk campaigns using shared audiences and conversion events.
- How to build SKU-level attribution reporting on Snowflake using The Trade Desk's Raw Event Data Stream (REDS). 

### What You’ll Need 
- A Snowflake account login with a role that has the permissions to create a new database, schema, and warehouse to be used by Hightouch.
- A Hightouch account with Customer Studio access. You can [sign up for a free Hightouch account here](https://app.hightouch.com/signup). Please [contact our team](https://hightouch.com/demo) to inquire about Customer Studio access.

### What You’ll Build 
- A Snowflake-native visual audience builder that is customized to your luxury hospitality brand's unique data & offering
- An activation platform for syndicating audiences and conversion events
- Closed-loop attribution reporting with SKU-level breakdowns

<!-- ------------------------ -->
## Import the mock datasets
Duration: 1

<!-- ------------------------ -->
## Enrich Snowflake with UID2
Duration: 1

<!-- ------------------------ -->
## Connect Hightouch to Snowflake
Duration: 1

### Log into Snowflake
If you already have a Snowflake account, you can use your credentials to log in. If you do not already have an account, you can visit [https://signup.snowflake.com/]https://signup.snowflake.com/ to sign up for a 30-day free trial. You will want to make sure that the account you use in Snowflake has the permissions to create a new database, schema, and warehouse to be used by Hightouch.

### Connect Hightouch through Partner Connect
1. Click the Partner Connect tab under Admin.
2. Search for Hightouch (or scroll to the Data Integration section), and select it.
3. View the Database, Warehouse, User, and Role that will be created for the integration, and click Launch.
4. When the creation is complete, you will see a pop-up telling you that the creation has finished. Click Activate to be taken to Hightouch to log in.
5. A new window will open where you are prompted to sign in to Hightouch. Once signed in, you will want to create an existing workspace.
6. Once a selection has been made, your Hightouch workspace will open with your Snowflake source configured in the sources tab.

### Enable audience snapshots
This will allow Hightouch to save snapshots of audience member IDs in your data warehouse after each sync of an audience. This will be useful when creating holdout groups to measure incrementality, since the holdout group snapshot will be saved in Snowflake for measurement in the future.
1. Go to **Integrations > Destinations** and select your Snowflake data source.
2. Select the **Sync Logs** tab at the top, enable **Audience Snapshots**, and click **Save changes**. 

<!-- ------------------------ -->
## Connect Hightouch to The Trade Desk
Duration: 1

Next, we will connect Hightouch to The Trade Desk so that you can sync audiences and conversion events from Snowflake to the ad platform.

### Create a Trade Desk destination
To push data to The Trade Desk you need to create a destination. Hightouch offers integrations with a number of different audience and conversion endpoints with The Trade Desk, including first-party audiences, CRM audiences, and third-party audiences that allow you to list them on the 3rd party data marketplace. For the sake of simplicity in this Quickstart, we will connect to The Trade Desk using the first-party endpoints. This allows us to either execute campaigns from our own advertising account for managed services or share the audience with our advertising partner's account for self-service.

To connect The Trade Desk destination:
1. Navigate to **Integrations > Destinations** and click **Add Destination**.
2. Search for **The Trade Desk**, select it, and click **Continue**.
3. Scroll down to the **First-Party Data Segment** section. Select the appropriate **environment** (e.g. server location of your choice) and provide the **Advertiser ID** and **Advertiser secret key** provided by The Trade Desk.
You can obtain your decoded advertiser secret key for uploading first-party data from your advertiser preferences page in The Trade Desk UI. If you can't find your secret key, contact your Account Manager. When you send data, the included secret key is validated against the secret key the platform has on file for the Advertiser ID.
4. Scroll down further to the **Conversion event integration** section. Input the **Advertiser ID**, **Advertiser secret key**, and **Offline data provider ID** provided to you by The Trade Desk.
5. Name the destination (e.g. The Trade Desk - Altuva) and click **Finish** to create the destination.

<!-- ------------------------ -->
## Build the audience schema
Duration: 1

INSERT BLURB ABOUT WHAT THE SCHEMA IS

### Create a Customer parent model
Parent models define the primary dataset you want to build your audiences off. In this example, we will create a Customers table that represents all Altuva Brands customers who have visited a hotel and/or signed up as a loyalty member.

To create a [parent model](https://hightouch.com/docs/customer-studio/schema#parent-model-setup) for Altuva use the following steps:
1. Go to the [Schema page](https://app.hightouch.com/schema-v2/view).
2. Select your Snowflake data source from Step 5 by selecting it from the dropdown.
3. Click **Create parent model**.
4. Select the **Customers** table from the Altuva database.

By default, Hightouch prompts you to select a table in your source. If you prefer to use a custom SQL query, dbt model, or another modeling method to define your own model, you can change it from the modeling method dropdown.
5. Once you've defined your model and previewed the results, click **Continue**.
6. Enter a **name** for your parent model. In this example, use “Customers”.
7. Select a **primary key**. You must select a column with unique values. In this example, we will use **CUSTOMER_ID** for the primary key.
8. Select columns for the model's **primary label** and **secondary label**. Hightouch displays these column values when previewing audiences. In this example, we will use **FIRST_NAME** as the primary label and **LAST_NAME** as the secondary label.
9. Click **Create parent model**.

The parent model now appears in the schema builder. You can edit an existing parent model by clicking on it and making changes in the Query tab. For more configuration options, refer to the [column configuration](https://hightouch.com/docs/customer-studio/schema#column-configuration) section.

### Create Memberships related model
Related models and events provide additional characteristics or actions on which you can filter your parent model. When you create a related model, you simultaneously set up the relationship between it and other objects in the schema.

We will start by creating a related model for Loyalty Memberships which has a 1:1 relationship between customers and memberships (e.g., customers can only hold one membership at a time).

![ Memberships ERD ]()

The Memberships related model will provide information like signup date, membership tier, and point level. This information will be used when building audiences so that advertisers can target Altuva Loyalty Members with specific offers based on their eligibility and suppress certain members based on known food allergies.

1. Click the **+** button on the **Customers parent model** that you created before and select **Create a related model**.
2. Select the **Memberships** table using the table selector and click **Continue**.
3. If you are building a schema using your own data, you can also use a custom SQL query, dbt model, or another modeling method by changing it from the modeling method dropdown.
4. Enter a **name** for your related model. In this example, name it “Memberships”.
5. Define the related model's **Relationship**. In this example, select the relationship's cardinality as **1:1**.
6. To join rows from the related model to rows in the parent model, select the relevant **foreign key columns** from the parent (Customers) and related model (Memberships). In this example, select **Membership_ID** under the Memberships model and select **Loyalty_ID** under the Customers model.
7. Turn on **Merge columns** to add columns from the parent model onto the related model.
8. Click **Create related model**.

The related model now appears in the schema builder. You can edit an existing related model by clicking on it and making changes in the Query tab.

![IMAGE OF PARENT AND RELATED MODEL]()

### Create a Hotel Visits event model
Event definition is a one-time step similar to related model setup. The only difference is that event models require a timestamp column.

In this example, we will create an event model for **Hotel Visits**. These events will be used to create audiences of upcoming visitors so that advertisers can influence Altuva visitors to purchase and use their in-hotel products. It will include data points like check-in date, check-out date, and hotel name.

![Hotel Visits ERD]()

1. Click the **+** button on the **Customers parent model** and select **Create a related event**.
2. Select the **Hotel Visits** table and click **Continue**.
3. If you are building a schema using your own data, you can also use a custom SQL query, dbt model, or another modeling method by changing it from the modeling method dropdown.
4. Enter a **name** for your event model. For this example, use "Hotel Visits."
5. Define the related event's **Relationship**. Select the relationship's cardinality **1:many**, because every 1 Customer can have many Hotel Visits.
6. Click **Create event**.
7. The **Hotel Visits event model** should now appear in the schema builder. You can edit an existing event model by clicking on it and making changes in the **Query** tab.

### Create a Hotels related model
Related models can also be connected to event models. This enables you to connect additional metadata to your events to provide more granular audience segmentation and conversion tracking.

In this example, we will create a **Hotels related model** that holds detailed information about the hotel that each customer is visiting, including the hotel brand and amenities. We will use this information to provide advertisers with the ability to segment customers based on which hotels they are visiting. This is important for certain advertisers who only sell their products through certain hotel brands.

![HOTELS ERD]()

1. Click the **+** button on the Hotel Visits event model and select **Create a related model**.
2. Select the **Hotels** table and click **Continue**.
3. Name your model "Hotels."
4. Define the related event's **Relationship**. Select the relationship's cardinality **1:1**.
5. Turn on **Merge columns** to add columns from the parent model onto the related model.
6. Click **Create related model**.

### Create a Purchase event model
Use the same steps we will create a model for Purchase events.

![Purchase Event ERD]()
1. Click the **+** button on the **Customers parent model** and select **Create a related event**.
2. Select the **Purchases** table and click **Continue**.
3. Name your model "Purchases."
4. Define the related event's **Relationship**. Select the relationship's cardinality **1:many**.
5. Click **Create event**.

### Create a Product Catalog related model
Finally, we will create a Product Catalog related model. This model contains detailed information about the type of products that the customer purchases at the hotel, including the brand, SKU, and price. This information will be used to enable advertisers to exclude people who recently purchased products from their brand.

![Products ERD]()

1. Click the **+** button on the **Purchases event model** and select **Create a related model**.
2. Select the **Product Catalog** table and click **Continue**.
3. Name your model "Product Catalog."
4. Define the related event's **Relationship**. Select the relationship's cardinality **1:many**.
5. Click **Create related model**.

<!-- ------------------------ -->
## Create a custom audience for monetization
Duration: 1

Now that we've built the audience schema, our non-technical media team can use Hightouch's audience builder to segment across all of the objects and events we have defined. We will use this audience builder to create a custom audience for our CPG partner's specific campaign.

Omnira wants to run an influence campaign to encourage Altuva visitors to buy and eat their truffles located in the minibar. But they want to carefully segment the audience to ensure the campaign is as effective as possible:
- Target customers with a visit coming up in the next 30 days
- Exclude recent purchasers
- Exclude visitors of the Cavara Residences, since they don’t offer the truffles there
- Exclude members with dairy allergies, since the truffles contain dairy

For most CDPs and audience managers, this audience would be too complex to build without the help of data engineering since most platforms don't have the concept of "hotel visits", "loyalty memberships", or "hotels". But with the customized schema we built using our Snowflake data, a business user in Hightouch can build this audience in a few minutes without limitations.

To build the audience:
1. Go to **Customer Studio > Audience** and click **Add audience**.
2. Select the **Customers parent model**.
3. Build the audience to match the definition here:
![Audience Definition]()

1. Select **Add filter** and choose **Events > Hotel Visits**. The frequency should be **at least 1 time**.
2. Select **Where event property is** and choose the **CHECK_IN_DATE** field, and select **within next 1 months**.
3. Select **Where event property is** again and choose the **HOTEL_BRAND** field. Click the **equals** box and change the logic to **does not equal** **Cavara Residences**.
4. Select **Add filter** and choose **Events > Purchases**.
5. Click on the filter that says **at least 1 time** and change the frequency to **at most 0 times**.
6. Select the **Time window filter** on the **Purchase event** and change the filter to **within the previous 1 year**.
7. Select **Add filter** and choose **Relations > Memberships**.
8. Select the **Where** filter and click **ALLERGIES**. Set the logic to **does not equal dairy**.
9. Scroll back to the top and click **Calculate size** to get an estimate of the number of customers in the audience.
10. Click **Continue** at the bottom. Name the audience “Omnira Truffle Influence Campaign” and click **Finish** to save the audience.

<!-- ------------------------ -->
## Sync the audience to The Trade Desk
Duration: 1

Now we will sync the audience that we created to The Trade Desk for targeting. For managed services, the audience can be used immediately in campaigns from Altuva’s Trade Desk seat.

1. Click **Add sync** from the Omnira Truffle Influence Campaign audience page.
2. Select **First-party data segment**. This will allow you to create, sync, and refresh a first-party audience to The Trade Desk using UID2 as the match key.
3. Keep the **create new segment** setting on and leave the **segment name** blank. The sync will automatically inherit the audience name, “Omnira Truffle Influence Campaign”.
4. Select the **UID2** field from your Snowflake Customers table. Make sure it is mapped to the **Unified ID 2.0 (UID2)** field from The Trade Desk. Click **Continue**.
5. Set the **Schedule Type** to **Interval**. Set the schedule to **Every 1 Day(s)**. With this interval set, Hightouch will automatically add and remove the appropriate users on a daily basis, ensuring your audience is always fresh and complies with opt-out requests.

<!-- ------------------------ -->
## Share the audience with the advertising partner
Duration: 1

<!-- ------------------------ -->
## Create a brand-specific conversion model
Duration: 1

<!-- ------------------------ -->
## Create an Offline Conversion Sync to The Trade Desk
Duration: 1

<!-- ------------------------ -->
## Share the conversion data with the advertiser
Duration: 1

<!-- ------------------------ -->
## Advertiser: Run a self-service campaign
Duration: 1

<!-- ------------------------ -->
## Set up REDS data sync
Duration: 1

<!-- ------------------------ -->
## Create attribution report
Duration: 1

<!-- ------------------------ -->
## Conclusion
Duration: 0





<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.


> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files
