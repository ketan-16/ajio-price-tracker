import os
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for
from db import Database
from price_tracker import show

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
    """Render the home page."""
    return render_template("index.html")

@app.route("/view_product_details")
def view_product():
    """Render the product details page with price tracking chart."""
    chart_json = show()  # Fetch price tracking chart data
    return render_template("view_product_details.html", chart_json=chart_json)

@app.route("/my_product")
def my_product():
    """Render the My Products page."""
    return render_template("my_product.html")

@app.route("/addproduct", methods=["GET", "POST"])
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
                else:
                    flash(f"Invalid product URL: {url}", "warning")

            flash("Products added successfully!", "success")

        except requests.exceptions.ConnectionError:
            flash("Connection error. Please check your internet connection.", "error")
            return redirect(url_for("add_product"))
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "error")
            return redirect(url_for("add_product"))

        # 🚀 Redirect to the view_product_details page after successful submission
        return redirect(url_for("view_product"))

    return render_template("add_product.html")

if __name__ == "__main__":
    app.run(debug=True)
