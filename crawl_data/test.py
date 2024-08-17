import psycopg2
conn = psycopg2.connect(database = "test", 
                        user = "postgres", 
                        host= 'localhost',
                        password = "cong2006",
                        port = 5432)

# Open a cursor to perform database operations
cur = conn.cursor()
# Execute a command: create datacamp_courses table
cur.execute("""
CREATE TABLE Hotel (
    HotelID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    Location TEXT,
    Latitude DECIMAL(9, 6),
    Longitude DECIMAL(9, 6),
    Rating DECIMAL(2, 1),
    Price_Range VARCHAR(50),
    Description TEXT,
    Img_URL JSON,
    Comments TEXT
);
""")
# Make the changes to the database persistent
conn.commit()
# Close cursor and communication with the database
cur.close()
conn.close()