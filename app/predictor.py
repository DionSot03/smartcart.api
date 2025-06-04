# app/predictor.py
import pandas as pd
from sklearn.linear_model import LogisticRegression
from app.db import create_connection

def get_logistic_prediction(product_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Παίρνουμε όλα τα order_id και product_id
    cursor.execute("SELECT order_id, product_id FROM order_items")
    rows = cursor.fetchall()
    conn.close()

    # Δημιουργία DataFrame
    df = pd.DataFrame(rows, columns=['order_id', 'product_id'])

    # Hot-encoding: πίνακας με κάθε παραγγελία και αν είχε το κάθε προϊόν
    basket = pd.get_dummies(df['product_id']).groupby(df['order_id']).sum()

    # Έλεγχος αν υπάρχει το προϊόν στον πίνακα
    if product_id not in basket.columns:
        return {"error": "Δεν υπάρχουν αρκετά δεδομένα για το προϊόν."}

    y = basket[product_id]
    X = basket.drop(columns=[product_id])

    if y.sum() < 2:
        return {"error": "Δεν υπάρχουν αρκετά δεδομένα για παλινδρόμηση."}

    # Εκπαίδευση λογιστικής παλινδρόμησης
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    # Επιλογή των 3 πιο σχετιζόμενων προϊόντων
    result = pd.Series(model.coef_[0], index=X.columns).sort_values(ascending=False).head(3)

    # Μετατροπή προτεινόμενων ids σε ονόματα
    conn = create_connection()
    cursor = conn.cursor()
    names = {}
    for pid in result.index.tolist():
        cursor.execute("SELECT name FROM products WHERE id = ?", (pid,))
        res = cursor.fetchone()
        if res:
            names[res[0]] = round(result[pid], 2)
    conn.close()

    # Όνομα προϊόντος εισόδου
    cursor = create_connection().cursor()
    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    input_name = cursor.fetchone()
    input_name = input_name[0] if input_name else f"ID {product_id}"

    return {
        "input_product": input_name,
        "suggested_products": names
    }
