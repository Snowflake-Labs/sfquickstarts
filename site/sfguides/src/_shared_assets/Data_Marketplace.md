### Snowflake Data Marketplace

#### Navigate to the Data Marketplace tab.

![data marketplace tab](assets/10Share_7.png)

Select “Explore the Snowflake Data Marketplace.” If it’s your first time using the Data Marketplace the following login screens will appear:

![login page](assets/10Share_8.png)

Enter your credentials to access the Snowflake Data Marketplace.

Positive
:  Make sure you are in the `ACCOUNTADMIN` role. 

![Snowflake data marketplace](assets/10Share_9.png)

To change your role, follow the steps below:


![check context](assets/10Share_11.png)

#### Find a listing
The search bar at the top center allows you to search for a listings. The menu below the search box lets you filter data listings by Provider, Business Needs, and Category.  Type **COVID** into the search box, then select the Starschema COVID-19 Epidemiological Data tile.

![health tab](assets/10Share_10.png)  


Here you can learn more about the data set and see some usage example querires.  Now click on the Get Data button to access this information within your Snowflake Account.

![get data fields](assets/10Share_starschema_get_data.png)

![get data fields](assets/10Share_starschema_get_data2.png)

![get data fields](assets/10Share_starschema_query_data.png)



Positive
:  You are now using the new Snowsight user interface.  To learn more about how to use this new user interface go here:  [Snowsight Docs](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#using-snowsight)

Now you can run any of the sample queries provided by Star Schema.
Just select the query you want to run, and click the run button in the upper right corner. You can view the data results in the bottom pane.  Once you are done running the sample queries, click on the **Home icon** in the upper left corner.

![get data fields](assets/10Share_starschema_query_data2.png)



Now navigate to the Databases view in the navigation panel on the left. Click on Data, then Databases, then click on the COVID19_BY_STARSCHEMA_DM Database.  Now you can see the schemas, tables, and views that are available to query.

![covid19 databases](assets/10Share_starschema_db_info.png)


You have now successfully subscribed to the COVID-19 dataset from StarSchema which is updated daily with global COVID data. Note that we didn’t have to create databases, tables, views, or an ETL process. We simply can search for and access shared data from the Snowflake Data Marketplace.

Positive
:  We highly encourage you to begin using the Snowsight user interface to run all of your queries.  To learn more about how to use this new user interface go here:  [Snowsight Docs](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#using-snowsight)
