from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import os
from datetime import datetime
import logging

# Database
from database import Base, User, Invoice, Mandate, ComplianceRule
from schemas import (
    UserCreate, UserResponse, InvoiceCreate, InvoiceResponse,
    MandateCreate, MandateResponse, ComplianceRuleResponse
)
from services import (
    UserService, InvoiceService, MandateService,
    ComplianceService, ValidationService
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="ComplianceInvoice API",
    description="SMB e-Invoicing Compliance SaaS for Multi-Country Mandates",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complianceinvoice.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# AUTHENTICATION & USER ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, tags=["Authentication"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user_service = UserService(db)
    existing_user = user_service.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    new_user = user_service.create_user(user)
    logger.info(f"New user registered: {new_user.email}")
    return new_user

@app.post("/api/auth/login", response_model=dict, tags=["Authentication"])
def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user and return token"""
    user_service = UserService(db)
    user = user_service.authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    token = user_service.generate_token(user)
    logger.info(f"User logged in: {email}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "company_name": user.company_name
    }

@app.get("/api/users/me", response_model=UserResponse, tags=["Users"])
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """Get current user profile"""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    """Update user profile"""
    user_service = UserService(db)
    user = user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    logger.info(f"User profile updated: {user_id}")
    return user

# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.post("/api/invoices", response_model=InvoiceResponse, tags=["Invoices"])
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice"""
    invoice_service = InvoiceService(db)
    validation_service = ValidationService(db)
    
    # Validate invoice data
    validation_errors = validation_service.validate_invoice(invoice)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_errors}
        )
    
    new_invoice = invoice_service.create_invoice(invoice)
    logger.info(f"Invoice created: {new_invoice.id}")
    return new_invoice

