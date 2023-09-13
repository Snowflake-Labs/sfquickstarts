author: Parag Jain
id: getting_started_with_dynamic_tables
summary: Getting Started with Snowflake Dynamic Tables
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Dynamic Tables, Data Engineering, Data Pipeline 

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 
Duration: 2

Dynamic tables are new declarative way of defining your data pipeline in Snowflake. It's a new kind of Snowflake table which is defined as a query and continually and automatically materializes the result of that query as a table. Dynamic Tables can join and aggregate across multiple source objects and incrementally update results as sources change. 

Dynamic Tables can also be chained together to create a DAG for more complex data pipelines. 

![DT overview](assets/DT.jpg)

Dynamic Tables are the building blocks for continuous data pipelines. They are the easiest way to build data transformation pipelines in snowflake across batch and streaming use cases. 

In this quickstart we will build a change data capture (CDC) pipeline and data validation using Dynamic tables. We will also look at some of the built in features around [Dynamic tables](https://docs.snowflake.com/user-guide/dynamic-tables-about).

### Prerequisites
- Use of the [Snowflake free 30-day trial environment](https://trial.snowflake.com) or your own Snowflake environment
- Basic knowledge of SQL, database concepts, and objects
- Familiarity with JSON semi-structured data

### What You’ll Learn 
- How to perform analytical queries on data in Snowflake, including joins between tables.
- How to create a declarative data pipeline using Dynamic tables
- How to pause and resume the data pipeline
- How to monitor Dynamic table continous data pipeline
- How to automate the data validation process using Dynamic tables
- How to setup alerts

### What You’ll Need 
- A [Snowflake](https://trial.snowflake.com) Account 

### What You’ll Build 
- A continous data pipeline using Dynamic tables
- Data validation automation and alerts

<!-- ------------------------ -->
## Setup
Duration: 4

- **Problem Statement**

We are data engineers at an online retail company, where a wide array of products are sold. In this role, we collect customer purchase and product sales data, initially storing it in a raw data table. Our primary tasks involve creating a continous data pipeline for generating sales reports and validate the data for an alert system to notify the team of potential low inventory levels for specific products

- **Data Pipeline Architecture**

![program architecture](assets/arch1.jpg)

- **Sample data**: 

We will use python "Faker" library to generate some test data required for this project. In order to run this python code we will buiild and use [Python UDTF](https://docs.snowflake.com/en/developer-guide/snowpark/python/creating-udtfs)

We are going to build our lab in a database call "demo" and schema name "dt_demo", so go to your Snowflake account and open a worksheet and write or paste this code. Feel free to use any database if "demo" database is already in use or you don't have access to it.

Open a new worksheet and call it setup

```
CREATE DATABASE IF NOT EXISTS DEMO;
CREATE SCHEMA DEMO.DT_DEMO;
```

Once the database is created, we will create 3 UDTF to generate our source data. First table is **cust_info** and insert 1000 customers into it using this new Python UDTF.

```
create or replace function gen_cust_info(num_records number)
returns table (custid number(10), cname varchar(100), spendlimit number(10,2))
language python
runtime_version=3.8
handler='CustTab'
packages = ('Faker')
as $$
from faker import Faker
import random

fake = Faker()
# Generate a list of customers  

class CustTab:
    # Generate multiple customer records
    def process(self, num_records):
        customer_id = 1000 # Starting customer ID                 
        for _ in range(num_records):
            custid = customer_id + 1
            cname = fake.name()
            spendlimit = round(random.uniform(1000, 10000),2)
            customer_id += 1
            yield (custid,cname,spendlimit)

$$;

create or replace table cust_info as select * from table(gen_cust_info(1000)) order by 1;

```

Next table is **prod_stock_inv** and insert 100 products inventory into it using this new Python UDTF.

```
create or replace function gen_prod_inv(num_records number)
returns table (pid number(10), pname varchar(100), stock number(10,2), stockdate date)
language python
runtime_version=3.8
handler='ProdTab'
packages = ('Faker')
as $$
from faker import Faker
import random
from datetime import datetime, timedelta
fake = Faker()

class ProdTab:
    # Generate multiple product records
    def process(self, num_records):
        product_id = 100 # Starting customer ID                 
        for _ in range(num_records):
            pid = product_id + 1
            pname = fake.catch_phrase()
            stock = round(random.uniform(500, 1000),0)
            # Get the current date
            current_date = datetime.now()
            
            # Calculate the maximum date (3 months from now)
            min_date = current_date - timedelta(days=90)
            
            # Generate a random date within the date range
            stockdate = fake.date_between_dates(min_date,current_date)

            product_id += 1
            yield (pid,pname,stock,stockdate)

$$;

create or replace table prod_stock_inv as select * from table(gen_prod_inv(100)) order by 1;
```

Next table is **salesdata** to store raw product sales by customer and purchase date 


```
create or replace function gen_cust_purchase(num_records number,ndays number)
returns table (custid number(10), purchase variant)
language python
runtime_version=3.8
handler='genCustPurchase'
packages = ('Faker')
as $$
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

class genCustPurchase:
    # Generate multiple customer purchase records
    def process(self, num_records,ndays):       
        for _ in range(num_records):
            c_id = fake.random_int(min=1001, max=1999)
            
            #print(c_id)
            customer_purchase = {
                'custid': c_id,
                'purchased': []
            }
            # Get the current date
            current_date = datetime.now()
            
            # Calculate the maximum date (days from now)
            min_date = current_date - timedelta(days=ndays)
            
            # Generate a random date within the date range
            pdate = fake.date_between_dates(min_date,current_date)
            
            purchase = {
                'prodid': fake.random_int(min=101, max=199),
                'quantity': fake.random_int(min=1, max=5),
                'purchase_amount': round(random.uniform(10, 1000),2),
                'purchase_date': pdate
            }
            customer_purchase['purchased'].append(purchase)
            
            #customer_purchases.append(customer_purchase)
            yield (c_id,purchase)

$$;



select * from table(gen_cust_purchase(10,1));
create or replace table salesdata as select * from table(gen_cust_purchase(10000,10));
```

This completes our sample data stored in raw base tables. In real world, you will load this data into Snowflake either using COPY COMMAND, connectors, Snowpipe or [Snowpipe Streaming](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)

Check if there is data in all 3 raw tables -

```
-- customer information table, each customer has spending limits
select * from cust_info limit 10;

-- product stock table, each product has stock level from fulfilment day

select * from prod_stock_inv limit 10;

-- sales data for products purchsaed online by various customers
select * from salesdata limit 10;
```


<!-- ------------------------ -->
## Build data pipeline using Dynamic Tables
Duration: 7

With Dynamic Tables, customers provide a query, and Snowflake automatically materializes the results of that query. 

That means, instead of creating a separate target table and writing code to transform source data and update the data in that table, you can define the target table as a Dynamic Table, specifying the query that performs the transformation and just forget about the scheduling and orchestration. 

The user specifies a minimum acceptable freshness in the result (target lag), and Snowflake automatically tries to meet that target, further enhancing the flexibility and control data engineers can have over their pipelines without the normally associated complexity.

![how DT works?](assets/howdt.jpg)

Ok great! lets create our first Dynamic Table. For this we will extract the sales information from the **salesdata** table and join it with **customer information** to build the **customer_sales_data_history** note that we are extracting raw json data and transforming it into meaningful columns and data type

```
CREATE OR REPLACE DYNAMIC TABLE customer_sales_data_history
    LAG='DOWNSTREAM'
    WAREHOUSE=lab_s_wh
AS
select 
    s.custid as customer_id,
    c.cname as customer_name,
    s.purchase:"prodid"::number(5) as product_id,
    s.purchase:"purchase_amount"::number(10) as saleprice,
    s.purchase:"quantity"::number(5) as quantity,
    s.purchase:"purchase_date"::date as salesdate
from
    cust_info c inner join salesdata s on c.custid = s.custid
;
```

Looking good, we will see what **DOWNSTREAM** means here in just a minute. lets run some quick sanity checks and hydrate this table by manually refreshing the DT.

```
alter dynamic table customer_sales_data_history refresh;

-- quick sanity check
select * from customer_sales_data_history limit 10;
select count(*) from customer_sales_data_history;
```


<!------------->
## logical pause

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