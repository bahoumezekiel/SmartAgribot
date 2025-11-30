from flask import Blueprint, request, jsonify # Blueprint pour organiser les routes # request pour obtenir les données de la requête # jsonify pour renvoyer des données au format JSON
from services.chatbot_service import ChatbotService
from datetime import datetime

"""
Ce fichier définit la route API /chat de notre backend Flask.C’est elle qui :
Reçoit les messages envoyés depuis le frontend. Les transmet au chatbot (ChatbotService)
Formate une réponse propre et simplifiée pour l’utilisateur
C’est donc la porte d’entrée HTTP de notre chatbot.
"""

chat_bp = Blueprint('chat', __name__) #on cree ici un model de route nommer chat

# Instance globale du chatbot (chargement unique de SpaCy)
chatbot_service = ChatbotService()

#cette route accepte uniquement les requêtes POST et attend un message JSON avec le champ "message"
@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Corps de requête vide',
                'message': 'Veuillez envoyer un JSON avec le champ "message"'
            }), 400

        message = data.get('message', '').strip()
        user_context = data.get('context', {})

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message vide',
                'message': 'Le champ "message" est requis'
            }), 400

        # Traitement du message
        result = chatbot_service.process_message(message, user_context)

        # RÉPONSE SIMPLIFIÉE
        return jsonify({
            "success": True,
            "response": result.get("response"),
            "suggestions": result.get("suggestions", []),
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erreur serveur',
            'message': str(e)
        }), 500
