import spacy
from spacy.matcher import PhraseMatcher
import re
import unicodedata

"""
   Ce fichier définit une classe appelée NLPService qui sert de moteur 
   d'analyse du langage naturel pour notre chatbot agricole.
"""
class NLPService:
    """Service NLP avancé avec gestion des accents"""

    try:
        nlp = spacy.load("fr_core_news_md")
    except OSError:
        print("Modèle SpaCy français non trouvé.")
        print("Installez-le avec : python -m spacy download fr_core_news_md")
        nlp = None

    # Patterns d'intentions améliorés
    INTENTION_PATTERNS = {
        'meteo': [
            r'\b(meteo|temps|temperature|pluie|chaleur|climat|previsions?)\b',
            r'\bfait[- ]il\b',
            r'\bquel\s+(temps|meteo)\b',
            r'\bconditions?\s+(climatiques?|meteo)\b',
        ],
        'plantation': [
            r'\b(planter|semer|semis|plantation|cultiver)\b',
            r'\bquand\s+(?:puis[- ]je\s+)?(?:planter|semer|cultiver)\b',
            r'\bperiode\s+(?:de\s+)?(?:plantation|semis|pour\s+(?:planter|semer|cultiver))\b',
            r'\bmoment\s+(?:pour|de)\s+(?:planter|semer|cultiver)\b',
            r'\bculture\s+d[eu]\b',
            r'\badapter?\s+pour\s+(?:la\s+)?culture\b',
        ],
        'recolte': [
            r'\b(recolter?|recolte|cueillir|ramasser)\b',
            r'\bperiode\s+(?:de\s+)?recolte\b',
            r'\bquand\s+recolter\b',
            r'\bmaturite\b',
        ],
        'maladie': [
            r'\b(maladie|parasite|traiter?|probleme|insecte|ravageur)\b',
            r'\battaque\s+de\b',
            r'\binfection\b',
            r'\bsoigner\b',
            r'\btraitement\s+(?:contre|pour)\b',
        ],
        'conseil': [
            r'\b(conseil|astuce|recommandation|aide|technique|methode)\b',
            r'\bcomment\s+(?:faire|cultiver)\b',
            r'\bbonnes?\s+pratiques?\b',
        ]
    }

    # Dictionnaire des cultures étendu
    CULTURES_DICT = {
        'coton': ['coton', 'cotonnier'],
        'mais': ['mais', 'maiz', 'maïs', 'maïz'],
        'mil': ['mil', 'millet'],
        'soja': ['soja', 'soya'],
        'tomate': ['tomate', 'tomates'],
        'pomme de terre': ['pomme de terre', 'patate', 'pommes de terre']
    }

    def __init__(self):
        if NLPService.nlp:
            self.matcher = PhraseMatcher(NLPService.nlp.vocab, attr="LOWER")

            for culture, variations in self.CULTURES_DICT.items():
                patterns = [
                    NLPService.nlp.make_doc(self.normalize_text(v))
                    for v in variations
                ]
                self.matcher.add(culture, patterns)
        else:
            self.matcher = None

    @staticmethod
    def remove_accents(text):
        """Supprime les accents d'un texte"""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    @staticmethod
    def normalize_text(text):
        """Normalise le texte : minuscules, sans accents, sans ponctuation"""
        text = text.lower()
        text = NLPService.remove_accents(text)
        text = re.sub(r'[^\w\s\-]', ' ', text)
        return text.strip()

    def preprocess_message(self, message):
        """Prétraite le message avant l'analyse"""
        return self.normalize_text(message)

    def detect_intention(self, message):
        """Détecte l'intention principale du message avec scoring"""
        msg = self.normalize_text(message)

        # Système de scoring pour gérer les intentions multiples
        scores = {}
        
        for intention, patterns in self.INTENTION_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, msg)
                score += len(matches)
            
            if score > 0:
                scores[intention] = score
        
        # Si plusieurs intentions détectées, prioriser
        if scores:
            # Ordre de priorité : maladie > plantation > recolte > conseil > meteo
            priority_order = ['maladie', 'plantation', 'recolte', 'conseil', 'meteo']
            
            for priority_intent in priority_order:
                if priority_intent in scores:
                    return priority_intent
            
            # Si aucune priorité, retourner celle avec le meilleur score
            return max(scores, key=scores.get)

        return 'general'

    def extract_culture(self, message):
        """
        Cherche une culture dans le message avec toutes ses variantes
        Retourne : mais, mil, soja, etc.
        """
        msg = self.normalize_text(message)

        # Méthode 1 : Recherche directe avec les variantes
        for culture, variations in self.CULTURES_DICT.items():
            for v in variations:
                v_normalized = self.normalize_text(v)
                # Recherche avec des frontières de mots pour éviter les faux positifs
                pattern = r'\b' + re.escape(v_normalized) + r'\b'
                if re.search(pattern, msg):
                    return culture

        # Méthode 2 : Utiliser le matcher SpaCy si disponible
        if self.matcher and NLPService.nlp:
            doc = NLPService.nlp(msg)
            matches = self.matcher(doc)
            if matches:
                match_id, start, end = matches[0]
                return NLPService.nlp.vocab.strings[match_id]

        return None

    def extract_region(self, message, regions):
        """
        Compare le message avec la liste des régions de la base
        Retourne la région trouvée (objet dict)
        """
        if not regions:
            return None

        msg = self.normalize_text(message)

        # Recherche exacte et partielle
        for region in regions:
            region_nom_normalized = self.normalize_text(region['nom'])
            
            # Recherche exacte
            if region_nom_normalized in msg:
                return region
            
            # Recherche des mots-clés de la région (ex: "centre" pour "Centre Sud")
            region_words = region_nom_normalized.split()
            if all(word in msg for word in region_words):
                return region

        return None

    def extract_entities(self, message):
        """
        Extrait les entités nommées (lieux, dates, etc.)
        Retourne un dict avec les listes d'entités trouvées
        """
        if not NLPService.nlp:
            return {}

        doc = NLPService.nlp(message)
        entities = {'locations': [], 'dates': [], 'orgs': []}

        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:
                entities['locations'].append(ent.text)
            elif ent.label_ == "DATE":
                entities['dates'].append(ent.text)
            elif ent.label_ == "ORG":
                entities['orgs'].append(ent.text)

        return entities

    def analyze_sentiment(self, message):
        """
        Analyse de sentiment basique avec mots-clés
        Détecte si le message est positif, négatif ou neutre
        """
        positive = ['bon', 'excellent', 'merci', 'super', 'bien', 'parfait', 'genial']
        negative = ['probleme', 'urgent', 'mauvais', 'inquiet', 'aide', 'sos', 'grave']

        tokens = self.normalize_text(message).split()

        pos = sum(1 for w in tokens if w in positive)
        neg = sum(1 for w in tokens if w in negative)

        if pos > neg:
            return 'positive'
        elif neg > pos:
            return 'negative'
        return 'neutral'

    def get_message_info(self, message, regions=None):
        """
        Fonction principale : retourne un résumé complet de l'analyse du message
        
        Returns:
            dict: {
                'intention': str,
                'culture': str or None,
                'region': dict or None,
                'entities': dict,
                'sentiment': str
            }
        """
        return {
            'intention': self.detect_intention(message),
            'culture': self.extract_culture(message),
            'region': self.extract_region(message, regions),
            'entities': self.extract_entities(message),
            'sentiment': self.analyze_sentiment(message)
        }