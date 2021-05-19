author: Bren Stokes
id: vhol_data_marketplace_app
summary: This is a sample Snowflake Guide
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Building an application on Snowflake with data from Snowflake Data Marketplace
<!-- ------------------------ -->
## Overview 
Duration: 1

Snowflake Data Market Place can provide rapid results to external data which can be used as an overlay or enhancement of your existing data to monitor trends and perform compelling results. Building an application to distribute your results rapidly on a modern data platform are key to innovating faster and gaining a competitive advantage.
Snowflake combined with Quasar, a modern Application framework together with AWS can help you achieve that competitive advantage. In this lab, we will show how to build a small web application we use the Quasar Application Framework and AWS Lambda Python Layer.  
### Images
![Architecture](/media/DataM.png)
![App Image](/media/vue-final.png)

### Prerequisites
- We will be using Visual Studio Code in this lab but you are welcome to use your preference.
- You will need to Sign-up for a free AWS trial account.
- You will need Sign-up for a free Snowflake trial account.
- We provided the snowflake connector for python and made it available for you to download:  

### What You’ll Learn about Data Marketplace 
- How to explore the Data Marketplace Listings
- How to import data from the Data Marketplace
- How to review data marketplace data for insight development

### What You’ll Learn about Building an Application  
- How simple it is to connect to Snowflake Datamarketplace Data
- How simple it is to query the data from the Marketplace Datasets 
- How to perform a quik regression analysis on the Datasets
- How to create a view of the Marketplace Datasets  
- How to create a line chart using the Quasar application framework
- How to attach the snow-flake connector in AWS 
- How to create the AWS lambda function to query snowflake and pass the data to the application endpoint.
- How to build the Lambda python script to support interaction with the quasar line charts.

