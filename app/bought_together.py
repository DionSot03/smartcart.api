from app.db import create_connection

def get_suggested_products(product_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Βρες το όνομα του προϊόντος
    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    product_name = result[0] if result else None

    if not product_name:
        conn.close()
        return {"όνομα προϊόντος": None, "συνήθως αγοράζεται μαζί με": []}

    # Βρες όλα τα order_ids που περιλαμβάνουν αυτό το προϊόν
    cursor.execute("""
        SELECT order_id FROM order_items
        WHERE product_id = ?
    """, (product_id,))
    order_ids = [row[0] for row in cursor.fetchall()]

    if not order_ids:
        conn.close()
        return {"όνομα προϊόντος": product_name, "συνήθως αγοράζεται μαζί": []}

    # Βρες όλα τα άλλα προϊόντα που αγοράστηκαν σε αυτά τα order_ids
    format_ids = ",".join("?" * len(order_ids))
    cursor.execute(f"""
        SELECT oi.product_id, p.name, COUNT(*) as times
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id IN ({format_ids}) AND oi.product_id != ?
        GROUP BY oi.product_id, p.name
        ORDER BY times DESC
    """, (*order_ids, product_id))

    suggested = [
        {"id προϊόντος": row[0], "όνομα": row[1], "φορές που αγοράστηκαν μαζί": row[2]}
        for row in cursor.fetchall()
    ]

    conn.close()
    return {"όνομα προϊόντος": product_name, "συνήθως αγοράζονται μαζί": suggested}
