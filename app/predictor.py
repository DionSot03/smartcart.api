# app/predictor.py
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import webbrowser
import os
from app.db import create_connection

def get_linear_prediction(product_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Παίρνουμε όλα τα order_id και product_id
    cursor.execute("SELECT order_id, product_id FROM order_items")
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=["order_id", "product_id"])
    basket = pd.get_dummies(df["product_id"]).groupby(df["order_id"]).sum()

    if product_id not in basket.columns or basket[product_id].sum() < 2:
        return {"message": "Δεν υπάρχουν αρκετά δεδομένα για το προϊόν."}

    y = basket[product_id]
    X = basket.drop(columns=[product_id])

    model = LinearRegression()
    model.fit(X, y)
    scores = pd.Series(model.coef_, index=X.columns).sort_values(ascending=False).head(3)

    # Μετατροπή ids σε ονόματα
    conn = create_connection()
    cursor = conn.cursor()

    # Όνομα προϊόντος εισόδου
    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    input_row = cursor.fetchone()
    input_name = input_row[0] if input_row else f"ID {product_id}"

    results = []
    for pid in scores.index:
        cursor.execute("SELECT name FROM products WHERE id = ?", (pid,))
        name_row = cursor.fetchone()
        name = name_row[0] if name_row else f"ID {pid}"
        results.append({
            "product_id": pid,
            "name": name,
            "score": round(scores[pid], 3)
        })

    conn.close()

    # Οπτικοποίηση
    _plot_recommendations(input_name, results)

    return {
        "input_product_id": product_id,
        "input_product_name": input_name,
        "suggested_products": results
    }

def _plot_recommendations(input_name, results):
    names = [r["name"] for r in results]
    scores = [r["score"] for r in results]

    plt.figure(figsize=(8, 4))
    plt.barh(names, scores)
    plt.xlabel("Συντελεστής Συσχέτισης")
    plt.title(f"Προτεινόμενα για το προϊόν: {input_name}")
    plt.tight_layout()

    # Αποθήκευση και άνοιγμα σε browser
    img_path = "recommendation_plot.png"
    plt.savefig(img_path)
    plt.close()

    webbrowser.open('file://' + os.path.realpath(img_path))
