"""
ComplianceInvoice - SMB e-Invoicing Compliance SaaS for Multi-Country Mandates
API Main Application Module

This module provides REST API endpoints for:
- User authentication and authorization
- Invoice submission and validation
- Multi-country compliance checking
- Report generation
- Webhook management
- Audit logging
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List, Tuple

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import jwt
import requests
import json
from functools import lru_cache

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', False)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///compliance_invoice.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt_manager = JWTManager(app)
cors = CORS(app, resources={r"/api/*": {"origins": os.getenv('ALLOWED_ORIGINS', '*').split(',')}})
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
cache = Cache(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/compliance_invoice.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =====================================================================
# DATABASE MODELS
# =====================================================================

class User(db.Model):
    """User model for authentication and account management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(2), nullable=False)
    subscription_tier = db.Column(db.String(50), default='starter')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    invoices = db.relationship('Invoice', backref='owner', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    webhooks = db.relationship('Webhook', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'country': self.country,
            'subscription_tier': self.subscription_tier,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Invoice(db.Model):
    """Invoice model for storing invoice data and compliance status"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invoice_number = db.Column(db.String(100), nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False)
    supplier_country = db.Column(db.String(2), nullable=False)
    buyer_country = db.Column(db.String(2), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50), default='pending')
    compliance_status = db.Column(db.String(50), default='pending')
    invoice_data = db.Column(db.JSON, nullable=False)
    xml_content = db.Column(db.Text)
    compliance_errors = db.Column(db.JSON, default=list)
    warnings = db.Column(db.JSON, default=list)
    validation_result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    
    compliance_checks = db.relationship('ComplianceCheck', backref='invoice', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice object to dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat(),
            'supplier_country': self.supplier_country,
            'buyer_country': self.buyer_country,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'compliance_status': self.compliance_status,
            'compliance_errors': self.compliance_errors,
            'warnings': self.warnings,
            'validation_result': self.validation_result,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }


class ComplianceCheck(db.Model):
    """Model for tracking compliance checks performed on invoices"""
    __tablename__ = 'compliance_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    check_type = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(2), nullable=False)
    rule_set = db.Column(db.String(50))
    passed = db.Column(db.Boolean)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert compliance check object to dictionary"""
        return {
            'id': self.id,
            'check_type': self.check_type,
            'country': self.country,
            'rule_set': self.rule_set,
            'passed': self.passed,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }


class APIKey(db.Model):
    """Model for API key management"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    key_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert API key object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class Webhook(db.Model):
    """Model for webhook management"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False)
    events = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, default=True)
    secret = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert webhook object to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'events': self.events,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class AuditLog(db.Model):
    """Model for audit logging"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(100))
    changes = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log object to dictionary"""
        return {
            'id': self.id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'changes': self.changes,
            'created_at': self.created_at.isoformat()
        }


# =====================================================================
# COMPLIANCE RULES ENGINE
# =====================================================================

class ComplianceRulesEngine:
    """Engine for validating invoices against multi-country compliance rules"""
    
    COMPLIANCE_RULES = {
        'BR': {
            'name': 'Brazil',
            'rules': ['nf_e_format', 'cnpj_validation', 'state_tax_id', 'fiscal_address'],
            'format': 'NFe',
            'version': '4.0'
        },
        'IT': {
            'name': 'Italy',
            'rules': ['fatturaPA_format', 'codice_fiscale', 'progressive_number', 'digital_signature'],
            'format': 'FatturaPA',
            'version': '1.2.2'
        },
        'ES': {
            'name': 'Spain',
            'rules': ['facturae_format', 'nif_validation', 'invoice_series', 'qr_code'],
            'format': 'FacturaE',
            'version': '3.2.2'
        },
        'DE': {
            'name': 'Germany',
            'rules': ['zugferd_format', 'tax_id_validation', 'ust_id', 'invoice_reference'],
            'format': 'ZUGFeRD',
            'version': '2.0'
        },
        'FR': {
            'name': 'France',
            'rules': ['chorus_pro_format', 'siret_validation', 'siren_validation', 'invoice_authentication'],
            'format': 'CHORUS Pro',
            'version': '1.0'
        },
        'IN': {
            'name': 'India',
            'rules': ['gst_invoice_format', 'gstin_validation', 'hsn_sac_code', 'irn_generation'],
            'format': 'GST Invoice',
            'version': '2.0'
        },
        'SG': {
            'name': 'Singapore',
            'rules': ['peppol_format', 'uen_validation', 'tax_registration', 'invoice_authentication'],
            'format': 'PEPPOL',
            'version': '3.0'
        },
        'AU': {
            'name': 'Australia',
            'rules': ['ausdigital_format', 'abn_validation', 'gst_handling', 'invoice_reference'],
            'format': 'AusDigital',
            'version': '1.0'
        },
        'EU': {
            'name': 'European Union',
            'rules': ['en16931_format', 'vat_validation', 'cross_border_rules', 'digital_signature'],
            'format': 'EN 16931',
            'version': '1.0'
        },
        'US': {
            'name': 'United States',
            'rules': ['invoice_format_validation', 'tax_id_validation', 'state_compliance', 'accessibility'],
            'format': 'UBL 2.1',
            'version': '2.1'
        },
        'MX': {
            'name': 'Mexico',
            'rules': ['cfdi