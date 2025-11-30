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

// Contexte utilisateur
let userContext = {
    default_region_id: null,
    last_culture: null
};

// Historique des questions
let questionHistory = JSON.parse(localStorage.getItem('smartagribot_history')) || [];

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Charger l'historique
    loadHistory();
    
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