import requests
import logging
import os
from dotenv import load_dotenv
from db import Database

load_dotenv()
MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()
    
logging.basicConfig(
        filename='tracker_logs.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

headers = {
        "Host": "www.ajio.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Alt-Used": "www.ajio.com",
        "Connection": "keep-alive",
        "Cookie": "bm_ss=ab8e18ef4e; bm_s=YAAQ3ZfmZ68AvFmVAQAA/Jf3fgOGq1NL288lfLqYF7VDSf7lHynGLwNHBx48G5UsxP/zAnqHuwkqj6I0cCsLT+WbG8PWLddM9785QeyaTdnvjtGK5ufgRUCfDLUV8g/HjUNP1zOquVMhoYjoeo1P892/EQRGerrbSny9j89YwETCo3lWrvotGt28r1YXHkXgzI/34oZYAlDqUGgvZwVgNOuszLIWSpMU4yAZ3Hvue90K5XXM9RH1zjrnnC3htWRegcJm5rRg1xKpM5fIez54E9PVXdgKhYIGuC0goPAi23VVvknTwAh9GX7xdtEfwOZYEMtP5ENMzZ5tJs4Bo/M1BoJxwiUu3Vmxy3fI9WkGK8xBHFW4oqn8bHbuQ0BujoLOjzC6+BfQ8x6EIxlGVZtjFhua3cCjtLH9k2tGl67COe3Vhoq8YCrFCa77MTZbISe/OufF+t9yNts=; V=201; TS01de1f4a=01ef61aed01f41cf51aca91fc80066339f8defe4b958785bbadd010cf69a795032aa4decfe213b2a91af76a8ab4307ff0d3d388de23bf02a917c9881e2e74acc3eb3d85dcb1da9379ac296eb49c0654abb833df2f970cbbf24aa59c90e31496ef8b11b9c86; TS01ac9890=01ef61aed0594ad3fe99a91e99cece069c1f5cb2ae58785bbadd010cf69a795032aa4decfee31980630ffff4d66e68c26d1183e871",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "TE": "trailers"
    }


def read_product_urls():
       return list(set([x['product_code'] for x in list(db.products.find())]))
        
product_code_list = read_product_urls()

try:
    for product_code in product_code_list:
        logging.info(f"Processing product {product_code}")
        API_URL = f"https://www.ajio.com/api/p/{product_code}"
        logging.info(f"Fetching data from {API_URL}")
            
        res = requests.get(API_URL, headers=headers)
        product_details = res.json()

        try:
            product_name = product_details['baseOptions'][0]['options'][0]['modelImage']['altText']
            stock_status = 'Available' if product_details['baseOptions'][0]['options'][0]['stock']['stockLevelStatus'] == 'inStock' else 'Out of Stock'
            stock_quantity = product_details['baseOptions'][0]['options'][0]['stock']['stockLevel']
            current_price = product_details['baseOptions'][0]['options'][0]['priceData']['value']
            best_promos = [{x['code']: x['maxSavingPrice']} for x in product_details.get('potentialPromotions', [])][:3]

            product_data = {
                "product_code": product_code,
                "name": product_name,
                "stock": stock_quantity,
                "availability":stock_status,
                "current_price": current_price,
                "best_promos": best_promos
            }
            logging.info("Writing information to database")
            db.price_history.insert_one(product_data)
            logging.info("Writing successful")
        except KeyError as e:
            logging.warning("Product has been removed, skipping")
except requests.exceptions.ConnectionError as e:
        print("No Internet Connection")
        logging.error(f"No Internet Connection: {e}")
except KeyError as e:
        logging.error(f"Key Error: {e}")
except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        

        

	