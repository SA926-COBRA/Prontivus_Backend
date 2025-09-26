from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging

from app.database.database import get_db
from app.models.financial_tiss import (
    TISSCode, TISSProcedure, Invoice, Payment, FinancialReport,
    TISSIntegration, TISSSubmission, HealthPlanFinancial
)
from app.models.user import User
from app.schemas.financial_tiss import (
    TISSCodeCreate, TISSCodeUpdate, TISSCode as TISSCodeSchema,
    TISSProcedureCreate, TISSProcedureUpdate, TISSProcedure as TISSProcedureSchema,
    InvoiceCreate, InvoiceUpdate, Invoice as InvoiceSchema,
    PaymentCreate, PaymentUpdate, Payment as PaymentSchema,
    FinancialReport as FinancialReportSchema,
    TISSIntegrationCreate, TISSIntegrationUpdate, TISSIntegration as TISSIntegrationSchema,
    TISSSubmission as TISSSubmissionSchema,
    HealthPlanFinancialCreate, HealthPlanFinancialUpdate, HealthPlanFinancial as HealthPlanFinancialSchema,
    TISSCodeSearchRequest, TISSProcedureSearchRequest, InvoiceSearchRequest,
    PaymentSearchRequest, TISSSubmissionRequest, FinancialSummary,
    TISSDashboardSummary
)
from app.services.auth_service import AuthService
from app.services.financial_tiss_service import FinancialTISSService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# TISS Code endpoints
@router.get("/tiss-codes", response_model=List[TISSCodeSchema], summary="Get TISS codes")
async def get_tiss_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    code: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tiss_version: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get TISS codes with filtering options"""
    try:
        service = FinancialTISSService(db)
        request = TISSCodeSearchRequest(
            code=code,
            description=description,
            category=category,
            tiss_version=tiss_version,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        tiss_codes = service.search_tiss_codes(request)
        return tiss_codes
    except Exception as e:
        logger.error(f"Error getting TISS codes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TISS codes: {str(e)}"
        )

@router.get("/tiss-codes/{tiss_code_id}", response_model=TISSCodeSchema, summary="Get TISS code by ID")
async def get_tiss_code(
    tiss_code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific TISS code by ID"""
    tiss_code = db.query(TISSCode).filter(TISSCode.id == tiss_code_id).first()
    if not tiss_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS code not found")
    return tiss_code

@router.post("/tiss-codes", response_model=TISSCodeSchema, status_code=status.HTTP_201_CREATED, summary="Create TISS code")
async def create_tiss_code(
    tiss_code_data: TISSCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new TISS code"""
    try:
        service = FinancialTISSService(db)
        tiss_code = service.create_tiss_code(tiss_code_data.dict())
        return tiss_code
    except Exception as e:
        logger.error(f"Error creating TISS code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create TISS code: {str(e)}"
        )

@router.put("/tiss-codes/{tiss_code_id}", response_model=TISSCodeSchema, summary="Update TISS code")
async def update_tiss_code(
    tiss_code_id: int,
    tiss_code_data: TISSCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a TISS code"""
    tiss_code = db.query(TISSCode).filter(TISSCode.id == tiss_code_id).first()
    if not tiss_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS code not found")
    
    update_data = tiss_code_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tiss_code, field, value)
    
    db.commit()
    db.refresh(tiss_code)
    return tiss_code

# TISS Procedure endpoints
@router.get("/procedures", response_model=List[TISSProcedureSchema], summary="Get TISS procedures")
async def get_tiss_procedures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    tiss_code_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """Get TISS procedures with filtering options"""
    try:
        service = FinancialTISSService(db)
        request = TISSProcedureSearchRequest(
            patient_id=patient_id,
            doctor_id=doctor_id,
            tiss_code_id=tiss_code_id,
            status=status,
            payment_status=payment_status,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        procedures = service.search_tiss_procedures(request)
        return procedures
    except Exception as e:
        logger.error(f"Error getting TISS procedures: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TISS procedures: {str(e)}"
        )

@router.get("/procedures/{procedure_id}", response_model=TISSProcedureSchema, summary="Get TISS procedure by ID")
async def get_tiss_procedure(
    procedure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific TISS procedure by ID"""
    procedure = db.query(TISSProcedure).filter(TISSProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS procedure not found")
    return procedure

@router.post("/procedures", response_model=TISSProcedureSchema, status_code=status.HTTP_201_CREATED, summary="Create TISS procedure")
async def create_tiss_procedure(
    procedure_data: TISSProcedureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new TISS procedure"""
    try:
        service = FinancialTISSService(db)
        procedure = service.create_tiss_procedure(procedure_data.dict(), current_user.id)
        return procedure
    except Exception as e:
        logger.error(f"Error creating TISS procedure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create TISS procedure: {str(e)}"
        )

@router.put("/procedures/{procedure_id}", response_model=TISSProcedureSchema, summary="Update TISS procedure")
async def update_tiss_procedure(
    procedure_id: int,
    procedure_data: TISSProcedureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a TISS procedure"""
    procedure = db.query(TISSProcedure).filter(TISSProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS procedure not found")
    
    update_data = procedure_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procedure, field, value)
    
    db.commit()
    db.refresh(procedure)
    return procedure

# Invoice endpoints
@router.get("/invoices", response_model=List[InvoiceSchema], summary="Get invoices")
async def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    health_plan_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get invoices with filtering options"""
    try:
        service = FinancialTISSService(db)
        request = InvoiceSearchRequest(
            patient_id=patient_id,
            health_plan_id=health_plan_id,
            status=status,
            payment_status=payment_status,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        invoices = service.search_invoices(request)
        return invoices
    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoices: {str(e)}"
        )

@router.get("/invoices/{invoice_id}", response_model=InvoiceSchema, summary="Get invoice by ID")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific invoice by ID"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice

@router.post("/invoices", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED, summary="Create invoice")
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice"""
    try:
        service = FinancialTISSService(db)
        invoice = service.create_invoice(invoice_data.dict(), current_user.id)
        return invoice
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )

@router.put("/invoices/{invoice_id}", response_model=InvoiceSchema, summary="Update invoice")
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    update_data = invoice_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice

# Payment endpoints
@router.get("/payments", response_model=List[PaymentSchema], summary="Get payments")
async def get_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    invoice_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """Get payments with filtering options"""
    try:
        service = FinancialTISSService(db)
        request = PaymentSearchRequest(
            patient_id=patient_id,
            invoice_id=invoice_id,
            status=status,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        payments = service.search_payments(request)
        return payments
    except Exception as e:
        logger.error(f"Error getting payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payments: {str(e)}"
        )

@router.get("/payments/{payment_id}", response_model=PaymentSchema, summary="Get payment by ID")
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific payment by ID"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.post("/payments", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED, summary="Create payment")
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new payment"""
    try:
        service = FinancialTISSService(db)
        payment = service.create_payment(payment_data.dict(), current_user.id)
        return payment
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )

@router.put("/payments/{payment_id}", response_model=PaymentSchema, summary="Update payment")
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a payment"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    update_data = payment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    return payment

# TISS Integration endpoints
@router.get("/integrations", response_model=List[TISSIntegrationSchema], summary="Get TISS integrations")
async def get_tiss_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None)
):
    """Get TISS integrations with filtering options"""
    query = db.query(TISSIntegration)
    
    if is_active is not None:
        query = query.filter(TISSIntegration.is_active == is_active)
    
    integrations = query.offset(skip).limit(limit).all()
    return integrations

