IF SCHEMA_ID('obf') IS NULL EXEC('CREATE SCHEMA obf');
GO
CREATE OR ALTER VIEW obf.[T51] AS
  SELECT
    [SystemInformationID] AS col_0001,
    [Database Version] AS col_0002,
    [VersionDate] AS col_0003,
    [ModifiedDate] AS col_0004
  FROM [dbo].[AWBuildVersion];
GO
CREATE OR ALTER VIEW obf.[T40] AS
  SELECT
    [DatabaseLogID] AS col_0005,
    [PostTime] AS col_0006,
    [DatabaseUser] AS col_0007,
    [Event] AS col_0008,
    [Schema] AS col_0009,
    [Object] AS col_0010,
    [TSQL] AS col_0011,
    [XmlEvent] AS col_0012
  FROM [dbo].[DatabaseLog];
GO
CREATE OR ALTER VIEW obf.[T43] AS
  SELECT
    [ErrorLogID] AS col_0013,
    [ErrorTime] AS col_0014,
    [UserName] AS col_0015,
    [ErrorNumber] AS col_0016,
    [ErrorSeverity] AS col_0017,
    [ErrorState] AS col_0018,
    [ErrorProcedure] AS col_0019,
    [ErrorLine] AS col_0020,
    [ErrorMessage] AS col_0021
  FROM [dbo].[ErrorLog];
GO
CREATE OR ALTER VIEW obf.[T08] AS
  SELECT
    [DepartmentID] AS col_0022,
    [Name] AS col_0023,
    [GroupName] AS col_0024,
    [ModifiedDate] AS col_0025
  FROM [HumanResources].[Department];
GO
CREATE OR ALTER VIEW obf.[T12] AS
  SELECT
    [BusinessEntityID] AS col_0026,
    [NationalIDNumber] AS col_0027,
    [LoginID] AS col_0028,
    [OrganizationNode] AS col_0029,
    [OrganizationLevel] AS col_0030,
    [JobTitle] AS col_0031,
    [BirthDate] AS col_0032,
    [MaritalStatus] AS col_0033,
    [Gender] AS col_0034,
    [HireDate] AS col_0035,
    [SalariedFlag] AS col_0036,
    [VacationHours] AS col_0037,
    [SickLeaveHours] AS col_0038,
    [CurrentFlag] AS col_0039,
    [rowguid] AS col_0040,
    [ModifiedDate] AS col_0041
  FROM [HumanResources].[Employee];
GO
CREATE OR ALTER VIEW obf.[T14] AS
  SELECT
    [BusinessEntityID] AS col_0042,
    [DepartmentID] AS col_0043,
    [ShiftID] AS col_0044,
    [StartDate] AS col_0045,
    [EndDate] AS col_0046,
    [ModifiedDate] AS col_0047
  FROM [HumanResources].[EmployeeDepartmentHistory];
GO
CREATE OR ALTER VIEW obf.[T15] AS
  SELECT
    [BusinessEntityID] AS col_0048,
    [RateChangeDate] AS col_0049,
    [Rate] AS col_0050,
    [PayFrequency] AS col_0051,
    [ModifiedDate] AS col_0052
  FROM [HumanResources].[EmployeePayHistory];
GO
CREATE OR ALTER VIEW obf.[T19] AS
  SELECT
    [JobCandidateID] AS col_0053,
    [BusinessEntityID] AS col_0054,
    [Resume] AS col_0055,
    [ModifiedDate] AS col_0056
  FROM [HumanResources].[JobCandidate];
GO
CREATE OR ALTER VIEW obf.[T33] AS
  SELECT
    [ShiftID] AS col_0057,
    [Name] AS col_0058,
    [StartTime] AS col_0059,
    [EndTime] AS col_0060,
    [ModifiedDate] AS col_0061
  FROM [HumanResources].[Shift];
GO
CREATE OR ALTER VIEW obf.[T45] AS
  SELECT
    [AddressID] AS col_0062,
    [AddressLine1] AS col_0063,
    [AddressLine2] AS col_0064,
    [City] AS col_0065,
    [StateProvinceID] AS col_0066,
    [PostalCode] AS col_0067,
    [SpatialLocation] AS col_0068,
    [rowguid] AS col_0069,
    [ModifiedDate] AS col_0070
  FROM [Person].[Address];
