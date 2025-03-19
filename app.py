import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for
from db import Database
import plotly.graph_objects as go
import plotly.io as pio

# Load environment variables
load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()


def fetch_product_data(product_code):
    """Fetch product details using Ajio API."""
    API_URL = f"https://www.ajio.com/api/p/{product_code}"
    headers = {
        "Host": "www.ajio.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        res.raise_for_status()
        product_details = res.json()

        
        current_price = product_details["baseOptions"][0]["options"][0]["priceData"]["value"]
        return float(current_price)
    except Exception as e:
        print(f"Error fetching product data: {e}")
        return 0.0


def generate_chart(price_history):
    """Generate a Plotly chart for price history."""
    dates = []
    prices = []

    for entry in price_history:
        try:
            
            date_obj = (
                entry["created_at"]
                if isinstance(entry["created_at"], datetime)
                else datetime.strptime(entry["created_at"], "%Y-%m-%d %H:%M:%S")
            )
            dates.append(date_obj.strftime("%Y-%m-%d %H:%M:%S"))  # Date and time
            prices.append(float(entry["current_price"]))
        except Exception as e:
            print(f"Error processing entry {entry}: {e}")
            continue

    if not dates or not prices:
        return None

   
    fig = go.Figure(
        data=go.Scatter(x=dates, y=prices, mode="lines+markers", name="Price")
    )

    fig.update_layout(
        title="Price History",
        xaxis_title="Date & Time",
        yaxis_title="Price (INR)",
        xaxis=dict(type="date", tickformat="%Y-%m-%d %H:%M"),
        template="plotly_dark",
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
    )

   
    return pio.to_json(fig)


@app.route("/")
def home():
    """Render the home page."""
    return render_template("index.html")

@app.route("/my-product")
def my_product():
    return render_template("my_product.html")


@app.route("/product-details", methods=["GET", "POST"])
def view_product():
    """Render the product details page with price tracking chart."""
    chart_json = None

    if request.method == "POST":
        product_code = request.form.get("product_code")
        if product_code:
            price_history = list(db.price_history.find({"product_code": product_code}))

            if not price_history:
                flash("No price history found for the selected product.", "info")
            else:
               
                chart_json = generate_chart(price_history)
                flash(f"Data fetched for product {product_code}", "success")

    
    product_list = list(set([x["product_code"] for x in db.products.find()]))
    return render_template(
        "product_details.html", product_list=product_list, chart_json=chart_json
    )


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    """Handle adding new product URLs to track."""
    if request.method == "POST":
        try:
            data = request.form.get("url", "").strip()
            if not data:
                flash("Please enter at least one product URL.", "error")
                return redirect(url_for("add_product"))

            product_urls = [url.strip() for url in data.split(",")]

            added_products = []
            for url in product_urls:
                match = re.search(r"/p/([^?]+)", url)
                if match:
                    product_code = match.group(1)

                    
                    current_price = fetch_product_data(product_code)

                    
                    db.products.update_one(
                        {"product_code": product_code},
                        {"$setOnInsert": {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}},
                        upsert=True,
                    )

                    
                    today_date = datetime.now().strftime("%Y-%m-%d")
                    existing_price = db.price_history.find_one(
                        {"product_code": product_code, "created_at": {"$regex": f"^{today_date}"}}
                    )

                    if not existing_price:
                        db.price_history.insert_one(
                            {
                                "product_code": product_code,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "current_price": current_price,
                            }
                        )
                        added_products.append(product_code)

                else:
                    flash(f"Invalid product URL: {url}", "error")

            if added_products:
                flash(
                    f"Products added successfully: {', '.join(added_products)}",
                    "success",
                )
            else:
                flash("No new products were added.", "info")

        except requests.exceptions.ConnectionError:
            flash("Connection error. Please check your internet connection.", "error")
            return redirect(url_for("add_product"))
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "error")
            return redirect(url_for("add_product"))

    return render_template("add_product.html")


if __name__ == "__main__":
    app.run(debug=True)
