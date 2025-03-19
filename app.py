import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for
from db import Database

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Database setup
MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/my-product")
def my_product():
    return render_template("my_product.html")

@app.route("/product-det")
def product_det():
    return render_template("product_details.html")

@app.route("/add_prod")
def add_prod():
    return render_template("add_product.html")

@app.route("/product-details", methods=["GET", "POST"])
def view_product():
    """Render the product details page with price tracking chart."""
    if request.method == "POST":
        product_code = request.form.get("product_code")
        print("needs implementation")
        price_history = db.price_history.find({"product_code": product_code})
        print(list(price_history))
        # Take the above data, and create a chart from that
        # chart_json = show()  # Fetch price tracking chart data
    chart_json = None

    product_list = list(set([x['product_code'] for x in list(db.products.find({}))]))
    print(product_list)
    return render_template("product_details.html", product_list=product_list, chart_json=chart_json)



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
            
            for url in product_urls:
                match = re.search(r"/p/([^?]+)", url)
                if match:
                    product_code = match.group(1)
                    db.products.insert_one({"product_code": product_code, "created_at": datetime.now()})
                    flash("Products added successfully!", "success")
                else:
                    flash(f"Invalid product URL: {url}", "error")

            

        except requests.exceptions.ConnectionError:
            flash("Connection error. Please check your internet connection.", "error")
            return redirect(url_for("add_product"))
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "error")
            return redirect(url_for("add_product"))

    return redirect(url_for("add_prod"))

if __name__ == "__main__":
    app.run(debug=True)