GO
CREATE OR ALTER VIEW obf.[T48] AS
  SELECT
    [AddressTypeID] AS col_0071,
    [Name] AS col_0072,
    [rowguid] AS col_0073,
    [ModifiedDate] AS col_0074
  FROM [Person].[AddressType];
GO
CREATE OR ALTER VIEW obf.[T59] AS
  SELECT
    [BusinessEntityID] AS col_0075,
    [rowguid] AS col_0076,
    [ModifiedDate] AS col_0077
  FROM [Person].[BusinessEntity];
GO
CREATE OR ALTER VIEW obf.[T62] AS
  SELECT
    [BusinessEntityID] AS col_0078,
    [AddressID] AS col_0079,
    [AddressTypeID] AS col_0080,
    [rowguid] AS col_0081,
    [ModifiedDate] AS col_0082
  FROM [Person].[BusinessEntityAddress];
GO
CREATE OR ALTER VIEW obf.[T64] AS
  SELECT
    [BusinessEntityID] AS col_0083,
    [PersonID] AS col_0084,
    [ContactTypeID] AS col_0085,
    [rowguid] AS col_0086,
    [ModifiedDate] AS col_0087
  FROM [Person].[BusinessEntityContact];
GO
CREATE OR ALTER VIEW obf.[T67] AS
  SELECT
    [ContactTypeID] AS col_0088,
    [Name] AS col_0089,
    [ModifiedDate] AS col_0090
  FROM [Person].[ContactType];
GO
CREATE OR ALTER VIEW obf.[T69] AS
  SELECT
    [CountryRegionCode] AS col_0091,
    [Name] AS col_0092,
    [ModifiedDate] AS col_0093
  FROM [Person].[CountryRegion];
GO
CREATE OR ALTER VIEW obf.[T11] AS
  SELECT
    [BusinessEntityID] AS col_0094,
    [EmailAddressID] AS col_0095,
    [EmailAddress] AS col_0096,
    [rowguid] AS col_0097,
    [ModifiedDate] AS col_0098
  FROM [Person].[EmailAddress];
GO
CREATE OR ALTER VIEW obf.[T21] AS
  SELECT
    [BusinessEntityID] AS col_0099,
    [PasswordHash] AS col_0100,
    [PasswordSalt] AS col_0101,
    [rowguid] AS col_0102,
    [ModifiedDate] AS col_0103
  FROM [Person].[Password];
GO
CREATE OR ALTER VIEW obf.[T23] AS
  SELECT
    [BusinessEntityID] AS col_0104,
    [PersonType] AS col_0105,
    [NameStyle] AS col_0106,
    [Title] AS col_0107,
    [FirstName] AS col_0108,
    [MiddleName] AS col_0109,
    [LastName] AS col_0110,
    [Suffix] AS col_0111,
    [EmailPromotion] AS col_0112,
    [AdditionalContactInfo] AS col_0113,
    [Demographics] AS col_0114,
    [rowguid] AS col_0115,
    [ModifiedDate] AS col_0116
  FROM [Person].[Person];
GO
CREATE OR ALTER VIEW obf.[T27] AS
  SELECT
    [BusinessEntityID] AS col_0117,
    [PhoneNumber] AS col_0118,
    [PhoneNumberTypeID] AS col_0119,
    [ModifiedDate] AS col_0120
  FROM [Person].[PersonPhone];
GO
CREATE OR ALTER VIEW obf.[T29] AS
  SELECT
    [PhoneNumberTypeID] AS col_0121,
    [Name] AS col_0122,
    [ModifiedDate] AS col_0123
  FROM [Person].[PhoneNumberType];
GO
CREATE OR ALTER VIEW obf.[T49] AS
  SELECT
    [StateProvinceID] AS col_0124,
    [StateProvinceCode] AS col_0125,
    [CountryRegionCode] AS col_0126,
    [IsOnlyStateProvinceFlag] AS col_0127,
    [Name] AS col_0128,
    [TerritoryID] AS col_0129,
    [rowguid] AS col_0130,
    [ModifiedDate] AS col_0131
  FROM [Person].[StateProvince];
