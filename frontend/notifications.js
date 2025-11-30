// notifications.js - Gestion des alertes météo
const API_BASE = 'http://localhost:5000/api';

class NotificationManager {
    constructor() {
        this.notifications = JSON.parse(localStorage.getItem('smartagribot_notifications')) || [];
        this.unreadCount = this.notifications.filter(n => !n.read).length;
        this.init();
    }

    init() {
        this.updateBadge();
        this.loadNotifications();
        this.setupEventListeners();
        
        // Vérifier les nouvelles alertes toutes les 30 minutes
        setInterval(() => this.checkWeatherAlerts(), 30 * 60 * 1000);
        
        // Vérifier immédiatement au chargement
        this.checkWeatherAlerts();
    }

    setupEventListeners() {
        // Toggle du panneau de notifications
        const notificationToggle = document.getElementById('notification-toggle');
        if (notificationToggle) {
            notificationToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotificationPanel();
            });
        }

        // Marquer tout comme lu
        const markAllRead = document.getElementById('mark-all-read');
        if (markAllRead) {
            markAllRead.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }

        // Effacer toutes les notifications
        const clearNotifications = document.getElementById('clear-notifications');
        if (clearNotifications) {
            clearNotifications.addEventListener('click', () => {
                this.clearAllNotifications();
            });
        }

        // Fermer le panneau en cliquant à l'extérieur
        const overlay = document.getElementById('notification-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.hideNotificationPanel();
            });
        }

        // Fermer le panneau en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-container')) {
                this.hideNotificationPanel();
            }
        });
    }

    toggleNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        const overlay = document.getElementById('notification-overlay');
        
        if (panel && overlay) {
            panel.classList.toggle('active');
            overlay.classList.toggle('active');
        }
    }

    hideNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        const overlay = document.getElementById('notification-overlay');
        
        if (panel && overlay) {
            panel.classList.remove('active');
            overlay.classList.remove('active');
        }
    }

    async checkWeatherAlerts() {
        try {
            // Récupérer les données météo de toutes les régions
            const response = await fetch(`${API_BASE}/meteo/all`);
            const data = await response.json();

            if (data.success) {
                this.analyzeWeatherData(data.data);
            }
        } catch (error) {
            console.error('Erreur lors de la vérification des alertes:', error);
        }
    }

    analyzeWeatherData(weatherData) {
        const newAlerts = [];

        Object.keys(weatherData).forEach(regionId => {
            const weather = weatherData[regionId];
            const regionName = weather.region;
            
            // Détection des risques d'inondation
            if (this.detectFloodRisk(weather)) {
                newAlerts.push(this.createAlert(
                    'inondation',
                    `🌧️ Risque d'inondation - ${regionName}`,
                    `Fortes précipitations détectées dans la région ${regionName}. Préparez vos cultures.`,
                    regionId
                ));
            }

            // Détection des risques de sécheresse
            if (this.detectDroughtRisk(weather)) {
                newAlerts.push(this.createAlert(
                    'secheresse',
                    `☀️ Risque de sécheresse - ${regionName}`,
                    `Faible humidité et températures élevées détectées dans la région ${regionName}. Pensez à l'irrigation.`,
                    regionId
                ));
            }

            // Détection des tempêtes
            if (this.detectStormRisk(weather)) {
                newAlerts.push(this.createAlert(
                    'tempete',
                    `🌪️ Conditions orageuses - ${regionName}`,
                    `Vents forts et conditions instables détectés dans la région ${regionName}. Protégez vos cultures.`,
                    regionId
                ));
            }

            // Alertes de température extrême
            if (this.detectExtremeTemperature(weather)) {
                newAlerts.push(this.createAlert(
                    'temperature',
                    `🌡️ Température extrême - ${regionName}`,
                    `Températures ${weather.temperature > 35 ? 'élevées' : 'basses'} détectées. Adaptez vos pratiques culturales.`,
                    regionId
                ));
            }
        });

        // Ajouter les nouvelles alertes
        newAlerts.forEach(alert => this.addNotification(alert));
    }

    detectFloodRisk(weather) {
        // Logique de détection d'inondation
        return weather.humidite > 85 && 
               weather.description.toLowerCase().includes('pluie');
    }

    detectDroughtRisk(weather) {
        // Logique de détection de sécheresse
        return weather.humidite < 30 && 
               weather.temperature > 35 &&
               !weather.description.toLowerCase().includes('pluie');
    }

    detectStormRisk(weather) {
        // Logique de détection de tempête
        return weather.vent > 8 && 
               (weather.description.toLowerCase().includes('orage') || 
                weather.description.toLowerCase().includes('tempête'));
    }

    detectExtremeTemperature(weather) {
        // Logique de détection de température extrême
        return weather.temperature > 38 || weather.temperature < 10;
    }

    createAlert(type, title, message, regionId) {
        return {
            id: Date.now() + Math.random(),
            type: type,
            title: title,
            message: message,
            regionId: regionId,
            timestamp: new Date().toISOString(),
            read: false,
            priority: this.getAlertPriority(type)
        };
    }

    getAlertPriority(type) {
        const priorities = {
            'inondation': 'high',
            'tempete': 'high', 
            'secheresse': 'medium',
            'temperature': 'medium'
        };
        return priorities[type] || 'low';
    }

    addNotification(notification) {
        // Vérifier si une notification similaire existe déjà (éviter les doublons)
        const similarExists = this.notifications.some(n => 
            n.type === notification.type && 
            n.regionId === notification.regionId &&
            this.isRecent(n.timestamp)
        );

        if (!similarExists) {
            this.notifications.unshift(notification);
            this.unreadCount++;
            this.saveToStorage();
            this.updateBadge();
            this.loadNotifications();
            
            // Afficher une notification toast pour les alertes importantes
            if (notification.priority === 'high') {
                this.showToast(notification);
            }
        }
    }

    isRecent(timestamp) {
        const notificationTime = new Date(timestamp);
        const now = new Date();
        return (now - notificationTime) < 2 * 60 * 60 * 1000; // 2 heures
    }

    showToast(notification) {
        // Créer un toast notification
        const toast = document.createElement('div');
        toast.className = `notification-toast ${notification.type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <strong>${notification.title}</strong>
                <p>${notification.message}</p>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 350px;
            border-left: 4px solid ${this.getAlertColor(notification.type)};
            display: flex;
            align-items: flex-start;
            gap: 10px;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(toast);

        // Fermer le toast après 5 secondes
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);

        // Fermer au clic
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
    }

    getAlertColor(type) {
        const colors = {
            'inondation': '#2196f3',
            'secheresse': '#ff9800',
            'tempete': '#9c27b0',
            'temperature': '#f44336'
        };
        return colors[type] || '#666';
    }

    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.unreadCount--;
            this.saveToStorage();
            this.updateBadge();
            this.loadNotifications();
        }
    }

    markAllAsRead() {
        this.notifications.forEach(notification => {
            if (!notification.read) {
                notification.read = true;
            }
        });
        this.unreadCount = 0;
        this.saveToStorage();
        this.updateBadge();
        this.loadNotifications();
    }

    clearAllNotifications() {
        if (confirm('Voulez-vous vraiment effacer toutes les notifications ?')) {
            this.notifications = [];
            this.unreadCount = 0;
            this.saveToStorage();
            this.updateBadge();
            this.loadNotifications();
        }
    }

    loadNotifications() {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;
        
        if (this.notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>Aucune alerte pour le moment</p>
                </div>
            `;
            return;
        }

        let html = '';
        this.notifications.forEach(notification => {
            const timeAgo = this.getTimeAgo(notification.timestamp);
            const iconClass = this.getIconClass(notification.type);
            
            html += `
                <div class="notification-item ${notification.read ? '' : 'unread'}" 
                     data-id="${notification.id}">
                    <div class="notification-icon-type ${this.getTypeClass(notification.type)}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        });

        notificationList.innerHTML = html;

        // Ajouter les événements de clic
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = parseFloat(item.getAttribute('data-id'));
                this.markAsRead(notificationId);
                this.hideNotificationPanel();
            });
        });
    }

    getTypeClass(type) {
        const classes = {
            'inondation': 'notification-flood',
            'secheresse': 'notification-drought',
            'tempete': 'notification-storm',
            'temperature': 'notification-temperature'
        };
        return classes[type] || 'notification-general';
    }

    getIconClass(type) {
        const icons = {
            'inondation': 'fas fa-cloud-showers-heavy',
            'secheresse': 'fas fa-sun',
            'tempete': 'fas fa-wind',
            'temperature': 'fas fa-thermometer-half'
        };
        return icons[type] || 'fas fa-info-circle';
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInMinutes = Math.floor((now - time) / (1000 * 60));
        
        if (diffInMinutes < 1) return 'À l\'instant';
        if (diffInMinutes < 60) return `Il y a ${diffInMinutes} min`;
        if (diffInMinutes < 1440) return `Il y a ${Math.floor(diffInMinutes / 60)} h`;
        return `Il y a ${Math.floor(diffInMinutes / 1440)} j`;
    }

    updateBadge() {
        const badge = document.getElementById('notification-count');
        if (!badge) return;
        
        badge.textContent = this.unreadCount;
        
        if (this.unreadCount === 0) {
            badge.style.display = 'none';
        } else {
            badge.style.display = 'flex';
            
            // Animation du badge pour les nouvelles notifications
            if (this.unreadCount > 0) {
                badge.style.animation = 'pulse 1s infinite';
            }
        }
    }

    saveToStorage() {
        localStorage.setItem('smartagribot_notifications', JSON.stringify(this.notifications));
    }
}

// Initialisation
let notificationManager;

document.addEventListener('DOMContentLoaded', function() {
    notificationManager = new NotificationManager();
});