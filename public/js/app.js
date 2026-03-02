// Marketplace App - JavaScript

const API_BASE = ''; // Same origin

// ==================== Auth ====================

async function register(username, email, password, fullName) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, full_name: fullName })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    return data;
}

async function login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    return data;
}

async function getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    return res.json();
}

async function updateProfile(data) {
    const res = await fetch(`${API_BASE}/auth/me`, {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(data)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Update failed');
    return result;
}

async function requestPasswordReset(email) {
    const res = await fetch(`${API_BASE}/auth/password-reset/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    return res.json();
}

async function confirmPasswordReset(token, newPassword) {
    const res = await fetch(`${API_BASE}/auth/password-reset/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Reset failed');
    return data;
}

// ==================== Items ====================

async function getCategories() {
    const res = await fetch(`${API_BASE}/items/categories`);
    return res.json();
}

async function getItems(category = null, limit = 20, offset = 0) {
    let url = `${API_BASE}/items?limit=${limit}&offset=${offset}`;
    if (category) url += `&category=${category}`;
    const res = await fetch(url);
    return res.json();
}

async function searchItems(params) {
    const res = await fetch(`${API_BASE}/items/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    });
    return res.json();
}

async function getItem(id) {
    const res = await fetch(`${API_BASE}/items/${id}`);
    if (!res.ok) throw new Error('Item not found');
    return res.json();
}

async function createItem(itemData) {
    const res = await fetch(`${API_BASE}/items/`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(itemData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Create failed');
    return data;
}

async function updateItem(id, itemData) {
    const res = await fetch(`${API_BASE}/items/${id}`, {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(itemData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Update failed');
    return data;
}

async function deleteItem(id) {
    const res = await fetch(`${API_BASE}/items/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Delete failed');
    }
}

async function uploadImages(files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }
    
    const res = await fetch(`${API_BASE}/items/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    return data;
}

// ==================== Transactions ====================

async function createTransaction(itemId, agreedPrice, note = '') {
    const res = await fetch(`${API_BASE}/transactions/`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ 
            item_id: itemId, 
            agreed_price: agreedPrice,
            note
        })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Create transaction failed');
    return data;
}

async function getMyTransactions(role = 'buyer') {
    const res = await fetch(`${API_BASE}/transactions/my?role=${role}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    return res.json();
}

async function getTransaction(id) {
    const res = await fetch(`${API_BASE}/transactions/${id}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    return res.json();
}

async function confirmTransaction(id) {
    const res = await fetch(`${API_BASE}/transactions/${id}/confirm`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Confirm failed');
    return data;
}

async function completeTransaction(id) {
    const res = await fetch(`${API_BASE}/transactions/${id}/complete`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Complete failed');
    return data;
}

async function cancelTransaction(id) {
    const res = await fetch(`${API_BASE}/transactions/${id}/cancel`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Cancel failed');
    return data;
}

// ==================== Chat ====================

async function createChatRoom(itemId) {
    const res = await fetch(`${API_BASE}/chat/rooms`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ item_id: itemId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Create chat failed');
    return data;
}

async function getChatRooms() {
    const res = await fetch(`${API_BASE}/chat/rooms`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    return res.json();
}

async function getMessages(roomId, limit = 50, offset = 0) {
    const res = await fetch(`${API_BASE}/chat/rooms/${roomId}/messages?limit=${limit}&offset=${offset}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    return res.json();
}

async function sendMessage(roomId, content, messageType = 'text') {
    const res = await fetch(`${API_BASE}/chat/rooms/${roomId}/messages`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ 
            room_id: roomId,
            content,
            message_type: messageType
        })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Send failed');
    return data;
}

// ==================== Utils ====================

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function isLoggedIn() {
    return !!getToken();
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function formatPrice(price) {
    return `$${parseFloat(price).toFixed(2)}`;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff/60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff/3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff/86400000)}d ago`;
    
    return date.toLocaleDateString();
}

function getCategoryLabel(category) {
    const labels = {
        'electronics': 'Electronics',
        'clothing': 'Clothing',
        'furniture': 'Furniture',
        'books': 'Books',
        'sports': 'Sports',
        'games': 'Games',
        'other': 'Other'
    };
    return labels[category] || category;
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// WebSocket connection
let ws = null;
let wsCallbacks = {};

function connectWebSocket(roomId, onMessage, onConnect, onDisconnect) {
    const token = getToken();
    if (!token) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}?token=${token}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        if (onConnect) onConnect();
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (onMessage) onMessage(data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (onDisconnect) onDisconnect();
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    return ws;
}

function sendWsMessage(content, messageType = 'text') {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ content, type: messageType }));
    }
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

// Image compression
async function compressImage(file, maxWidth = 1200, quality = 0.7) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
