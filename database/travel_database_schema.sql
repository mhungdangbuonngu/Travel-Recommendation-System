-- SET search_path TO GROUP_PROJECT;
DROP SCHEMA IF EXISTS travel_database CASCADE;
CREATE SCHEMA IF NOT EXISTS travel_database;
SET search_path TO travel_database;

-- Create a custom type for the Address structure
CREATE TYPE Address AS (
	details TEXT,
	street TEXT,
	district TEXT,
	city TEXT
);

-- Create the Hotel table
CREATE TABLE Hotel (
    HotelID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    Location Address,
    Latitude DECIMAL(9, 6),
    Longitude DECIMAL(9, 6),
    Rating DECIMAL(2, 1),
    Price_Range VARCHAR(50),
    Description TEXT,
    Img_URL VARCHAR(255),
    Comments JSON
);

-- Create an index on the district of the Location and Rating columns for the Hotel table
CREATE INDEX HOTEL_IDX_ADDRESS_RATING ON Hotel(((Location).district), Rating);

-- Create the TouristAttraction table
CREATE TABLE TouristAttraction (
    PlayID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    Location Address,
    Latitude DECIMAL(9, 6),
    Longitude DECIMAL(9, 6),
    Rating DECIMAL(2, 1),
    Price_Range VARCHAR(50),
    Tour_Duration VARCHAR(50),
    Description TEXT,
    Img_URL VARCHAR(255),
    Comments JSON
);

-- Create an index on the district of the Location and Rating columns for the TouristAttraction table
CREATE INDEX PLAY_IDX_ADDRESS_RATING ON TouristAttraction(((Location).district), Rating);

-- Create the Restaurant table
CREATE TABLE Restaurant (
    ResID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    Location Address,
    Latitude DECIMAL(9, 6),
    Longitude DECIMAL(9, 6),
    Rating DECIMAL(2, 1),
    Price_Range VARCHAR(50),
    Description TEXT,
    Img_URL VARCHAR(255),
    Comments JSON
);

-- Create an index on the district of the Location and Rating columns for the Restaurant table
CREATE INDEX RES_IDX_ADDRESS_RATING ON Restaurant(((Location).district), Rating);