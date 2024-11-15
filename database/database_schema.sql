
-- Enable PostGIS and vector extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Drop the existing schema if it exists
DROP SCHEMA IF EXISTS travel_database CASCADE;
CREATE SCHEMA IF NOT EXISTS travel_database;
SET search_path TO travel_database, public;

-- Create a custom type for the Address structure
CREATE TYPE Address AS (
    street TEXT,
    district TEXT,
    city TEXT
);

CREATE TYPE OpeningHours AS (
    open_time TIME WITH TIME ZONE,
    close_time TIME WITH TIME ZONE
);

-- Create the Hotel table with an embedding vector column
CREATE TABLE Hotel (
    hotel_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    address Address,
    location GEOMETRY(POINT),
    amenities TEXT[ ],
    style TEXT,
    rating DECIMAL(2, 1),
    description TEXT,
    embedding_description vector(768),
    img_url JSON,
    comments JSON
);

-- Create an index on the district of the Address and Rating columns for the Hotel table
-- CREATE INDEX idx_hotel_address_rating ON Hotel(((address).district), rating);

-- Create the Price table for the Hotel table
CREATE TABLE HotelPrice (
    hprice_id SERIAL PRIMARY KEY,
    hotel_id INT REFERENCES Hotel(hotel_id) ON DELETE CASCADE,
    room_type VARCHAR(255),
    capacity INT,
    price INT NOT NULL
);

-- Create an index on the hotel_id for the HotelPrice table
-- CREATE INDEX hotel_idx_address_district ON Hotel(((address).district));
-- CREATE INDEX hotel_idx_rating ON Hotel(rating);
-- CREATE INDEX hotel_idx_location ON Hotel USING GIST(location);


-- Create the TouristAttraction table with an embedding vector column
CREATE TABLE TouristAttraction (
    attraction_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    address Address,
    location GEOMETRY(POINT),
    attraction_type VARCHAR(255),
    working_hour OpeningHours,
    rating DECIMAL(2, 1),
    tour_duration INTERVAL,
    description TEXT,
    embedding_description vector(768),
    img_url JSON,
    comments JSON
);

-- Create an index on the district of the Address and Rating columns for the TouristAttraction table
-- CREATE INDEX attraction_idx_address_district ON TouristAttraction(((address).district));
-- CREATE INDEX attraction_idx_rating ON TouristAttraction(rating);
-- CREATE INDEX attraction_idx_location ON TouristAttraction USING GIST(location);


-- Create the Price table for the TouristAttraction table
CREATE TABLE AttractionPrice (
    aprice_id SERIAL PRIMARY KEY,
    attraction_id INT REFERENCES TouristAttraction(attraction_id) ON DELETE CASCADE,
    ticket_type VARCHAR(255),
    number_people INT,
    price INT NOT NULL
);

-- Create an index on the attraction_id for the AttractionPrice table
-- CREATE INDEX idx_attractionprice_attractionid ON AttractionPrice(attraction_id);

-- Create the Restaurant table with an embedding vector column
CREATE TABLE Restaurant (
    res_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    address Address,
    location GEOMETRY(POINT),
    working_hour OpeningHours,
    suitable_for TEXT[],
    restaurant_type TEXT[],
    rating DECIMAL(2, 1),
    description TEXT,
    embedding_description vector(768),
    price_range JSON,
    parking_available BOOLEAN NOT NULL,
    kids_play_area BOOLEAN NOT NULL,
    img_url JSON,
    comments JSON
);

-- Create an index on the district of the Address and Rating columns for the Restaurant table
-- CREATE INDEX res_idx_address_district ON Restaurant(((address).district));
-- CREATE INDEX res_idx_rating ON Restaurant(rating);
-- CREATE INDEX res_idx_location ON Restaurant USING GIST(location);
