import re
import os
from dotenv import load_dotenv
from datetime import datetime

import requests
from db import Database
from flask import Flask, render_template, request, flash, redirect, url_for


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")



MONGO_SRV = os.getenv("MONGO_SRV")
mongo = Database(MONGO_SRV)
db = mongo.get_db()

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            data = request.form['url']
            product_urls = [url.strip() for url in data.split(',')]
            print(f"URL(s) loaded: {product_urls}")
            
            for url in product_urls:
                product_code_regex = r"/p/([^?]+)"  
                product_code = re.findall(product_code_regex, url)[0]
                db.products.insert_one({"product_code": product_code, "created_at": datetime.now()})
                print(f"Product Code: {product_code}")
                flash("Data Submitted Successfully", 'success')
                
        except requests.exceptions.ConnectionError:
            print("Connection error. Please check your internet connection.")
            flash("Connection error. Please check your internet connection.", 'error')
            return redirect(url_for('home'))
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            flash("An unexpected error occurred. Please try again.", 'error')
            return redirect(url_for('home'))
    
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)