import sqlite3
from config import Config

def get_db_connection():
    """Crée une connexion à la base de données"""
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn