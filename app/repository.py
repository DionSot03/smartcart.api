# app/repository.py
from app.db import create_connection
from app.models import Product, Cart, CartItem
from datetime import datetime


def get_all_products(search=None):
    conn = create_connection()
    cursor = conn.cursor()

    if search:
        try:
            price = float(search)
            cursor.execute("""
                SELECT id, name, category, description, image_url, price
                FROM products
                WHERE price = ?
            """, (price,))
        except ValueError:
            cursor.execute("""
                SELECT id, name, category, description, image_url, price
                FROM products
                WHERE LOWER(name) LIKE ?
            """, (f"%{search.lower()}%",))
    else:
        cursor.execute("""
            SELECT id, name, category, description, image_url, price
            FROM products
        """)

    rows = cursor.fetchall()
    conn.close()

    return [Product.from_tuple(row) for row in rows]


def insert_products(products_data):
    conn = create_connection()
    cursor = conn.cursor()
    results = []

    for item in products_data:
        cursor.execute("""
            SELECT id FROM products WHERE name = ? AND category = ?
        """, (item['name'], item['category']))
        exists = cursor.fetchone()

        if exists:
            results.append({'name': item['name'], 'status': 'Υπάρχει ήδη'})
            continue

        cursor.execute("""
            INSERT INTO products (name, category, description, image_url, price)
            VALUES (?, ?, ?, ?, ?)
        """, (item['name'], item['category'], item.get('description', ''),
              item.get('image_url', ''), item['price']))

        results.append({'name': item['name'], 'status': 'Προστέθηκε επιτυχώς'})

    conn.commit()
    conn.close()
    return results


def delete_product_by_id(product_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def delete_all_products():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()


def create_cart():
    conn = create_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO carts (created_at, completed)
        VALUES (?, 0)
    """, (created_at,))

    cart_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return cart_id


def delete_cart(cart_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
    cursor.execute("DELETE FROM carts WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()


def add_to_cart(cart_id, product_id, quantity):
    conn = create_connection()
    cursor = conn.cursor()

    # Έλεγχος αν υπάρχει καλάθι και αν είναι ολοκληρωμένο
    cursor.execute("SELECT completed FROM carts WHERE id = ?", (cart_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False  # Δεν υπάρχει καλάθι
    if result[0] == 1:
        conn.close()
        return False  # Το καλάθι είναι ολοκληρωμένο

    # Αν όλα καλά, προχωρά στην προσθήκη προϊόντος
    cursor.execute("""
        INSERT INTO cart_items (cart_id, product_id, quantity)
        VALUES (?, ?, ?)
    """, (cart_id, product_id, quantity))

    conn.commit()
    conn.close()
    return True



def view_cart(cart_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.name, p.category, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.cart_id = ?
    """, (cart_id,))

    rows = cursor.fetchall()
    conn.close()

    cart_items = []
    for row in rows:
        cart_items.append({
            'product_id': row[0],
            'name': row[1],
            'category': row[2],
            'price': row[3],
            'quantity': row[4],
            'subtotal': round(row[3] * row[4], 2)
        })

    return cart_items


def remove_from_cart(cart_id, product_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?
    """, (cart_id, product_id))

    conn.commit()
    conn.close()


def checkout_cart(cart_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Έλεγχος αν υπάρχει καλάθι και δεν έχει ήδη ολοκληρωθεί
    cursor.execute("SELECT completed FROM carts WHERE id = ?", (cart_id,))
    result = cursor.fetchone()
    if not result:
        return False, "Το καλάθι δεν βρέθηκε"
    if result[0] == 1:
        return False, "Το καλάθι έχει ήδη ολοκληρωθεί"

    # Δημιουργία παραγγελίας
    cursor.execute("INSERT INTO orders DEFAULT VALUES")
    order_id = cursor.lastrowid

    # Μεταφορά προϊόντων στην παραγγελία
    cursor.execute("SELECT product_id, quantity FROM cart_items WHERE cart_id = ?", (cart_id,))
    items = cursor.fetchall()
    for product_id, quantity in items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (order_id, product_id, quantity))

    # Ολοκλήρωση καλαθιού
    cursor.execute("UPDATE carts SET completed = 1 WHERE id = ?", (cart_id,))

    conn.commit()
    conn.close()

    return True, f"Η παραγγελία ολοκληρώθηκε (Order ID: {order_id})"

