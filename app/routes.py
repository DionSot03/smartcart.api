from flask import request, jsonify
from app import app
from app.db import create_connection
import pandas as pd
from app.recipes import get_recipe_for 
from app.analytics import get_purchase_statistics
from app.analytics import generate_suggested_cart
from app.analytics import get_frequently_bought_together
from app.bought_together import get_suggested_products
from app.predictor import get_logistic_prediction
from bs4 import BeautifulSoup

from app.repository import (
    get_all_products, insert_products, delete_product_by_id, delete_all_products,
    create_cart, delete_cart, add_to_cart, view_cart,
    remove_from_cart, checkout_cart
)
from app.models import Product

@app.route('/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '').strip()
    products = get_all_products(search)
    return jsonify([p.to_dict() for p in products])

@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    if isinstance(data, dict):
        data = [data]
    results = insert_products(data)
    return jsonify({'results': results}), 201

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    success = delete_product_by_id(id)
    if success:
        return jsonify({'message': f'Product {id} deleted'})
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/products', methods=['DELETE'])
def delete_all_products():
    delete_all_products()
    return jsonify({'message': 'All products deleted successfully'}), 200

@app.route('/carts', methods=['POST'])
def create_new_cart():
    cart_id = create_cart()

    if cart_id is None:
        return jsonify({
            'error': 'Υπάρχει ήδη ενεργό καλάθι. Ολοκληρώστε πρώτα την τρέχουσα αγορά.'
        }), 400

    return jsonify({
        'message': 'Καλάθι δημιουργήθηκε επιτυχώς.',
        'cart_id': cart_id
    }), 201


@app.route('/carts/<int:cart_id>', methods=['DELETE'])
def delete_existing_cart(cart_id):
    delete_cart(cart_id)
    return jsonify({'message': f'Cart {cart_id} deleted successfully.'}), 200

@app.route('/carts/<int:cart_id>/items', methods=['POST'])
def add_item_to_cart(cart_id):
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    if not product_id or not quantity:
        return jsonify({'error': 'Missing product_id or quantity'}), 400
    success = add_to_cart(cart_id, product_id, quantity)
    if not success:
        return jsonify({'error': f'Cart {cart_id} not found'}), 404
    return jsonify({'message': f'Added product {product_id} to cart {cart_id}'}), 201

@app.route('/carts/<int:cart_id>', methods=['GET'])
def get_cart(cart_id):
    items = view_cart(cart_id)
    return jsonify({
        'cart_id': cart_id,
        'items': items,
        'total': round(sum(item['subtotal'] for item in items), 2)
    })

@app.route('/carts/<int:cart_id>/items/<int:cart_item_id>', methods=['DELETE'])
def remove_item_from_cart(cart_id, cart_item_id):
    remove_from_cart(cart_id, cart_item_id)
    return jsonify({'message': f'Product {cart_item_id} removed from cart {cart_id}'}), 200

@app.route('/carts/<int:cart_id>/checkout', methods=['POST'])
def checkout(cart_id):
    success, message = checkout_cart(cart_id)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400



@app.route('/scrape/compare', methods=['GET'])
def compare_price():
    product_name = request.args.get("product")
    if not product_name:
        return jsonify({"error": "Λείπει το όνομα προϊόντος (parameter: ?product=...)"}), 400

    #  1. Ανάκτηση από βάση
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description, image_url FROM products WHERE name LIKE ?", (f"%{product_name}%",))
    db_product = cursor.fetchone()
    conn.close()

    if not db_product:
        return jsonify({"error": "Το προϊόν δεν βρέθηκε στη βάση"}), 404

    db_name, db_price, db_desc, db_img = db_product

    #  2. Scraping από StaticShop1
    with open("StaticShop1.html", "r", encoding="utf-8") as f1:
        soup1 = BeautifulSoup(f1, "html.parser")

    found1 = None
    for div in soup1.find_all("div", class_="product"):
        name = div.find("h2", class_="name").text.strip()
        if product_name.lower() in name.lower():
            try:
                price = float(div.find("span", class_="price").text.strip())
                description = div.find("p", class_="description").text.strip()
                image_url = div.find("img", class_="image")["src"]
                found1 = {
                    "Κατάστημα": "StaticShop1",
                    "Τιμή": price,
                    "Περιγραφή": description,
                    "Εικόνα": image_url
                }
            except:
                pass
            break

    #  3. Scraping από StaticShop2
    with open("StaticShop2.html", "r", encoding="utf-8") as f2:
        soup2 = BeautifulSoup(f2, "html.parser")

    found2 = None
    for div in soup2.find_all("div", class_="product"):
        name = div.find("h2", class_="name").text.strip()
        if product_name.lower() in name.lower():
            try:
                price = float(div.find("span", class_="price").text.strip())
                description = div.find("p", class_="description").text.strip()
                image_url = div.find("img", class_="image")["src"]
                found2 = {
                    "Κατάστημα": "StaticShop2",
                    "Τιμή": price,
                    "Περιγραφή": description,
                    "Εικόνα": image_url
                }
            except:
                pass
            break

    #  4. Σύγκριση
    all_prices = [{
        "Κατάστημα": "UnipiShop",
        "Τιμή": db_price,
        "Περιγραφή": db_desc,
        "Εικόνα": db_img
    }]

    if found1:
        all_prices.append(found1)
    if found2:
        all_prices.append(found2)

    if all_prices:
        cheapest = min(all_prices, key=lambda x: x["Τιμή"])["Κατάστημα"]
    else:
        cheapest = "Καμία τιμή δεν βρέθηκε"

    return jsonify({
        "Προϊόν": db_name,
        "Τιμή στο UnipiShop": db_price,
        "Στατικά Καταστήματα": all_prices[1:],  # αγνοεί UnipiShop
        "Φθηνότερο στο": cheapest
    })



@app.route("/ai/recipe/<product_name>")
def recipe(product_name):
    result = get_recipe_for(product_name)
    if result:
        return jsonify(result)
    return jsonify({"error": "Δεν υπάρχει συνταγή για αυτό το προϊόν"}), 404

@app.route('/analytics/stats', methods=['GET'])
def analytics_stats():
    stats = get_purchase_statistics()
    return jsonify(stats)



@app.route("/analytics/suggest/<int:product_id>", methods=["GET"])
def suggest(product_id):
    result = get_suggested_products(product_id)
    if result["όνομα προϊόντος"] is None:
        return jsonify({"error": "Το προϊόν δεν βρέθηκε."}), 404
    return jsonify(result)



@app.route("/analytics/predict/<int:product_id>", methods=["GET"])
def predict_next(product_id):
    result = get_logistic_prediction(product_id)
    return jsonify(result)
