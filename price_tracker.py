import requests
import logging
import os
from dotenv import load_dotenv
from db import Database
from datetime import datetime


load_dotenv()
MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()


logging.basicConfig(
    filename="tracker_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


headers = {
    "Host": "www.ajio.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def read_product_urls():
    """Fetch product codes from the database."""
    return list(set([x["product_code"] for x in db.products.find()]))


product_code_list = read_product_urls()

try:
    for product_code in product_code_list:
        logging.info(f"Processing product {product_code}")
        API_URL = f"https://www.ajio.com/api/p/{product_code}"
        logging.info(f"Fetching data from {API_URL}")

        try:
            res = requests.get(API_URL, headers=headers, timeout=10)
            res.raise_for_status()

            product_details = res.json()
            try:
                # Extract product details
                product_name = product_details["baseOptions"][0]["options"][0]["modelImage"]["altText"]
                stock_status = (
                    "Available"
                    if product_details["baseOptions"][0]["options"][0]["stock"]["stockLevelStatus"].lower()
                    == "instock"
                    else "Out of Stock"
                )
                stock_quantity = product_details["baseOptions"][0]["options"][0]["stock"]["stockLevel"]
                current_price = product_details["baseOptions"][0]["options"][0]["priceData"]["value"]

                best_promos = [
                    {x["code"]: x["maxSavingPrice"]}
                    for x in product_details.get("potentialPromotions", [])
                ][:3]

                product_data = {
                    "product_code": product_code,
                    "name": product_name,
                    "stock": stock_quantity,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Date + Time
                    "availability": stock_status,
                    "current_price": current_price,
                    "best_promos": best_promos,
                }
                db.price_history.update_one(
                    {
                        "product_code": product_code,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Match date & time correctly
                    },
                    {"$set": product_data},
                    upsert=True,  
                )
            except KeyError as e:
                logging.warning(f"Product data incomplete or removed, skipping. Error: {e}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")

except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")
