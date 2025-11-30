import sys
import os

"""
    Point d'entrée principal de l'application Flask pour SmartAgriBot.
    il configure l'application, enregistre les routes et gère les erreurs globales.
"""
# Ajouter le dossier backend au path pour que Python trouve routes et services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config  

# Import des routes
from routes.chat_routes import chat_bp
from routes.data_routes import data_bp
from routes.meteo_routes import meteo_bp

def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Activer CORS pour le frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Enregistrer les blueprints
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(meteo_bp, url_prefix='/api')

    @app.route('/')
    def index():
        """Page d'accueil de l'API"""
        return jsonify({
            'message': 'Bienvenue sur SmartAgriBot API 🌱',
            'version': '1.0.0',
            'nlp': 'SpaCy fr_core_news_md',
            'endpoints': {
                'chat': {'url': '/api/chat', 'method': 'POST', 'description': 'Envoyer un message au chatbot'},
                'health': {'url': '/api/chat/health', 'method': 'GET', 'description': 'Vérifier le statut du service NLP'},
                'regions': {'url': '/api/regions', 'method': 'GET', 'description': 'Liste des régions'},
                'cultures': {'url': '/api/cultures', 'method': 'GET', 'description': 'Liste des cultures'},
                'meteo': {'url': '/api/meteo/<region_id>', 'method': 'GET', 'description': 'Météo d\'une région'},
                'calendrier': {'url': '/api/calendrier/<culture_id>/<region_id>', 'method': 'GET', 'description': 'Calendrier de culture'}
            },
            'documentation': 'https://github.com/votre-repo/smartagribot'
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Endpoint non trouvé', 'message': 'Consultez / pour la liste des endpoints disponibles'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Erreur serveur interne', 'message': str(error)}), 500

    return app

if __name__ == '__main__':
    # Vérifier que SpaCy est installé
    try:
        import spacy
        try:
            nlp = spacy.load("fr_core_news_md")
            print("SpaCy chargé avec succès (fr_core_news_md)")
        except OSError:
            print("ATTENTION : Modèle SpaCy non trouvé !")
            print("Installez-le avec: python -m spacy download fr_core_news_md")
            print("L'API fonctionnera en mode dégradé.\n")
    except ImportError:
        print("ERREUR : SpaCy n'est pas installé !")
        print("   Installez-le avec: pip install spacy")
        sys.exit(1)

    # Créer et lancer l'application
    app = create_app()

    
    print("SMARTAGRIBOT API - DÉMARRAGE")
    print(f"URL: http://localhost:5000")
    print(f"Endpoints: http://localhost:5000/")
    print(f"Chat: http://localhost:5000/api/chat")
     
    app.run(debug=True, host='0.0.0.0', port=5000)
