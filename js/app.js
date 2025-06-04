/**
 * OIOIO AI - Main Application
 * A modern AI chat interface with modular architecture
 */

class OIOIOApp {
    constructor() {
        this.messages = [];
        this.isTyping = false;
        this.currentConversationId = null;
        
        // Configuration
        this.config = {
            maxMessageLength: 4000,
            typingDelay: 1000,
            apiEndpoint: null, // Will be set when user configures
            welcomeMessages: [
                "Hello! I'm OIOIO AI, your intelligent assistant.",
                "I'm here to help you with various tasks and answer your questions.",
                "To get started, you can type a message below or try one of the quick actions."
            ]
        };
        
        // DOM elements
        this.elements = {};
        
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.bindEvents();
        this.setupWelcomeScreen();
        this.loadConversationHistory();
    }
    
    cacheElements() {
        this.elements = {
            chatContainer: document.getElementById('chat-container'),
            chatMessages: document.getElementById('chat-messages'),
            chatInput: document.getElementById('chat-input'),
            sendButton: document.getElementById('send-button'),
            chatForm: document.getElementById('chat-form'),
            welcomeScreen: document.getElementById('welcome-screen'),
            statusIndicator: document.getElementById('status-indicator'),
            chatStatus: document.getElementById('chat-status'),
            quickActions: document.querySelectorAll('.quick-action')
        };
    }
    
