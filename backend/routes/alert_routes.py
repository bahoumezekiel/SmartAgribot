from flask import Blueprint, jsonify, request
from services.db_service import DatabaseService

alert_bp = Blueprint('alert', __name__)

@alert_bp.route('/alertes', methods=['GET'])
def get_alertes():
    """Récupère les alertes météo pour l'utilisateur"""
    try:
        region_id = request.args.get('region_id', type=int)
        non_lues_seulement = request.args.get('non_lues_seulement', 'true').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        alertes = DatabaseService.get_alertes_utilisateur(
            region_id=region_id,
            non_lues_seulement=non_lues_seulement,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'alertes': alertes,
            'count': len(alertes),
            'has_new_alerts': any(not alerte.get('est_lue', 0) for alerte in alertes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la récupération des alertes: {str(e)}"
        }), 500

@alert_bp.route('/alertes/<int:alerte_id>/marquer-lue', methods=['POST'])
def marquer_alerte_lue(alerte_id):
    """Marque une alerte comme lue"""
    try:
        success = DatabaseService.marquer_alerte_lue(alerte_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alerte marquée comme lue'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors du marquage de l\'alerte'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Erreur lors du marquage de l'alerte: {str(e)}"
        }), 500

@alert_bp.route('/alertes/marquer-toutes-lues', methods=['POST'])
def marquer_toutes_lues():
    """Marque toutes les alertes comme lues"""
    try:
        data = request.get_json() or {}
        region_id = data.get('region_id')
        
        conn = DatabaseService.get_db_connection()
        cursor = conn.cursor()
        
        if region_id:
            cursor.execute('''
                UPDATE alertes_meteo 
                SET est_lue = 1 
                WHERE region_id = ?
            ''', (region_id,))
        else:
            cursor.execute('''
                UPDATE alertes_meteo 
                SET est_lue = 1 
            ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Toutes les alertes marquées comme lues'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Erreur lors du marquage des alertes: {str(e)}"
        }), 500

@alert_bp.route('/alertes/verifier-nouvelles', methods=['POST'])
def verifier_nouvelles_alertes():
    """Vérifie et génère de nouvelles alertes météo"""
    try:
        data = request.get_json() or {}
        regions_ids = data.get('regions', [])
        
        nouvelles_alertes = []
        
        if not regions_ids:
            # Récupérer toutes les régions si aucune spécifiée
            regions = DatabaseService.get_all_regions()
            regions_ids = [region['id_reg'] for region in regions]
        
        for region_id in regions_ids:
            from services.alert_service import AlertService
            alertes = AlertService.detecter_alertes_meteo(region_id)
            nouvelles_alertes.extend(alertes)
        
        # Nettoyer les anciennes alertes
        DatabaseService.supprimer_anciennes_alertes(jours=7)
        
        return jsonify({
            'success': True,
            'nouvelles_alertes': nouvelles_alertes,
            'count': len(nouvelles_alertes),
            'message': f"{len(nouvelles_alertes)} nouvelle(s) alerte(s) détectée(s)"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la vérification des alertes: {str(e)}"
        }), 500

@alert_bp.route('/alertes/statistiques', methods=['GET'])
def get_statistiques_alertes():
    """Récupère les statistiques des alertes"""
    try:
        stats = DatabaseService.get_statistiques_alertes()
        
        return jsonify({
            'success': True,
            'statistiques': stats
        })
        
    except Exception as e:
        print(f"[ALERTES ERROR] Erreur dans /alertes/statistiques: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la récupération des statistiques: {str(e)}"
        }), 500