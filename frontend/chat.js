// Configuration de l'API
const API_BASE = 'http://localhost:5000/api';

// Éléments DOM
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const suggestions = document.getElementById('suggestions');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history');
const menuToggle = document.getElementById('menu-toggle');
const chatSidebar = document.getElementById('chat-sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

// Éléments DOM pour les notifications (dans le chat)
const notificationToggle = document.getElementById('notification-toggle');
const notificationPanel = document.getElementById('notification-panel');
const notificationBadge = document.getElementById('notification-badge');
const notificationList = document.getElementById('notification-list');
const notificationEmpty = document.getElementById('notification-empty');
const notificationOverlay = document.getElementById('notification-overlay');
const markAllReadBtn = document.getElementById('mark-all-read');
const refreshAlertsBtn = document.getElementById('refresh-alerts');

// Contexte utilisateur
let userContext = {
    default_region_id: null,
    last_culture: null
};

// Historique des questions
let questionHistory = JSON.parse(localStorage.getItem('smartagribot_history')) || [];

// État des notifications
let notifications = [];
let isNotificationPanelOpen = false;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Charger l'historique
    loadHistory();
    
    // Initialiser les notifications
    initializeNotifications();
    
    // Événements
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Questions rapides
    document.querySelectorAll('.quick-question, .suggestion-btn').forEach(button => {
        button.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            messageInput.value = question;
            sendMessage();
        });
    });
    
    // Effacer l'historique
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Menu mobile
    menuToggle.addEventListener('click', function() {
        chatSidebar.classList.toggle('active');
    });
    
    // Toggle sidebar (bouton dans la sidebar)
    sidebarToggle.addEventListener('click', function() {
        chatSidebar.classList.toggle('closed');
        sidebarToggle.classList.toggle('sidebar-closed');
        
        // Changer l'icône
        const icon = sidebarToggle.querySelector('i');
        if (chatSidebar.classList.contains('closed')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-chevron-right');
        } else {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-bars');
        }
    });
    
    // Fermer le menu en cliquant à l'extérieur (mobile)
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768 && 
            !chatSidebar.contains(event.target) && 
            !menuToggle.contains(event.target)) {
            chatSidebar.classList.remove('active');
        }
    });
});

// Fonction pour initialiser les notifications dans le chat
function initializeNotifications() {
    // Charger les alertes au démarrage
    loadNotifications();
    
    // Événements pour les notifications
    if (notificationToggle) {
        notificationToggle.addEventListener('click', toggleNotificationPanel);
    }
    if (notificationOverlay) {
        notificationOverlay.addEventListener('click', closeNotificationPanel);
    }
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllAsRead);
    }
    if (refreshAlertsBtn) {
        refreshAlertsBtn.addEventListener('click', loadNotifications);
    }
    
    // Fermer le panneau en cliquant à l'extérieur
    document.addEventListener('click', function(event) {
        if (isNotificationPanelOpen && 
            notificationPanel && 
            !notificationPanel.contains(event.target) && 
            notificationToggle && 
            !notificationToggle.contains(event.target)) {
            closeNotificationPanel();
        }
    });
    
    // Recharger les notifications toutes les 2 minutes
    setInterval(loadNotifications, 120000);
    
    // Vérifier les nouvelles alertes toutes les 30 secondes
    setInterval(checkNewAlerts, 30000);
}

// Fonction pour envoyer un message
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Ajouter le message de l'utilisateur à l'interface
    addMessage(message, 'user');
    
    // Sauvegarder dans l'historique
    saveToHistory(message);
    
    // Effacer le champ de saisie
    messageInput.value = '';
    
    // Afficher l'indicateur de frappe
    showTypingIndicator();
    
    try {
        // Envoyer la requête à l'API
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                context: userContext
            })
        });
        
        const data = await response.json();
        
        // Supprimer l'indicateur de frappe
        removeTypingIndicator();
        
        if (data.success) {
            // Afficher la réponse du bot
            addMessage(data.response, 'bot');
            
            // Mettre à jour les suggestions
            updateSuggestions(data.suggestions);
            
            // Mettre à jour le contexte si nécessaire
            if (data.data && data.data.culture) {
                userContext.last_culture = data.data.culture.id_culture;
            }
            
            // Si la réponse contient des alertes, mettre à jour les notifications
            if (data.data && data.data.alertes) {
                loadNotifications();
            }
            
            // Si le message concerne les alertes, ouvrir le panneau
            if (message.toLowerCase().includes('alerte') || message.toLowerCase().includes('notification')) {
                setTimeout(() => {
                    openNotificationPanel();
                }, 500);
            }
        } else {
            addMessage(`❌ Désolé, une erreur s'est produite: ${data.error}`, 'bot');
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage(`❌ Erreur de connexion: ${error.message}`, 'bot');
        console.error('Erreur:', error);
    }
}

