// ComplianceInvoice - SMB e-Invoicing Compliance SaaS
// Main application logic

class ComplianceInvoice {
    constructor() {
        this.currentUser = null;
        this.invoices = [];
        this.mandates = {
            'EU': { name: 'EU (Peppol)', required: true, formats: ['UBL', 'CII'] },
            'IT': { name: 'Italy (FatturaPA)', required: true, formats: ['XML'] },
            'ES': { name: 'Spain (Facturae)', required: true, formats: ['XML'] },
            'FR': { name: 'France (Chorus)', required: true, formats: ['XML', 'PDF'] },
            'DE': { name: 'Germany (ZUGFeRD)', required: true, formats: ['XML', 'PDF'] },
            'UK': { name: 'UK (HMRC)', required: false, formats: ['XML'] },
            'BR': { name: 'Brazil (NF-e)', required: true, formats: ['XML'] },
            'MX': { name: 'Mexico (CFDI)', required: true, formats: ['XML'] },
            'SG': { name: 'Singapore (PEPPOL)', required: false, formats: ['UBL', 'CII'] },
            'AU': { name: 'Australia (PEPPOL)', required: false, formats: ['UBL', 'CII'] }
        };
        this.complianceRules = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadMandates();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('[data-nav]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleNavigation(e));
        });

        // Authentication
        const loginBtn = document.getElementById('login-btn');
        const signupBtn = document.getElementById('signup-btn');
        if (loginBtn) loginBtn.addEventListener('click', () => this.showLoginModal());
        if (signupBtn) signupBtn.addEventListener('click', () => this.showSignupModal());

        // Invoice management
        const uploadInvoiceBtn = document.getElementById('upload-invoice-btn');
        if (uploadInvoiceBtn) uploadInvoiceBtn.addEventListener('click', () => this.showUploadModal());

        const createInvoiceBtn = document.getElementById('create-invoice-btn');
        if (createInvoiceBtn) createInvoiceBtn.addEventListener('click', () => this.showInvoiceBuilder());