    bindEvents() {
        // Form submission
        this.elements.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendMessage();
        });
        
        // Input handling
        this.elements.chatInput.addEventListener('input', () => {
            this.handleInputResize();
        });
        
        this.elements.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Quick actions
        this.elements.quickActions.forEach(action => {
            action.addEventListener('click', () => {
                const message = action.textContent;
                this.elements.chatInput.value = message;
                this.handleSendMessage();
            });
        });
        
        // Auto-scroll handling
        this.elements.chatMessages.addEventListener('scroll', () => {
            this.handleScroll();
        });
    }
    
    setupWelcomeScreen() {
        if (this.messages.length === 0) {
            this.showWelcomeScreen();
        }
    }
    
    showWelcomeScreen() {
        this.elements.welcomeScreen.classList.remove('hidden');
        this.elements.chatContainer.classList.add('hidden');
    }
    
    hideWelcomeScreen() {
        this.elements.welcomeScreen.classList.add('hidden');
        this.elements.chatContainer.classList.remove('hidden');
    }
    
    handleSendMessage() {
        const message = this.elements.chatInput.value.trim();
        
        if (!message || message.length > this.config.maxMessageLength) {
            this.showError('Message is too long or empty');
            return;
        }
        
        if (this.isTyping) {
            return;
        }
        
        // Hide welcome screen if first message
        if (this.messages.length === 0) {
            this.hideWelcomeScreen();
        }
        
        // Add user message
        this.addMessage('user', message);
        
        // Clear input
        this.elements.chatInput.value = '';
        this.handleInputResize();
        
        // Process AI response
        this.processAIResponse(message);
    }
    
    addMessage(sender, content, timestamp = new Date()) {
        const message = {
            id: this.generateId(),
            sender,
            content,
            timestamp
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        this.saveConversationHistory();
        
        return message;
    }
    
    renderMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}`;
        messageElement.dataset.messageId = message.id;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.textContent = message.content;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = this.formatTime(message.timestamp);
        
        messageElement.appendChild(contentElement);
        messageElement.appendChild(timeElement);
        
        this.elements.chatMessages.appendChild(messageElement);
    }
    
    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        
        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant';
        typingElement.id = 'typing-indicator';
        
        const indicatorContent = document.createElement('div');
        indicatorContent.className = 'typing-indicator';
        indicatorContent.innerHTML = `
            <span>AI is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        typingElement.appendChild(indicatorContent);
        this.elements.chatMessages.appendChild(typingElement);
        this.scrollToBottom();
        
        // Update UI state
        this.elements.sendButton.disabled = true;
        this.updateStatus('AI is responding...');
    }
    
    hideTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
        
        this.isTyping = false;
        this.elements.sendButton.disabled = false;
        this.updateStatus('Ready');
    }
    
    async processAIResponse(userMessage) {
        this.showTypingIndicator();
        
        try {
            // Simulate AI processing time
            await this.delay(this.config.typingDelay + Math.random() * 2000);
            
            // Generate AI response (placeholder - in real implementation would call API)
            const aiResponse = this.generateAIResponse(userMessage);
            
            this.hideTypingIndicator();
            this.addMessage('assistant', aiResponse);
            
        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Failed to get AI response. Please try again.');
            console.error('AI Response Error:', error);
        }
    }
    
    generateAIResponse(userMessage) {
        // Placeholder AI responses - in real implementation would call actual AI API
        const responses = [
            "That's an interesting question! Let me think about that...",
            "I understand what you're asking. Based on my knowledge, I would say...",
            "Great question! Here's what I think about that topic...",
            "I'd be happy to help you with that. Let me provide some information...",
            "That's a complex topic. Let me break it down for you...",
            "I see what you're getting at. Here's my perspective on that...",
            "Thank you for asking! I can definitely help you with that...",
            "That's something I can assist with. Here's what I know about it..."
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        // Add some context based on the user message
        if (userMessage.toLowerCase().includes('hello') || userMessage.toLowerCase().includes('hi')) {
            return "Hello! I'm OIOIO AI, your intelligent assistant. How can I help you today?";
        }
        
        if (userMessage.toLowerCase().includes('help')) {
            return "I'm here to help! I can assist with various tasks like answering questions, providing information, helping with analysis, creative writing, and much more. What would you like to work on?";
        }
        
        if (userMessage.toLowerCase().includes('what') && userMessage.toLowerCase().includes('you')) {
            return "I'm OIOIO AI, an intelligent assistant designed to help with a wide range of tasks. I can answer questions, provide information, help with analysis, assist with creative projects, and engage in meaningful conversations. What would you like to explore together?";
        }
        
        return randomResponse + " " + this.generateContextualResponse(userMessage);
    }
    
    generateContextualResponse(userMessage) {
        const contextualParts = [
            "Based on your message about '" + userMessage.substring(0, 30) + (userMessage.length > 30 ? '...' : '') + "', I can provide more specific guidance if you'd like.",
            "Feel free to ask follow-up questions if you need more details.",
            "Is there a particular aspect of this topic you'd like to explore further?",
            "I'm here to help with any additional questions you might have.",
            "Would you like me to elaborate on any specific part of this?"
        ];
        
        return contextualParts[Math.floor(Math.random() * contextualParts.length)];
    }
    
    handleInputResize() {
        const input = this.elements.chatInput;
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }, 100);
    }
    
    handleScroll() {
        // Optional: Implement scroll-based features like loading older messages
    }
    
    updateStatus(status) {
        this.elements.chatStatus.textContent = status;
    }
    
    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        this.elements.chatMessages.appendChild(errorElement);
        this.scrollToBottom();
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorElement.remove();
        }, 5000);
    }
    
    // Utility methods
    generateId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    formatTime(timestamp) {
        return timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Persistence methods
    saveConversationHistory() {
        try {
            const history = {
                messages: this.messages,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('oioio_chat_history', JSON.stringify(history));
        } catch (error) {
            console.warn('Failed to save conversation history:', error);
        }
    }
    
    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('oioio_chat_history');
            if (saved) {
                const history = JSON.parse(saved);
                if (history.messages && Array.isArray(history.messages)) {
                    // Only load recent messages (last 50)
                    this.messages = history.messages.slice(-50);
                    this.renderExistingMessages();
                }
            }
        } catch (error) {
            console.warn('Failed to load conversation history:', error);
        }
    }
    
    renderExistingMessages() {
        if (this.messages.length > 0) {
            this.hideWelcomeScreen();
            this.messages.forEach(message => {
                message.timestamp = new Date(message.timestamp);
                this.renderMessage(message);
            });
            this.scrollToBottom();
        }
    }
    
    clearHistory() {
        this.messages = [];
        this.elements.chatMessages.innerHTML = '';
        localStorage.removeItem('oioio_chat_history');
        this.showWelcomeScreen();
    }
}

// Utility functions for the application
class AppUtils {
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    static sanitizeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.oioioApp = new OIOIOApp();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OIOIOApp, AppUtils };
}