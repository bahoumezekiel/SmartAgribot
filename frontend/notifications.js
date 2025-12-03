// Configuration de l'API
const API_BASE = 'http://localhost:5000/api';

// Éléments DOM pour les notifications
const notificationToggle = document.getElementById('notification-toggle');
const notificationPanel = document.getElementById('notification-panel');
const notificationBadge = document.getElementById('notification-badge');
const notificationList = document.getElementById('notification-list');
const notificationEmpty = document.getElementById('notification-empty');
const notificationOverlay = document.getElementById('notification-overlay');
const markAllReadBtn = document.getElementById('mark-all-read');
const refreshAlertsBtn = document.getElementById('refresh-alerts');

// État des notifications
let notifications = [];
let isNotificationPanelOpen = false;

// Initialisation des notifications
document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
});

function initializeNotifications() {
    // Charger les alertes au démarrage
    loadNotifications();
    
    // Événements
    notificationToggle.addEventListener('click', toggleNotificationPanel);
    notificationOverlay.addEventListener('click', closeNotificationPanel);
    markAllReadBtn.addEventListener('click', markAllAsRead);
    refreshAlertsBtn.addEventListener('click', loadNotifications);
    
    // Fermer le panneau en cliquant à l'extérieur
    document.addEventListener('click', function(event) {
        if (isNotificationPanelOpen && 
            !notificationPanel.contains(event.target) && 
            !notificationToggle.contains(event.target)) {
            closeNotificationPanel();
        }
    });
    
    // Recharger les notifications toutes les 2 minutes
    setInterval(loadNotifications, 120000);
    
    // Vérifier les nouvelles alertes toutes les 30 secondes
    setInterval(checkNewAlerts, 30000);
}

// Fonction pour basculer l'affichage du panneau de notifications
function toggleNotificationPanel(event) {
    event.stopPropagation();
    
    if (isNotificationPanelOpen) {
        closeNotificationPanel();
    } else {
        openNotificationPanel();
    }
}

function openNotificationPanel() {
    notificationPanel.classList.add('active');
    notificationOverlay.classList.add('active');
    isNotificationPanelOpen = true;
    
    // Recharger les notifications à l'ouverture
    loadNotifications();
}

function closeNotificationPanel() {
    notificationPanel.classList.remove('active');
    notificationOverlay.classList.remove('active');
    isNotificationPanelOpen = false;
}

// Fonction pour charger les notifications
async function loadNotifications() {
    try {
        const response = await fetch(`${API_BASE}/alertes?non_lues_seulement=true`);
        const data = await response.json();
        
        if (data.success) {
            notifications = data.alertes || [];
            updateNotificationDisplay();
            updateNotificationBadge();
        } else {
            console.error('Erreur chargement alertes:', data.error);
        }
    } catch (error) {
        console.error('Erreur réseau:', error);
        showNotificationError();
    }
}

// Fonction pour vérifier les nouvelles alertes (sans ouvrir le panneau)
async function checkNewAlerts() {
    try {
        const response = await fetch(`${API_BASE}/alertes/statistiques`);
        const data = await response.json();
        
        if (data.success) {
            const newCount = data.statistiques.alertes_non_lues || 0;
            const currentCount = parseInt(notificationBadge.textContent) || 0;
            
            // Si nouvelles alertes, mettre à jour le badge
            if (newCount > currentCount) {
                updateNotificationBadge(newCount);
                
                // Afficher une notification toast si de nouvelles alertes
                if (newCount > currentCount && !isNotificationPanelOpen) {
                    showNewAlertToast(newCount - currentCount);
                }
            }
        }
    } catch (error) {
        console.error('Erreur vérification nouvelles alertes:', error);
    }
}