### What You’ll Need 
- A [AWS] (https://aws.amazon.com/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all) free trial Account 
- A [Snowflake](https://signup.snowflake.com/?_ga=2.216496658.583434456.1619544527-1296939414.1603389593) trial Account 
- [Download](https://download) snowflake-connector-python, snowflake queries, quasar sample application code.
- [Quasar CLI](https://quasar.dev/start/pick-quasar-flavour/) Installed
- [Quasar Installation Video ](https://www.youtube.com/watch?v=BK66mQTSl7U) Installed
- [Download snowflake-connector-python.zip](https://github.com/Snowflake-Labs/sfguide-marketplace-data-app/releases/tag/v1)
-  [Getting your AWS Lambda Functions to work with Snowflake -Connector Download ](https://medium.com/snowflake/getting-your-aws-lambda-functions-to-work-with-snowflake-a14b453bb5ee) 



### What You’ll Build 
- A Quasar .vue chart sourced with Snowflake data marketplace Knoema Economy and Poverty Data.
- A Snowflake Query using the Regression function
- A AWS Lambda with the snowflake python connector

<!-- ------------------------ -->

## Working with Data Market Place 
Duration: 2

Snowflake’s Data Marketplace provides visibility to a wide variety of datasets from third party data stewards which broaden access to data points used to transform business process.  The Data Marketplace also removes the need to integrate and model data by providing secure access to data sets fully maintained by the data provider. Preview Levi's video in this VHOL to select the Knoema datasets from the Snowflake MarketPlace.

```markdown

## Step 1  Review the available data tables
Duration: 8
--Review the datasets available
select * from "KNOEMA_POVERTY_DATA_ATLAS"."POVERTY"."DATASETS";
select * from "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."DATASETS";

## Step 2 identify the columns by which data sets can be joined by running simple select statements for a variety of different data views.  This will allow you to see patterns in data which join views to produce a combined view of many datasets.

select * from "KNOEMA_POVERTY_DATA_ATLAS"."POVERTY"."sdg_01_20" agi;
--Poverty Thresholds -ilc_li01  geo, geoName, geoRegionid month start date
select * from "KNOEMA_POVERTY_DATA_ATLAS"."POVERTY"."ilc_li01";
--Household Investment rate tec00098  geo, geoName, geoRegionid annual start date
select * from "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."tec00098";
--Household Saving rate teina500-20160217 geo, geoName, geoRegionid quarter start date
select * from "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."teina500-20160217";
--Key indicators annual nasa_10_ki-20180427 geo, geoName, geoRegionid annual start date
select * from "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."nasa_10_ki-20180427";
--Proverty and Equity WBPED2020  Country, Country Name, Country Regiono annual start date
select * from "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."WBPED2020"
```
  Review the datasets available and identify which data sets can be joined by running simple select statements for a variety of different data views.  This will allow you to see patterns in data which join views to produce a combined view of many datasets. 
<!-- ------------------------ -->
## Create Snowflake Views
Duration: 1

Using Snowflake's Regression function returns the slope of the linear regression line for non-null pairs in a group. It is computed for non-null pairs, a powerful way to compare multiple variables in a set of data. It will help us evaluate in this case, Credit worthiness of Single Persons relative to poverty. We also look at Savings rate and average investment rates by geography and time.

```markdown

## Step 1 Create a View from the Regression query
Duration: 1

create view VHOLAPP2 as select 
agi."geo RegionId" as GeoRegionIdAgi
, agi."Date" as dateAgi
, agi."Value" as ValueAgi
, pth."geo RegionId" as GeoRegionIdPth
, pth."Date"  as datePth
, pth."hhtyp Name" as hhtypNamePth
, pth."indic_il Name" as NamePth
, pth."currency Name"as Name3
, pth."Value" as ValuePth
, ir."geo RegionId"as GeoRegionIdIr
, ir."Date" as  DateIr
, ir."na_item Name" as na_itemNameIr
, ir."Measure Name" as MeasuerNameIr 
, ir."Value" as ValueIr
, sr."geo RegionId" as GeoRegionIdSr
, sr."Date" as  DateSr
, sr."na_item Name" as na_itemNameSr
, sr."Measure Name" as MeasuerNameSr 
, sr."Value" as ValueSr
,REGR_SLOPE(pth."Value", ir."Value") OVER (  PARTITION BY pth."geo RegionId",pth.
"hhtyp Name" ) as ir_lin
,REGR_SLOPE(pth."Value", sr."Value") OVER (  PARTITION BY pth."geo RegionId",pth.
"hhtyp Name" ) as sr_lin

from "KNOEMA_POVERTY_DATA_ATLAS"."POVERTY"."sdg_01_20" agi  --pov atlas
inner join "KNOEMA_POVERTY_DATA_ATLAS"."POVERTY"."ilc_li01" pth on agi."geo 
RegionId"=pth."geo RegionId" and agi."Date"=pth."Date"  -- join thresholds
inner join "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."tec00098" ir on agi."geo 
RegionId"=ir."geo RegionId" and agi."Date"=ir."Date" -- join investment rate
inner join "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."teina500-20160217" sr on agi."geo - RegionId"=sr."geo RegionId" and agi."Date"=sr."Date"  -- join saving rate


## Step 2 Create a view to pair down the variables for the APP --
Duration: 2

create view VHOLAPP3 as select 
 GeoRegionIdPth, dateagi
 ,hhtypNamePth
 ,min(ValuePth) ValuePth
 ,avg(ir_lin) avg_Investment_Rate
 ,avg(sr_lin) avg_Savings_Rate
 from VHOLAPP2
 where GeoRegionIdAgi = 'AT' and hhtypNamePth = 'Single person'
 
  group by dateagi,GeoRegionIdPth,hhtypNamePth--, ir_lin, sr_lin
  order by dateagi,GeoRegionIdPth,hhtypNamePth--, ir_lin, sr_lin 

```
  Limiting the variables that will be presented on the appliacation layer (in this case our chart) is an efficient use of data and compute resourses.Hence why we created the VHOLAPP3 view. 
<!-- ------------------------ -->

## Create Application Code for Line Chart
Duration: 1

This example uses the Quasar Application Framework we review the vue.js file. Please  see the prerequisits for this lab.  

```markdown
## Create Index.vue
Duration: 2

<template>
  <q-page>
    <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
      <q-card class="my-card">
        <div class="row">
          <div class="col-3">
            <q-card-section>
              <div class="text-h6">Please select a geography:</div>
              <q-select
                filled
                v-model="selectedCountry"
                :options="countryOptions"
                label="Geography"
                style="width: 300px"
              />
            </q-card-section>
          </div>
          <div class="col-3">
            <q-card-section>
              <div class="text-h6">Please select the period:</div>
              <q-range
                v-model="selectedPeriod"
                :min="2013"
                :max="2020"
                :step="1"
                style="width: 300px"
                label
              />
            </q-card-section>
          </div>
          <div class="self-center">
            <q-btn color="primary" label="refresh" @click="refreshGraph" />
          </div>
        </div>

        <q-card-section> </q-card-section>
      </q-card>
    </q-form><br/>
    <q-separator />
        <q-card class="my-card">
    <echarts :option="chartOptions" :height="400" :width="1200"></echarts>
        </q-card>
  </q-page>
</template>

<script>
import echarts from "src/components/echarts.vue";
export default {
  name: "PageIndex",
  components: { echarts },
  //Let's add the list of Geography codes to selecton filter....
  data() {
    return {
      countryOptions: [
        "AT",
        "BE",
        "CZ",
        "DE",
        "DK",
        "ES",
        "FI",
        "FR",
        "GB",
        "HR",
        "IE",
        "IT",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "SE",
        "SI",
      ],
      selectedCountry: null,
      selectedPeriod: {
        min: 2013,
        max: 2020,
      },
      chartOptions: null,
    };
  },
  //Let's enforce selecton of Geography, and Start and End for time period...
  methods: {
    refreshGraph: function () {
      if (!this.selectedCountry) {
        this.$q.notify({
          type: "negative",
          message: `You must select a geography.`,
        });
        this.chartOptions = null;
        return;
      }

      if (!this.selectedPeriod.min || !this.selectedPeriod.max) {
        this.$q.notify({
          type: "negative",
          message: `You must select a period.`,
        });
        this.chartOptions = null;
        this.chartOptions = null;
        return;
      }
      //Here we GET the json data passed through the lambda function from the embeded SQL query from snowflake view through our API endpoint
      return this.$axios
        .get(
          "https://rkpnrd2qf1.execute-api.us-west-1.amazonaws.com/default/snowdemo?geo=" +
            this.selectedCountry +
            "&startYear=" +
            this.selectedPeriod.min +
            "&endYear=" +
            this.selectedPeriod.max
        )
        .then((response) => {
          console.log(response);

          let results = response.data;
          let VALUEPTHValues = [];
          let AVG_INVESTMENT_RATEValues = [];
          let AVG_SAVINGS_RATEValues =[]
          //Now lets push the variables from Snowflake View  to the chart Here...
          let xDates = [];
          results.map((item) => {
            VALUEPTHValues.push(item.VALUEPTH);
            AVG_INVESTMENT_RATEValues.push(item.AVG_INVESTMENT_RATE);
             AVG_SAVINGS_RATEValues.push(item.AVG_SAVINGS_RATE)
            xDates.push(item.DATEAGI);
          });

          //Now lets add the chart title  and assign the tool tip here.....
          this.chartOptions = {
            title: {
              text: "Credit Worthiness of Single Persons Relative to Poverty",
            },
            tooltip: {
              trigger: "axis",
            },
            legend: {
              data: ["VALUEPTH", "AVG_INVESTMENT_RATE"],
            },
            grid: {
              left: "3%",
              right: "4%",
              bottom: "3%",
              containLabel: true,
            },
            toolbox: {
              feature: {
                saveAsImage: {},
              },
            },
            xAxis: {
              type: "category",
              boundaryGap: false,
              data: xDates,
            },
            yAxis: {
              type: "value",
            },
            //Now lets pass the values to the line charts for all three values here....
            series: [
              {
                name: "POVERTY THRESHOLD",
                type: "line",

                data: VALUEPTHValues,
              },
              {
            name: 'SAVINGS RATE',
            type: 'line',
       data: AVG_SAVINGS_RATEValues
        },

              {
                name: "AVG INVESTMENT RATE",
                type: "line",

                data: AVG_INVESTMENT_RATEValues,
              },
            ],
          };
        });
    },
  },
};
</script>

```

### quasar.config.js
```  
// Quasar plugins
      plugins: ['Notify']
    },
```


<!-- ------------------------ -->
## Building the Lambda
Duration: 8

From the AWS services console, go straight into the Lambda and follow the video instructions presented in this VHOL by Bren Stokes. 


### Lambda.py Function 
```javascript
{
  "queryStringParameters": {
    "startYear": "2015",
    "endYear": "2020",
    "geo": "DK"
  }
}

10)	Greetings and Save/ create 
11)	Configuration – add trigger -API Trigger  Rest, Authorization, None 
12)	Review the function

import json, decimal, datetime 
import snowflake.connector
from snowflake.connector import DictCursor
def default_json_transform(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError
def lambda_handler(event, context):
    print('event:',json.dumps(event))
    #print('queryStringParameters:', json.dumps(event['queryStringParameters'])
    # 1. Test query string parameters
    # TODO implement
    #startY= event["startYear"]
    #endY= event["endYear"]
    #geo= event["geo"]
     # Lets Parse query string parameters
    startY= event["queryStringParameters"]["startYear"]
    endY= event["queryStringParameters"]["endYear"]
    geo= event["queryStringParameters"]["geo"]
  
    
    # Lets get connection going...
    ctx = snowflake.connector.connect(
        user='yournusername',
        account='sfsenorthamerica_youraccount',
        password='SnowGlowXXX',
        role='ACCOUNTADMIN',
        warehouse='SNOWBALL',
        database="TEMP",
        schema='PUBLIC')
        # set the cursor...
    cs = ctx.cursor(DictCursor)

    # Let's execute the query to snowflake.....
    cs.execute("select  ValuePth, DateAgi, Avg_Investment_Rate, Avg_Savings_Rate, GeoRegionIdPth from TEMP.public.VHOLAPP3 WHERE  hhtypNamePth = 'Single person' and GeoRegionIdPth='" + geo + "' AND DateAgi >=TO_DATE('" + startY + "-01-01','YYYY-DD-MM') AND DateAgi <= TO_DATE('"+endY +"-01-01','YYYY-DD-MM')") 
    
    # Here it goes to the Array.....
    dataArr= []
    # It dumps the string to Json....WHEW! Finish up done
    for rec in cs:
        dataArr.append(rec)
    json_formatted_str = json.dumps(dataArr, default=default_json_transform)
    cs.close()
    return {
        'statusCode': 200,
        'body': json_formatted_str,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
            },
    }

```

### Test Script using the AWS Lambda Test Tab
```
{
  "queryStringParameters": {
    "startYear": "2015",
    "endYear": "2020",
    "geo": "DK"
  }
}

```
<!-- ------------------------ -->
## Additional References
Duration: 2

A fantastic reference for downloading the snowflake-python connector .zip file  [Getting your AWS Lambda Functions to work with Snowflake](https://medium.com/snowflake/getting-your-aws-lambda-functions-to-work-with-snowflake-a14b453bb5ee) to see how to use markdown to generate these elements. 


### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>


<!-- ------------------------ -->
## Conclusion
Duration: 1



To learn more about Snowflake Data MarketPlace visit the official website here: [Snowflake Data MarketPlace](https://www.snowflake.com/data-marketplace/)

To learn more about Building Data Aapplications isit the official  website here: ([Building Data Aapplications](https://www.snowflake.com/workloads/data-applications/)



 [Register for Snowflake Summit 2021](https://www.snowflake.com/summit/?utm_source=paidsearch&utm_medium=ppc&utm_campaign=NA-Branded&_bt=513345067347&_bk=%2Bsnowflake%20%2Bsummit&_bm=b&_bn=g&_bg=111755576146&gclid=CjwKCAjw7J6EBhBDEiwA5UUM2iW-7BWtxKYf9hV5qno24Wvie0GWuaqoHyToZvEC0xRjga0Z5N_Y0BoCr9MQAvD_BwE&gclsrc=aw.ds) 


### What we've covered
- You were aquainted with Snowflake's Data MarketPlace
- You became familiar with building an application using the Quasar Application Framework
- We guided you through using the Snowflake-Connector for Python via AWS Lambda
- We created the API Gateway and tested the functionaltiy of the application