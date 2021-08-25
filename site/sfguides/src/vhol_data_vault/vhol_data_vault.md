author: yarodmi
id: vhol_data_vault
summary: Building a Real-time Data Vault in Snowflake
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Vault, Data Enineering

# Building a Real-Time Data Vault in Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 3

 
In this day and age, with the ever-increasing availability and volume of data from many types of sources such as IoT, mobile devices, and weblogs, there is a growing need, and yes, demand, to go from batch load processes to streaming or “real-time” (RT) loading of data. Businesses are changing at an alarming rate and are becoming more competitive all the time. Those that can harness the value of their data faster to drive better business outcomes will be the ones to prevail.

One of the benefits of using the Data Vault 2.0 architecture is that it was designed from inception not only to accept data loaded using traditional batch mode (which was the prevailing mode in the early 2000s when [Dan Linstedt](https://datavaultalliance.com/certification/standards-board/) introduced Data Vault) but also to easily accept data loading in real or near-realtime (NRT). In the early 2000s, that was a nice-to-have aspect of the approach and meant the methodology was effectively future-proofed from that perspective. Still, few database systems had the capacity to support that kind of requirement. Today, RT or at least NRT loading is almost becoming a mandatory requirement for modern data platforms. Granted, not all loads or use cases need to be NRT, but most forward-thinking organizations need to onboard data for analytics in an NRT manner.

Those who have been using the Data Vault approach don’t need to change much other than figure out how to engineer their data pipeline to serve up data to the Data Vault in NRT. The data models don’t need to change; the reporting views don’t need to change; even the loading patterns don’t need to change. (NB: For those that aren’t using Data Vault already, if they have real-time loading requirements, this architecture and method might be worth considering.)

### Data Vault on Snowflake

There have been numerous [blog posts](https://www.snowflake.com/blog/tips-for-optimizing-the-data-vault-architecture-on-snowflake/), user groups, and webinars over the last few years, discussing the best practices and customer success stories around implementing Data Vaults on Snowflake.  So the question now is how do you build a Data Vault on Snowflake that has real-time or near real-time data streaming into it.

Luckily, streaming data is one of the [use-cases](https://www.snowflake.com/cloud-data-platform/) that Snowflake was built to support, so we have many features to help us achieve this goal. **This guide is an extended version of the [article](https://datavaultalliance.com/news/building-a-real-time-data-vault-in-snowflake/) posted on Data Vault Alliance website, now including practical steps to build an example of real-time Data Vault feed on Snowflake. Join us on simple-to-follow steps to see it in action.**

### Prerequisites
* A Snowflake account. Existing or if you are not(yet) a Snowflake user, you can always get a [trial](https://trial.snowflake.com/) account
* Familiarity with Snowflake and Snowflake objects

### What You’ll Learn 
* how to use Data Vault on Snowflake

* how to build basic objects and write ELT code for it

* how to leverage [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro.html) and [Continous Data Pipelines](https://docs.snowflake.com/en/user-guide/data-pipelines.html) to automate data processing

* how to apply data virtualization to accellerate data access

### What You’ll Build 
* a Data Vault environment on Snowflake, based on sample dataset 
* data pipelines, leveraging streams, tasks and Snowpipe

<!-- ------------------------ -->
## Reference Architecture
Duration: 5

Let’s start with the overall architecture to put everything in context. 

![dbt_project.yml](assets/img1.png)  


On the very left of figure above we have a list of **data providers** that typically include a mix of existing operational databases, old data warehouses, files, lakes as well as 3rd party apps. There is now also the  possibility to leverage Snowflake Data Sharing/Marketplace as a way to tap into new 3rd party data assets to augment your data set. 

On the very right we have our ultimate **data consumers**: business users, data scientists, IT systems or even other companies you decided to exchange your data with.
 
Architecturally, we will split the data lifecycle into following layers:
* **Data Acquisition:** extracting data from source systems and making it accessible for Snowflake.
* **Loading & Staging:** moving the source data into Snowflake. For this Snowflake has multiple options, including batch load, external tables and Snowpipe(our managed service for onboarding streaming data). Snowflake allows you to load and store structured and semi-structured in the original format whilst automatically optimizing the physical structure for efficient query access. The data is immutable and should be stored as it was received from source with no changes to the content. From a Data Vault perspective, functionally, this layer is also responsible for adding technical metadata (record source,, load date timestamp, etc.) as well as calculating business keys. 
* **Raw Data Vault:** a data vault model with no soft business rules or transformations applied (only hard rules are allowed) loading all records received from source.
* **Business Data Vault:** data vault objects with soft business rules applied. The raw data vault data is getting augmented by the intelligence of the system. It is not a copy of the raw data vault, but rather a sparse addition with perhaps calculated satellites,  mastered records,or maybe even commonly used aggregations. This could also optionally include PIT and Bridge tables helping to simplify access to bi-temporal view of the data. From a Snowflake perspective, raw and business data vaults could be separated by object naming convention or represented as different schemas or even different databases. 
* **Information Delivery:** a layer of consumer-oriented models. This could be implemented as a set (or multiple sets) of views. It is common to see the use of dimensional models (star/snowflake) or denormalized flat tables (for example for data science or sharing) but it could be any other modeling stye (e.g., unified star schema, supernova, key-value, document object mode, etc.) that fits best for your data consumer. Snowflake’s scalability will support the required speed of access at any point of this data lifecycle. You should consider Business Vault and Information Delivery objects materialization as optional. This specific topic (virtualization) is going to be covered later in this article. 


<!-- ------------------------ -->
## Environment setup & data model
Duration: 10

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Building Data Pipelines
Duration: 10

![dbt_project.yml](assets/img2.png)  

Snowflake supports multiple options for engineering data pipelines. In this post we are going to show one of the most efficient ways to implement incremental NRT integration leveraging Snowflake [Continuous Data Pipelines](https://docs.snowflake.com/en/user-guide/data-pipelines.html).  Let's take a look at the architecture diagram (figure 2) to understand how it works. 

Snowflake has a special [stream](https://docs.snowflake.com/en/user-guide/streams.html) object that tracks all data changes on a table (inserts, updates, and deletes). This process is 100% automatic and unlike traditional databases will never impact the speed of data loading. The change log from a stream is automatically ‘consumed’ once there is a successfully completed DML operation using the stream object as a source. 

So, loading new data into a staging table, would immediately be reflected in a stream showing the [‘delta’](https://docs.snowflake.com/en/user-guide/streams.html#data-flow) that requires processing.

The second component we are going to use is [tasks](https://docs.snowflake.com/en/user-guide/tasks-intro.html). It is a Snowflake managed data processing unit that will wake up on a defined interval (e.g., every 1-2 min), check if there is any data in the associated stream and if so, will run SQL to push it to the Raw Data Vault objects. Tasks could be arranged in a [tree-like dependency graph](https://docs.snowflake.com/en/user-guide/tasks-intro.html#simple-tree-of-tasks), executing child tasks the moment the predecessor finished its part. 

Last but not least, following Data Vault 2.0 best practices for NRT data integration (to load data in parallel) we are going to use Snowflake’s [multi-table insert (MTI)](https://docs.snowflake.com/en/sql-reference/sql/insert-multi-table.html) inside tasks to populate multiple Raw Data Vault objects by a single DML command. (Alternatively you can create multiple streams & tasks from the same table in stage in order to populate each data vault object by its own asynchronous flow.) 

Next step, you assign tasks to one or many virtual warehouses. This means you always have enough [compute power](https://docs.snowflake.com/en/user-guide/warehouses-overview.html#warehouse-size) (XS to 6XL) to deal with any size workload, whilst the [multi-cluster virtual warehouse](https://docs.snowflake.com/en/user-guide/warehouses-multicluster.html#multi-cluster-warehouses) option will automatically scale-out and load balance all the tasks as you introduce more hubs, links and satellites to your vault. 

As your raw vault is updated, streams can then be used to propagate those changes to Business Vault objects (such as derived Sats, PITS, or Bridges, if needed) in the next layer. This setup can be repeated to move data through all the layers in small increments very quickly and efficiently. All the way until it is ready to be accessed by data consumers (if materialization of the data is required for performance). 

Following this approach will result in a hands-off production data pipeline that feeds your Data Vault architecture.



<!-- ------------------------ -->
## Views for Agile Reporting
Duration: 10

One of the great benefits of having the compute power from Snowflake is that now it is totally possible to have most of your business vault and information marts in a Data Vault architecture be built exclusively from views. There are numerous customers using this approach in production today. There is no longer a need to have the argument that there are “too many joins” or that the response won’t be fast enough. The elasticity of the Snowflake virtual warehouses combined with our dynamic optimization engine have solved that problem. (For more details, see this [post](https://www.snowflake.com/blog/tips-for-optimizing-the-data-vault-architecture-on-snowflake-part-3/))

If you really want to deliver data to the business users and data scientists in NRT, in our opinion using views is the only option. Once you have the streaming loads built to feed your Data Vault, the fastest way to make that data visible downstream will be views. Using views allows you to deliver the data faster by eliminating any latency that would be incurred by having additional ELT processes between the Data Vault and the data consumers downstream.

All the business logic, alignment, and formatting of the data can be in the view code. That means fewer moving parts to debug, and reduces the storage needed as well.


![dbt_project.yml](assets/img3.png)  

Looking at the diagram above you will see an example of how virtualization could fit in the architecture. Here, solid lines are representing physical tables and dotted lines - views. You incrementally ingest data into **Raw Data Vault** and all downstream transformations are applied as views. From a data consumer perspective when working with a virtualized information mart, the query always shows everything known by your data vault, right up to the point the query was submitted. 

With Snowflake you have the ability to provide as much compute as required, on-demand,  without a risk of causing performance impact on any surrounding processes and pay only for what you use. This makes materialization of transformations in layers like **Business Data Vault** and **Information delivery** an option rather than a must-have. Instead of “optimizing upfront” you can now make this decision based on the usage pattern characteristics, such as frequency of use, type of queries, latency requirements, readiness of the requirements etc. 


Many modern data engineering automation frameworks are already actively supporting virtualization of logic. Several tools offer a low-code or configuration-like ability to switch between materializing an object as a view or a physical table, automatically generating all required DDL & DML. This could be applied on specific objects, layers or/and be environment specific. So even if you start with a view, you can easily refactor to use a table if user requirements evolve.

As a quick example of such an approach, here is how enrichment of customer descriptive data could happen in Business Data Vault, connecting data received from source with some reference data.

```SQL
CREATE OR REPLACE VIEW l20_bdv.sat_customer_bv
AS
SELECT 
  rsc.md5_hub_customer  
, rsc.ldts                   
, rsc.c_name                 
, rsc.c_address              
, rsc.c_phone                 
, rsc.c_acctbal              
, rsc.c_mktsegment               
, rsc.c_comment              
, rsc.nationcode             
, rsc.rscr 
-- derived 
, rrn.n_name                 nation_name
, rrr.r_name                 region_name
  FROM l10_rdv.sat_customer          rsc
  LEFT OUTER JOIN l10_rdv.ref_nation rrn
    ON (rsc.nationcode = rrn.nationcode)
  LEFT OUTER JOIN l10_rdv.ref_region rrr
    ON (rrn.regioncode = rrr.regioncode)
;
```

As said before, virtualization is not only a way to improve time-to-value and provide near real time access to the data, given the scalability and workload isolation of Snowflake, virtualization also is a design technique that could make your Data Vault excel: minimizing cost-of-change, accelerating the time-to-delivery and becoming an extremely agile, future proof solution for ever growing business needs. 



<!-- ------------------------ -->
## Conclusion
Duration: 1

Simplicity of engineering, openness, scalable performance, enterprise-grade governance enabled by the core of the Snowflake platform are now allowing teams to focus on what matters most for the business and build truly agile, collaborative data environments. Teams can now connect data from all parts of the landscape, until there are no stones left unturned. They are even tapping into new datasets via live access to the Snowflake Data Marketplace. The Snowflake Data Cloud combined with a Data Vault 2.0 approach is allowing teams to democratize access to all their data assets at any scale. We can now easily derive more and more value through insights and intelligence, day after day, bringing businesses to the next level of being truly data-driven.  

Delivering more usable data faster is no longer an option for today’s business environment. Using the Snowflake platform, combined with the Data Vault 2.0 architecture it is now possible to build a world class analytics platform that delivers data for all users in near real-time. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files