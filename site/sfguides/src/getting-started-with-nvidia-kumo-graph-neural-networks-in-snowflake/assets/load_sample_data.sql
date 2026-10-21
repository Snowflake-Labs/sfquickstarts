/*
  Load the four sample tables used by the NVIDIA Kumo quickstart.

  Source: Microsoft SQL Server sample OLTP install script (MIT license)
  https://github.com/Microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script

  1. Download the four data files into your current directory:

     BASE=https://raw.githubusercontent.com/microsoft/sql-server-samples/master/samples/databases/adventure-works/oltp-install-script
     for t in Customer Product SalesOrderHeader SalesOrderDetail; do curl -sLO "$BASE/$t.csv"; done

  2. From that same directory, run this script with the Snowflake CLI:

     snow sql -f load_sample_data.sql -D "db=<DB>" -D "schema=<SCHEMA>" -D "wh=<WAREHOUSE>"

  Table names are quoted mixed case ("Customer", "Product", ...) to match the guide.
*/

USE WAREHOUSE <% wh %>;
CREATE DATABASE IF NOT EXISTS <% db %>;
CREATE SCHEMA IF NOT EXISTS <% db %>.<% schema %>;
USE SCHEMA <% db %>.<% schema %>;

-- Files are tab delimited, no header, UTF-8.
CREATE OR REPLACE FILE FORMAT kumo_sample_tsv
  TYPE = CSV
  FIELD_DELIMITER = '\t'
  SKIP_HEADER = 0
  EMPTY_FIELD_AS_NULL = TRUE
  ENCODING = 'UTF8';

CREATE OR REPLACE TEMPORARY STAGE kumo_sample_stage FILE_FORMAT = kumo_sample_tsv;

PUT file://Customer.csv @kumo_sample_stage AUTO_COMPRESS = TRUE OVERWRITE = TRUE;
PUT file://Product.csv @kumo_sample_stage AUTO_COMPRESS = TRUE OVERWRITE = TRUE;
PUT file://SalesOrderHeader.csv @kumo_sample_stage AUTO_COMPRESS = TRUE OVERWRITE = TRUE;
PUT file://SalesOrderDetail.csv @kumo_sample_stage AUTO_COMPRESS = TRUE OVERWRITE = TRUE;

CREATE OR REPLACE TABLE "Customer" (
  "CustomerID" NUMBER,
  "PersonID" NUMBER,
  "StoreID" NUMBER,
  "TerritoryID" NUMBER,
  "AccountNumber" VARCHAR,
  "rowguid" VARCHAR,
  "ModifiedDate" TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE "Product" (
  "ProductID" NUMBER,
  "Name" VARCHAR,
  "ProductNumber" VARCHAR,
  "MakeFlag" BOOLEAN,
  "FinishedGoodsFlag" BOOLEAN,
  "Color" VARCHAR,
  "SafetyStockLevel" NUMBER,
  "ReorderPoint" NUMBER,
  "StandardCost" NUMBER(19,4),
  "ListPrice" NUMBER(19,4),
  "Size" VARCHAR,
  "SizeUnitMeasureCode" VARCHAR,
  "WeightUnitMeasureCode" VARCHAR,
  "Weight" NUMBER(8,2),
  "DaysToManufacture" NUMBER,
  "ProductLine" VARCHAR,
  "Class" VARCHAR,
  "Style" VARCHAR,
  "ProductSubcategoryID" NUMBER,
  "ProductModelID" NUMBER,
  "SellStartDate" TIMESTAMP_NTZ,
  "SellEndDate" TIMESTAMP_NTZ,
  "DiscontinuedDate" TIMESTAMP_NTZ,
  "rowguid" VARCHAR,
  "ModifiedDate" TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE "SalesOrderHeader" (
  "SalesOrderID" NUMBER,
  "RevisionNumber" NUMBER,
  "OrderDate" TIMESTAMP_NTZ,
  "DueDate" TIMESTAMP_NTZ,
  "ShipDate" TIMESTAMP_NTZ,
  "Status" NUMBER,
  "OnlineOrderFlag" BOOLEAN,
  "SalesOrderNumber" VARCHAR,
  "PurchaseOrderNumber" VARCHAR,
  "AccountNumber" VARCHAR,
  "CustomerID" NUMBER,
  "SalesPersonID" NUMBER,
  "TerritoryID" NUMBER,
  "BillToAddressID" NUMBER,
  "ShipToAddressID" NUMBER,
  "ShipMethodID" NUMBER,
  "CreditCardID" NUMBER,
  "CreditCardApprovalCode" VARCHAR,
  "CurrencyRateID" NUMBER,
  "SubTotal" NUMBER(19,4),
  "TaxAmt" NUMBER(19,4),
  "Freight" NUMBER(19,4),
  "TotalDue" NUMBER(19,4),
  "Comment" VARCHAR,
  "rowguid" VARCHAR,
  "ModifiedDate" TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE "SalesOrderDetail" (
  "SalesOrderID" NUMBER,
  "SalesOrderDetailID" NUMBER,
  "CarrierTrackingNumber" VARCHAR,
  "OrderQty" NUMBER,
  "ProductID" NUMBER,
  "SpecialOfferID" NUMBER,
  "UnitPrice" NUMBER(19,4),
  "UnitPriceDiscount" NUMBER(19,4),
  "LineTotal" NUMBER(38,6),
  "rowguid" VARCHAR,
  "ModifiedDate" TIMESTAMP_NTZ
);

COPY INTO "Customer" FROM @kumo_sample_stage/Customer.csv.gz ON_ERROR = ABORT_STATEMENT;
COPY INTO "Product" FROM @kumo_sample_stage/Product.csv.gz ON_ERROR = ABORT_STATEMENT;
COPY INTO "SalesOrderHeader" FROM @kumo_sample_stage/SalesOrderHeader.csv.gz ON_ERROR = ABORT_STATEMENT;
COPY INTO "SalesOrderDetail" FROM @kumo_sample_stage/SalesOrderDetail.csv.gz ON_ERROR = ABORT_STATEMENT;

-- Expected: Customer 19820, Product 504, SalesOrderHeader 31465, SalesOrderDetail 121317
SELECT 'Customer' AS table_name, COUNT(*) AS row_count FROM "Customer"
UNION ALL SELECT 'Product', COUNT(*) FROM "Product"
UNION ALL SELECT 'SalesOrderHeader', COUNT(*) FROM "SalesOrderHeader"
UNION ALL SELECT 'SalesOrderDetail', COUNT(*) FROM "SalesOrderDetail";
