-- EDW
create or replace schema ADVENTUREWORKSDW.EDW;

create or replace TABLE ADVENTUREWORKSDW.EDW."DimAccount" (
	"AccountKey" NUMBER(38,0) NOT NULL autoincrement COMMENT 'Unique Identifier of the Account data',
	"ParentAccountKey" NUMBER(38,0) COMMENT 'Identifier of parent Account',
	"AccountCodeAlternateKey" NUMBER(38,0),
	"ParentAccountCodeAlternateKey" NUMBER(38,0),
	"AccountDescription" VARCHAR(50),
	"AccountType" VARCHAR(50),
	"Operator" VARCHAR(50),
	"CustomMembers" VARCHAR(300),
	"ValueType" VARCHAR(50),
	"CustomMemberOptions" VARCHAR(200),
	constraint PK_DimAccount primary key ("AccountKey")
)COMMENT='Holds all Account information'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimCurrency" (
	"CurrencyKey" NUMBER(38,0) NOT NULL autoincrement COMMENT 'Currency Identifier',
	"CurrencyAlternateKey" VARCHAR(3) NOT NULL COMMENT 'Alternate Currency Identifier',
	"CurrencyName" VARCHAR(50) NOT NULL COMMENT 'Name of the Currency',
	constraint PK_DimCurrency primary key ("CurrencyKey")
)COMMENT='Dimension for Currency Data'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimCustomer" (
	"CustomerKey" NUMBER(38,0) NOT NULL autoincrement COMMENT 'Customer Identifier',
	"GeographyKey" NUMBER(38,0) COMMENT 'Geographic informatio',
	"CustomerAlternateKey" VARCHAR(15) NOT NULL COMMENT 'Alternate Key',
	"Title" VARCHAR(8) COMMENT 'Title of the Customer',
	"FirstName" VARCHAR(50),
	"MiddleName" VARCHAR(50),
	"LastName" VARCHAR(50),
	"NameStyle" VARCHAR(5),
	"BirthDate" DATE,
	"MaritalStatus" VARCHAR(1),
	"Suffix" VARCHAR(10),
	"Gender" VARCHAR(1),
	"EmailAddress" VARCHAR(50),
	"YearlyIncome" NUMBER(38,0),
	"TotalChildren" NUMBER(38,0),
	"NumberChildrenAtHome" NUMBER(38,0),
	"EnglishEducation" VARCHAR(40),
	"SpanishEducation" VARCHAR(40),
	"FrenchEducation" VARCHAR(40),
	"EnglishOccupation" VARCHAR(100),
	"SpanishOccupation" VARCHAR(100),
	"FrenchOccupation" VARCHAR(100),
	"HouseOwnerFlag" VARCHAR(1),
	"NumberCarsOwned" NUMBER(38,0),
	"AddressLine" VARCHAR(120),
	"AddressLine2" VARCHAR(120),
	"Phone" VARCHAR(20),
	"DateFirstPurchase" DATE,
	"CommuteDistance" VARCHAR(15),
	constraint PK_DimCustomer primary key ("CustomerKey"),
	constraint FK_DimCustomer_401 foreign key ("GeographyKey") references ADVENTUREWORKSDW.EDW."DimGeography"(GeographyKey)
)COMMENT='Dimension for Customer Data'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimDate" (
	"DateKey" NUMBER(38,0) NOT NULL,
	"FullDateAlternateKey" DATE NOT NULL,
	"DayNumberOfWeek" NUMBER(38,0) NOT NULL,
	"EnglishDayNameOfWeek" VARCHAR(10) NOT NULL,
	"SpanishDayNameOfWeek" VARCHAR(10) NOT NULL,
	"FrenchDayNameOfWeek" VARCHAR(10) NOT NULL,
	"DayNumberOfMonth" NUMBER(38,0) NOT NULL,
	"DayNumberOfYear" NUMBER(38,0) NOT NULL,
	"WeekNumberOfYear" NUMBER(38,0) NOT NULL,
	"EnglishMonthName" VARCHAR(10) NOT NULL,
	"SpanishMonthName" VARCHAR(10) NOT NULL,
	"FrenchMonthName" VARCHAR(10) NOT NULL,
	"MonthNumberOfYear" NUMBER(38,0) NOT NULL,
	"CalendarQuarter" NUMBER(38,0) NOT NULL,
	"CalendarYear" NUMBER(38,0) NOT NULL,
	"CalendarSemester" NUMBER(38,0) NOT NULL,
	"FiscalQuarter" NUMBER(38,0) NOT NULL,
	"FiscalYear" NUMBER(38,0) NOT NULL,
	"FiscalSemester" NUMBER(38,0) NOT NULL,
	constraint PK_DimDate primary key ("DateKey")
)COMMENT='Dimension for Date time'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimDepartmentGroup" (
	"DepartmentGroupKey" NUMBER(38,0) NOT NULL autoincrement,
	"ParentDepartmentGroupKey" NUMBER(38,0),
	"DepartmentGroupName" VARCHAR(50),
	constraint PK_DimDepartmentGroup primary key ("DepartmentGroupKey")
)COMMENT='Dimension for Department groups'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimEmployee" (
	"EmployeeKey" NUMBER(38,0) NOT NULL autoincrement,
	"ParentEmployeeKey" NUMBER(38,0),
	"EmployeeNationalIDAlternateKey" VARCHAR(15),
	"ParentEmployeeNationalIDAlternateKey" VARCHAR(15),
	"SalesTerritoryKey" NUMBER(38,0),
	"FirstName" VARCHAR(50) NOT NULL,
	"LastName" VARCHAR(50) NOT NULL,
	"MiddleName" VARCHAR(50),
	"NameStyle" NUMBER(38,0) NOT NULL,
	"Title" VARCHAR(50),
	"HireDate" DATE,
	"BirthDate" DATE,
	"LoginID" VARCHAR(256),
	"EmailAddress" VARCHAR(50),
	"Phone" VARCHAR(25),
	"MaritalStatus" VARCHAR(1),
	"EmergencyContactName" VARCHAR(50),
	"EmergencyContactPhone" VARCHAR(25),
	"SalariedFlag" NUMBER(38,0),
	"Gender" VARCHAR(1),
	"PayFrequency" NUMBER(38,0),
	"BaseRate" NUMBER(38,0),
	"VacationHours" NUMBER(38,0),
	"SickLeaveHours" NUMBER(38,0),
	"CurrentFlag" NUMBER(38,0) NOT NULL,
	"SalesPersonFlag" NUMBER(38,0) NOT NULL,
	"DepartmentName" VARCHAR(50),
	"StartDate" DATE,
	"EndDate" DATE,
	"Status" VARCHAR(50),
	constraint PK_DimEmployee primary key ("EmployeeKey"),
	constraint FK_DimEmployee_403 foreign key ("ParentEmployeeKey") references ADVENTUREWORKSDW.EDW."DimEmployee"(EmployeeKey),
	constraint FK_DimEmployee_405 foreign key ("SalesTerritoryKey") references ADVENTUREWORKSDW.EDW."DimSalesTerritory"(SalesTerritoryKey)
)COMMENT='This table holds all Employee Information'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimGeography" (
	"GeographyKey" NUMBER(38,0) NOT NULL autoincrement,
	"City" VARCHAR(30),
	"StateProvinceCode" VARCHAR(3),
	"StateProvinceName" VARCHAR(50),
	"CountryRegionCode" VARCHAR(3),
	"EnglishCountryRegionName" VARCHAR(50),
	"SpanishCountryRegionName" VARCHAR(50),
	"FrenchCountryRegionName" VARCHAR(50),
	"PostalCode" VARCHAR(15),
	"SalesTerritoryKey" NUMBER(38,0),
	"IpAddressLocator" VARCHAR(15),
	constraint PK_DimGeography primary key ("GeographyKey")
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimOrganization" (
	"OrganizationKey" NUMBER(38,0) NOT NULL autoincrement,
	"ParentOrganizationKey" NUMBER(38,0),
	"PercentageOfOwnership" VARCHAR(16),
	"OrganizationName" VARCHAR(50),
	"CurrencyKey" NUMBER(38,0),
	constraint PK_DimOrganization primary key ("OrganizationKey")
)COMMENT='Dimension for Organizational Data'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimProduct" (
	"ProductKey" NUMBER(38,0) NOT NULL autoincrement,
	"ProductAlternateKey" VARCHAR(25),
	"ProductSubcategoryKey" NUMBER(38,0),
	"WeightUnitMeasureCode" VARCHAR(3),
	"SizeUnitMeasureCode" VARCHAR(3),
	"EnglishProductName" VARCHAR(50) NOT NULL,
	"SpanishProductName" VARCHAR(50),
	"FrenchProductName" VARCHAR(50),
	"StandardCost" NUMBER(38,0),
	"FinishedGoodsFlag" NUMBER(38,0) NOT NULL,
	"Color" VARCHAR(15) NOT NULL,
	"SafetyStockLevel" NUMBER(38,0),
	"ReorderPoint" NUMBER(38,0),
	"ListPrice" NUMBER(38,0),
	"Size" VARCHAR(50),
	"SizeRange" VARCHAR(50),
	"Weight" FLOAT,
	"DaysToManufacture" NUMBER(38,0),
	"ProductLine" VARCHAR(2),
	"DealerPrice" NUMBER(38,0),
	"Class" VARCHAR(2),
	"Style" VARCHAR(2),
	"ModelName" VARCHAR(50),
	"EnglishDescription" VARCHAR(400),
	"FrenchDescription" VARCHAR(400),
	"ChineseDescription" VARCHAR(400),
	"ArabicDescription" VARCHAR(400),
	"HebrewDescription" VARCHAR(400),
	"ThaiDescription" VARCHAR(400),
	"GermanDescription" VARCHAR(400),
	"JapaneseDescription" VARCHAR(400),
	"TurkishDescription" VARCHAR(400),
	"Status" VARCHAR(7),
	constraint PK_DimProduct primary key ("ProductKey"),
	constraint FK_DimProduct_407 foreign key ("ProductSubcategoryKey") references ADVENTUREWORKSDW.EDW."DimProductSubcategory"(ProductSubcategoryKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimProductCategory" (
	"ProductCategoryKey" NUMBER(38,0) NOT NULL autoincrement,
	"ProductCategoryAlternateKey" NUMBER(38,0),
	"EnglishProductCategoryName" VARCHAR(50) NOT NULL,
	"SpanishProductCategoryName" VARCHAR(50) NOT NULL,
	"FrenchProductCategoryName" VARCHAR(50) NOT NULL,
	constraint PK_DimProductCategory primary key ("ProductCategoryKey")
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimProductSubcategory" (
	"ProductSubcategoryKey" NUMBER(38,0) NOT NULL autoincrement,
	"ProductSubcategoryAlternateKey" NUMBER(38,0),
	"EnglishProductSubcategoryName" VARCHAR(50) NOT NULL,
	"SpanishProductSubcategoryName" VARCHAR(50) NOT NULL,
	"FrenchProductSubcategoryName" VARCHAR(50) NOT NULL,
	"ProductCategoryKey" NUMBER(38,0),
	constraint PK_DimProductSubcategory primary key ("ProductSubcategoryKey"),
	constraint FK_DimProductSubcategory_409 foreign key ("ProductCategoryKey") references ADVENTUREWORKSDW.EDW."DimProductCategory"(ProductCategoryKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimPromotion" (
	"PromotionKey" NUMBER(38,0) NOT NULL autoincrement,
	"PromotionAlternateKey" NUMBER(38,0),
	"EnglishPromotionName" VARCHAR(255),
	"SpanishPromotionName" VARCHAR(255),
	"FrenchPromotionName" VARCHAR(255),
	"DiscountPct" FLOAT,
	"EnglishPromotionType" VARCHAR(50),
	"SpanishPromotionType" VARCHAR(50),
	"FrenchPromotionType" VARCHAR(50),
	"EnglishPromotionCategory" VARCHAR(50),
	"SpanishPromotionCategory" VARCHAR(50),
	"FrenchPromotionCategory" VARCHAR(50),
	"MinQty" NUMBER(38,0),
	"MaxQty" NUMBER(38,0),
	constraint PK_DimPromotion primary key ("PromotionKey")
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimReseller" (
	"ResellerKey" NUMBER(38,0) NOT NULL autoincrement,
	"GeographyKey" NUMBER(38,0),
	"ResellerAlternateKey" VARCHAR(15),
	"Phone" VARCHAR(25),
	"BusinessType" VARCHAR(20) NOT NULL,
	"ResellerName" VARCHAR(50) NOT NULL,
	"NumberEmployees" NUMBER(38,0),
	"OrderFrequency" VARCHAR(1),
	"OrderMonth" NUMBER(38,0),
	"FirstOrderYear" NUMBER(38,0),
	"LastOrderYear" NUMBER(38,0),
	"ProductLine" VARCHAR(50),
	"AddressLine1" VARCHAR(60),
	"AddressLine2" VARCHAR(60),
	"AnnualSales" NUMBER(38,0),
	"BankName" VARCHAR(50),
	"MinPaymentType" NUMBER(38,0),
	"MinPaymentAmount" NUMBER(38,0),
	"AnnualRevenue" NUMBER(38,0),
	"YearOpened" NUMBER(38,0),
	constraint PK_DimReseller primary key ("ResellerKey"),
	constraint FK_DimReseller_411 foreign key ("GeographyKey") references ADVENTUREWORKSDW.EDW."DimGeography"(GeographyKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."DimSalesTerritory" (
	"SalesTerritoryKey" NUMBER(38,0) NOT NULL autoincrement,
	"SalesTerritoryAlternateKey" NUMBER(38,0),
	"SalesTerritoryRegion" VARCHAR(50) NOT NULL,
	"SalesTerritoryCountry" VARCHAR(50) NOT NULL,
	"SalesTerritoryGroup" VARCHAR(50),
	constraint PK_DimSalesTerritory primary key ("SalesTerritoryKey")
)COMMENT='Sales Territory data'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."DimScenario" (
	"ScenarioKey" NUMBER(38,0) NOT NULL autoincrement COMMENT 'Scenario Identifier',
	"ScenarioName" VARCHAR(50) COMMENT 'Name of the Scenario',
	"CreatedBy" VARCHAR(50) NOT NULL COMMENT 'Who Created this Scenario',
	"CreatedDate" TIMESTAMP_NTZ(9) NOT NULL COMMENT 'Scenario Creation Date',
	"UpdatedDate" TIMESTAMP_NTZ(9) NOT NULL,
	"UpdatedBy" VARCHAR(50) NOT NULL,
	"TestCol" VARCHAR(50) NOT NULL,
	constraint PK_DimScenario primary key ("ScenarioKey")
)COMMENT='Dimension Scenario'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."FactCurrencyRate" (
	"CurrencyKey" NUMBER(38,0) NOT NULL,
	"DateKey" NUMBER(38,0) NOT NULL,
	"AverageRate" FLOAT NOT NULL,
	"EndOfDayRate" FLOAT NOT NULL,
	constraint FK_FactCurrencyRate_413 foreign key ("CurrencyKey") references ADVENTUREWORKSDW.EDW."DimCurrency"(CurrencyKey),
	constraint FK_FactCurrencyRate_415 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."FactFinance" (
	"FinanceKey" NUMBER(38,0) NOT NULL autoincrement,
	"DateKey" NUMBER(38,0) NOT NULL,
	"OrganizationKey" NUMBER(38,0) NOT NULL,
	"DepartmentGroupKey" NUMBER(38,0) NOT NULL,
	"ScenarioKey" NUMBER(38,0) NOT NULL,
	"AccountKey" NUMBER(38,0) NOT NULL,
	"Amount" FLOAT NOT NULL,
	constraint FK_FactFinance_417 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactFinance_419 foreign key ("OrganizationKey") references ADVENTUREWORKSDW.EDW."DimOrganization"(OrganizationKey),
	constraint FK_FactFinance_421 foreign key ("DepartmentGroupKey") references ADVENTUREWORKSDW.EDW."DimDepartmentGroup"(DepartmentGroupKey),
	constraint FK_FactFinance_423 foreign key ("ScenarioKey") references ADVENTUREWORKSDW.EDW."DimScenario"(ScenarioKey),
	constraint FK_FactFinance_425 foreign key ("AccountKey") references ADVENTUREWORKSDW.EDW."DimAccount"(AccountKey)
)COMMENT='Facts for Finance'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."FactInternetSales" (
	"ProductKey" NUMBER(38,0) NOT NULL,
	"OrderDateKey" NUMBER(38,0) NOT NULL,
	"DueDateKey" NUMBER(38,0) NOT NULL,
	"ShipDateKey" NUMBER(38,0) NOT NULL,
	"CustomerKey" NUMBER(38,0) NOT NULL,
	"PromotionKey" NUMBER(38,0) NOT NULL,
	"CurrencyKey" NUMBER(38,0) NOT NULL,
	"SalesTerritoryKey" NUMBER(38,0) NOT NULL,
	"SalesOrderNumber" VARCHAR(20) NOT NULL,
	"SalesOrderLineNumber" NUMBER(38,0) NOT NULL,
	"RevisionNumber" NUMBER(38,0) NOT NULL,
	"OrderQuantity" NUMBER(38,0) NOT NULL,
	"UnitPrice" NUMBER(38,0) NOT NULL,
	"ExtendedAmount" NUMBER(38,0) NOT NULL,
	"UnitPriceDiscountPct" FLOAT NOT NULL,
	"DiscountAmount" FLOAT NOT NULL,
	"ProductStandardCost" NUMBER(38,0) NOT NULL,
	"TotalProductCost" NUMBER(38,0) NOT NULL,
	"SalesAmount" NUMBER(38,0) NOT NULL,
	"TaxAmt" NUMBER(38,0) NOT NULL,
	"Freight" NUMBER(38,0) NOT NULL,
	"CarrierTrackingNumber" VARCHAR(25),
	"CustomerPONumber" VARCHAR(25),
	constraint FK_FactInternetSales_427 foreign key ("ProductKey") references ADVENTUREWORKSDW.EDW."DimProduct"(ProductKey),
	constraint FK_FactInternetSales_429 foreign key ("CustomerKey") references ADVENTUREWORKSDW.EDW."DimCustomer"(CustomerKey),
	constraint FK_FactInternetSales_431 foreign key ("PromotionKey") references ADVENTUREWORKSDW.EDW."DimPromotion"(PromotionKey),
	constraint FK_FactInternetSales_433 foreign key ("CurrencyKey") references ADVENTUREWORKSDW.EDW."DimCurrency"(CurrencyKey),
	constraint FK_FactInternetSales_435 foreign key ("SalesTerritoryKey") references ADVENTUREWORKSDW.EDW."DimSalesTerritory"(SalesTerritoryKey),
	constraint FK_FactInternetSales_437 foreign key ("OrderDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactInternetSales_439 foreign key ("DueDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactInternetSales_441 foreign key ("ShipDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
)COMMENT='Fact table to hold Currency Data'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."FactProductInventory" (
	"ProductKey" NUMBER(38,0) NOT NULL,
	"DateKey" NUMBER(38,0) NOT NULL,
	"MovementDate" DATE NOT NULL,
	"UnitCost" NUMBER(38,0) NOT NULL,
	"UnitsIn" NUMBER(38,0) NOT NULL,
	"UnitsOut" NUMBER(38,0) NOT NULL,
	"UnitsBalance" NUMBER(38,0) NOT NULL,
	constraint FK_FactProductInventory_443 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."FactResellerSales" (
	"ProductKey" NUMBER(38,0) NOT NULL,
	"OrderDateKey" NUMBER(38,0) NOT NULL,
	"DueDateKey" NUMBER(38,0) NOT NULL,
	"ShipDateKey" NUMBER(38,0) NOT NULL,
	"ResellerKey" NUMBER(38,0) NOT NULL,
	"EmployeeKey" NUMBER(38,0) NOT NULL,
	"PromotionKey" NUMBER(38,0) NOT NULL,
	"CurrencyKey" NUMBER(38,0) NOT NULL,
	"SalesTerritoryKey" NUMBER(38,0) NOT NULL,
	"SalesOrderNumber" VARCHAR(20) NOT NULL,
	"SalesOrderLineNumber" NUMBER(38,0) NOT NULL,
	"RevisionNumber" NUMBER(38,0),
	"OrderQuantity" NUMBER(38,0),
	"UnitPrice" NUMBER(38,0),
	"ExtendedAmount" NUMBER(38,0),
	"UnitPriceDiscountPct" FLOAT,
	"DiscountAmount" FLOAT,
	"ProductStandardCost" NUMBER(38,0),
	"TotalProductCost" NUMBER(38,0),
	"SalesAmount" NUMBER(38,0),
	"TaxAmt" NUMBER(38,0),
	"Freight" NUMBER(38,0),
	"CarrierTrackingNumber" VARCHAR(25),
	"CustomerPONumber" VARCHAR(25),
	constraint FK_FactResellerSales_445 foreign key ("ProductKey") references ADVENTUREWORKSDW.EDW."DimProduct"(ProductKey),
	constraint FK_FactResellerSales_447 foreign key ("ResellerKey") references ADVENTUREWORKSDW.EDW."DimReseller"(ResellerKey),
	constraint FK_FactResellerSales_449 foreign key ("EmployeeKey") references ADVENTUREWORKSDW.EDW."DimEmployee"(EmployeeKey),
	constraint FK_FactResellerSales_451 foreign key ("PromotionKey") references ADVENTUREWORKSDW.EDW."DimPromotion"(PromotionKey),
	constraint FK_FactResellerSales_453 foreign key ("CurrencyKey") references ADVENTUREWORKSDW.EDW."DimCurrency"(CurrencyKey),
	constraint FK_FactResellerSales_455 foreign key ("SalesTerritoryKey") references ADVENTUREWORKSDW.EDW."DimSalesTerritory"(SalesTerritoryKey),
	constraint FK_FactResellerSales_457 foreign key ("OrderDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactResellerSales_459 foreign key ("DueDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactResellerSales_461 foreign key ("ShipDateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
)COMMENT='Fact data of Reseller Sales'
;
create or replace TABLE ADVENTUREWORKSDW.EDW."FactSalesQuota" (
	"SalesQuotaKey" NUMBER(38,0) NOT NULL autoincrement,
	"EmployeeKey" NUMBER(38,0) NOT NULL,
	"DateKey" NUMBER(38,0) NOT NULL,
	"CalendarYear" NUMBER(38,0) NOT NULL,
	"CalendarQuarter" NUMBER(38,0) NOT NULL,
	"SalesAmountQuota" NUMBER(38,0) NOT NULL,
	constraint FK_FactSalesQuota_463 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."FactSurveyResponse" (
	"SurveyResponseKey" NUMBER(38,0) NOT NULL autoincrement,
	"DateKey" NUMBER(38,0) NOT NULL,
	"CustomerKey" NUMBER(38,0) NOT NULL,
	"ProductCategoryKey" NUMBER(38,0) NOT NULL,
	"EnglishProductCategoryName" VARCHAR(50) NOT NULL,
	"ProductSubcategoryKey" NUMBER(38,0) NOT NULL,
	"EnglishProductSubcategoryName" VARCHAR(50) NOT NULL,
	constraint FK_FactSurveyResponse_465 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey),
	constraint FK_FactSurveyResponse_467 foreign key ("ProductCategoryKey") references ADVENTUREWORKSDW.EDW."DimProductCategory"(ProductCategoryKey)
);
create or replace TABLE ADVENTUREWORKSDW.EDW."NewFactCurrencyRate" (
	"AverageRate" FLOAT,
	"CurrencyID" VARCHAR(3),
	"CurrencyDate" DATE,
	"EndOfDayRate" FLOAT,
	"CurrencyKey" NUMBER(38,0),
	"DateKey" NUMBER(38,0),
	constraint FK_NewFactCurrencyRate_469 foreign key ("CurrencyKey") references ADVENTUREWORKSDW.EDW."DimCurrency"(CurrencyKey),
	constraint FK_NewFactCurrencyRate_471 foreign key ("DateKey") references ADVENTUREWORKSDW.EDW."DimDate"(DateKey)
);

Create or Replace View ADVENTUREWORKSDW.EDW.DIM_PRODUCT_CAT_SUBCAT_V 

  comment = 'Product details with cat and subcat english names. For fwd/rev engineering' 

AS
(
WITH cat_subcat as (
SELECT cat.* , sub."ProductSubcategoryKey" as "SubProductSubcategoryKey", sub."EnglishProductSubcategoryName"  FROM "DimProductCategory" cat
inner join  "DimProductSubcategory" sub
on  cat."ProductCategoryKey" = sub."ProductCategoryKey"
) 
  select 
 "ProductKey"           
, "ProductAlternateKey"  
, "ProductSubcategoryKey"
, "WeightUnitMeasureCode"
, "SizeUnitMeasureCode"  
, "EnglishProductName"   
, "StandardCost"         
, "FinishedGoodsFlag"    
, "Color"                
, "SafetyStockLevel"     
, "ReorderPoint"         
, "ListPrice"            
, "Size"                 
 ,"SizeRange"            
 ,"Weight"               
 ,"DaysToManufacture"    
 ,"ProductLine"          
 ,"DealerPrice"          
 ,"Class"                
 ,"Style"                
 ,"ModelName"            
 ,"EnglishDescription"   
 ,"Status"                   
,"ProductCategoryKey"         
,"ProductCategoryAlternateKey"
,"EnglishProductCategoryName" 
,"EnglishProductSubcategoryName"
 from "DimProduct" prod
  left join cat_subcat 
  on prod."ProductSubcategoryKey" = cat_subcat."SubProductSubcategoryKey"
);

CREATE OR REPLACE FILE FORMAT ADVENTUREWORKSDW.EDW.FILEFORMAT_431
	TYPE = JSON
	NULL_IF = ()
;