// Fonction pour mettre à jour l'affichage des notifications
function updateNotificationDisplay() {
    if (notifications.length === 0) {
        notificationList.style.display = 'none';
        notificationEmpty.style.display = 'block';
        return;
    }
    
    notificationEmpty.style.display = 'none';
    notificationList.style.display = 'block';
    
    let html = '';
    notifications.forEach(notification => {
        const iconClass = getNotificationIconClass(notification.type);
        const timeAgo = getTimeAgo(notification.timestamp);
        const isUnread = !notification.est_lue;
        
        html += `
            <div class="notification-item ${isUnread ? 'unread' : ''}" data-id="${notification.id}">
                <div class="notification-icon-type ${iconClass}">
                    <i class="${getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.titre}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
            </div>
        `;
    });
    
    notificationList.innerHTML = html;
    
    // Ajouter les événements de clic
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-id');
            markAsRead(notificationId);
            // Optionnel: rediriger vers le chat avec un message sur les alertes
            if (window.location.pathname.includes('chat.html')) {
                // Déjà sur la page chat, on peut envoyer un message automatique
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.value = 'alertes';
                    const sendButton = document.getElementById('send-button');
                    if (sendButton) sendButton.click();
                }
            } else {
                // Rediriger vers le chat
                window.location.href = 'chat.html';
            }
            closeNotificationPanel();
        });
    });
}

// Fonction pour mettre à jour le badge de notification
function updateNotificationBadge(count = null) {
    const unreadCount = count !== null ? count : notifications.filter(n => !n.est_lue).length;
    
    if (unreadCount > 0) {
        notificationBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        notificationBadge.style.display = 'flex';
        
        // Animation de pulsation pour nouvelles alertes
        if (unreadCount > 0) {
            notificationBadge.style.animation = 'pulse 2s infinite';
        }
    } else {
        notificationBadge.style.display = 'none';
        notificationBadge.style.animation = 'none';
    }
}

// Fonction pour marquer une notification comme lue
async function markAsRead(notificationId) {
    try {
        const response = await fetch(`${API_BASE}/alertes/${notificationId}/marquer-lue`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Mettre à jour localement
            const notification = notifications.find(n => n.id == notificationId);
            if (notification) {
                notification.est_lue = true;
            }
            updateNotificationDisplay();
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('Erreur marquage comme lu:', error);
    }
}

// Fonction pour marquer toutes les notifications comme lues
async function markAllAsRead() {
    try {
        const response = await fetch(`${API_BASE}/alertes/marquer-toutes-lues`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            // Mettre à jour localement
            notifications.forEach(notification => {
                notification.est_lue = true;
            });
            updateNotificationDisplay();
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('Erreur marquage tout comme lu:', error);
    }
}

// Fonctions utilitaires
function getNotificationIcon(type) {
    const icons = {
        'secheresse': 'fas fa-sun',
        'inondation': 'fas fa-cloud-rain',
        'vent_violent': 'fas fa-wind',
        'froid_intense': 'fas fa-snowflake',
        'default': 'fas fa-exclamation-triangle'
    };
    return icons[type] || icons.default;
}

function getNotificationIconClass(type) {
    const classes = {
        'secheresse': 'notification-drought',
        'inondation': 'notification-flood',
        'vent_violent': 'notification-storm',
        'froid_intense': 'notification-temperature',
        'default': 'notification-general'
    };
    return classes[type] || classes.default;
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);
    
    if (diffInSeconds < 60) {
        return 'À l\'instant';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `Il y a ${minutes} min`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `Il y a ${hours} h`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `Il y a ${days} j`;
    }
}

function showNotificationError() {
    notificationList.innerHTML = `
        <div class="notification-item">
            <div class="notification-content">
                <div class="notification-title">Erreur de connexion</div>
                <div class="notification-message">Impossible de charger les alertes</div>
            </div>
        </div>
    `;
}

function showNewAlertToast(newAlertCount) {
    // Créer un toast notification
    const toast = document.createElement('div');
    toast.className = 'notification-toast';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-bell"></i>
            <span>${newAlertCount} nouvelle(s) alerte(s) météo</span>
        </div>
    `;
    
    // Styles pour le toast
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: var(--primary-color);
        color: white;
        padding: 12px 20px;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        cursor: pointer;
        max-width: 300px;
    `;
    
    document.body.appendChild(toast);
    
    // Fermer automatiquement après 5 secondes
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
    
    // Fermer au clic
    toast.addEventListener('click', function() {
        openNotificationPanel();
        if (this.parentNode) {
            this.parentNode.removeChild(this);
        }
    });
}

// Exposer les fonctions globalement pour un usage externe
window.notificationManager = {
    loadNotifications,
    markAllAsRead,
    openNotificationPanel,
    closeNotificationPanel
};