USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.Inventory (

    InventoryID int IDENTITY(1,1) NOT NULL, 
    TruckID int NOT NULL, 
    IngredientName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    QuantityOnHand decimal(10, 2) NOT NULL CONSTRAINT [DF__Inventory__Quant__59FA5E80] DEFAULT ((0.00)), 
    UnitOfMeasure varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    ReorderLevel decimal(10, 2) NOT NULL CONSTRAINT [DF__Inventory__Reord__5AEE82B9] DEFAULT ((10.00)), 
    ExpirationDate date NULL, 
    SupplierNotes nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    LastRestocked datetime NULL
)