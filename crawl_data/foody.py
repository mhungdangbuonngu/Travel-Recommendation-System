import requests
from bs4 import BeautifulSoup as bp
import psycopg2
import csv
import time

# Thông tin user-agent để giả lập trình duyệt
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
REQUEST_HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-language': 'en-US, en;q=0.5',
}

def get_page_html(url):
    res = requests.get(url=url, headers=REQUEST_HEADER)
    return res.text

def get_restaurant_name(soup):
    name = soup.find('div', class_='resname')  # Class của tên nhà hàng
    return name.text.strip() if name else None

def get_restaurant_address(soup):
    address = soup.find('div', class_='address')  # Class của địa chỉ
    return address.text.strip() if address else None

def get_restaurant_location(soup):
    location=soup.find('div',class_='location')
    return location.text.strip().replace('\t','') if location else None

def get_restaurant_rating(soup):
    rating = soup.find('div', class_='rating-point')  
    return rating.text.strip() if rating else None

def get_restaurant_description(soup):
    description = soup.find('div', class_='description') 
    return description.text.strip() if description else None

def get_restaurant_comments(soup):
    comments = []
    comment_elements = soup.findAll('div', class_='comment') 
    for comment in comment_elements:
        comments.append(comment.text.strip())
    return comments

def extract_restaurant_info(url, i):
    info = {}
    print(f"Scraping URL number: {i}")
    html = get_page_html(url=url)
    soup = bp(html, 'lxml')
    info['id'] = i
    info['name'] = get_restaurant_name(soup)
    info['address'] = get_restaurant_address(soup)
    info['location'] = get_restaurant_location(soup)
    info['rating'] = get_restaurant_rating(soup)
    info['description'] = get_restaurant_description(soup)
    info['comments'] = get_restaurant_comments(soup)
    return info

if __name__ == "__main__":
    # Kết nối với cơ sở dữ liệu
    conn = psycopg2.connect(database="test",
                            user="postgres",
                            host='localhost',
                            password="cong2006",
                            port=5432)
    cur = conn.cursor()

    with open('restaurants.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for i, row in enumerate(reader):
            url = row[0]
            data = extract_restaurant_info(url, i)
            sql_query = """
            INSERT INTO restaurant (RestaurantID, Name, Address, Location, Rating, Description, Comments)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql_query, (
                data['id'],
                data['name'],
                data['address'],
                data['location'],
                data['rating'],
                data['description'],
                ','.join(data['comments'])  
            ))
            conn.commit()
            print(f'Data for {i} inserted into DB')

    cur.close()
    conn.close()
