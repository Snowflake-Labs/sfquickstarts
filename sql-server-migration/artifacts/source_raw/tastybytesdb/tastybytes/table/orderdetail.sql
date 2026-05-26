USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.OrderDetail (

    OrderID int NOT NULL, 
    LineNumber int NOT NULL, 
    MenuItemID int NOT NULL, 
    Quantity int NOT NULL CONSTRAINT [DF__OrderDeta__Quant__571DF1D5] DEFAULT ((1)), 
    UnitPrice smallmoney NOT NULL, 
    Discount smallmoney NOT NULL CONSTRAINT [DF__OrderDeta__Disco__5812160E] DEFAULT ((0.00)), 
    LineTotal decimal(10, 2) NULL, 
    SpecialRequests nvarchar(300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL
)