@app.get("/api/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
def list_invoices(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List invoices for a user"""
    invoice_service = InvoiceService(db)
    invoices = invoice_service.get_invoices(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=status_filter
    )
    return invoices

@app.get("/api/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice details"""
    invoice_service = InvoiceService(db)
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice

@app.put("/api/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
def update_invoice(
    invoice_id: int,
    invoice_data: dict,
    db: Session = Depends(get_db)
):
    """Update invoice"""
    invoice_service = InvoiceService(db)
    invoice = invoice_service.update_invoice(invoice_id, invoice_data)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    logger.info(f"Invoice updated: {invoice_id}")
    return invoice

@app.delete("/api/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Invoices"])
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete invoice"""
    invoice_service = InvoiceService(db)
    success = invoice_service.delete_invoice(invoice_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    logger.info(f"Invoice deleted: {invoice_id}")

@app.post("/api/invoices/{invoice_id}/submit", response_model=dict, tags=["Invoices"])
def submit_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Submit invoice for compliance check and transmission"""
    invoice_service = InvoiceService(db)
    compliance_service = ComplianceService(db)
    
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Run compliance check
    compliance_result = compliance_service.check_invoice_compliance(invoice)
    
    if not compliance_result["is_compliant"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invoice does not meet compliance requirements",
                "violations": compliance_result["violations"]
            }
        )
    
    # Submit invoice
    submitted_invoice = invoice_service.submit_invoice(invoice_id)
    logger.info(f"Invoice submitted: {invoice_id}")
    
    return {
        "status": "submitted",
        "invoice_id": submitted_invoice.id,
        "submission_date": submitted_invoice.submission_date,
        "compliance_status": "compliant"
    }

@app.get("/api/invoices/{invoice_id}/compliance", response_model=dict, tags=["Invoices"])
def check_invoice_compliance(invoice_id: int, db: Session = Depends(get_db)):
    """Check invoice compliance status"""
    invoice_service = InvoiceService(db)
    compliance_service = ComplianceService(db)
    
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    result = compliance_service.check_invoice_compliance(invoice)
    return result

# ============================================================================
# MANDATE ENDPOINTS
# ============================================================================

@app.get("/api/mandates", response_model=List[MandateResponse], tags=["Mandates"])
def list_mandates(
    country: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List e-invoicing mandates"""
    mandate_service = MandateService(db)
    mandates = mandate_service.get_mandates(country=country, skip=skip, limit=limit)
    return mandates

@app.get("/api/mandates/{mandate_id}", response_model=MandateResponse, tags=["Mandates"])
def get_mandate(mandate_id: int, db: Session = Depends(get_db)):
    """Get mandate details"""
    mandate_service = MandateService(db)
    mandate = mandate_service.get_mandate(mandate_id)
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandate not found"
        )
    return mandate

@app.post("/api/mandates", response_model=MandateResponse, tags=["Mandates"])
def create_mandate(mandate: MandateCreate, db: Session = Depends(get_db)):
    """Create a new mandate (admin only)"""
    mandate_service = MandateService(db)
    new_mandate = mandate_service.create_mandate(mandate)
    logger.info(f"Mandate created: {new_mandate.id} for {new_mandate.country}")
    return new_mandate

# ============================================================================
# COMPLIANCE RULES ENDPOINTS
# ============================================================================

@app.get("/api/compliance-rules", response_model=List[ComplianceRuleResponse], tags=["Compliance"])
def list_compliance_rules(
    mandate_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List compliance rules"""
    compliance_service = ComplianceService(db)
    rules = compliance_service.get_rules(mandate_id=mandate_id, skip=skip, limit=limit)
    return rules

@app.get("/api/compliance-rules/{rule_id}", response_model=ComplianceRuleResponse, tags=["Compliance"])
def get_compliance_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get compliance rule details"""
    compliance_service = ComplianceService(db)
    rule = compliance_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance rule not found"
        )
    return rule

# ============================================================================
# REPORTING & ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/reports/compliance-summary", response_model=dict, tags=["Reports"])
def get_compliance_summary(user_id: int, db: Session = Depends(get_db)):
    """Get compliance summary for user"""
    invoice_service = InvoiceService(db)
    summary = invoice_service.get_compliance_summary(user_id)
    return summary

@app.get("/api/reports/submission-status", response_model=dict, tags=["Reports"])
def get_submission_status(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get submission status report"""
    invoice_service = InvoiceService(db)
    status_report = invoice_service.get_submission_status(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    return status_report

@app.get("/api/reports/mandate-coverage", response_model=dict, tags=["Reports"])
def get_mandate_coverage(user_id: int, db: Session = Depends(get_db)):
    """Get mandate coverage report"""
    mandate_service = MandateService(db)
    coverage = mandate_service.get_coverage_for_user(user_id)
    return coverage

# ============================================================================
# EXPORT & INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/invoices/{invoice_id}/export", response_model=dict, tags=["Export"])
def export_invoice(
    invoice_id: int,
    format: str = "xml",
    db: Session = Depends(get_db)
):
    """Export invoice in specified format (xml, pdf, json)"""
    invoice_service = InvoiceService(db)
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if format not in ["xml", "pdf", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format"
        )
    
    exported_data = invoice_service.export_invoice(invoice, format)
    logger.info(f"Invoice exported: {invoice_id} as {format}")
    
    return {
        "status": "success",
        "invoice_id": invoice_id,
        "format": format,
        "data": exported_data
    }

@app.post("/api/invoices/batch-import", response_model=dict, tags=["Import"])
def batch_import_invoices(
    user_id: int,
    invoices: List[InvoiceCreate],
    db: Session = Depends(get_db)
):
    """Batch import invoices"""
    invoice_service = InvoiceService(db)
    validation_service = ValidationService(db)
    
    results = {
        "total": len(invoices),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for idx, invoice_data in enumerate(invoices):
        try:
            validation_errors = validation_service.validate_invoice(invoice_data)
            if validation_errors:
                results["failed"] += 1
                results["errors"].append({
                    "index": idx,
                    "errors": validation_errors
                })
                continue
            
            invoice_service.create_invoice(invoice_