GO
CREATE OR ALTER VIEW obf.[T53] AS
  SELECT
    [BillOfMaterialsID] AS col_0132,
    [ProductAssemblyID] AS col_0133,
    [ComponentID] AS col_0134,
    [StartDate] AS col_0135,
    [EndDate] AS col_0136,
    [UnitMeasureCode] AS col_0137,
    [BOMLevel] AS col_0138,
    [PerAssemblyQty] AS col_0139,
    [ModifiedDate] AS col_0140
  FROM [Production].[BillOfMaterials];
GO
CREATE OR ALTER VIEW obf.[T02] AS
  SELECT
    [CultureID] AS col_0141,
    [Name] AS col_0142,
    [ModifiedDate] AS col_0143
  FROM [Production].[Culture];
GO
CREATE OR ALTER VIEW obf.[T09] AS
  SELECT
    [DocumentNode] AS col_0144,
    [DocumentLevel] AS col_0145,
    [Title] AS col_0146,
    [Owner] AS col_0147,
    [FolderFlag] AS col_0148,
    [FileName] AS col_0149,
    [FileExtension] AS col_0150,
    [Revision] AS col_0151,
    [ChangeNumber] AS col_0152,
    [Status] AS col_0153,
    [DocumentSummary] AS col_0154,
    [Document] AS col_0155,
    [rowguid] AS col_0156,
    [ModifiedDate] AS col_0157
  FROM [Production].[Document];
GO
CREATE OR ALTER VIEW obf.[T18] AS
  SELECT
    [IllustrationID] AS col_0158,
    [Diagram] AS col_0159,
    [ModifiedDate] AS col_0160
  FROM [Production].[Illustration];
GO
CREATE OR ALTER VIEW obf.[T20] AS
  SELECT
    [LocationID] AS col_0161,
    [Name] AS col_0162,
    [CostRate] AS col_0163,
    [Availability] AS col_0164,
    [ModifiedDate] AS col_0165
  FROM [Production].[Location];
GO
CREATE OR ALTER VIEW obf.[T30] AS
  SELECT
    [ProductID] AS col_0166,
    [Name] AS col_0167,
    [ProductNumber] AS col_0168,
    [MakeFlag] AS col_0169,
    [FinishedGoodsFlag] AS col_0170,
    [Color] AS col_0171,
    [SafetyStockLevel] AS col_0172,
    [ReorderPoint] AS col_0173,
    [StandardCost] AS col_0174,
    [ListPrice] AS col_0175,
    [Size] AS col_0176,
    [SizeUnitMeasureCode] AS col_0177,
    [WeightUnitMeasureCode] AS col_0178,
    [Weight] AS col_0179,
    [DaysToManufacture] AS col_0180,
    [ProductLine] AS col_0181,
    [Class] AS col_0182,
    [Style] AS col_0183,
    [ProductSubcategoryID] AS col_0184,
    [ProductModelID] AS col_0185,
    [SellStartDate] AS col_0186,
    [SellEndDate] AS col_0187,
    [DiscontinuedDate] AS col_0188,
    [rowguid] AS col_0189,
    [ModifiedDate] AS col_0190
  FROM [Production].[Product];
GO
CREATE OR ALTER VIEW obf.[T34] AS
  SELECT
    [ProductCategoryID] AS col_0191,
    [Name] AS col_0192,
    [rowguid] AS col_0193,
    [ModifiedDate] AS col_0194
  FROM [Production].[ProductCategory];
GO
CREATE OR ALTER VIEW obf.[T36] AS
  SELECT
    [ProductID] AS col_0195,
    [StartDate] AS col_0196,
    [EndDate] AS col_0197,
    [StandardCost] AS col_0198,
    [ModifiedDate] AS col_0199
  FROM [Production].[ProductCostHistory];
GO
CREATE OR ALTER VIEW obf.[T37] AS
  SELECT
    [ProductDescriptionID] AS col_0200,
    [Description] AS col_0201,
    [rowguid] AS col_0202,
    [ModifiedDate] AS col_0203
  FROM [Production].[ProductDescription];
GO
CREATE OR ALTER VIEW obf.[T39] AS
  SELECT
    [ProductID] AS col_0204,
    [DocumentNode] AS col_0205,
    [ModifiedDate] AS col_0206
  FROM [Production].[ProductDocument];
GO
CREATE OR ALTER VIEW obf.[T41] AS
  SELECT
    [ProductID] AS col_0207,
    [LocationID] AS col_0208,
    [Shelf] AS col_0209,
    [Bin] AS col_0210,
    [Quantity] AS col_0211,
    [rowguid] AS col_0212,
    [ModifiedDate] AS col_0213
  FROM [Production].[ProductInventory];
GO
CREATE OR ALTER VIEW obf.[T44] AS
  SELECT
    [ProductID] AS col_0214,
    [StartDate] AS col_0215,
    [EndDate] AS col_0216,
    [ListPrice] AS col_0217,
    [ModifiedDate] AS col_0218
  FROM [Production].[ProductListPriceHistory];
GO
CREATE OR ALTER VIEW obf.[T47] AS
  SELECT
    [ProductModelID] AS col_0219,
    [Name] AS col_0220,
    [CatalogDescription] AS col_0221,
    [Instructions] AS col_0222,
    [rowguid] AS col_0223,
    [ModifiedDate] AS col_0224
  FROM [Production].[ProductModel];
GO
CREATE OR ALTER VIEW obf.[T50] AS
  SELECT
    [ProductModelID] AS col_0225,
    [IllustrationID] AS col_0226,
    [ModifiedDate] AS col_0227
  FROM [Production].[ProductModelIllustration];
GO
CREATE OR ALTER VIEW obf.[T52] AS
  SELECT
    [ProductModelID] AS col_0228,
    [ProductDescriptionID] AS col_0229,
    [CultureID] AS col_0230,
    [ModifiedDate] AS col_0231
  FROM [Production].[ProductModelProductDescriptionCulture];
GO
CREATE OR ALTER VIEW obf.[T55] AS
  SELECT
    [ProductPhotoID] AS col_0232,
    [ThumbNailPhoto] AS col_0233,
    [ThumbnailPhotoFileName] AS col_0234,
    [LargePhoto] AS col_0235,
    [LargePhotoFileName] AS col_0236,
    [ModifiedDate] AS col_0237
  FROM [Production].[ProductPhoto];
GO
CREATE OR ALTER VIEW obf.[T56] AS
  SELECT
    [ProductID] AS col_0238,
    [ProductPhotoID] AS col_0239,
    [Primary] AS col_0240,
    [ModifiedDate] AS col_0241
  FROM [Production].[ProductProductPhoto];
GO
CREATE OR ALTER VIEW obf.[T58] AS
  SELECT
    [ProductReviewID] AS col_0242,
    [ProductID] AS col_0243,
    [ReviewerName] AS col_0244,
    [ReviewDate] AS col_0245,
    [EmailAddress] AS col_0246,
    [Rating] AS col_0247,
    [Comments] AS col_0248,
    [ModifiedDate] AS col_0249
  FROM [Production].[ProductReview];
GO
CREATE OR ALTER VIEW obf.[T61] AS
  SELECT
    [ProductSubcategoryID] AS col_0250,
    [ProductCategoryID] AS col_0251,
    [Name] AS col_0252,
    [rowguid] AS col_0253,
    [ModifiedDate] AS col_0254
  FROM [Production].[ProductSubcategory];
GO
CREATE OR ALTER VIEW obf.[T32] AS
  SELECT
    [ScrapReasonID] AS col_0255,
    [Name] AS col_0256,
    [ModifiedDate] AS col_0257
  FROM [Production].[ScrapReason];
GO
CREATE OR ALTER VIEW obf.[T57] AS
  SELECT
    [TransactionID] AS col_0258,
    [ProductID] AS col_0259,
    [ReferenceOrderID] AS col_0260,
    [ReferenceOrderLineID] AS col_0261,
    [TransactionDate] AS col_0262,
    [TransactionType] AS col_0263,
    [Quantity] AS col_0264,
    [ActualCost] AS col_0265,
    [ModifiedDate] AS col_0266
  FROM [Production].[TransactionHistory];
GO
CREATE OR ALTER VIEW obf.[T60] AS
  SELECT
    [TransactionID] AS col_0267,
    [ProductID] AS col_0268,
    [ReferenceOrderID] AS col_0269,
    [ReferenceOrderLineID] AS col_0270,
    [TransactionDate] AS col_0271,
    [TransactionType] AS col_0272,
    [Quantity] AS col_0273,
    [ActualCost] AS col_0274,
    [ModifiedDate] AS col_0275
  FROM [Production].[TransactionHistoryArchive];
