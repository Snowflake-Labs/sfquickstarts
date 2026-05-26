USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.Country (

    CountryID int IDENTITY(1,1) NOT NULL, 
    CountryName nvarchar(100) COLLATE Albanian_BIN NOT NULL, 
    CountryCode char(3) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    CurrencyCode char(3) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    TaxRate decimal(5, 2) NOT NULL CONSTRAINT [DF__Country__TaxRate__37A5467C] DEFAULT ((0.00)), 
    DisplayName nvarchar(9) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    IsActive bit NOT NULL CONSTRAINT [DF__Country__IsActiv__38996AB5] DEFAULT ((1)), 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__Country__Created__398D8EEE] DEFAULT (getdate()), 
    ModifiedAt datetime NULL
)