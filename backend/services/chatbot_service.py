from services.nlp_service import NLPService
from services.db_service import DatabaseService
from services.weather_service import WeatherService
from services.alert_service import AlertService
import re

class ChatbotService:
    """
    Service principal du chatbot avec NLP SpaCy
    But : recevoir une phrase de l'utilisateur, l'analyser (intention, entités, sentiment), 
    et renvoyer une réponse métier adaptée (météo, calendrier de plantation/récolte, maladies, conseils, alertes).

    Flux : process_message → NLP → fallback contexte → dispatch → handler → préparation de la réponse → retour d'un dict structuré.

    Intégration : dépend fortement de NLPService, DatabaseService, WeatherService et AlertService. 
    Le code assemble ces services et applique la logique métier.

    Personnalisation : utilise le sentiment pour ajuster le ton (empathie) et le user_context pour la région par défaut.
    """

    def __init__(self):
        """Initialise le service NLP"""
        self.nlp_service = NLPService()

    def clean_text(self, text):
        """Nettoie le texte : supprime espaces multiples et retours à la ligne inutiles"""
        if not text:
            return ""
        text = re.sub(r'[\r\n\t]+', ' ', text)  # Supprime retours à la ligne et tabulations
        text = re.sub(r'\s+', ' ', text)        # Remplace plusieurs espaces par un seul
        return text.strip()                      # Supprime espaces début/fin

    def process_message(self, message, user_context=None):
        """Traite un message utilisateur avec analyse NLP complète"""
        # 1. Récupérer toutes les régions pour l'extraction
        regions = DatabaseService.get_all_regions()

        # 2. Analyse NLP complète du message
        analysis = self.nlp_service.get_message_info(message, regions)
        intention = analysis['intention']
        culture_nom = analysis['culture']
        region = analysis['region']
        sentiment = analysis['sentiment']

        # 3. Gérer le contexte utilisateur
        if not region and user_context and 'default_region_id' in user_context:
            region = next((r for r in regions if r['id_reg'] == user_context['default_region_id']), None)

        # 4. Système de fallback : affiner l'intention si nécessaire
        message_lower = message.lower()
        
        # Mots-clés pour affiner l'intention
        plantation_keywords = ['planter', 'semer', 'cultiver', 'culture', 'semis', 'période', 'moment', 'quand', 'adapter']
        recolte_keywords = ['récolter', 'récolte', 'ramasser', 'cueillir', 'maturité']
        maladie_keywords = ['maladie', 'parasite', 'traiter', 'traitement', 'insecte', 'pest', 'infection', 'attaque']
        conseil_keywords = ['conseil', 'recommandation', 'technique', 'méthode', 'astuce', 'comment']
        meteo_keywords = ['météo', 'temps', 'climat', 'température', 'pluie', 'chaleur']
        alerte_keywords = ['alerte', 'danger', 'risque', 'urgence', 'problème', 'sécheresse', 'inondation', 'vent', 'orage']
        
        # Si l'intention est 'general' mais qu'on détecte des mots-clés spécifiques
        if intention == 'general':
            if any(keyword in message_lower for keyword in plantation_keywords):
                if not any(keyword in message_lower for keyword in recolte_keywords):
                    intention = 'plantation'
                    print(f"[DEBUG] Intention affinée par fallback : {intention}")
            elif any(keyword in message_lower for keyword in recolte_keywords):
                intention = 'recolte'
                print(f"[DEBUG] Intention affinée par fallback : {intention}")
            elif any(keyword in message_lower for keyword in maladie_keywords):
                intention = 'maladie'
                print(f"[DEBUG] Intention affinée par fallback : {intention}")
            elif any(keyword in message_lower for keyword in conseil_keywords):
                intention = 'conseil'
                print(f"[DEBUG] Intention affinée par fallback : {intention}")
            elif any(keyword in message_lower for keyword in meteo_keywords):
                intention = 'meteo'
                print(f"[DEBUG] Intention affinée par fallback : {intention}")
            elif any(keyword in message_lower for keyword in alerte_keywords):
                intention = 'alerte'
                print(f"[DEBUG] Intention affinée par fallback : {intention}")

        # 5. Log de l'analyse (pour debug)
        print(f"[DEBUG] ========== ANALYSE NLP ==========")
        print(f"[DEBUG] Message original : {message}")
        print(f"[DEBUG] Intention détectée : {intention}")
        print(f"[DEBUG] Culture détectée : {culture_nom}")
        print(f"[DEBUG] Région détectée : {region['nom'] if region else 'Non détectée'}")
        print(f"[DEBUG] Sentiment : {sentiment}")
        print(f"[DEBUG] ====================================")

        # 6. Traiter selon l'intention avec gestion des erreurs
        try:
            if intention == 'meteo':
                return self.handle_meteo(region, sentiment)
            elif intention == 'plantation':
                return self.handle_plantation(culture_nom, region, sentiment)
            elif intention == 'recolte':
                return self.handle_recolte(culture_nom, region, sentiment)
            elif intention == 'maladie':
                return self.handle_maladie(culture_nom, sentiment)
            elif intention == 'conseil':
                return self.handle_conseil(culture_nom, sentiment)
            elif intention == 'alerte':
                return self.handle_alerte(region, sentiment)
            else:
                return self.handle_general(message, sentiment)
        except Exception as e:
            print(f"[ERROR] Exception dans le traitement : {str(e)}")
            import traceback
            traceback.print_exc()
            return self.handle_error(str(e))

    # ================== HANDLERS ==================
    
    def handle_meteo(self, region, sentiment):
        """Gère les questions sur la météo"""
        if not region:
            return {
                'response': "Pour quelle région souhaitez-vous connaître la météo ?\n\n"
                            "Régions disponibles:\n"
                            "• Centre Sud\n"
                            "• Boucle de Mouhoun\n"
                            "• Nord",
                'suggestions': ['Météo Centre Sud', 'Météo Nord', 'Météo Boucle de Mouhoun']
            }

        weather = WeatherService.get_weather(region['id_reg'])
        if 'error' in weather:
            return {'response': f"❌ Désolé, je n'ai pas pu récupérer la météo : {weather['error']}", 'data': None}

        response = f"Météo actuelle pour {weather['region']} :\n\n" if sentiment != 'negative' else \
                   f"Je comprends votre inquiétude. Voici la météo actuelle pour {weather['region']} :\n\n"

        response += f"🌡️ Température : {weather['temperature']}°C (ressenti {weather['temperature_ressentie']}°C)\n"
        response += f"💧 Humidité : {weather['humidite']}%\n"
        response += f"☁️ Conditions : {self.clean_text(weather['description'].capitalize())}\n"
        response += f"💨 Vent : {weather['vent']} m/s\n"
        response += f"Pression : {weather['pression']} hPa"

        # Vérifier si des alertes sont actives pour cette région
        alertes = AlertService.detecter_alertes_meteo(region['id_reg'])
        if alertes:
            response += f"\n\n🚨 **{len(alertes)} ALERTE(S) ACTIVE(S) POUR CETTE RÉGION**\n"
            for alerte in alertes[:2]:  # Afficher max 2 alertes
                response += f"• {alerte['titre']}\n"
            response += "\nTapez 'alertes' pour plus de détails."

        elif weather['temperature'] > 35:
            response += "\n\n⚠️ Attention : Forte chaleur. Arrosez vos cultures en fin de journée."
        elif weather['humidite'] > 80:
            response += "\n\n💡 Conseil : Humidité élevée. Surveillez les maladies fongiques."

        return {
            'response': response, 
            'data': weather, 
            'suggestions': ['Calendrier de plantation', 'Conseils culture', 'Voir les alertes']
        }

    def handle_plantation(self, culture_nom, region, sentiment):
        """Gère les questions sur la plantation"""
        if not culture_nom:
            cultures = DatabaseService.get_all_cultures()
            response = "🌱 Pour quelle culture voulez-vous connaître la période de plantation ?\n\n"
            response += "Cultures disponibles:\n"
            for culture in cultures:
                response += f"• {self.clean_text(culture['nom'].capitalize())}\n"
            return {'response': response, 'suggestions': [f"Planter {c['nom']}" for c in cultures[:3]]}

        culture = DatabaseService.get_culture_by_name(culture_nom)
        if not culture:
            return {'response': f"Désolé, je ne connais pas cette culture : {culture_nom}\n\n"
                                "Cultures disponibles : coton, maïs, mil, soja, tomate, pomme de terre",
                    'suggestions': ['Voir toutes les cultures']}

        if not region:
            regions = DatabaseService.get_all_regions()
            region = regions[0] if regions else None
            if not region:
                return {'response': "Aucune région disponible dans la base de données.", 'data': None}
            region_info = f" (région par défaut : {self.clean_text(region['nom'])})"
        else:
            region_info = f" dans la région {self.clean_text(region['nom'])}"

        calendrier = DatabaseService.get_calendrier(culture['id_culture'], region['id_reg'])
        if not calendrier:
            return {'response': f"Pas d'information de calendrier pour {culture_nom}{region_info}", 'data': None}

        response = f"🌱 **Plantation de {self.clean_text(culture_nom.capitalize())}**{region_info}\n\n"
        response += f" Période de semis : {self.clean_text(calendrier['periode_semis'])}\n\n"

        try:
            weather = WeatherService.get_weather(region['id_reg'])
            if 'temperature' in weather:
                response += f"Conditions actuelles : {weather['temperature']}°C, {self.clean_text(weather['description'])}\n\n"
                
                # Vérifier les alertes pour conseils de plantation
                alertes = AlertService.detecter_alertes_meteo(region['id_reg'])
                if alertes:
                    response += "🚨 **CONSEIL SPÉCIAL** : Consultez les alertes météo actuelles avant de planter.\n\n"
        except:
            pass

        conseils = DatabaseService.get_conseils_by_culture(culture['id_culture'])
        if conseils:
            conseil_text = self.clean_text(conseils[0]['bonnes_pratique'])
            if len(conseil_text) > 300:
                conseil_text = conseil_text[:297] + "..."
            response += f"Conseil pratique : {conseil_text}"

        return {
            'response': response,
            'data': {
                'calendrier': calendrier,
                'culture': culture
            },
            'suggestions': [
                f'Récolte {culture_nom}',
                f'Maladies {culture_nom}',
                f'Météo {region["nom"]}',
                'Alertes météo'
            ]
        }

    def handle_recolte(self, culture_nom, region, sentiment):
        """Gère les questions sur la récolte"""
        if not culture_nom:
            return {'response': "🌾 Pour quelle culture voulez-vous connaître la période de récolte ?",
                    'suggestions': ['Récolte maïs', 'Récolte coton', 'Récolte mil']}

        culture = DatabaseService.get_culture_by_name(culture_nom)
        if not culture:
            return {'response': f"❌ Désolé, je ne connais pas cette culture : {culture_nom}",
                    'suggestions': ['Voir toutes les cultures']}

        if not region:
            regions = DatabaseService.get_all_regions()
            region = regions[0] if regions else None
            if not region:
                return {'response': "Aucune région disponible dans la base de données.", 'data': None}

        calendrier = DatabaseService.get_calendrier(culture['id_culture'], region['id_reg'])
        if not calendrier:
            return {'response': f"Pas d'information de récolte pour {culture_nom} dans la région {region['nom']}",
                    'data': None}

        response = f"🌾 **Récolte de {self.clean_text(culture_nom.capitalize())}** dans la région {self.clean_text(region['nom'])}\n\n"
        response += f"Période de récolte : {self.clean_text(calendrier['periode_recolte'])}\n\n"
        
        # Vérifier les alertes pour conseils de récolte
        alertes = AlertService.detecter_alertes_meteo(region['id_reg'])
        if alertes:
            response += "⚠️ **ATTENTION** : Conditions météo défavorables détectées. "
            response += "Consultez les alertes avant de récolter.\n\n"
        else:
            response += "✅ Conditions météo favorables pour la récolte.\n\n"
            
        response += "Conseil : Surveillez bien la maturité de vos plants avant de récolter."

        return {
            'response': response, 
            'data': calendrier, 
            'suggestions': [f'Maladies {culture_nom}', 'Conseils récolte', 'Alertes météo']
        }

    def handle_maladie(self, culture_nom, sentiment):
        """Gère les questions sur les maladies"""
        if not culture_nom:
            return {'response': "Pour quelle culture voulez-vous connaître les maladies et parasites ?",
                    'suggestions': ['Maladies coton', 'Maladies maïs', 'Maladies tomate']}

        culture = DatabaseService.get_culture_by_name(culture_nom)
        if not culture:
            return {'response': f"❌ Désolé, je ne connais pas cette culture : {culture_nom}",
                    'suggestions': ['Voir toutes les cultures']}

        maladies = DatabaseService.get_maladies_by_culture(culture['id_culture'])
        if not maladies:
            return {'response': f"Bonne nouvelle ! Aucune maladie majeure enregistrée pour {culture_nom}.", 'data': None}

        response = f"Maladies et parasites du {self.clean_text(culture_nom.capitalize())} :**\n\n" \
            if sentiment != 'negative' else \
            f"Je comprends votre inquiétude. Voici les maladies courantes du {self.clean_text(culture_nom)} et leurs traitements :\n\n"

        for i, maladie in enumerate(maladies, 1):
            response += f"**{i}. {self.clean_text(maladie['nom'])}**\n"
            traitement = self.clean_text(maladie['traitement'])
            if len(traitement) > 250:
                traitement = traitement[:247] + "..."
            response += f"Traitement : {traitement}\n\n"

        return {
            'response': response, 
            'data': maladies, 
            'suggestions': [f'Conseils {culture_nom}', 'Prévention maladies', 'Alertes météo']
        }

    def handle_conseil(self, culture_nom, sentiment):
        """Gère les demandes de conseils"""
        if not culture_nom:
            return {'response': "Pour quelle culture voulez-vous des conseils pratiques ?",
                    'suggestions': ['Conseils coton', 'Conseils maïs', 'Conseils soja']}

        culture = DatabaseService.get_culture_by_name(culture_nom)
        if not culture:
            return {'response': f"Désolé, je ne connais pas cette culture : {culture_nom}",
                    'suggestions': ['Voir toutes les cultures']}

        conseils = DatabaseService.get_conseils_by_culture(culture['id_culture'])
        if not conseils:
            return {'response': f"Aucun conseil disponible pour {culture_nom} pour le moment.", 'data': None}

        response = f"Conseils pratiques pour la culture de {self.clean_text(culture_nom.capitalize())} :**\n\n"
        response += self.clean_text(conseils[0]['bonnes_pratique'])

        return {
            'response': response, 
            'data': conseils,
            'suggestions': [f'Planter {culture_nom}', f'Maladies {culture_nom}', 'Alertes météo']
        }

    def handle_alerte(self, region, sentiment):
        """Gère les demandes d'alertes météo"""
        if not region:
            return {
                'response': "Pour quelle région souhaitez-vous vérifier les alertes météo ?\n\n"
                            "Régions disponibles:\n"
                            "• Centre Sud\n"
                            "• Boucle de Mouhoun\n"
                            "• Nord",
                'suggestions': ['Alertes Centre Sud', 'Alertes Nord', 'Alertes Boucle de Mouhoun']
            }

        # Récupérer les alertes pour cette région
        return self.get_alertes_utilisateur(region['id_reg'])

    def get_alertes_utilisateur(self, region_id=None):
        """Récupère les alertes météo pour l'utilisateur"""
        try:
            alertes = DatabaseService.get_alertes_utilisateur(region_id=region_id, non_lues_seulement=True)
            
            if not alertes:
                return {
                    'response': "✅ Aucune alerte météo active pour le moment. Les conditions sont favorables.",
                    'data': {'alertes': []},
                    'has_alerts': False,
                    'suggestions': ['Météo actuelle', 'Calendrier de plantation', 'Vérifier alertes']
                }
            
            response = "🚨 **ALERTES MÉTÉO ACTIVES** 🚨\n\n"
            
            for i, alerte in enumerate(alertes, 1):
                # Icônes selon le type d'alerte
                icone = {
                    'secheresse': '🌵',
                    'inondation': '🌧️',
                    'vent_violent': '💨',
                    'froid_intense': '❄️'
                }.get(alerte['type'], '⚠️')
                
                # Couleur selon le niveau
                niveau_emoji = {
                    'danger': '🔴',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(alerte['niveau'], '⚪')
                
                response += f"{niveau_emoji} {icone} **{alerte['titre']}**\n"
                response += f"   📍 Région: {alerte.get('region_nom', 'Non spécifiée')}\n"
                response += f"   📅 Détecté: {alerte['timestamp'][:16].replace('T', ' ')}\n"
                response += f"   {alerte['message']}\n"
                
                if alerte.get('conseils'):
                    response += "\n   💡 **Conseils pratiques :**\n"
                    for conseil in alerte['conseils']:
                        response += f"   • {conseil}\n"
                
                response += "\n" + "─" * 40 + "\n\n"
            
            response += "**Recommandation :** Suivez ces conseils pour protéger vos cultures."
            
            return {
                'response': response,
                'data': {'alertes': alertes},
                'has_alerts': True,
                'suggestions': ['Météo détaillée', 'Conseils de protection', 'Marquer comme lues']
            }
            
        except Exception as e:
            print(f"[ALERTE ERROR] Erreur récupération alertes: {str(e)}")
            return {
                'response': "❌ Impossible de récupérer les alertes météo pour le moment. Veuillez réessayer plus tard.",
                'data': None,
                'has_alerts': False,
                'suggestions': ['Météo actuelle', 'Réessayer alertes']
            }

    def handle_general(self, message, sentiment):
        """Gère les messages généraux, salutations et questions hors sujet"""
        # Détection de salutation simple
        message_lower = message.lower().strip()
        salutations = ['bonjour', 'salut', 'bonsoir', 'hello', 'hi', 'hey', 'bsr', 'bjr', 'coucou']
        alerte_keywords = ['alerte', 'alertes', 'danger', 'problème', 'urgence']
        
        # Vérifier s'il y a des alertes non lues
        alertes_non_lues = DatabaseService.get_alertes_utilisateur(non_lues_seulement=True)
        has_alertes = len(alertes_non_lues) > 0
        
        # Si c'est juste une salutation ou un message très court
        if any(salut in message_lower for salut in salutations) or len(message_lower) < 20:
            response = "Bonjour ! Je suis **SmartAgriBot**, votre assistant agricole intelligent pour le Burkina Faso. 🇧🇫\n\n"
            
            if has_alertes:
                response += f"🚨 **ATTENTION : {len(alertes_non_lues)} ALERTE(S) MÉTÉO ACTIVE(S)**\n"
                response += "Tapez 'alertes' pour consulter les détails.\n\n"
            
            response += "Je peux vous aider avec :\n\n"
            response += "🌤️  La météo de votre région\n"
            response += "🌱  Les périodes de plantation\n"
            response += "🌾  Les périodes de récolte\n"
            response += "🐛  Les maladies et traitements\n"
            response += "💡  Les conseils de culture\n"
            response += "🚨  Les alertes météo\n\n"
            response += "**Exemple de questions :**\n"
            response += "• \"Quelle est la météo au Nord ?\"\n"
            response += "• \"Quand planter le maïs ?\"\n"
            response += "• \"Y a-t-il des alertes météo ?\"\n"
            response += "• \"Comment traiter les parasites du coton ?\""
            
            suggestions = ['Météo aujourd\'hui', 'Calendrier de plantation', 'Conseils de culture']
            if has_alertes:
                suggestions = ['Voir les alertes'] + suggestions
            
            return {
                'response': response, 
                'suggestions': suggestions,
                'has_alerts': has_alertes
            }
        
        # Détection de demande d'alertes
        if any(keyword in message_lower for keyword in alerte_keywords):
            return self.handle_alerte(None, sentiment)
        
        # Pour les autres questions hors sujet
        response = "Je suis désolé, je ne peux répondre qu'aux questions concernant :\n\n"
        response += "🌤️  La météo agricole\n"
        response += "🌱  Les périodes de plantation\n"
        response += "🌾  Les périodes de récolte\n"
        response += "🐛  Les maladies des cultures\n"
        response += "💡  Les conseils de culture\n"
        response += "🚨  Les alertes météo\n\n"
        
        if has_alertes:
            response += f"💡 **Astuce :** Il y a {len(alertes_non_lues)} alerte(s) active(s). Tapez 'alertes' pour les consulter.\n\n"
        
        response += "Pourriez-vous reformuler votre question sur l'un de ces sujets ?"
        
        suggestions = ['Météo aujourd\'hui', 'Quand planter le maïs ?', 'Maladies du coton']
        if has_alertes:
            suggestions = ['Voir les alertes'] + suggestions
        
        return {
            'response': response, 
            'suggestions': suggestions,
            'has_alerts': has_alertes
        }

    def handle_error(self, error_message):
        """Gère les erreurs"""
        return {
            'response': f"❌ Une erreur s'est produite : {error_message}\n\nVeuillez réessayer ou reformuler votre question.",
            'error': True,
            'suggestions': ['Météo aujourd\'hui', 'Calendrier de plantation', 'Vérifier alertes']
        }