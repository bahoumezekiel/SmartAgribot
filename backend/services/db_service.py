from database import get_db_connection
from datetime import datetime, timedelta
from config import Config

"""
Ce fichier contient une classe qui centralise toutes les interactions entre le chatbot et la base de données.
Il utilise un helper get_db_connection() pour ouvrir une connexion SQLite.
DatabaseService est la couche qui fait le lien entre le chatbot et la base de données SQLite.
"""

class DatabaseService:
    """Service pour toutes les requêtes SQL"""
    
    # ==================== RÉGIONS ====================
    
    @staticmethod
    def get_all_regions():
        """Récupère toutes les régions"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Region")
        regions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return regions
    
    # ==================== CULTURES ====================
    
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
    
    # ==================== CALENDRIER ====================
    
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
    
    # ==================== MALADIES ====================
    
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
    
    # ==================== CONSEILS ====================
    
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
    
    # ==================== MÉTÉO CACHE ====================
    
    @staticmethod
    def get_meteo_cache(region_id):
        """Récupère les données météo en cache"""
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
    
    @staticmethod
    def save_meteo_cache(region_id, data_json):
        """Sauvegarde les données météo en cache"""
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
    
    # ==================== ALERTES MÉTÉO ====================
    
    @staticmethod
    def creer_table_alertes():
        """Crée la table pour stocker les alertes météo"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertes_meteo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    niveau TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    message TEXT NOT NULL,
                    conseils TEXT,
                    region_id INTEGER,
                    timestamp TEXT NOT NULL,
                    est_lue INTEGER DEFAULT 0,
                    FOREIGN KEY (region_id) REFERENCES Region (id_reg)
                )
            ''')
            
            # Créer les index pour les performances
            DatabaseService._creer_index_alertes(cursor)
            
            conn.commit()
            conn.close()
            print("[DB] Table alertes_meteo créée avec succès")
            
        except Exception as e:
            print(f"[DB ERROR] Erreur création table alertes: {str(e)}")
    
    @staticmethod
    def _creer_index_alertes(cursor):
        """Crée les index pour la table des alertes"""
        index_queries = [
            'CREATE INDEX IF NOT EXISTS idx_alertes_region_timestamp ON alertes_meteo(region_id, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_alertes_lues ON alertes_meteo(est_lue, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_alertes_type ON alertes_meteo(type, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_alertes_niveau ON alertes_meteo(niveau, timestamp)'
        ]
        
        for query in index_queries:
            try:
                cursor.execute(query)
            except Exception as e:
                print(f"[DB WARNING] Erreur création index: {e}")
    
    @staticmethod
    def sauvegarder_alerte(alerte_data):
        """Sauvegarde une alerte dans la base de données"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alertes_meteo 
                (type, niveau, titre, message, conseils, region_id, timestamp, est_lue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alerte_data['type'],
                alerte_data['niveau'],
                alerte_data['titre'],
                alerte_data['message'],
                alerte_data.get('conseils'),  # Peut être None
                alerte_data.get('region_id'),  # Peut être None
                alerte_data['timestamp'],
                alerte_data.get('est_lue', 0)
            ))
            
            alerte_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return alerte_id
            
        except Exception as e:
            print(f"[DB ERROR] Erreur sauvegarde alerte: {str(e)}")
            return None
    
    @staticmethod
    def get_alertes_utilisateur(region_id=None, non_lues_seulement=True, limit=50):
        """Récupère les alertes pour un utilisateur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT am.*, r.nom as region_nom
                FROM alertes_meteo am
                LEFT JOIN Region r ON am.region_id = r.id_reg
                WHERE 1=1
            '''
            params = []
            
            if region_id:
                query += ' AND am.region_id = ?'
                params.append(region_id)
            
            if non_lues_seulement:
                query += ' AND am.est_lue = 0'
            
            query += ' ORDER BY am.timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            alertes = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return alertes
            
        except Exception as e:
            print(f"[DB ERROR] Erreur récupération alertes: {str(e)}")
            return []
    
    @staticmethod
    def marquer_alerte_lue(alerte_id):
        """Marque une alerte comme lue"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alertes_meteo 
                SET est_lue = 1 
                WHERE id = ?
            ''', (alerte_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Erreur marquage alerte lue: {str(e)}")
            return False
    
    @staticmethod
    def supprimer_anciennes_alertes(jours=7):
        """Supprime les alertes de plus de X jours"""
        try:
            date_limite = (datetime.now() - timedelta(days=jours)).isoformat()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM alertes_meteo 
                WHERE timestamp < ?
            ''', (date_limite,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Erreur suppression anciennes alertes: {str(e)}")
            return False
    
    @staticmethod
    def get_statistiques_alertes():
        """Récupère les statistiques des alertes"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Compter les alertes non lues
            cursor.execute('SELECT COUNT(*) FROM alertes_meteo WHERE est_lue = 0')
            alertes_non_lues = cursor.fetchone()[0]
            
            # Compter par type d'alerte
            cursor.execute('''
                SELECT type, COUNT(*) as count 
                FROM alertes_meteo 
                WHERE est_lue = 0 
                GROUP BY type
            ''')
            alertes_par_type = {row['type']: row['count'] for row in cursor.fetchall()}
            
            # Compter par niveau
            cursor.execute('''
                SELECT niveau, COUNT(*) as count 
                FROM alertes_meteo 
                WHERE est_lue = 0 
                GROUP BY niveau
            ''')
            alertes_par_niveau = {row['niveau']: row['count'] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'alertes_non_lues': alertes_non_lues,
                'par_type': alertes_par_type,
                'par_niveau': alertes_par_niveau
            }
            
        except Exception as e:
            print(f"[DB ERROR] Erreur récupération statistiques: {str(e)}")
            return {}