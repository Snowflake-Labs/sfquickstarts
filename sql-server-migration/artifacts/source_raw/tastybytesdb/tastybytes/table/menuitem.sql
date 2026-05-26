USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.MenuItem (

    MenuItemID int IDENTITY(1,1) NOT NULL, 
    MenuID int NOT NULL, 
    ItemName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    ItemDescription nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    BasePrice money NOT NULL, 
    CalorieCount int NULL, 
    IsVegetarian bit NOT NULL CONSTRAINT [DF__MenuItem__IsVege__46E78A0C] DEFAULT ((0)), 
    IsGlutenFree bit NOT NULL CONSTRAINT [DF__MenuItem__IsGlut__47DBAE45] DEFAULT ((0)), 
    IsSpicy bit NOT NULL CONSTRAINT [DF__MenuItem__IsSpic__48CFD27E] DEFAULT ((0)), 
    PriceWithTax decimal(10, 2) NULL, 
    RowVer timestamp NOT NULL, 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__MenuItem__Create__49C3F6B7] DEFAULT (getdate())
)