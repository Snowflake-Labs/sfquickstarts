USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.FoodTruck (

    TruckID int IDENTITY(1,1) NOT NULL, 
    TruckGUID uniqueidentifier NOT NULL CONSTRAINT [DF__FoodTruck__Truck__3D5E1FD2] DEFAULT (newid()), 
    TruckName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    LicensePlate varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    CityID int NOT NULL, 
    TruckConfig nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    YearPurchased int NULL, 
    MaxCapacity int NOT NULL CONSTRAINT [DF__FoodTruck__MaxCa__3E52440B] DEFAULT ((500)), 
    IsOperational bit NOT NULL CONSTRAINT [DF__FoodTruck__IsOpe__3F466844] DEFAULT ((1)), 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__FoodTruck__Creat__403A8C7D] DEFAULT (getdate()), 
    ModifiedAt datetime NULL
)