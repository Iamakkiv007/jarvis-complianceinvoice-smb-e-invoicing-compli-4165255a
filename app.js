/**
 * ComplianceInvoice - SMB e-Invoicing Compliance SaaS
 * Multi-Country Mandates Application
 * Main Application Logic
 */

// ============================================================================
// APPLICATION STATE & CONFIGURATION
// ============================================================================

const APP_CONFIG = {
  apiBaseUrl: process.env.API_BASE_URL || 'https://api.complianceinvoice.com',
  version: '1.0.0',
  supportedCountries: ['IT', 'ES', 'FR', 'DE', 'PL', 'NL', 'AT', 'BE', 'CZ', 'DK', 'SE', 'NO', 'FI', 'PT', 'GR', 'RO', 'HU', 'SK', 'SI', 'HR', 'LT', 'LV', 'EE', 'CY', 'LU', 'MT', 'IE', 'GB'],
  mandateTypes: {
    IT: { name: 'Italy', platform: 'SDI', deadline: '2024-01-01', format: 'UBL 2.1' },
    ES: { name: 'Spain', platform: 'FACe', deadline: '2024-06-15', format: 'UBL 2.1' },
    FR: { name: 'France', platform: 'Chorus Pro', deadline: '2024-01-01', format: 'UBL 2.1' },
    DE: { name: 'Germany', platform: 'ZUGFeRD', deadline: '2025-12-31', format: 'ZUGFeRD 2.1' },
    PL: { name: 'Poland', platform: 'JPK', deadline: '2024-07-01', format: 'XML' },
    NL: { name: 'Netherlands', platform: 'eIFU', deadline: '2024-01-01', format: 'UBL 2.1' },
    AT: { name: 'Austria', platform: 'eb-interface', deadline: '2024-01-01', format: 'ebInterface 6.1' },
    BE: { name: 'Belgium', platform: 'e-invoice', deadline: '2024-06-15', format: 'UBL 2.1' },
  }
};

const appState = {
  user: null,
  authenticated: false,
  currentStep: 'dashboard',
  selectedCountries: [],
  invoices: [],
  templates: [],
  apiKeys: [],
  compliance: {},
  notifications: [],
  loading: false,
  errors: []
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

function initializeApp() {
  console.log('Initializing ComplianceInvoice Application v' + APP_CONFIG.version);
  
  setupEventListeners();
  checkAuthentication();
  loadUserPreferences();
  initializeTheme();
}

// ============================================================================
// AUTHENTICATION & USER MANAGEMENT
// ============================================================================

function checkAuthentication() {
  const token = localStorage.getItem('ci_auth_token');
  const user = localStorage.getItem('ci_user');
  
  if (token && user) {
    appState.authenticated = true;
    appState.user = JSON.parse(user);
    showDashboard();
  } else {
    showAuthenticationFlow();
  }
}

function showAuthenticationFlow() {
  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>ComplianceInvoice</h1>
          <p class="subtitle">Multi-Country e-Invoicing Compliance</p>
        </div>
        
        <div class="auth-tabs">
          <button class="auth-tab-btn active" data-tab="login">Sign In</button>
          <button class="auth-tab-btn" data-tab="signup">Create Account</button>
        </div>
        
        <div id="login-tab" class="auth-tab-content active">
          <form id="login-form" class="auth-form">
            <div class="form-group">
              <label for="login-email">Email Address</label>
              <input type="email" id="login-email" placeholder="your@company.com" required>
            </div>
            <div class="form-group">
              <label for="login-password">Password</label>
              <input type="password" id="login-password" placeholder="••••••••" required>
            </div>
            <div class="form-group checkbox">
              <input type="checkbox" id="remember-me">
              <label for="remember-me">Remember me</label>
            </div>
            <button type="submit" class="btn btn-primary btn-full">Sign In</button>
            <button type="button" class="btn btn-link">Forgot password?</button>
          </form>
        </div>
        
        <div id="signup-tab" class="auth-tab-content">
          <form id="signup-form" class="auth-form">
            <div class="form-group">
              <label for="signup-company">Company Name</label>
              <input type="text" id="signup-company" placeholder="Your Company Ltd" required>
            </div>
            <div class="form-group">
              <label for="signup-email">Email Address</label>
              <input type="email" id="signup-email" placeholder="your@company.com" required>
            </div>
            <div class="form-group">
              <label for="signup-password">Password</label>
              <input type="password" id="signup-password" placeholder="••••••••" required>
            </div>
            <div class="form-group">
              <label for="signup-confirm">Confirm Password</label>
              <input type="password" id="signup-confirm" placeholder="••••••••" required>
            </div>
            <div class="form-group checkbox">
              <input type="checkbox" id="agree-terms" required>
              <label for="agree-terms">I agree to Terms of Service & Privacy Policy</label>
            </div>
            <button type="submit" class="btn btn-primary btn-full">Create Account</button>
          </form>
        </div>
        
        <div class="auth-footer">
          <p>ComplianceInvoice © 2024. All rights reserved.</p>
          <div class="auth-links">
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
            <a href="#support">Support</a>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Attach event listeners
  document.querySelectorAll('.auth-tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => switchAuthTab(e.target.dataset.tab));
  });
  
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('signup-form').addEventListener('submit', handleSignup);
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.auth-tab-btn').forEach(el => el.classList.remove('active'));
  
  document.getElementById(tab + '-tab').classList.add('active');
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
}

