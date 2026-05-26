USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.Customer (

    CustomerID int IDENTITY(1,1) NOT NULL, 
    CustomerGUID uniqueidentifier NOT NULL CONSTRAINT [DF__Customer__Custom__4BAC3F29] DEFAULT (newid()), 
    FirstName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    LastName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    Email varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    PhoneNumber varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    PreferredCityID int NULL, 
    LoyaltyPoints int NOT NULL CONSTRAINT [DF__Customer__Loyalt__4CA06362] DEFAULT ((0)), 
    MemberSince date NOT NULL CONSTRAINT [DF__Customer__Member__4D94879B] DEFAULT (getdate()), 
    IsActive bit NOT NULL CONSTRAINT [DF__Customer__IsActi__4E88ABD4] DEFAULT ((1)), 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__Customer__Create__4F7CD00D] DEFAULT (getdate()), 
    ModifiedAt datetime NULL
)