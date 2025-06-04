from app.db import create_connection

def get_purchase_statistics():
    conn = create_connection()
    cursor = conn.cursor()

    # Πόσες φορές έχει αγοραστεί κάθε προϊόν
    cursor.execute("""
        SELECT p.name, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.name
        ORDER BY total_quantity DESC
        LIMIT 10
    """)
    most_common_products = cursor.fetchall()

    # Συνολικές αγορές ανά κατηγορία
    cursor.execute("""
        SELECT p.category, COUNT(*) as count
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.category
        ORDER BY count DESC
    """)
    most_common_categories = cursor.fetchall()

    conn.close()

    return {
        "most_frequent_products": [{"product": row[0], "times_purchased": row[1]} for row in most_common_products],
        "most_frequent_categories": [{"category": row[0], "total_items": row[1]} for row in most_common_categories]
    }

def generate_suggested_cart(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, COUNT(*) as frequency
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON p.id = oi.product_id
        WHERE o.user_id = ?
        GROUP BY p.name
        ORDER BY frequency DESC
        LIMIT 5
    """, (user_id,))

    suggested_products = cursor.fetchall()
    conn.close()

    return {
        "user_id": user_id,
        "suggested_cart": [row[0] for row in suggested_products]
    }

def get_frequently_bought_together(product_name):
    conn = create_connection()
    cursor = conn.cursor()

    # Βρίσκουμε το id του προϊόντος
    cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
    row = cursor.fetchone()
    if not row:
        return {"error": f"Το προϊόν '{product_name}' δεν βρέθηκε στη βάση."}
    product_id = row[0]

    # Βρίσκουμε παραγγελίες που περιέχουν το προϊόν
    cursor.execute("""
        SELECT order_id
        FROM order_items
        WHERE product_id = ?
    """, (product_id,))
    order_ids = [r[0] for r in cursor.fetchall()]

    if not order_ids:
        return {"message": "Δεν υπάρχουν παραγγελίες με αυτό το προϊόν."}

    # Βρίσκουμε προϊόντα που αγοράστηκαν μαζί
    placeholders = ",".join(["?"] * len(order_ids))
    cursor.execute(f"""
        SELECT p.name, COUNT(*) as freq
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id IN ({placeholders}) AND oi.product_id != ?
        GROUP BY p.name
        ORDER BY freq DESC
        LIMIT 5
    """, (*order_ids, product_id))

    result = cursor.fetchall()
    conn.close()

    return {
        "product": product_name,
        "frequently_bought_together": [{"product": r[0], "times": r[1]} for r in result]
    }
