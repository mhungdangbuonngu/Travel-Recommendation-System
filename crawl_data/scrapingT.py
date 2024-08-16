import requests
from bs4 import BeautifulSoup as bp
import csv
from datetime import datetime

USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
REQUEST_HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-language': 'en-US, en;q=0.5',
}
def get_page_html(url):
    res= requests.get(url=url,headers= REQUEST_HEADER)
    return res.content


def get_hotel_price(soup):
    price_element=soup.find('div', class_ = 'css-901oao r-a5wbuh r-b88u0q r-135wba7 r-1ff274t')
    if price_element:
        true_price = price_element.text.strip().replace('VND', '').replace('.', '')
        try:
            return float(true_price)
        except ValueError:
            print('value obtained for price cannot find')
            exit()
    return None
def get_hotel_name(soup):
    name=soup.find('h1',class_='css-4rbku5 css-901oao css-cens5h r-cwxd7f r-a5wbuh r-1x35g6 r-b88u0q r-fdjqy7')
    return name.text.strip() if name else None


def get_hotel_rating(soup):
    rating=soup.find('div',class_ = 'css-901oao r-a5wbuh r-1x35g6 r-b88u0q r-fdjqy7')
    return rating.text.strip() if rating else None


def get_hotel_des(soup):
    des=soup.find('div',attrs={'style':'font-family:Godwit, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol;font-size:14px;line-height:20px;max-height:80px;overflow:hidden'})
    return des.text.strip() if des else None

def get_hotel_location(soup):
    location=soup.find('div',class_='css-901oao css-cens5h r-cwxd7f r-13awgt0 r-a5wbuh r-1b43r93 r-majxgm r-rjixqe r-fdjqy7')
    return location.text.strip() if location else None

def extract_hotels_url(url):
    info={}
    print(f"scraping URL number: {1}")
    html = get_page_html(url=url)
    soup=bp(html,'lxml')
    info['name'] = get_hotel_name(soup)
    info['price']=get_hotel_price(soup)
    info['rating']=get_hotel_rating(soup)
    info['location'] = get_hotel_location(soup)
    info['description']=get_hotel_des(soup)
    return info

if __name__ =="__main__":
    data=[]
    with open('hotels.csv',newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            url=row[0]
            data.append(extract_hotels_url(url))
    
    
    
            