from database import get_db_connection
"""
Ce fichier contient une classe qui centralise toutes les interactions entre le chatbot et la base de données.
Il utilise un helper get_db_connection() pour ouvrir une connexion SQLite.
De defacon resumer cette class (DatabaseService) est la couche qui fait le lien entre le chatbot et la base de données SQLite.
"""
class DatabaseService:
    """Service pour toutes les requêtes SQL"""
    
    @staticmethod
    def get_all_regions():
        """Récupère toutes les régions"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Region")
        regions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return regions
    
    @staticmethod
    def get_all_cultures():
        """Récupère toutes les cultures"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Cultures")
        cultures = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cultures
    
    @staticmethod
    def get_culture_by_name(nom):
        """Récupère une culture par nom"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Cultures WHERE LOWER(nom) = LOWER(?)", (nom,))
        result = cursor.fetchone()
        culture = dict(result) if result else None
        conn.close()
        return culture
    
    @staticmethod
    def get_calendrier(culture_id, region_id):
        """Récupère le calendrier pour une culture et région"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, cu.nom as culture_nom, r.nom as region_nom
            FROM calendrier_cultural c
            JOIN Cultures cu ON c.id_culture = cu.id_culture
            JOIN Region r ON c.id_reg = r.id_reg
            WHERE c.id_culture = ? AND c.id_reg = ?
        """, (culture_id, region_id))
        result = cursor.fetchone()
        calendrier = dict(result) if result else None
        conn.close()
        return calendrier
    
    @staticmethod
    def get_maladies_by_culture(culture_id):
        """Récupère les maladies d'une culture"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*
            FROM maladies_parasites m
            JOIN affecter a ON m.id_parasite = a.id_parasite
            WHERE a.id_culture = ?
        """, (culture_id,))
        maladies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return maladies
    
    @staticmethod
    def get_conseils_by_culture(culture_id):
        """Récupère les conseils pour une culture"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM conseils_pratiques
            WHERE id_culture = ?
        """, (culture_id,))
        conseils = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return conseils
    
    @staticmethod
    def save_meteo_cache(region_id, data_json):
        """Sauvegarde les données météo en cache"""
        from datetime import datetime
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Supprimer l'ancien cache pour cette région
        cursor.execute("DELETE FROM meteo_cache WHERE region_id = ?", (region_id,))
        
        # Insérer le nouveau cache
        cursor.execute("""
            INSERT INTO meteo_cache (region_id, data_json, timestamp_)
            VALUES (?, ?, ?)
        """, (region_id, data_json, datetime.now()))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_meteo_cache(region_id):
        """Récupère les données météo en cache"""
        from datetime import datetime, timedelta
        from config import Config
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meteo_cache
            WHERE region_id = ?
            ORDER BY timestamp_ DESC LIMIT 1
        """, (region_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        cache = dict(result)
        
        # Vérifier si le cache est encore valide
        cache_time = datetime.fromisoformat(cache['timestamp_'])
        if datetime.now() - cache_time > timedelta(seconds=Config.CACHE_DURATION):
            return None  # Cache expiré
        
        return cache

