-- SET search_path TO GROUP_PROJECT;
DROP SCHEMA IF EXISTS travel_database CASCADE;
CREATE SCHEMA IF NOT EXISTS travel_database;
SET search_path TO travel_database;

-- Create a custom type for the Address structure
CREATE TYPE Address AS (
	street TEXT,
	district TEXT,
	city TEXT
);

CREATE TYPE Location AS (
    Latitude DECIMAL(9, 6),
    Longitude DECIMAL(9, 6)
);

-- Create the Hotel table
CREATE TABLE Hotel (
    HotelID SERIAL NOT NULL PRIMARY KEY,
    Name VARCHAR(255),
    Address Address,
    Location Location,
    Rating DECIMAL(2, 1),
    Description TEXT,
    Img_URL JSON,
    Comments JSON
-- price_range JSONB
);

-- Create an index on the district of the Location and Rating columns for the Hotel table
CREATE INDEX HOTEL_IDX_ADDRESS_RATING ON Hotel(((Address).district), Rating);

-- Create the Price table for the Hotel table
CREATE TABLE HotelPrice (
	HPriceID SERIAL NOT NULL PRIMARY KEY,
	HotelID SERIAL NOT NULL,
	RoomType VARCHAR(255),
	Capacity INT,
	Price INT NOT NULL,
	CONSTRAINT hotel_price_foreign
    	FOREIGN KEY (HotelID)
    		REFERENCES travel_database.Hotel (HotelID)
    		ON DELETE CASCADE
   			ON UPDATE NO ACTION
	
);

-- Create an index on the hotelID for the HotelPrice table
CREATE INDEX IDX_HOTELPRICE_HOTELID ON HotelPrice(HotelID);

-- WITH PriceRanges AS (
-- 	SELECT
--     	HotelID,
--     	MIN(Price) AS min_price,
--     	MAX(Price) AS max_price
-- 	FROM HotelPrice
-- 	WHERE Price IS NOT NULL
-- 	GROUP BY HotelID
-- )
-- UPDATE Hotel h
-- 	SET price_range = jsonb_build_object('min', pr.min_price, 'max', pr.max_price)
-- 	FROM PriceRanges pr
-- 	WHERE h.hotelid = pr.hotelid;

-- Create the TouristAttraction table
CREATE TABLE TouristAttraction (
    AttractionID SERIAL NOT NULL PRIMARY KEY,
    Name VARCHAR(255),
    Address Address,
    Location Location,
    AttractionType VARCHAR(255),
    Rating DECIMAL(2, 1),
    Tour_Duration VARCHAR(50),
    Description TEXT,
    Img_URL JSON,
    Comments JSON
);

-- Create an index on the district of the Location and Rating columns for the TouristAttraction table
CREATE INDEX ATTRACTION_IDX_ADDRESS_RATING ON TouristAttraction(((Address).district), Rating);

-- Create the Price table for the TouristAttraction table
CREATE TABLE AttractionPrice (
	APriceID SERIAL NOT NULL PRIMARY KEY,
	AttractionID SERIAL NOT NULL,
	TicketType VARCHAR(255),
	NumberPeople INT,
	Price INT NOT NULL,
	CONSTRAINT attraction_price_foreign
    	FOREIGN KEY (AttractionID)
    		REFERENCES travel_database.TouristAttraction (AttractionID)
    		ON DELETE CASCADE
   			ON UPDATE NO ACTION
	
);

-- Create an index on the AttractionID for the AttractionPrice table
CREATE INDEX IDX_ATTRACTIONPRICE_ATTRACTIONID ON AttractionPrice(AttractionID);

-- Create the Restaurant table
CREATE TABLE Restaurant (
    ResID SERIAL NOT NULL PRIMARY KEY,
    Name VARCHAR(255),
    Address Address,
    Location Location,
    Rating DECIMAL(2, 1),
    -- Price_Range VARCHAR(50),
    Description TEXT,
    Img_URL JSON,
    Comments JSON
);

-- Create an index on the district of the Location and Rating columns for the Restaurant table
CREATE INDEX RES_IDX_ADDRESS_RATING ON Restaurant(((Address).district), Rating);
