USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.Menu (

    MenuID int IDENTITY(1,1) NOT NULL, 
    MenuName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    TruckID int NOT NULL, 
    CuisineType nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    MenuDescription ntext COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    BasePriceTier money NOT NULL CONSTRAINT [DF__Menu__BasePriceT__4222D4EF] DEFAULT ((0.00)), 
    IsSeasonalMenu bit NOT NULL CONSTRAINT [DF__Menu__IsSeasonal__4316F928] DEFAULT ((0)), 
    EffectiveFrom date NOT NULL CONSTRAINT [DF__Menu__EffectiveF__440B1D61] DEFAULT (getdate()), 
    EffectiveTo date NULL, 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__Menu__CreatedAt__44FF419A] DEFAULT (getdate())
)