GO
CREATE OR ALTER VIEW obf.[T65] AS
  SELECT
    [UnitMeasureCode] AS col_0276,
    [Name] AS col_0277,
    [ModifiedDate] AS col_0278
  FROM [Production].[UnitMeasure];
GO
CREATE OR ALTER VIEW obf.[T70] AS
  SELECT
    [WorkOrderID] AS col_0279,
    [ProductID] AS col_0280,
    [OrderQty] AS col_0281,
    [StockedQty] AS col_0282,
    [ScrappedQty] AS col_0283,
    [StartDate] AS col_0284,
    [EndDate] AS col_0285,
    [DueDate] AS col_0286,
    [ScrapReasonID] AS col_0287,
    [ModifiedDate] AS col_0288
  FROM [Production].[WorkOrder];
GO
CREATE OR ALTER VIEW obf.[T03] AS
  SELECT
    [WorkOrderID] AS col_0289,
    [ProductID] AS col_0290,
    [OperationSequence] AS col_0291,
    [LocationID] AS col_0292,
    [ScheduledStartDate] AS col_0293,
    [ScheduledEndDate] AS col_0294,
    [ActualStartDate] AS col_0295,
    [ActualEndDate] AS col_0296,
    [ActualResourceHrs] AS col_0297,
    [PlannedCost] AS col_0298,
    [ActualCost] AS col_0299,
    [ModifiedDate] AS col_0300
  FROM [Production].[WorkOrderRouting];
GO
CREATE OR ALTER VIEW obf.[T63] AS
  SELECT
    [ProductID] AS col_0301,
    [BusinessEntityID] AS col_0302,
    [AverageLeadTime] AS col_0303,
    [StandardPrice] AS col_0304,
    [LastReceiptCost] AS col_0305,
    [LastReceiptDate] AS col_0306,
    [MinOrderQty] AS col_0307,
    [MaxOrderQty] AS col_0308,
    [OnOrderQty] AS col_0309,
    [UnitMeasureCode] AS col_0310,
    [ModifiedDate] AS col_0311
  FROM [Purchasing].[ProductVendor];
GO
CREATE OR ALTER VIEW obf.[T71] AS
  SELECT
    [PurchaseOrderID] AS col_0312,
    [PurchaseOrderDetailID] AS col_0313,
    [DueDate] AS col_0314,
    [OrderQty] AS col_0315,
    [ProductID] AS col_0316,
    [UnitPrice] AS col_0317,
    [LineTotal] AS col_0318,
    [ReceivedQty] AS col_0319,
    [RejectedQty] AS col_0320,
    [StockedQty] AS col_0321,
    [ModifiedDate] AS col_0322
  FROM [Purchasing].[PurchaseOrderDetail];
GO
CREATE OR ALTER VIEW obf.[T05] AS
  SELECT
    [PurchaseOrderID] AS col_0323,
    [RevisionNumber] AS col_0324,
    [Status] AS col_0325,
    [EmployeeID] AS col_0326,
    [VendorID] AS col_0327,
    [ShipMethodID] AS col_0328,
    [OrderDate] AS col_0329,
    [ShipDate] AS col_0330,
    [SubTotal] AS col_0331,
    [TaxAmt] AS col_0332,
    [Freight] AS col_0333,
    [TotalDue] AS col_0334,
    [ModifiedDate] AS col_0335
  FROM [Purchasing].[PurchaseOrderHeader];
GO
CREATE OR ALTER VIEW obf.[T35] AS
  SELECT
    [ShipMethodID] AS col_0336,
    [Name] AS col_0337,
    [ShipBase] AS col_0338,
    [ShipRate] AS col_0339,
    [rowguid] AS col_0340,
    [ModifiedDate] AS col_0341
  FROM [Purchasing].[ShipMethod];
GO
CREATE OR ALTER VIEW obf.[T66] AS
  SELECT
    [BusinessEntityID] AS col_0342,
    [AccountNumber] AS col_0343,
    [Name] AS col_0344,
    [CreditRating] AS col_0345,
    [PreferredVendorStatus] AS col_0346,
    [ActiveFlag] AS col_0347,
    [PurchasingWebServiceURL] AS col_0348,
    [ModifiedDate] AS col_0349
  FROM [Purchasing].[Vendor];
