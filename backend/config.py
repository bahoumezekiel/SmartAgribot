import os

"""
   Ce fichier définit une classe de configuration pour notre application
    Il centralise tous les paramètres importants dont l’application a besoin pour fonctionner.
    De facon globale, il permet de stocker et gérer les réglages essentiels de l’application au même endroit.
"""
class Config:
    """Configuration de l'application"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'e1bedcad3d98e2c2cc55958a6966e2022410b8473e95b4585235d79831c43a10'
    DB_NAME = 'smartAgribot.db'
    OPENWEATHER_API_KEY = 'e6daa01220b0861c5aa37c05de9d2896'  # cle generer sur openweathermap.org
    CACHE_DURATION = 3600  # Cache météo valide 1h
