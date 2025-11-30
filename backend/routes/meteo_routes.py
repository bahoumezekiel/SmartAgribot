from flask import Blueprint, jsonify
from services.weather_service import WeatherService

"""
   Ce module expose deux endpoints REST qui appellent WeatherService pour fournir la météo d’une région
   (ou de toutes les régions), formate la réponse JSON, gère les erreurs et renvoie un indicateur simple (cached)
   pour savoir si la valeur paraît valide — c’est la couche HTTP entre notre front/chatbot et la logique métier météo.gg
"""


meteo_bp = Blueprint('meteo', __name__)

@meteo_bp.route('/meteo/<int:region_id>', methods=['GET'])
def get_meteo(region_id):
    """
    Récupère la météo pour une région
    
    Exemple: GET /api/meteo/1
    
    Response:
    {
        "success": true,
        "data": {
            "region": "Centre Sud",
            "temperature": 30.5,
            "humidite": 65,
            "description": "ensoleillé",
            ...
        }
    }
    """
    try:
        weather = WeatherService.get_weather(region_id)
        
        if 'error' in weather:
            return jsonify({
                'success': False,
                'error': weather['error']
            }), 500
        
        return jsonify({
            'success': True,
            'data': weather,
            'cached': 'temperature' in weather  # True si données valides
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@meteo_bp.route('/meteo/all', methods=['GET'])
def get_all_meteo():
    """
    Récupère la météo pour toutes les régions
    
    Response:
    {
        "success": true,
        "data": {
            "1": {...},
            "2": {...},
            "3": {...}
        }
    }
    """
    try:
        from services.db_service import DatabaseService
        
        regions = DatabaseService.get_all_regions()
        weather_data = {}
        
        for region in regions:
            weather = WeatherService.get_weather(region['id_reg'])
            if 'error' not in weather:
                weather_data[str(region['id_reg'])] = weather
        
        return jsonify({
            'success': True,
            'count': len(weather_data),
            'data': weather_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

