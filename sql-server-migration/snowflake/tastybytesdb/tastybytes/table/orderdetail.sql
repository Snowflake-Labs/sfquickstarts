USE DATABASE TastyBytesDB;

CREATE OR REPLACE TABLE TastyBytes.OrderDetail (
    OrderID INT NOT NULL,
    LineNumber INT NOT NULL,
    MenuItemID INT NOT NULL,
    Quantity INT NOT NULL DEFAULT ((1)) /*** SSC-FDM-0012 - CONSTRAINT NAME 'DF__OrderDeta__Quant__571DF1D5' IN DEFAULT EXPRESSION CONSTRAINT IS NOT SUPPORTED IN SNOWFLAKE ***/,
    UnitPrice NUMBER(38, 4) NOT NULL,
    Discount NUMBER(38, 4) NOT NULL DEFAULT ((0.00)) /*** SSC-FDM-0012 - CONSTRAINT NAME 'DF__OrderDeta__Disco__5812160E' IN DEFAULT EXPRESSION CONSTRAINT IS NOT SUPPORTED IN SNOWFLAKE ***/,
    LineTotal DECIMAL(10, 2) NULL,
    SpecialRequests NVARCHAR(300) COLLATE 'EN-CI-AS' /*** SSC-PRF-0002 - CASE INSENSITIVE COLUMNS CAN DECREASE THE PERFORMANCE OF QUERIES ***/ /*** SSC-FDM-TS0002 - COLLATION FOR VALUE CP1 NOT SUPPORTED ***/ NULL
)
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
;