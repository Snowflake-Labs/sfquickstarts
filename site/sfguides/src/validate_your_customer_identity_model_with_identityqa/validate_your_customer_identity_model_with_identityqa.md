author: Simon Data
id: validate_your_customer_identity_model_with_identityqa
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 
Duration: 1

Please use [this markdown file](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) as a template for writing your own Snowflake Quickstarts. This example guide has elements that you will use when writing your own guides, including: code snippet highlighting, downloading files, inserting photos, and more. 

It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build. Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code).

The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- how to set the metadata for a guide (category, author, id, etc)
- how to set the amount of time each slide will take to finish 
- how to include code snippets 
- how to hyperlink items 
- how to include images 

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed
- [GoLang](https://golang.org/doc/install) Installed

### What You’ll Build 
- A Snowflake Guide

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: sample 
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Science, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Daniel Myers 
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

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

1. Overview

In this guide, we’ll be walking you through how to validate that the assumptions you’ve made about your identity model are correct using Simon Data’s Snowflake Native App, IdentityQA.  All source code for this guide can be found on GitHub.  Let’s get going!


## Prerequisites



* A Snowflake account with an accessible warehouse, database, schema, and role 
    * The role must have the ability to install Snowflake native apps & grant usage to the application (the ACCOUNTADMIN role works here)


## What You’ll Need



* A basic understanding of your company’s identity model and the relationships between customer identifiers
* A single source table that contains at least two identifier columns to validate (e.g. user_id & email_address)


## What You'll Learn



* How to install & use a Snowflake native app
* Whether or not the assumptions you’ve made about your company’s identity model are true
    * For example: is your stable identifier truly unique?  Is user_id truly 1:1 with email_address?
* % of invalid email addresses & phone numbers in your identity table with examples of each for easy cleanup
* How to improve your identity model based on the native app’s findings


## What You'll Build



* A QA report on your company’s identity model that provides insights into how the model and/or underlying data can be improved to support better & more accurate marketing use cases
2.  Application Architecture

First, it’s important to understand how Snowflake native apps work and the benefits they provide from a security & privacy standpoint.



* Provider (in this case, Simon Data) creates an application package with manifest (metadata), setup script (SQL), and business logic (resource files).
* Provider publishes the application package as a listing on the Snowflake native app marketplace.
* Consumer (in this case, you) installs the application package from the listing in their own Snowflake account in order to create the application.



<p id="gdcalert1" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image1.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert2">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image1.png "image_tooltip")


By default, the application has no permissions to do anything in your Snowflake account.  You must grant account- & object-level privileges to the application.  Once permission is granted, the app only has read-only access to the data within and will never make any changes or transformations to the data.  Once the app is run, the output is a set of tables in the application schema that you can query to see the results of the QA on your identity model.



1.  App Setup

In Snowflake, under **Marketplace**, search for Simon Data’s **_IdentityQA_** listing.  Click **Get** to request the application for your Snowflake account. 



<p id="gdcalert2" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image2.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert3">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image2.png "image_tooltip")


You will be asked to select a warehouse to be used for installation and name the application.



<p id="gdcalert3" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image3.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert4">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image3.png "image_tooltip")


In Snowflake, under **Data → Private Sharing**, install the **_IdentityQA_** listing. 

Once installed, you'll have to change the name of the app to what you named it upon installation by running the following command in a worksheet:


```
CREATE APPLICATION <CHOSEN APP NAME>
  FROM APPLICATION PACKAGE IDQAAPP;
```


Expand the **APP** schema and see a number of **Procedures**.  This guide will walk you through how to use those procedures.

Before the app can run, however, you need to give it access to the correct database, schema, and table. Run the following commands:


```
GRANT USAGE ON DATABASE <YOUR_DATA_DB_NAME> to APPLICATION <CHOSEN APP NAME>;  
GRANT USAGE ON SCHEMA <YOUR_DATA_SCHEMA_NAME> to APPLICATION <CHOSEN APP NAME>;  
GRANT SELECT ON TABLE <YOUR_TABLE_NAME> TO APPLICATION <CHOSEN APP NAME>;

```



* **YOUR_DB_NAME** is the database name that contains your input table or view and will contain the IdentityQA output.
* **YOUR_SCHEMA_NAME** is the database schema from the last argument that contains your input table or view and will contain the IdentityQA output.
* **YOUR_TABLE_NAME** is the table name that will serve as the input for the IdentityQA application.
2.  Streamlit

The following instructions are also available in the **IdentityQA Streamlit**. To navigate to the Streamlit, follow the steps below: 



* Return to **Snowsight**.
* Click **Apps** in the lefthand navigation bar.
* Select the **IdentityQA** application, which will appear as whatever you named the app upon installation.
* Select a warehouse in the upper righthand corner of the Streamlit if one is not chosen already.
* Your Streamlit will now load! 
* The following pages are available to you:
    * **Welcome**
        * This page gives an overview of what to expect when using the app.
    * **How It Works**
        * A duplicate of this document! Detailed, step-by-step instructions on how to use the app.
    * **Configuration**
        * Once you've run some of the commands listed below and on the **How It Works** page, your identity configurations will appear on this page. 
    * **Report**
        * Once you've run the app end-to-end, your identity report will appear on this page.
    * **About Simon Data**
3.  Set Input Table

In a worksheet, run the **SET_INPUT_TABLE** stored procedure, as follows. Be sure to include as many lines as you have identifiers in your source table.


```
CALL <CHOSEN APP NAME>.APP.SET_INPUT_TABLE('SOURCE_TABLE', 
[['SOURCE_COLUMN', 'IDENTIFIER_TYPE', IS_STABLE],
['SOURCE_COLUMN', 'IDENTIFIER_TYPE', IS_STABLE],
['SOURCE_COLUMN', 'IDENTIFIER_TYPE', IS_STABLE]]);

```



* **SOURCE_TABLE** is the table name you specified when setting up and granting usage to the app. This should be fully qualified, meaning it should be formatted like: 'YOUR_DB_NAME.YOUR_SCHEMA_NAME.YOUR_TABLE_NAME'
* **SOURCE_COLUMN** is the column name that contains the identifier you are configuring.
* **IDENTIFIER_TYPE** defines the type of identifier in the previous argument.  Examples of supported identifier types are:
    * email
    * user_id
    * phone_number
    * custom_id
    * NOTE: **email** and/or **phone_number** must be included (and named in this format) in order for some identifier validations to run.  
* **IS_STABLE** is a boolean field that tells us whether or not the identifier should be stable. A stable identifier is one that is unique, is 1:1 with a single profile, and cannot be shared across profiles.
    * If the identifier you’re configuring is stable, put **TRUE** here. If it is not stable, put **FALSE**.
    * **NOTE: By definition, you can only have one stable identifier.**


### **EXAMPLE QUERY:**


```
CALL <CHOSEN APP NAME>.APP.SET_INPUT_TABLE('SOURCE_TABLE', [['EMAIL_ADDR', 'EMAIL', FALSE),  
                                                            ['PHONE_NBR', 'PHONE_NUMBER', FALSE],  
                                                            ['USER_ID', 'USER_ID', TRUE]]);

```



4.  Set Constraints

Once you've configured your identifiers, you can set certain constraints (or assumptions) to validate. These constraints outline the relationships between two identifiers (i.e. 1:1 or 1:many) and identifier-specific limits (e.g. device_id can be shared across a maximum of 5 profiles).


### **SET_RELATIONSHIP_CONSTRAINT**


```
CALL <CHOSEN APP NAME>.APP.SET_RELATIONSHIP_CONSTRAINT('RELATIONSHIP_TYPE', 'IDENTIFIER_1', 'IDENTIFIER_2');
CALL <CHOSEN APP NAME>.APP.SET_RELATIONSHIP_CONSTRAINT('RELATIONSHIP_TYPE', 'IDENTIFIER_2', 'IDENTIFIER_1');

```



* **RELATIONSHIP_TYPE** is the relationship between the identifiers in the next two arguments.  **The only supported type today is ONE-TO-ONE.** Later versions of the app will support other types, such as ONE-TO-MANY.
* **IDENTIFIER_1** is the name of the first identifier for which you’re validating the relationship type.
* **IDENTIFIER_2** is the name of the second identifier for which you’re validating the relationship type.

NOTE: If you want to check the 1:1 relationship going both ways, make sure you set two relationship constraints. If you only check the 1:1 relationship going one way (e.g. 1 user_id per email address only), you may get a false positive in the report. In this case, you would also want to check for 1 email address per user_id.


#### **SET_RELATIONSHIP_CONSTRAINT EXAMPLE QUERY:**

The query below tells the application to validate whether or not **user_id** and **email** truly have a 1:1 relationship. If there are instances where the 1:1 relationship constraint is invalidated, the app flags them in the generated report.


```
CALL <CHOSEN APP NAME>.APP.SET_RELATIONSHIP_CONSTRAINT('ONE-TO-ONE', 'USER_ID', 'EMAIL_ADDR');
CALL <CHOSEN APP NAME>.APP.SET_RELATIONSHIP_CONSTRAINT('ONE-TO-ONE', 'EMAIL_ADDR', 'USER_ID');
```



### **SET_UNIQUE_CONSTRAINT**

This constraint checks for the uniqueness of the values for a particular identifier.


```
CALL <CHOSEN APP NAME>.APP.SET_UNIQUE_CONSTRAINT('IDENTIFIER_NAME');

```



* **IDENTIFIER_NAME** is the name of the identifier for which you want to check the uniqueness.


#### **SET_UNIQUE_CONSTRAINT EXAMPLE QUERY:**


```
CALL <CHOSEN APP NAME>.APP.SET_UNIQUE_CONSTRAINT('EMAIL');
```



### **NOTE**


    If you set a shared identifier limit, you should _not_ run a uniqueness check on your stable identifier or else you'll get a false negative.


     


    This is because if a non-stable identifier can be shared across profiles, there are inherently going to be multiple rows for a single stable identifier in your input table.


### **SET_SHARED_IDENTIFIER_LIMIT**

This constraint sets a maximum threshold for which a single identifier can be shared across different profiles. 


```
CALL <CHOSEN APP NAME>.APP.SET_SHARED_IDENTIFIER_LIMIT('IDENTIFIER_NAME', THRESHOLD);

```



* **IDENTIFIER_NAME** is the name of the identifier for which you want to set a maximum threshold.
* **THRESHOLD** is the maximum number of different profiles on which the IDENTIFIER_NAME in the previous argument can exist. This field should be an integer.


#### **SET_SHARED_IDENTIFIER_LIMIT EXAMPLE QUERY:**

A customer may have a landline that they share with everyone in the household. Let’s say the average number of people in a household is 3 and you believe your customer base tends to have landlines. You could set your shared identifier limit threshold to 3 to validate this assumption.


```
CALL <CHOSEN APP NAME>.APP.SET_SHARED_IDENTIFIER_LIMIT('phone_number', 3);

```



5.  Generate Report


## Manual Inspection

Run the following stored procedure to generate your IdentityQA report!


```
CALL <CHOSEN APP NAME>.APP.generate_report();
```


The output will be available in the following tables in the **REPORT** schema within the **SIMON_IDENTITY_QA** application as well as on the **Report** page in the Streamlit. To query the tables directly in the REPORT schema within the application, you can run the following:


```
-- RUN THIS QUERY TO PULL THE TABLE NAMES SPECIFIC TO YOUR IDENTIFIERS
SELECT * FROM <CHOSEN APP NAME>.REPORT.CARDINALITY_CHECK_TABLES
-- THEN RUN A SELECT * ON EACH OF THE TABLES GENERATED.  FOR EXAMPLE:
SELECT * FROM <CHOSEN APP NAME>.REPORT.CARDINALITY_CHECK_USER_ID_EMAIL

-- THE REST OF THESE QUERIES CAN BE RUN TO INSPECT OTHER RESULTS
SELECT * FROM <CHOSEN APP NAME>.REPORT.IDENTIFIER_VALIDATION
SELECT * FROM <CHOSEN APP NAME>.REPORT.INVALID_IDENTIFIERS
SELECT * FROM <CHOSEN APP NAME>.REPORT.RELATIONSHIP_CONSTRAINTS_CHECK
SELECT * FROM <CHOSEN APP NAME>.REPORT.SHARED_IDENTIFIER_LIMIT_CHECK
SELECT * FROM <CHOSEN APP NAME>.REPORT.UNIQUE_CONSTRAINTS_CHECK
```



## Streamlit Report

To view your report in Streamlit, return to the app & launch it in Streamlit. Steps below:



* If you're in a worksheet, click the **back arrow** in the top left corner of your screen to return to Snowsight.
* Click **Apps**. Make sure you're in the correct Snowflake role!
* Click the **SIMON_IDENTITY_QA** application to launch the Streamlit. The name of the app on this page should be what you named it upon installation.
* Select a warehouse in the upper righthand corner of the Streamlit if one is not chosen already.
* Your Streamlit will now load! It may take a little while depending on how many rows of data you ran through the application.
* Click on the **Report** page in the lefthand navigation of the Streamlit.
6.  Interpreting the Report

This is an example input table that we used to generate the report shown in screenshots below.  

<p id="gdcalert4" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image4.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert5">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image4.png "image_tooltip")


NOTE: Additional screenshots in this section are from the Streamlit report.

The top of the report shows you the name of the input table you configured as well as the total number of rows in said input table.



<p id="gdcalert5" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image5.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert6">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image5.png "image_tooltip")



## Constraint Checks

Next, the report will show pass/fail statuses on the constraints you configured.  

As you can see in the screenshot below, the **client_id** & **email** identifiers passed the 1:1 relationship check going one way but not the other.  This tells you that for every **client_id** there is only one **email**, but the app found instances where an **email** had more than one **client_id**.  Examples of these failures will be explored later.



<p id="gdcalert6" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image6.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert7">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image6.png "image_tooltip")


Additionally, the shared identifier limit check failed on **phone_number**.  This means that the app discovered instances where a single **phone_number** appears on more than 3 profiles, which violates the assumption that **phone_number** is shared at most across 3 profiles at any given time.  


## Cardinality Checks

The next check is a high-cardinality test for each identifier in the input table compared to the stable identifier.  IdentityQA tests for cardinality because exceptionally high counts of any identifier per single stable identifier generally mean that there is an issue with the underlying data.  In the screenshot below, you can see that there are 10 profiles that have an abnormally high count of **client_ids** compared to the other 15 profiles in the sample.  This tells you that these emails may be fake, or maybe they’re emails used for testing purposes and should be excluded from marketing. 

Your next step here should be to dive into these email addresses and determine why they might have so many **client_ids** associated with them and if they’re valid profiles or not. 



<p id="gdcalert7" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image7.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert8">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image7.png "image_tooltip")



## Identifier Validation

Next, the report shows **email** & **phone_number** validations.  You can see in this example that out of the ~1M total records in the input table, ~30K emails are considered invalid and ~80M phone numbers are considered invalid.  

NOTE: “Invalid” in this case means that the email or phone number is missing one or more properties in order to be considered a “valid” identifier.  Example: emails with no “@” are flagged here, as well as phone numbers with letters in them or fewer/greater than 10 numbers.  

We are not testing whether or not these emails or phone numbers belong to real people rather than bots. 



<p id="gdcalert8" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image8.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert9">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image8.png "image_tooltip")




<p id="gdcalert9" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image9.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert10">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image9.png "image_tooltip")




7.  Conclusion & Resources

Congratulations!  You’ve successfully QA’d your customer identity model using Simon Data’s Native Snowflake App, **IdentityQA**!  You now have the insight you need to be able to finetune & improve your identity model.  


## What You Learned



* How to install & use a Snowflake native app
* Whether or not the assumptions you’ve made about your company’s identity model are true
* % of invalid email addresses & phone numbers in your identity table with examples of each for easy cleanup
* How to improve your identity model based on the native app’s findings


## Related Resources



* Source code on GitHub
* [IdentityQA docs](https://docs.simondata.com/developers/docs/identityqa)