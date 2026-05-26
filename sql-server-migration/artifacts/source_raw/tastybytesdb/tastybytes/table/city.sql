USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.City (

    CityID int IDENTITY(1,1) NOT NULL, 
    CityName nvarchar(150) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    CountryID int NOT NULL, 
    StateProvince nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    Latitude decimal(9, 6) NULL, 
    Longitude decimal(9, 6) NULL, 
    PopulationSize int NULL, 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__City__CreatedAt__3B75D760] DEFAULT (getdate())
)