import json
import sqlite3

def search_products_by_keyword(keyword, json_path="bakalmarket_products.json", db_path="smartcart.db"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keyword = keyword.strip().lower()

    # Συνδέσου στη βάση SmartCart
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    results = []
    for item in data:
        if keyword in item["name"].lower():
            name = item["name"]
            bakal_price = item["price"]

            # Κανονικοποίηση ονομάτων για καλύτερη αντιστοίχιση
            def normalize(s):
                return s.lower().strip().replace("ά", "α").replace("έ", "ε").replace("ή", "η").replace("ί", "ι").replace("ό", "ο").replace("ύ", "υ").replace("ώ", "ω").replace("ς", "σ")

            norm_name = normalize(name)
            # Fetch all product names and prices from the database
            cursor.execute("SELECT name, price FROM products")
            db_products = cursor.fetchall()
            smartcart_price = None
            for db_name, db_price in db_products:
                if normalize(db_name) == norm_name:
                    smartcart_price = db_price
                    break

            if smartcart_price is not None:
                if smartcart_price < bakal_price:
                    cheaper_store = "SmartCart"
                elif bakal_price < smartcart_price:
                    cheaper_store = "Bakalmarket"
                else:
                    cheaper_store = "Same price"
            else:
                cheaper_store = "Only in Bakalmarket"

            results.append({
                "name": name,
                "bakal_price": bakal_price,
                "smartcart_price": smartcart_price,
                "cheaper_store": cheaper_store,
                "image_url": item["image_url"],
                "description": item["description"]
            })

    conn.close()

    if not results:
        raise ValueError(f"Κανένα προϊόν δεν περιέχει την λέξη '{keyword}'")

    return results
