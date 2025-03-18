import requests
import os
from dotenv import load_dotenv
from db import Database
import plotly.graph_objects as go
import plotly.utils
import json

# Load environment variables
load_dotenv()
MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()

# Headers for requests
headers = {
    "Host": "www.ajio.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "TE": "trailers"
}

def read_product_urls():
    """Retrieve all unique product codes from the database."""
    return list(set([x['product_code'] for x in list(db.products.find())]))

def show():
    """Fetch product details and generate a price comparison chart."""
    product_code_list = read_product_urls()
    data_for_plot = []

    try:
        for product_code in product_code_list:
            API_URL = f"https://www.ajio.com/api/p/{product_code}"
            res = requests.get(API_URL, headers=headers)
            product_details = res.json()

            product_name = product_details['baseOptions'][0]['options'][0]['modelImage']['altText']
            current_price = product_details['baseOptions'][0]['options'][0]['priceData']['value']

            # Safe extraction of maxSavingPrice to avoid KeyError
            best_promos = [
                {x['code']: x.get('maxSavingPrice', 0)}  # Default to 0 if missing
                for x in product_details.get('potentialPromotions', [])
            ][:3]

            # Sum up best discount values
            best_discount = sum(x.get(list(x.keys())[0], 0) for x in best_promos)

            # Append data for visualization
            data_for_plot.append((product_name, current_price, best_discount))

    except Exception as e:
        print(f"Error: {e}")  # Debugging output
        return None

    if data_for_plot:
        product_names, current_prices, best_discounts = zip(*data_for_plot)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
    x=product_names,
    y=current_prices,
    mode='lines+markers',  # Line with markers
    name='Price',
    line=dict(color='lightblue', width=4),  # Line color and width
    marker=dict(size=9, color='blue')  # Marker size and color
))
        
        fig.update_layout(
            title='Product Prices and Discount Amounts',
            xaxis_title='Products',
            yaxis_title='Value (₹)',
            barmode='group'
        )

        print("Generated Chart JSON:", json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))  # Debugging output
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return None
