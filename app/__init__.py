# app/__init__.py

from flask import Flask
from app.db import create_tables
app = Flask(__name__)

# Φόρτωση των routes (οι διαδρομές προστίθενται στο app)
from app import routes
