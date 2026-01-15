id: liveramp-identity-and-translation-quickstart
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/community-sourced, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Identity Resolution and Transcoding with LiveRamp and Snowflake 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Identity Resolution and Transcoding with LiveRamp and Snowflake
<!-- ------------------------ -->
## Overview 

In this guide, we walk through how to use LiveRamp to create an Identity Key on top of Snowflake.

Being able to join, consolidate and measure different data sources that are using different keys (Name, Address, Phone, Email, Cookies, Maids, Connected TVs) by using LiveRamp Identity resolution keys. 


### Target Audience
- Data Engineering teams wanting to consolidate, measure or collaborate using a secure common identifier versus raw or hashed PII

### What You’ll Learn 
- How to setup an Identity Resolution Application
- How to Execute the application for Identity Resolution
- How to Audit application and output created 
- How to Execute the application for Translation
- How to Audit the output created 
- How to use the Translation output with partners

Note: To complete this quickstart, you must have access to the full version of LiveRamp Identity Resolution and Transcoding. Please reach out to the LiveRamp team to get access. 

### Prerequisites
- Use of the LiveRamp Identity and Translation Native Application
- Basic knowledge of SQL, database concepts, and objects
- Basic knowledge of Identity Resolution 
- Table with one or more of the following Personal Identifiable Information components (Name, Address, Email, Phone)
- 
### What You'll Need
[Snowflake](https://snowflake.com/) Account

### Additional Information
LiveRamp has a [video](https://www.youtube.com/watch?v=RN7k4TNyfaQ) describing a basic use case as well as a demo of the execution.

<!-- ------------------------ -->
## Setup Identity Resolution Application

#### If not yet done, request for the LiveRamp Identity Resolution and Transcoding Native Application

* The LiveRamp application is available in AWS US East 1, AWS US West 2, Azure East US 2, GCP US Central 1

* LiveRamp will walk through the implementation and deliver keys that will be used in this Quickstart

> 
> 
>  \*\*Consider This: \*\*
This Quickstart will focus on Personally Identifiable Information (PII) setup and resolution. Other identifiers are available and require slightly different configurations that are discussed [here](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html)

#### Setup the Input Table
* Table must contain one or more of the following: First Name, Last Name, Address, City, State, Zip Code, Raw Email, Phone
* The column names for the input table can be whatever you want to use, as long as the names match the values specified in the metadata table.
* Do not use any column names that are the same as the column names returned in the output table for the identity resolution operation you're going to run.
* Every column name must be unique in a table.
* Try not to use additional columns in the input tables required for the identity resolution operation as having extra columns slows down processing.
* Per Snowflake guidelines, table names cannot begin with a number.
* More Information can be found [here](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html#create-the-input-table-for-identity-resolution-44)

#### Setup the Metadata Table
For the PII execution mode we will be using the standard process. The Metadata table describes the PII components for use in the process as well as specify the type of identity resolution will be executed. The following is described in more detail for other types [here](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html#create-the-metadata-table-44)

Keep track of what will be used for the following variables and will be used in the below SQL:

- client_id:Provided in implementation by LiveRamp.
- client_secret: Provided in implementation by LiveRamp
- <up to 4 name column names>: Enter the names of the column(s) in the input table to be used for the “name” element. Each input table column name should be enclosed in double quotes. Enter a maximum of 4 name columns. If entering multiple column names, separate the column names with commas.
- <up to 7 address column names>: Enter the names of the column(s) in the input table to be used for the “address” element. Each input table column name should be enclosed in double quotes. Enter a maximum of 7 address columns. If entering multiple column names, separate the column names with commas.
- City: Enter the name of the column to be used for the “city” element.
- State: Enter the name of the column to be used for the “state” element.
- Zip Code: Enter the name of the column to be used for the “zipcode” element.
- Phone: Enter the name of the column to be used for the “phone” element.
- Email: Enter the name of the column to be used for the “email” element.

The Completed Metatable will be built using the following SQL. If you do not have a PII component, please remove it from the SQL.
```
create or replace table identifier($customer_meta_table_name) as
select
    TO_VARCHAR(DECRYPT(ENCRYPT('<client_id>', 'HideFromLogs'), 'HideFromLogs'), 'utf-8') as client_id,
    TO_VARCHAR(DECRYPT(ENCRYPT('<client_secret>', 'HideFromLogs'), 'HideFromLogs'), 'utf-8') as client_secret,
    'resolution' as execution_mode,
    'pii' as execution_type,
    parse_json($$
    {
      "name": ["<up to 4 name column names>"],
      "streetAddress": ["<up to 7 address column names>"],
      "city": "<city column>",
      "state": "<state column>",
      "zipCode": "<zipcode column>",
      "phone": "<phone column>",
      "email": "<email column>"
    }
    $$) as target_columns,
    1 as limit;
```
#### Validate the Permissions on all tables
To set up the permissions for the tables used for resolution, run the SQL in the Execution Steps worksheet shown below
```
grant usage on database identifier ($customer_db_name) to application identifier($application_name);
grant usage on schema identifier ($customer_schema_name) to application identifier($application_name);
grant select on table identifier ($customer_input_table_name) to application identifier($application_name);
grant select on table identifier ($customer_meta_table_name) to application identifier($application_name);


use database identifier ($application_name);
use schema lr_app_schema;
```

<!-- ------------------------ -->
## Executing the Identity Resolution Application

#### This process will involve two separate steps for completing the application execution

* Initiate the Resolution Application Procedure
* Initiate the Output Check Procedure

More details for this step can be found [here](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html#perform-the-identity-resolution-operation)

The following SQL will execute the identity resolution process. The stored procedure will. be located in your Snowflake account. It will be listed under the 
You need to replace the following variable below
* <customer_input_table_name> - Name of the Input table built in the previous step
* <customer_meta_table_name> - Name of the Metadata table built in the previous step
* <output_table_name> - Table name only


> 
> 
>  \*\*Consider This: \*\*
When executing PII it is recommended starting with a 2XL size warehouse

```
call lr_resolution_and_transcoding(
    <customer_input_table_name>,
    <customer_meta_table_name>,
    <output_table_name>
);
```
> 
> 
>  **Execution Note**
This process will execute inside your warehouse, so do not kill this process

When the above process completes you will need to run one more process to get the output table visible in your warehouse. You will use the output_table variable from the initial job invocation

```
call check_for_output(
	$output_table_name
);
```

A table should now be visible in your Snowflake warehouse under the LiveRamp native application

## Audit the Identity Resolution Process

#### Sample Audits
Since you have executed a PII Resolution job there are two additional columns that LiveRamp includes in the [output table](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html#view-the-pii-resolution-output-table--without-deconfliction--44)
These columns provide the level at which the included PII was resolved against the LiveRamp application.  The following columns will be included in an additional columns called __lr_filter_name
* name_address_zip
* name_email
* name_phone
* partial_name_email
* partial_name_phone
* strict_name (name + zip)
* email
* phone
* last_name_address

The following SQL will use a variable that defines your output from the previous step.
```
SET final_output = '$output_table_name';
```
Once you have that table you can check the frequency of each match on your output table.
```
select __LR_RANK, count(__LR_RANK) as Count1 from identifier($final_output)
group by (__LR_RANK)
order by Count1 desc;

select __LR_FILTER_NAME, count(__LR_FILTER_NAME) as Count1 from identifier($final_output)
group by (__LR_FILTER_NAME)
order by Count1 desc;

--select FILTER_NAME, count(FILTER_NAME) as count1 from identifier($final_output);
--group by FILTER_NAME
--ORDER BY COUNT1 DESC;
select FILTER_NAME, count(FILTER_NAME) as Count1 from  LR_APP_SHARE_RESOLUTION_DEMO.LR_JOB_SCHEMA.DS_TEST_1A_POST_V5
group by (FILTER_NAME)
order by Count1 desc;
```
It is also recommended to look at the number of [maintained](https://docs.liveramp.com/connect/en/identity-and-identifier-terms-and-concepts.html#maintained-identifier) and [derived](https://docs.liveramp.com/connect/en/identity-and-identifier-terms-and-concepts.html#derived-identifier) identifiers which are based on the first two bytes.
* XY is Maintained
* Xi is Derived

```
SELECT 
    SUBSTR(RAMPID, 1, 2) AS first_two_chars,
    COUNT(*) AS frequency
FROM 
    identifier($final_output)
GROUP BY 
    SUBSTR(RAMPID, 1, 2)
ORDER BY 
    frequency DESC;
```
It is always good to validate the output count from your final execution
```
SELECT COUNT(RAMPID) FROM   identifier($final_output);
```




## Setup Identity Translation Application

#### If not yet done, request for the LiveRamp Identity Resolution and Transcoding Native Application

* The LiveRamp application is available in AWS US East 1, AWS US West 2, Azure East US 2, GCP US Central 1

* LiveRamp will walk through the implementation and deliver keys that will be used in this Quickstart

> 
> 
>  \*\*Consider This: \*\*
This Quickstart will focus on Translation from one RampID to another RampID domain. Please reach out to LiveRamp for the correct domain for your translation use case.

More Documentation can be found [here](https://docs.liveramp.com/identity/en/perform-rampid-transcoding-in-snowflake.html#perform-rampid-transcoding-in-snowflake)

#### Setup the Input Table
* Table must contain the following Data values in three columns: Source RampsIDs, Destination RampID Domain and ID Type
* The column names for the input table can be whatever you want to use, as long as the names match the values specified in the metadata table.
* Do not use any column names that are the same as the column names returned in the output table for the identity resolution operation you're going to run.
* Every column name must be unique in a table.
* Do not use additional columns in the input tables required for the identity translation operation, since they will not be returned.
* Per Snowflake guidelines, table names cannot begin with a number.
* More Information can be found [here](https://docs.liveramp.com/identity/en/perform-rampid-transcoding-in-snowflake.html#create-the-input-table-for-translation)

The following SQL will create the correct Translation input table.
```
CREATE OR REPLACE TABLE <Translation Input Table>
AS SELECT RAMPID , 'ZZZZ' AS TARGET_DOMAIN , 'RampID' AS TARGET_TYPE FROM <Table with a valid RampID Column>;
```

#### Setup the Metadata Table
For the Translation execution mode we will be using the standard process. The Metadata table describes the components for use in the process as well as specify the type of translation that will be executed. The following is described in more detail for other types [here](https://docs.liveramp.com/identity/en/perform-identity-resolution-in-snowflake.html#create-the-metadata-table-44)

Keep track of what will be used for the following variables and will be used in the below SQL:

- client_id:Provided in implementation by LiveRamp.
- client_secret: Provided in implementation by LiveRamp
- column to be translated: Enter the column name of the input table which contains the RampIDs to be translated.
- column containing target domain: Enter the column name of the input table which contains the target domain for the encoding the RampIDs should be translated to.
- column containing target type: Enter the column name of the input table which contains the target identifier type.

The Completed Metatable will be built using the following SQL.  

```
create or replace table identifier($customer_meta_table_name) as
select
    TO_VARCHAR(DECRYPT(ENCRYPT('<client_id>', 'HideFromLogs'), 'HideFromLogs'), 'utf-8') as client_id,
    TO_VARCHAR(DECRYPT(ENCRYPT('<client_secret>', 'HideFromLogs'), 'HideFromLogs'), 'utf-8') as client_secret,
    'transcoding' as execution_mode,
    'transcoding' as execution_type,
    '<column to be translated>' as target_column,
    '<column containing target domain>' as target_domain_column,
    '<column containing target type>' as target_type_column;
```
#### Validate the Permissions on all tables
To set up the permissions for the tables used for resolution, run the SQL in the Execution Steps worksheet shown below
```
grant usage on database identifier ($customer_db_name) to application identifier($application_name);
grant usage on schema identifier ($customer_schema_name) to application identifier($application_name);
grant select on table identifier ($customer_input_table_name) to application identifier($application_name);
grant select on table identifier ($customer_meta_table_name) to application identifier($application_name);


use database identifier ($application_name);
use schema lr_app_schema;
```

<!-- ------------------------ -->
## Executing the Identity Translation Application

#### This process will involve two separate steps for completing the application execution

* Initiate the Resolution Application Procedure
* Initiate the Output Check Procedure

More details for this step can be found [here](https://docs.liveramp.com/identity/en/perform-rampid-transcoding-in-snowflake.html#perform-translation)

The following SQL will execute the identity resolution process. The stored procedure will. be located in your Snowflake account. It will be listed under the 
You need to replace the following variable below
* <customer_input_table_name> - Name of the Input table built in the previous step
* <customer_meta_table_name> - Name of the Metadata table built in the previous step
* <output_table_name> - Table name only


> 
> 
>  \*\*Consider This: \*\*
When executing Translation it is recommended starting with a Large size warehouse

```
call lr_resolution_and_transcoding(
    <customer_input_table_name>,
    <customer_meta_table_name>,
    <output_table_name>
);
```
> 
> 
>  **Execution Note**
This process will execute inside your warehouse, so do not kill this process

When the above process completes you will need to run one more process to get the output table visible in your warehouse. You will use the output_table variable from the initial job invocation

```
call check_for_output(
	$output_table_name
);
```

A table should now be visible in your Snowflake warehouse under the LiveRamp native application

## Auditing Translation

This section will describe some sample audits for the Translation process. Each client is encouraged to reach out to their LiveRamp representative for more examples and guidance on audits. 

Set Up some variables for use in the SQL below. You will need the following:
* Output Table from the transcoding process
* A newly created table that will contain the results of canned audit tests

```
-- setting the input table for the rest of the script
set audit_table = 'your Transcoding Output';
set audit_table_output = 'Extr Audit Table';
```

Once you have set up the variables you can execute the different audits

This first audit is a count where the translation did not work as expected 
```
-- Counts of where the input and output are different.
SELECT COUNT(*) AS count_of_different_lengths
FROM  identifier($audit_table)
WHERE LENGTH(rampid) <> LENGTH(TRANSCODED_IDENTIFIER);
```
This will create a new table that is the results of several queries
```
-- create a table of the rows that are different for audit review   
CREATE or REPLACE TABLE identifier($audit_table_output) AS
SELECT *,
       CASE 
           WHEN  TRANSCODED_IDENTIFIER LIKE '%Error, target key missing for transcoding%' THEN 'Target Access Mismatch'
           WHEN  TRANSCODED_IDENTIFIER LIKE '%Error, Invalid RampID Format. Overall.%' THEN 'Data Input Mismatch'
           WHEN LENGTH(rampid) <> LENGTH(TRANSCODED_IDENTIFIER) 
                AND LEFT(rampid, 2) <> LEFT(TRANSCODED_IDENTIFIER, 2) THEN 'Size and Maintained Mismatch'
           WHEN LENGTH(rampid) <> LENGTH(TRANSCODED_IDENTIFIER) THEN 'Size Mismatch'
           WHEN LEFT(rampid, 2) <> LEFT(TRANSCODED_IDENTIFIER, 2) THEN 'Maintained Mismatch'
       END AS mismatch_type
FROM identifier($audit_table)
WHERE LENGTH(rampid) <> LENGTH(TRANSCODED_IDENTIFIER)
   OR LEFT(rampid, 2) <> LEFT(TRANSCODED_IDENTIFIER, 2)
   OR TRANSCODED_IDENTIFIER LIKE '%Error, target key missing for transcoding%'
   OR TRANSCODED_IDENTIFIER LIKE '%Error, Invalid RampID Format. Overall%';
```

Run a select off the audit table you created

```
-- quick check of output table
select * from identifier($audit_table_output)
limit 10;
```
You have now completed the audit of the translation table


## Collaborating using the Translation Output

You are now ready to create a file for collaboration with your partner. With the ability to generate RampIDs that match your partner's, you now have a shared exchange key. The SQL query below will generate an attribute file by replacing your RampID with the client’s RampID. The resulting output table can be shared, exported, or leveraged for further collaborative efforts with your partner.

#### Build a Table to share
Making sure you share your identified attributes but using the newly created Translation table you have a key that can be exchanged with your partner

```
CREATE TABLE NewTable AS
SELECT 
    t1.* EXCLUDE (RampID),
    t2.Transcoded_Identifier
FROM 
    <Your RampID and Attribute Table> t1
JOIN 
    <Your Output from Translation> t2
ON 
    t1.RampID = t2.RampID;
```

After creating make sure to run a quick select on the table to make sure it has what you expect.
```
select * from NewTable limit 100;
```



## Conclusion And Resources

Congratulations! You have successfully learned how to transform your Data Cloud into an Identity Resolution Engine.

This lab was designed as a hands-on introduction to Snowflake and LiveRamp Identity Resolution and Transcoding to simultaneously teach best practices on how to use them together in an effective manner.

#### What you learned

- How to setup and execute an Identity Resolution Process within your own Snowflake instance
- How to Audit a LiveRamp Identity Resolution Process
- How to set up and execute an Identity Translation Process within your own Snowflake instance.
- How to Audit the Translation Process and share the data using a privacy compliant key

We encourage you to continue with your Identity and Transcoding journey by loading in more of your own sample or production data and by using some of the more advanced capabilities not covered in this lab.

#### Additional Capabilities not discussed
* Alternate resolution types like Cookies, Maids and Connected TVs
* LiveRamp offers deconfliction job types that offer enhanced matching capabilities
* LiveRamp offers additional Digital Activation capabilities not outlined in this Quickstart

#### Related Resources

Want to learn more about LiveRamp and Identity? Check out the following resources:
* [LiveRamp Embedded Identity in Snowflake](https://docs.liveramp.com/identity/en/liveramp-embedded-identity-in-snowflake.html#liveramp-embedded-identity-in-snowflake)

* [LiveRamp and Snowflake Video](https://www.youtube.com/watch?v=RN7k4TNyfaQ)
* [Watch the Demo](https://youtu.be/uL7hh4A_ggI?list=TLGG2L1hs9hxONQyNDA5MjAyNQ)
* [Download Reference Architecture](/content/dam/snowflake-site/developers/2024/10/LiveRamp-Snowflake-Reference-Architecture.pptx.pdf)
* [Read the Blog](https://medium.com/snowflake/liveramp-embedded-identity-and-deconfliction-a-powerful-solution-for-marketers-on-snowflake-7cdbec33d8ba)