@router.get("/integrations/{integration_id}", response_model=TISSIntegrationSchema, summary="Get TISS integration by ID")
async def get_tiss_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific TISS integration by ID"""
    integration = db.query(TISSIntegration).filter(TISSIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS integration not found")
    return integration

@router.post("/integrations", response_model=TISSIntegrationSchema, status_code=status.HTTP_201_CREATED, summary="Create TISS integration")
async def create_tiss_integration(
    integration_data: TISSIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new TISS integration"""
    try:
        service = FinancialTISSService(db)
        integration = service.create_tiss_integration(integration_data.dict(), current_user.id)
        return integration
    except Exception as e:
        logger.error(f"Error creating TISS integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create TISS integration: {str(e)}"
        )

@router.put("/integrations/{integration_id}", response_model=TISSIntegrationSchema, summary="Update TISS integration")
async def update_tiss_integration(
    integration_id: int,
    integration_data: TISSIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a TISS integration"""
    integration = db.query(TISSIntegration).filter(TISSIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS integration not found")
    
    update_data = integration_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)
    
    db.commit()
    db.refresh(integration)
    return integration

# TISS Submission endpoints
@router.get("/submissions", response_model=List[TISSSubmissionSchema], summary="Get TISS submissions")
async def get_tiss_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    integration_id: Optional[int] = Query(None),
    procedure_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get TISS submissions with filtering options"""
    query = db.query(TISSSubmission)
    
    if integration_id:
        query = query.filter(TISSSubmission.integration_id == integration_id)
    
    if procedure_id:
        query = query.filter(TISSSubmission.procedure_id == procedure_id)
    
    if status:
        query = query.filter(TISSSubmission.status == status)
    
    submissions = query.order_by(desc(TISSSubmission.submission_date)).offset(skip).limit(limit).all()
    return submissions

@router.get("/submissions/{submission_id}", response_model=TISSSubmissionSchema, summary="Get TISS submission by ID")
async def get_tiss_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific TISS submission by ID"""
    submission = db.query(TISSSubmission).filter(TISSSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TISS submission not found")
    return submission

@router.post("/submissions", response_model=TISSSubmissionSchema, status_code=status.HTTP_201_CREATED, summary="Submit to TISS")
async def submit_to_tiss(
    submission_data: TISSSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit procedure to TISS"""
    try:
        service = FinancialTISSService(db)
        submission = service.submit_to_tiss(submission_data)
        return submission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting to TISS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit to TISS: {str(e)}"
        )

# Summary endpoints
@router.get("/financial-summary", response_model=FinancialSummary, summary="Get financial summary")
async def get_financial_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get financial summary statistics"""
    try:
        service = FinancialTISSService(db)
        summary = service.get_financial_summary(start_date, end_date)
        return summary
    except Exception as e:
        logger.error(f"Error getting financial summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial summary: {str(e)}"
        )

@router.get("/tiss-dashboard-summary", response_model=TISSDashboardSummary, summary="Get TISS dashboard summary")
async def get_tiss_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get TISS dashboard summary"""
    try:
        service = FinancialTISSService(db)
        summary = service.get_tiss_dashboard_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting TISS dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TISS dashboard summary: {str(e)}"
        )

# Health check endpoint
@router.get("/health", summary="Financial TISS service health check")
async def health_check():
    """Check the health of the Financial TISS service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "financial_tiss",
        "features": {
            "tiss_codes": True,
            "tiss_procedures": True,
            "invoices": True,
            "payments": True,
            "tiss_integration": True,
            "financial_reports": True
        }
    }