async function handleLogin(e) {
  e.preventDefault();
  
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  
  try {
    appState.loading = true;
    const response = await fetch(`${APP_CONFIG.apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) throw new Error('Authentication failed');
    
    const data = await response.json();
    
    localStorage.setItem('ci_auth_token', data.token);
    localStorage.setItem('ci_user', JSON.stringify(data.user));
    
    appState.authenticated = true;
    appState.user = data.user;
    
    showNotification('Login successful', 'success');
    showDashboard();
  } catch (error) {
    showNotification('Login failed: ' + error.message, 'error');
    console.error(error);
  } finally {
    appState.loading = false;
  }
}

async function handleSignup(e) {
  e.preventDefault();
  
  const company = document.getElementById('signup-company').value;
  const email = document.getElementById('signup-email').value;
  const password = document.getElementById('signup-password').value;
  const confirm = document.getElementById('signup-confirm').value;
  
  if (password !== confirm) {
    showNotification('Passwords do not match', 'error');
    return;
  }
  
  try {
    appState.loading = true;
    const response = await fetch(`${APP_CONFIG.apiBaseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, email, password })
    });
    
    if (!response.ok) throw new Error('Registration failed');
    
    const data = await response.json();
    
    localStorage.setItem('ci_auth_token', data.token);
    localStorage.setItem('ci_user', JSON.stringify(data.user));
    
    appState.authenticated = true;
    appState.user = data.user;
    
    showNotification('Account created successfully', 'success');
    showDashboard();
  } catch (error) {
    showNotification('Registration failed: ' + error.message, 'error');
    console.error(error);
  } finally {
    appState.loading = false;
  }
}

function logout() {
  localStorage.removeItem('ci_auth_token');
  localStorage.removeItem('ci_user');
  localStorage.removeItem('ci_preferences');
  
  appState.authenticated = false;
  appState.user = null;
  appState.selectedCountries = [];
  
  showAuthenticationFlow();
  showNotification('Logged out successfully', 'info');
}

// ============================================================================
// DASHBOARD & MAIN INTERFACE
// ============================================================================

function showDashboard() {
  const mainContent = document.getElementById('main-content');
  
  mainContent.innerHTML = `
    <div class="dashboard-container">
      <!-- Sidebar Navigation -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h2>ComplianceInvoice</h2>
          <button class="sidebar-toggle" id="sidebar-toggle">☰</button>
        </div>
        
        <nav class="sidebar-nav">
          <button class="nav-item active" data-view="dashboard">
            <span class="icon">📊</span>
            <span>Dashboard</span>
          </button>
          <button class="nav-item" data-view="invoices">
            <span class="icon">📄</span>
            <span>Invoices</span>
          </button>
          <button class="nav-item" data-view="mandates">
            <span class="icon">⚖️</span>
            <span>Mandates</span>
          </button>
          <button class="nav-item" data-view="templates">
            <span class="icon">🎨</span>
            <span>Templates</span>
          </button>
          <button class="nav-item" data-view="integrations">
            <span class="icon">🔗</span>
            <span>Integrations</span>
          </button>
          <button class="nav-item" data-view="compliance">
            <span class="icon">✓</span>
            <span>Compliance</span>
          </button>
          <button class="nav-item" data-view="settings">
            <span class="icon">⚙️</span>
            <span>Settings</span>
          </button>
        </nav>
        
        <div class="sidebar-footer">
          <button class="nav-item" data-view="help">
            <span class="icon">?</span>
            <span>Help</span>
          </button>
          <button class="nav-item logout-btn" id="logout-btn">
            <span class="icon">🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>
      
      <!-- Top Bar -->
      <div class="topbar">
        <div class="topbar-left">
          <button id="topbar-menu-toggle" class="topbar-menu-toggle">☰</button>
          <h1 id="page-title">Dashboard</h1>
        </div>
        
        <div class="topbar-right">
          <div class="search-bar">
            <input type="text" id="search-input" placeholder="Search invoices...">
            <button class="search-btn">🔍</button>
          </div>
          
          <div class="notifications-container">
            <button class="notification-bell" id="notification-bell">
              🔔
              <span class="notification-badge" id="notification-count">0</span>
            </button>
            <div class="notification-panel" id="notification-panel"></div>
          </div>
          
          <div class="user-menu">
            <button class="user-avatar" id="user-menu-toggle">
              ${appState.user?.name?.charAt(0) || 'U'}
            </button>
            <div class="user-dropdown" id="user-dropdown">
              <div class="user-info">
                <p class="user-name">${appState.user?.name || 'User'}</p>
                <p class="user-email">${appState.user?.email || ''}</p>
                <p class="user-company">${appState.user?.company || ''}</p>
              </div>
              <hr>
              <button class="dropdown-item" data-view="settings">Account Settings</button>
              <button class="dropdown-item" data-view="billing">Billing</button>
              <hr>
              <button class="dropdown-item" id="logout-dropdown">Logout</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Main Content -->
      <main class="main-content" id="view-container">
        <!-- Content will be loaded here -->
      </main>
    </div>
  `;
  
  setupDashboardEventListeners();
  loadDashboardView('dashboard');
}

function setupDashboardEventListeners() {
  // Navigation
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const view = e.currentTarget.dataset.view;
      if (view === 'logout' || e.currentTarget.classList.contains('logout-btn')) {
        logout();
      } else {
        loadDashboardView(view);
      }
    });
  });
  
  // Logout button
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
  
  const logoutDropdown = document.getElementById('logout-dropdown');
  if (logoutDropdown) logoutDropdown.addEventListener('click', logout);
  
  // User menu toggle
  document.getElementById('user-menu-toggle').addEventListener('click', toggleUserMenu);
  document.getElementById('logout-dropdown').addEventListener('click', logout);
  
  // Notification bell
  document.getElementById('notification-bell').addEventListener('click', toggleNotificationPanel);
  
  // Sidebar toggle
  document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
  document.getElementById('topbar-menu-toggle').addEventListener('click', toggleS