// Fonction pour ajouter un message à l'interface
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    if (sender === 'user') {
        avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
    } else {
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Formater le texte avec sauts de ligne
    const formattedText = formatMessage(text);
    contentDiv.innerHTML = formattedText;
    
    // Ajouter l'heure
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    contentDiv.appendChild(timeDiv);
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Faire défiler vers le bas
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fonction pour formater le message (gérer les sauts de ligne)
function formatMessage(text) {
    return text.replace(/\n/g, '<br>');
}

// Fonction pour afficher l'indicateur de frappe
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typing-indicator';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content typing-indicator';
    
    const dotContainer = document.createElement('div');
    dotContainer.className = 'typing-dots';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        dotContainer.appendChild(dot);
    }
    
    contentDiv.appendChild(dotContainer);
    typingDiv.appendChild(avatarDiv);
    typingDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fonction pour supprimer l'indicateur de frappe
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Fonction pour mettre à jour les suggestions
function updateSuggestions(suggestionList) {
    if (!suggestionList || suggestionList.length === 0) {
        suggestions.innerHTML = '';
        return;
    }
    
    let html = '';
    suggestionList.forEach(suggestion => {
        // Ajouter des icônes selon le type de suggestion
        let icon = 'fas fa-lightbulb';
        if (suggestion.includes('Météo')) icon = 'fas fa-cloud-sun';
        if (suggestion.includes('plantation')) icon = 'fas fa-seedling';
        if (suggestion.includes('Maladies')) icon = 'fas fa-bug';
        if (suggestion.includes('Conseils')) icon = 'fas fa-lightbulb';
        if (suggestion.includes('Alerte')) icon = 'fas fa-bell';
        
        html += `<button class="suggestion-btn" data-question="${suggestion}">
                    <i class="${icon}"></i> ${suggestion}
                 </button>`;
    });
    
    suggestions.innerHTML = html;
    
    // Réattacher les événements
    document.querySelectorAll('.suggestion-btn').forEach(button => {
        button.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            messageInput.value = question;
            sendMessage();
        });
    });
}

// Fonction pour sauvegarder dans l'historique
function saveToHistory(question) {
    // Limiter l'historique à 20 questions
    if (questionHistory.length >= 20) {
        questionHistory.shift();
    }
    
    questionHistory.push({
        question: question,
        timestamp: new Date().toISOString()
    });
    
    localStorage.setItem('smartagribot_history', JSON.stringify(questionHistory));
    loadHistory();
}

// Fonction pour charger l'historique
function loadHistory() {
    if (questionHistory.length === 0) {
        historyList.innerHTML = '<div class="history-item" style="text-align: center; color: var(--text-light);">Aucune question posée</div>';
        return;
    }
    
    let html = '';
    // Afficher les 10 dernières questions (les plus récentes en premier)
    const recentHistory = [...questionHistory].reverse().slice(0, 10);
    
    recentHistory.forEach(item => {
        const date = new Date(item.timestamp);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Tronquer les questions trop longues
        const shortQuestion = item.question.length > 50 
            ? item.question.substring(0, 47) + '...' 
            : item.question;
            
        html += `
            <div class="history-item" data-question="${item.question}">
                <div class="question">${shortQuestion}</div>
                <div class="timestamp">${formattedDate}</div>
            </div>
        `;
    });
    
    historyList.innerHTML = html;
    
    // Ajouter les événements de clic
    document.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            messageInput.value = question;
            sendMessage();
            // Fermer le menu sur mobile après sélection
            if (window.innerWidth <= 768) {
                chatSidebar.classList.remove('active');
            }
        });
    });
}

// Fonction pour effacer l'historique
function clearHistory() {
    if (confirm('Voulez-vous vraiment effacer tout l\'historique des questions ?')) {
        questionHistory = [];
        localStorage.removeItem('smartagribot_history');
        loadHistory();
    }
}

// ==================== FONCTIONS DE NOTIFICATION ====================

// Fonction pour basculer l'affichage du panneau de notifications
function toggleNotificationPanel(event) {
    if (event) event.stopPropagation();
    
    if (isNotificationPanelOpen) {
        closeNotificationPanel();
    } else {
        openNotificationPanel();
    }
}

function openNotificationPanel() {
    if (!notificationPanel) return;
    
    notificationPanel.classList.add('active');
    if (notificationOverlay) notificationOverlay.classList.add('active');
    isNotificationPanelOpen = true;
    
    // Recharger les notifications à l'ouverture
    loadNotifications();
}

function closeNotificationPanel() {
    if (!notificationPanel) return;
    
    notificationPanel.classList.remove('active');
    if (notificationOverlay) notificationOverlay.classList.remove('active');
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
            showNotificationError();
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
            const currentCount = parseInt(notificationBadge?.textContent) || 0;
            
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
    if (!notificationList || !notificationEmpty) return;
    
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
            
            // Envoyer un message au chatbot sur les alertes
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.value = 'alertes';
                setTimeout(() => {
                    sendMessage();
                }, 100);
            }
            
            closeNotificationPanel();
        });
    });
}

// Fonction pour mettre à jour le badge de notification
function updateNotificationBadge(count = null) {
    if (!notificationBadge) return;
    
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

// Fonctions utilitaires pour les notifications
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
    if (!notificationList) return;
    
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

// Vérifier s'il y a des alertes au chargement de la page
setTimeout(() => {
    loadNotifications();
}, 1000);