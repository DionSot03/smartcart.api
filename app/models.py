# app/models.py

class Product:
    def __init__(self, id, name, category, description, image_url, price):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.image_url = image_url
        self.price = price

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
            "price": self.price
        }

    @staticmethod
    def from_tuple(t):
        # t = (id, name, category, description, image_url, price)
        return Product(t[0], t[1], t[2], t[3], t[4], t[5])



class Cart:
    def __init__(self, id, created_at, completed):
        self.id = id
        self.created_at = created_at
        self.completed = completed

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "completed": self.completed
        }

    @staticmethod
    def from_tuple(t):
        # t = (id, created_at, completed)
        return Cart(t[0], t[1], t[2])



class CartItem:
    def __init__(self, id, cart_id, product_id, quantity):
        self.id = id
        self.cart_id = cart_id
        self.product_id = product_id
        self.quantity = quantity

    def to_dict(self):
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity
        }

    @staticmethod
    def from_tuple(t):
        # t = (id, cart_id, product_id, quantity)
        return CartItem(t[0], t[1], t[2], t[3])
