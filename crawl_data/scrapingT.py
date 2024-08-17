import requests
from bs4 import BeautifulSoup as bp
import csv
import psycopg2

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
REQUEST_HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-language': 'en-US, en;q=0.5',
}

def get_page_html(url):
    res = requests.get(url=url, headers=REQUEST_HEADER)
    return res.text

def get_hotel_name(soup):
    name = soup.find('div', class_='css-901oao r-a5wbuh r-1enofrn r-b88u0q r-1cwl3u0 r-fdjqy7 r-3s2u2q')
    return name.text.strip() if name else None

def extract_hotels_url(url, i):
    info = {}
    print(f"Scraping URL number: {i}")
    html = get_page_html(url=url)
    soup = bp(html, 'lxml')
    info['name'] = get_hotel_name(soup)
    return info

if __name__ == "__main__":
    conn = psycopg2.connect(
        database="test", 
        user="postgres", 
        host='localhost',
        password="cong2006",
        port=5432
    )
    cur = conn.cursor()
    
    with open('hotels.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        
        for i, row in enumerate(reader):
            url = row[0]
            data = extract_hotels_url(url, i)
            sql_query = """INSERT INTO Hotel (Name) VALUES (%s)"""
            cur.execute(sql_query, (data['name'],))  # Note the comma after data['name']
            conn.commit()
            print(f'Data for {i} inserted into DB')

    cur.close()
    conn.close()
