import json
import sqlite3
from datetime import datetime, timedelta
from services.weather_service import WeatherService
from services.db_service import DatabaseService

class AlertService:
    """Service de gestion des alertes météo"""
    
    # Seuils pour les alertes
    SEUILS = {
        'secheresse': {
            'humidite_max': 30,
            'temperature_min': 35,
            'jours_sans_pluie': 7
        },
        'inondation': {
            'humidite_min': 85,
            'precipitation_min': 20  # mm
        },
        'vent_violent': {
            'vent_min': 10  # m/s
        },
        'froid_intense': {
            'temperature_max': 10
        }
    }
    
    @staticmethod
    def detecter_alertes_meteo(region_id):
        """Détecte les conditions météo défavorables pour une région"""
        alertes = []
        
        try:
            # Récupérer les données météo
            meteo = WeatherService.get_weather(region_id)
            if 'error' in meteo:
                return alertes
            
            # Vérifier les conditions pour chaque type d'alerte
            if AlertService._detecter_secheresse(meteo):
                alertes.append({
                    'type': 'secheresse',
                    'niveau': 'danger',
                    'titre': '🌵 Alerte Sécheresse',
                    'message': f"Conditions de sécheresse détectées dans la région {meteo['region']}. Température élevée et humidité faible.",
                    'conseils': [
                        "Arrosez vos cultures en fin de journée",
                        "Utilisez du paillage pour conserver l'humidité",
                        "Évitez les travaux agricoles en milieu de journée"
                    ],
                    'region_id': region_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            if AlertService._detecter_inondation(meteo):
                alertes.append({
                    'type': 'inondation',
                    'niveau': 'danger',
                    'titre': '🌧️ Alerte Inondation',
                    'message': f"Risque d'inondation détecté dans la région {meteo['region']}. Humidité élevée et précipitations importantes.",
                    'conseils': [
                        "Surveillez le drainage de vos champs",
                        "Protégez vos équipements agricoles",
                        "Évitez les semis en zones basses"
                    ],
                    'region_id': region_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            if AlertService._detecter_vent_violent(meteo):
                alertes.append({
                    'type': 'vent_violent',
                    'niveau': 'warning',
                    'titre': '💨 Vent Violent',
                    'message': f"Vents forts détectés dans la région {meteo['region']}. Vitesse du vent : {meteo['vent']} m/s.",
                    'conseils': [
                        "Protégez les jeunes plants",
                        "Rentrez les équipements légers",
                        "Reportez les pulvérisations"
                    ],
                    'region_id': region_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            if AlertService._detecter_froid_intense(meteo):
                alertes.append({
                    'type': 'froid_intense',
                    'niveau': 'warning',
                    'titre': '❄️ Froid Intense',
                    'message': f"Températures basses détectées dans la région {meteo['region']}. Température : {meteo['temperature']}°C.",
                    'conseils': [
                        "Protégez les cultures sensibles au froid",
                        "Utilisez des voiles d'hivernage",
                        "Évitez les arrosages en soirée"
                    ],
                    'region_id': region_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Sauvegarder les alertes détectées
            for alerte in alertes:
                AlertService._sauvegarder_alerte(alerte)
                
        except Exception as e:
            print(f"[ALERTE ERROR] Erreur lors de la détection des alertes: {str(e)}")
        
        return alertes
    
    @staticmethod
    def _detecter_secheresse(meteo):
        """Détecte les conditions de sécheresse"""
        return (meteo['humidite'] <= AlertService.SEUILS['secheresse']['humidite_max'] and 
                meteo['temperature'] >= AlertService.SEUILS['secheresse']['temperature_min'])
    
    @staticmethod
    def _detecter_inondation(meteo):
        """Détecte les risques d'inondation"""
        return (meteo['humidite'] >= AlertService.SEUILS['inondation']['humidite_min'])
    
    @staticmethod
    def _detecter_vent_violent(meteo):
        """Détecte les vents violents"""
        return meteo['vent'] >= AlertService.SEUILS['vent_violent']['vent_min']
    
    @staticmethod
    def _detecter_froid_intense(meteo):
        """Détecte les températures trop basses"""
        return meteo['temperature'] <= AlertService.SEUILS['froid_intense']['temperature_max']
    
    @staticmethod
    def _sauvegarder_alerte(alerte):
        """Sauvegarde une alerte dans la base de données"""
        try:
            conn = DatabaseService.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO alertes_meteo 
                (type, niveau, titre, message, conseils, region_id, timestamp, est_lue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alerte['type'],
                alerte['niveau'],
                alerte['titre'],
                alerte['message'],
                json.dumps(alerte['conseils']),
                alerte['region_id'],
                alerte['timestamp'],
                0  # Non lue par défaut
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[ALERTE ERROR] Erreur sauvegarde alerte: {str(e)}")
    
    @staticmethod
    def get_alertes_utilisateur(region_id=None, non_lues_seulement=True):
        """Récupère les alertes pour un utilisateur"""
        try:
            conn = DatabaseService.get_db_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM alertes_meteo 
                WHERE 1=1
            '''
            params = []
            
            if region_id:
                query += ' AND region_id = ?'
                params.append(region_id)
            
            if non_lues_seulement:
                query += ' AND est_lue = 0'
            
            query += ' ORDER BY timestamp DESC LIMIT 50'
            
            cursor.execute(query, params)
            alertes = [dict(row) for row in cursor.fetchall()]
            
            # Convertir les conseils JSON en liste
            for alerte in alertes:
                if alerte.get('conseils'):
                    alerte['conseils'] = json.loads(alerte['conseils'])
            
            conn.close()
            return alertes
            
        except Exception as e:
            print(f"[ALERTE ERROR] Erreur récupération alertes: {str(e)}")
            return []
    
    @staticmethod
    def marquer_alerte_lue(alerte_id):
        """Marque une alerte comme lue"""
        try:
            conn = DatabaseService.get_db_connection()
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
            print(f"[ALERTE ERROR] Erreur marquage alerte lue: {str(e)}")
            return False
    
    @staticmethod
    def supprimer_anciennes_alertes(jours=7):
        """Supprime les alertes de plus de X jours"""
        try:
            date_limite = (datetime.now() - timedelta(days=jours)).isoformat()
            
            conn = DatabaseService.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM alertes_meteo 
                WHERE timestamp < ?
            ''', (date_limite,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[ALERTE ERROR] Erreur suppression anciennes alertes: {str(e)}")
            return False