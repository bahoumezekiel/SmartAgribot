import requests
import json
from config import Config
from services.db_service import DatabaseService, get_db_connection

"""
Ce code définit un service météo central appelé WeatherService.
Son objectif est de :

Récupérer la météo d’une région
Utiliser les coordonnées GPS stockées en base
Appeler l’API OpenWeather
Mettre en cache les résultats en base de données
Éviter les appels inutiles à l’API externe
"""

class WeatherService:
    """Service pour récupérer les données météo"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    @staticmethod
    def get_weather(region_id):

        cache = DatabaseService.get_meteo_cache(region_id)
        if cache:
            return json.loads(cache['data_json'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Region WHERE id_reg = ?", (region_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {'error': 'Région non trouvée'}

        region = dict(row)

        try:
            params = {
                'lat': region['latitude'],
                'lon': region['longitude'],
                'appid': Config.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'fr'
            }

            response = requests.get(WeatherService.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            weather_data = {
                'region': region['nom'],
                'temperature': data['main']['temp'],
                'temperature_ressentie': data['main']['feels_like'],
                'humidite': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'vent': data['wind']['speed'],
                'pression': data['main']['pressure']
            }

            DatabaseService.save_meteo_cache(region_id, json.dumps(weather_data))
            return weather_data

        except requests.exceptions.RequestException as e:
            return {'error': f'Erreur réseau : {str(e)}'}
        except Exception as e:
            return {'error': f'Erreur lors de la récupération de la météo : {str(e)}'}