GO
CREATE OR ALTER VIEW obf.[T68] AS
  SELECT
    [CountryRegionCode] AS col_0350,
    [CurrencyCode] AS col_0351,
    [ModifiedDate] AS col_0352
  FROM [Sales].[CountryRegionCurrency];
GO
CREATE OR ALTER VIEW obf.[T01] AS
  SELECT
    [CreditCardID] AS col_0353,
    [CardType] AS col_0354,
    [CardNumber] AS col_0355,
    [ExpMonth] AS col_0356,
    [ExpYear] AS col_0357,
    [ModifiedDate] AS col_0358
  FROM [Sales].[CreditCard];
GO
CREATE OR ALTER VIEW obf.[T04] AS
  SELECT
    [CurrencyCode] AS col_0359,
    [Name] AS col_0360,
    [ModifiedDate] AS col_0361
  FROM [Sales].[Currency];
GO
CREATE OR ALTER VIEW obf.[T06] AS
  SELECT
    [CurrencyRateID] AS col_0362,
    [CurrencyRateDate] AS col_0363,
    [FromCurrencyCode] AS col_0364,
    [ToCurrencyCode] AS col_0365,
    [AverageRate] AS col_0366,
    [EndOfDayRate] AS col_0367,
    [ModifiedDate] AS col_0368
  FROM [Sales].[CurrencyRate];
GO
CREATE OR ALTER VIEW obf.[T07] AS
  SELECT
    [CustomerID] AS col_0369,
    [PersonID] AS col_0370,
    [StoreID] AS col_0371,
    [TerritoryID] AS col_0372,
    [AccountNumber] AS col_0373,
    [rowguid] AS col_0374,
    [ModifiedDate] AS col_0375
  FROM [Sales].[Customer];
GO
CREATE OR ALTER VIEW obf.[T26] AS
  SELECT
    [BusinessEntityID] AS col_0376,
    [CreditCardID] AS col_0377,
    [ModifiedDate] AS col_0378
  FROM [Sales].[PersonCreditCard];
GO
CREATE OR ALTER VIEW obf.[T10] AS
  SELECT
    [SalesOrderID] AS col_0379,
    [SalesOrderDetailID] AS col_0380,
    [CarrierTrackingNumber] AS col_0381,
    [OrderQty] AS col_0382,
    [ProductID] AS col_0383,
    [SpecialOfferID] AS col_0384,
    [UnitPrice] AS col_0385,
    [UnitPriceDiscount] AS col_0386,
    [LineTotal] AS col_0387,
    [rowguid] AS col_0388,
    [ModifiedDate] AS col_0389
  FROM [Sales].[SalesOrderDetail];
GO
CREATE OR ALTER VIEW obf.[T13] AS
  SELECT
    [SalesOrderID] AS col_0390,
    [RevisionNumber] AS col_0391,
    [OrderDate] AS col_0392,
    [DueDate] AS col_0393,
    [ShipDate] AS col_0394,
    [Status] AS col_0395,
    [OnlineOrderFlag] AS col_0396,
    [SalesOrderNumber] AS col_0397,
    [PurchaseOrderNumber] AS col_0398,
    [AccountNumber] AS col_0399,
    [CustomerID] AS col_0400,
    [SalesPersonID] AS col_0401,
    [TerritoryID] AS col_0402,
    [BillToAddressID] AS col_0403,
    [ShipToAddressID] AS col_0404,
    [ShipMethodID] AS col_0405,
    [CreditCardID] AS col_0406,
    [CreditCardApprovalCode] AS col_0407,
    [CurrencyRateID] AS col_0408,
    [SubTotal] AS col_0409,
    [TaxAmt] AS col_0410,
    [Freight] AS col_0411,
    [TotalDue] AS col_0412,
    [Comment] AS col_0413,
    [rowguid] AS col_0414,
    [ModifiedDate] AS col_0415
  FROM [Sales].[SalesOrderHeader];
GO
CREATE OR ALTER VIEW obf.[T16] AS
  SELECT
    [SalesOrderID] AS col_0416,
    [SalesReasonID] AS col_0417,
    [ModifiedDate] AS col_0418
  FROM [Sales].[SalesOrderHeaderSalesReason];
