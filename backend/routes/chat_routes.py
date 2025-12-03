from flask import Blueprint, request, jsonify
from services.chatbot_service import ChatbotService
from services.alert_service import AlertService
from datetime import datetime

"""
Ce fichier définit les routes API /chat de notre backend Flask.
Il gère :
- La réception des messages depuis le frontend
- Le traitement par le ChatbotService
- La gestion des alertes météo dans le chat
- Le formatage des réponses pour l'utilisateur
C'est la porte d'entrée HTTP de notre chatbot.
"""

chat_bp = Blueprint('chat', __name__)

# Instance globale du chatbot (chargement unique de SpaCy)
chatbot_service = ChatbotService()


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal pour le chat
    Accepte uniquement les requêtes POST avec un JSON contenant le champ "message"
    """
    try:
        data = request.get_json() or {}

        message = (data.get('message') or '').strip()
        user_context = data.get('context', {})

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message vide',
                'message': 'Le champ "message" est requis'
            }), 400

        # Traitement du message par le chatbot
        result = chatbot_service.process_message(message, user_context)

        return jsonify({
            "success": True,
            "response": result.get("response"),
            "suggestions": result.get("suggestions", []),
            "data": result.get("data"),
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"[CHAT ERROR] Erreur dans /chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors du traitement de votre message'
        }), 500


@chat_bp.route('/chat/alertes', methods=['POST'])
def get_alertes_chat():
    """
    Endpoint pour récupérer les alertes dans le contexte du chat
    """
    try:
        data = request.get_json() or {}
        user_context = data.get('user_context', {})
        region_id = user_context.get('default_region_id')

        # Utiliser l'instance globale du chatbot
        result = chatbot_service.get_alertes_utilisateur(region_id=region_id or None)

        return jsonify({
            'success': True,
            'response': result.get('response'),
            'data': result.get('data'),
            'has_alerts': result.get('has_alerts', False),
            'suggestions': result.get('suggestions', []),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[ALERTES CHAT ERROR] Erreur dans /chat/alertes: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la récupération des alertes: {str(e)}"
        }), 500


@chat_bp.route('/chat/health', methods=['GET'])
def health_check():
    """
    Endpoint de santé pour vérifier le statut du service NLP
    """
    try:
        test_message = "Bonjour"
        result = chatbot_service.process_message(test_message)

        test_response = result.get('response', '')
        return jsonify({
            'success': True,
            'status': 'healthy',
            'nlp_loaded': True,
            'timestamp': datetime.now().isoformat(),
            'test_response': test_response[:100] + '...' if test_response else ''
        })

    except Exception as e:
        print(f"[HEALTH CHECK ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'nlp_loaded': False
        }), 500


@chat_bp.route('/chat/context', methods=['POST'])
def update_context():
    """
    Endpoint pour mettre à jour le contexte utilisateur
    """
    try:
        data = request.get_json() or {}

        user_id = data.get('user_id')
        new_context = data.get('context')

        if not user_id or not new_context:
            return jsonify({
                'success': False,
                'error': 'Données manquantes',
                'message': 'Les champs "user_id" et "context" sont requis'
            }), 400

        # Appel du service pour mettre à jour le contexte utilisateur
        chatbot_service.update_user_context(user_id, new_context)

        return jsonify({
            'success': True,
            'message': 'Contexte utilisateur mis à jour avec succès',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[CONTEXT UPDATE ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur',
            'message': 'Impossible de mettre à jour le contexte utilisateur'
        }), 500
