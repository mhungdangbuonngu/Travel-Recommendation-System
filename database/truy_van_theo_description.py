import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np

# Khởi tạo mô hình embedding
model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')

# Kết nối đến cơ sở dữ liệu
conn = psycopg2.connect(
    host="localhost",
    database="your_database",
    user="your_username",
    password="your_password",
    port=5432
)
cur = conn.cursor()

def search_hotels_and_restaurants(query_description, district_name):
    # Tạo embedding cho query_description
    query_embedding = model.encode(query_description).tolist()
    
    # Tìm 10 khách sạn trong quận với độ tương đồng cao nhất
    cur.execute("""
        SELECT 
            hotel_id,
            name,
            address,
            location,
            rating,
            description,
            description_embedding <#> %s AS similarity  -- Tính khoảng cách cosine
        FROM 
            Hotel
        WHERE 
            (address).district = %s
        ORDER BY 
            similarity ASC,  -- Sắp xếp theo độ tương đồng (càng nhỏ càng tốt)
            rating DESC
        LIMIT 10
    """, (query_embedding, district_name))
    
    hotels = cur.fetchall()
    
    results = []
    
    for hotel in hotels:
        hotel_id, hotel_name, hotel_address, hotel_location, hotel_rating, hotel_description, hotel_similarity = hotel
        
        # Tìm 5 nhà hàng gần nhất với khách sạn dựa trên khoảng cách địa lý và độ tương đồng mô tả
        cur.execute("""
            SELECT 
                res_id,
                name,
                address,
                location,
                rating,
                description,
                ST_Distance(hotel_location::geography, location::geography) AS distance,
                description_embedding <#> %s AS similarity
            FROM 
                Restaurant
            ORDER BY 
                hotel_location <-> location,  -- Sắp xếp theo khoảng cách địa lý
                similarity ASC  -- Sắp xếp theo độ tương đồng
            LIMIT 5
        """, (hotel_location, hotel_description_embedding))
        
        restaurants = cur.fetchall()
        
        results.append({
            'hotel': {
                'id': hotel_id,
                'name': hotel_name,
                'address': hotel_address,
                'location': hotel_location,
                'rating': hotel_rating,
                'description': hotel_description,
                'similarity': hotel_similarity
            },
            'restaurants': [
                {
                    'id': res[0],
                    'name': res[1],
                    'address': res[2],
                    'location': res[3],
                    'rating': res[4],
                    'description': res[5],
                    'distance': res[6],
                    'similarity': res[7]
                } for res in restaurants
            ]
        })
    
    return results

if __name__ == "__main__":
    query_description = "Khách sạn sang trọng với không gian thoáng đãng và dịch vụ chuyên nghiệp."
    district_name = "Quận 1"
    
    results = search_hotels_and_restaurants(query_description, district_name)
    
    for result in results:
        print("Hotel:", result['hotel']['name'], "- Similarity:", result['hotel']['similarity'])
        print("Nearby Restaurants:")
        for res in result['restaurants']:
            print(f" - {res['name']} (Distance: {res['distance']} meters, Similarity: {res['similarity']})")
        print("\n")
    
    cur.close()
    conn.close()