        // Mandate selection
        document.querySelectorAll('[data-mandate]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.updateMandateSelection(e));
        });

        // Form submissions
        const loginForm = document.getElementById('login-form');
        if (loginForm) loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        const signupForm = document.getElementById('signup-form');
        if (signupForm) signupForm.addEventListener('submit', (e) => this.handleSignup(e));

        const invoiceForm = document.getElementById('invoice-form');
        if (invoiceForm) invoiceForm.addEventListener('submit', (e) => this.handleInvoiceSubmit(e));

        // Settings
        document.querySelectorAll('[data-settings-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchSettingsTab(e));
        });
    }

    checkAuthStatus() {
        const token = localStorage.getItem('ci_token');
        const user = localStorage.getItem('ci_user');
        
        if (token && user) {
            this.currentUser = JSON.parse(user);
            this.updateAuthUI();
            this.loadUserData();
        }
    }

    showLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) {
            modal.classList.add('active');
            document.body.classList.add('modal-open');
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.classList.remove('modal-open');
        }
    }

    showSignupModal() {
        const modal = document.getElementById('signup-modal');
        if (modal) {
            modal.classList.add('active');
            document.body.classList.add('modal-open');
        }
    }

    handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        if (!this.validateEmail(email) || password.length < 6) {
            this.showNotification('Invalid email or password', 'error');
            return;
        }

        this.simulateApiCall('/auth/login', { email, password }, (response) => {
            if (response.success) {
                localStorage.setItem('ci_token', response.token);
                localStorage.setItem('ci_user', JSON.stringify(response.user));
                this.currentUser = response.user;
                this.updateAuthUI();
                this.closeModal('login-modal');
                this.showNotification('Login successful!', 'success');
                this.loadUserData();
            } else {
                this.showNotification(response.message || 'Login failed', 'error');
            }
        });
    }

    handleSignup(e) {
        e.preventDefault();
        const companyName = document.getElementById('signup-company').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;

        if (!companyName || !this.validateEmail(email) || password.length < 6) {
            this.showNotification('Please fill in all fields correctly', 'error');
            return;
        }

        if (password !== confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        this.simulateApiCall('/auth/signup', { companyName, email, password }, (response) => {
            if (response.success) {
                localStorage.setItem('ci_token', response.token);
                localStorage.setItem('ci_user', JSON.stringify(response.user));
                this.currentUser = response.user;
                this.updateAuthUI();
                this.closeModal('signup-modal');
                this.showNotification('Account created successfully!', 'success');
            } else {
                this.showNotification(response.message || 'Signup failed', 'error');
            }
        });
    }

    updateAuthUI() {
        const authSection = document.querySelector('.auth-section');
        const userSection = document.querySelector('.user-section');

        if (this.currentUser) {
            if (authSection) authSection.style.display = 'none';
            if (userSection) {
                userSection.style.display = 'flex';
                const userName = userSection.querySelector('.user-name');
                if (userName) userName.textContent = this.currentUser.companyName || this.currentUser.email;
            }
        } else {
            if (authSection) authSection.style.display = 'flex';
            if (userSection) userSection.style.display = 'none';
        }
    }

    showUploadModal() {
        if (!this.currentUser) {
            this.showNotification('Please login first', 'warning');
            this.showLoginModal();
            return;
        }

        const modal = document.getElementById('upload-modal');
        if (modal) {
            modal.classList.add('active');
            document.body.classList.add('modal-open');

            const dropZone = modal.querySelector('.drop-zone');
            if (dropZone) {
                dropZone.addEventListener('dragover', (e) => e.preventDefault());
                dropZone.addEventListener('drop', (e) => this.handleFileDrop(e, modal));
                dropZone.addEventListener('click', () => {
                    const input = modal.querySelector('input[type="file"]');
                    if (input) input.click();
                });
            }

            const fileInput = modal.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => this.handleFileSelect(e, modal));
            }
        }
    }

    handleFileDrop(e, modal) {
        e.preventDefault();
        const files = e.dataTransfer.files;
        this.processFiles(files, modal);
    }

    handleFileSelect(e, modal) {
        const files = e.target.files;
        this.processFiles(files, modal);
    }

    processFiles(files, modal) {
        Array.from(files).forEach(file => {
            if (this.isValidInvoiceFile(file)) {
                this.uploadFile(file);
            } else {
                this.showNotification(`Invalid file format: ${file.name}`, 'error');
            }
        });
    }

    isValidInvoiceFile(file) {
        const validFormats = ['application/xml', 'application/pdf', 'text/xml'];
        const validExtensions = ['.xml', '.pdf', '.ubl', '.ublx'];
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return validFormats.includes(file.type) || validExtensions.includes(extension);
    }

    uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('userId', this.currentUser.id);

        // Simulate file upload
        const progressBar = document.querySelector('.upload-progress');
        if (progressBar) {
            progressBar.style.display = 'block';
        }

        setTimeout(() => {
            const invoice = {
                id: this.generateId(),
                fileName: file.name,
                uploadDate: new Date().toLocaleDateString(),
                status: 'Processing',
                complianceStatus: 'Validating',
                mandates: []
            };

            this.invoices.push(invoice);
            this.validateInvoice(invoice);
            this.showNotification(`File uploaded: ${file.name}`, 'success');
            this.closeModal('upload-modal');
            this.refreshInvoiceList();
        }, 1500);
    }

    showInvoiceBuilder() {
        if (!this.currentUser) {
            this.showNotification('Please login first', 'warning');
            this.showLoginModal();
            return;
        }

        const modal = document.getElementById('invoice-builder-modal');
        if (modal) {
            modal.classList.add('active');
            document.body.classList.add('modal-open');
        }
    }

    handleInvoiceSubmit(e) {
        e.preventDefault();

        const invoiceData = {
            id: this.generateId(),
            invoiceNumber: document.getElementById('invoice-number')?.value,
            issueDate: document.getElementById('issue-date')?.value,
            dueDate: document.getElementById('due-date')?.value,
            supplier: {
                name: document.getElementById('supplier-name')?.value,
                taxId: document.getElementById('supplier-tax-id')?.value,
                address: document.getElementById('supplier-address')?.value
            },
            customer: {
                name: document.getElementById('customer-name')?.value,
                taxId: document.getElementById('customer-tax-id')?.value,
                address: document.getElementById('customer-address')?.value
            },
            items: this.getInvoiceItems(),
            totalAmount: this.calculateTotal(),
            currency: document.getElementById('currency')?.value || 'USD'
        };

        if (this.validateInvoiceData(invoiceData)) {
            this.invoices.push(invoiceData);
            this.validateInvoice(invoiceData);
            this.showNotification('Invoice created successfully', 'success');
            document.getElementById('invoice-form').reset();
            this.closeModal('invoice-builder-modal');
            this.refreshInvoiceList();
        } else {
            this.showNotification('Please fill in all required fields', 'error');
        }
    }

    getInvoiceItems() {
        const items = [];
        document.querySelectorAll('.invoice-item-row').forEach((row, index) => {
            items.push({
                description: row.querySelector('.item-description')?.value,
                quantity: parseFloat(row.querySelector('.item-quantity')?.value) || 0,
                unitPrice: parseFloat(row.querySelector('.item-price')?.value) || 0,
                amount: (parseFloat(row.querySelector('.item-quantity')?.value) || 0) * 
                        (parseFloat(row.querySelector('.item-price')?.value) || 0)
            });
        });
        return items.filter(item => item.description && item.quantity > 0);
    }

    calculateTotal() {
        return this.getInvoiceItems().reduce((sum, item) => sum + item.amount, 0);
    }

    validateInvoiceData(data) {
        return data.invoiceNumber && 
               data.issueDate && 
               data.supplier.name && 
               data.supplier.taxId && 
               data.customer.name && 
               data.customer.taxId &&
               data.items.length > 0;
    }

    validateInvoice(invoice) {
        const applicableMandates = this.getApplicableMandates();
        const complianceResults = {
            invoice: invoice.id,
            timestamp: new Date().toISOString(),
            mandates: {},
            overallStatus: 'Compliant',
            warnings: [],
            errors: []
        };

        applicableMandates.forEach(country => {
            const mandate = this.mandates[country];
            const result = this.checkCompliance(invoice, country, mandate);
            complianceResults.mandates[country] = result;

            if (result.status === 'Non-Compliant') {
                complianceResults.overallStatus = 'Non-Compliant';
            }
            if (result.warnings.length > 0) {
                complianceResults.warnings.push(...result.warnings);
            }
            if (result.errors.length > 0) {
                complianceResults.errors.push(...result.errors);
            }
        });

        invoice.complianceResults = complianceResults;
        invoice.complianceStatus = complianceResults.overallStatus;
        this.saveInvoice(invoice);
    }

    getApplicableMandates() {
        const selected = document.querySelectorAll('[data-mandate]:checked');
        if (selected.length > 0) {
            return Array.from(selected).map(el => el.value);
        }
        return Object.keys(this.mandates);
    }

    checkCompliance(invoice, country, mandate) {
        const result = {
            status: 'Compliant',
            mandate: mandate.name,
            format: 'Unknown',
            checklist: [],
            warnings: [],
            errors: []
        };

        // Format validation
        const hasValidFormat = mandate.formats.some(fmt => this.checkFormat(invoice, fmt));
        if (!hasValidFormat) {
            result.errors.push(`Invalid format. Required: ${mandate.formats.join(', ')}`);
            result.status = 'Non-Compliant';
        } else {
            result.format = this.detectFormat(invoice);
        }

        // Tax ID validation
        if (!this.validateTaxId(invoice.supplier.taxId, country)) {
            result.errors.push(`Invalid tax ID format for ${country}`);
            result.status = 'Non-Compliant';
        } else {
            result.checklist.push('✓ Tax ID format valid');
        }

        // Required fields validation
        const requiredFields = this.getRequiredFields(country);
        requiredFields.forEach(field => {
            if (this.hasField(invoice, field)) {
                result.checklist.push(`✓ ${field