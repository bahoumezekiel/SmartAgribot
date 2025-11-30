from flask import Blueprint, jsonify, request
from services.db_service import DatabaseService

"""
Ce fichier définit toutes les routes API liées aux données agricoles stockées dans la base de données.
c'est la couche d'acces au donnees statiques de notre systeme
"""

data_bp = Blueprint('data', __name__)#on cree ici un model de route nommer data

@data_bp.route('/regions', methods=['GET'])
def get_regions():
    """
    Récupère toutes les régions
    
    Response:
    [
        {
            "id_reg": 1,
            "nom": "Centre Sud",
            "zone_climat": "zone sud-soudanienne",
            "latitude": 11.6713,
            "longitude": -1.0737
        },
        ...
    ]
    """
    try:
        regions = DatabaseService.get_all_regions()
        return jsonify({
            'success': True,
            'count': len(regions),
            'data': regions
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/cultures', methods=['GET'])
def get_cultures():
    """
    Récupère toutes les cultures
    
    Response:
    [
        {
            "id_culture": 1,
            "nom": "Coton",
            "type": "cereal",
            "description": "..."
        },
        ...
    ]
    """
    try:
        cultures = DatabaseService.get_all_cultures()
        return jsonify({
            'success': True,
            'count': len(cultures),
            'data': cultures
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/calendrier/<int:culture_id>/<int:region_id>', methods=['GET'])
def get_calendrier(culture_id, region_id):
    """
    Récupère le calendrier pour une culture et région
    
    Exemple: GET /api/calendrier/1/2
    """
    try:
        calendrier = DatabaseService.get_calendrier(culture_id, region_id)
        
        if not calendrier:
            return jsonify({
                'success': False,
                'error': 'Calendrier non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'data': calendrier
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/maladies/<int:culture_id>', methods=['GET'])
def get_maladies(culture_id):
    """
    Récupère les maladies d'une culture
    
    Exemple: GET /api/maladies/1
    """
    try:
        maladies = DatabaseService.get_maladies_by_culture(culture_id)
        
        return jsonify({
            'success': True,
            'count': len(maladies),
            'data': maladies
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/conseils/<int:culture_id>', methods=['GET'])
def get_conseils(culture_id):
    """
    Récupère les conseils pour une culture
    
    Exemple: GET /api/conseils/1
    """
    try:
        conseils = DatabaseService.get_conseils_by_culture(culture_id)
        
        return jsonify({
            'success': True,
            'count': len(conseils),
            'data': conseils
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