GO
CREATE OR ALTER VIEW obf.[T17] AS
  SELECT
    [BusinessEntityID] AS col_0419,
    [TerritoryID] AS col_0420,
    [SalesQuota] AS col_0421,
    [Bonus] AS col_0422,
    [CommissionPct] AS col_0423,
    [SalesYTD] AS col_0424,
    [SalesLastYear] AS col_0425,
    [rowguid] AS col_0426,
    [ModifiedDate] AS col_0427
  FROM [Sales].[SalesPerson];
GO
CREATE OR ALTER VIEW obf.[T22] AS
  SELECT
    [BusinessEntityID] AS col_0428,
    [QuotaDate] AS col_0429,
    [SalesQuota] AS col_0430,
    [rowguid] AS col_0431,
    [ModifiedDate] AS col_0432
  FROM [Sales].[SalesPersonQuotaHistory];
GO
CREATE OR ALTER VIEW obf.[T24] AS
  SELECT
    [SalesReasonID] AS col_0433,
    [Name] AS col_0434,
    [ReasonType] AS col_0435,
    [ModifiedDate] AS col_0436
  FROM [Sales].[SalesReason];
GO
CREATE OR ALTER VIEW obf.[T25] AS
  SELECT
    [SalesTaxRateID] AS col_0437,
    [StateProvinceID] AS col_0438,
    [TaxType] AS col_0439,
    [TaxRate] AS col_0440,
    [Name] AS col_0441,
    [rowguid] AS col_0442,
    [ModifiedDate] AS col_0443
  FROM [Sales].[SalesTaxRate];
GO
CREATE OR ALTER VIEW obf.[T28] AS
  SELECT
    [TerritoryID] AS col_0444,
    [Name] AS col_0445,
    [CountryRegionCode] AS col_0446,
    [Group] AS col_0447,
    [SalesYTD] AS col_0448,
    [SalesLastYear] AS col_0449,
    [CostYTD] AS col_0450,
    [CostLastYear] AS col_0451,
    [rowguid] AS col_0452,
    [ModifiedDate] AS col_0453
  FROM [Sales].[SalesTerritory];
GO
CREATE OR ALTER VIEW obf.[T31] AS
  SELECT
    [BusinessEntityID] AS col_0454,
    [TerritoryID] AS col_0455,
    [StartDate] AS col_0456,
    [EndDate] AS col_0457,
    [rowguid] AS col_0458,
    [ModifiedDate] AS col_0459
  FROM [Sales].[SalesTerritoryHistory];
GO
CREATE OR ALTER VIEW obf.[T38] AS
  SELECT
    [ShoppingCartItemID] AS col_0460,
    [ShoppingCartID] AS col_0461,
    [Quantity] AS col_0462,
    [ProductID] AS col_0463,
    [DateCreated] AS col_0464,
    [ModifiedDate] AS col_0465
  FROM [Sales].[ShoppingCartItem];
GO
CREATE OR ALTER VIEW obf.[T42] AS
  SELECT
    [SpecialOfferID] AS col_0466,
    [Description] AS col_0467,
    [DiscountPct] AS col_0468,
    [Type] AS col_0469,
    [Category] AS col_0470,
    [StartDate] AS col_0471,
    [EndDate] AS col_0472,
    [MinQty] AS col_0473,
    [MaxQty] AS col_0474,
    [rowguid] AS col_0475,
    [ModifiedDate] AS col_0476
  FROM [Sales].[SpecialOffer];
GO
CREATE OR ALTER VIEW obf.[T46] AS
  SELECT
    [SpecialOfferID] AS col_0477,
    [ProductID] AS col_0478,
    [rowguid] AS col_0479,
    [ModifiedDate] AS col_0480
  FROM [Sales].[SpecialOfferProduct];
GO
CREATE OR ALTER VIEW obf.[T54] AS
  SELECT
    [BusinessEntityID] AS col_0481,
    [Name] AS col_0482,
    [SalesPersonID] AS col_0483,
    [Demographics] AS col_0484,
    [rowguid] AS col_0485,
    [ModifiedDate] AS col_0486
  FROM [Sales].[Store];
GO
