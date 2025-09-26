from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.database.database import get_db
from app.models.commercial import (
    SurgicalProcedure, SurgicalEstimate, SurgicalContract, 
    ContractPayment, CommercialPackage, SalesTarget
)
from app.models.patient import Patient
from app.models.user import User
from app.schemas.commercial import (
    SurgicalProcedureCreate, SurgicalProcedureUpdate, SurgicalProcedure as SurgicalProcedureSchema,
    SurgicalEstimateCreate, SurgicalEstimateUpdate, SurgicalEstimate as SurgicalEstimateSchema,
    SurgicalContractCreate, SurgicalContractUpdate, SurgicalContract as SurgicalContractSchema,
    ContractPaymentCreate, ContractPaymentUpdate, ContractPayment as ContractPaymentSchema,
    CommercialPackageCreate, CommercialPackageUpdate, CommercialPackage as CommercialPackageSchema,
    SalesTargetCreate, SalesTargetUpdate, SalesTarget as SalesTargetSchema,
    CommercialDashboardStats, EstimateAnalytics, ContractAnalytics
)
from app.services.auth_service import AuthService
from app.core.exceptions import ValidationError

router = APIRouter()

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Surgical Procedures endpoints
@router.get("/procedures", response_model=List[SurgicalProcedureSchema], summary="Get all surgical procedures")
async def get_procedures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    procedure_type: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all surgical procedures with filtering options"""
    query = db.query(SurgicalProcedure)
    
    if search:
        query = query.filter(
            SurgicalProcedure.name.ilike(f"%{search}%") |
            SurgicalProcedure.code.ilike(f"%{search}%") |
            SurgicalProcedure.description.ilike(f"%{search}%")
        )
    
    if procedure_type:
        query = query.filter(SurgicalProcedure.procedure_type == procedure_type)
    
    if specialty:
        query = query.filter(SurgicalProcedure.specialty.ilike(f"%{specialty}%"))
    
    if is_active is not None:
        query = query.filter(SurgicalProcedure.is_active == is_active)
    
    procedures = query.offset(skip).limit(limit).all()
    return procedures

@router.get("/procedures/{procedure_id}", response_model=SurgicalProcedureSchema, summary="Get surgical procedure by ID")
async def get_procedure(
    procedure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific surgical procedure by ID"""
    procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical procedure not found")
    return procedure

@router.post("/procedures", response_model=SurgicalProcedureSchema, status_code=status.HTTP_201_CREATED, summary="Create new surgical procedure")
async def create_procedure(
    procedure_data: SurgicalProcedureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new surgical procedure"""
    # Check if code already exists
    existing_procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.code == procedure_data.code).first()
    if existing_procedure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A procedure with this code already exists"
        )
    
    procedure = SurgicalProcedure(
        **procedure_data.dict(),
        created_by=current_user.id
    )
    
    db.add(procedure)
    db.commit()
    db.refresh(procedure)
    return procedure

@router.put("/procedures/{procedure_id}", response_model=SurgicalProcedureSchema, summary="Update surgical procedure")
async def update_procedure(
    procedure_id: int,
    procedure_data: SurgicalProcedureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a surgical procedure"""
    procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical procedure not found")
    
    update_data = procedure_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procedure, field, value)
    
    db.commit()
    db.refresh(procedure)
    return procedure

@router.delete("/procedures/{procedure_id}", summary="Delete surgical procedure")
async def delete_procedure(
    procedure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a surgical procedure (soft delete by setting is_active=False)"""
    procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical procedure not found")
    
    procedure.is_active = False
    db.commit()
    return {"message": "Surgical procedure deactivated successfully"}

# Surgical Estimates endpoints
@router.get("/estimates", response_model=List[SurgicalEstimateSchema], summary="Get all surgical estimates")
async def get_estimates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    procedure_id: Optional[int] = Query(None)
):
    """Get all surgical estimates with filtering options"""
    query = db.query(SurgicalEstimate)
    
    if status:
        query = query.filter(SurgicalEstimate.status == status)
    
    if patient_id:
        query = query.filter(SurgicalEstimate.patient_id == patient_id)
    
    if doctor_id:
        query = query.filter(SurgicalEstimate.doctor_id == doctor_id)
    
    if procedure_id:
        query = query.filter(SurgicalEstimate.procedure_id == procedure_id)
    
    estimates = query.offset(skip).limit(limit).all()
    return estimates

@router.get("/estimates/{estimate_id}", response_model=SurgicalEstimateSchema, summary="Get surgical estimate by ID")
async def get_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific surgical estimate by ID"""
    estimate = db.query(SurgicalEstimate).filter(SurgicalEstimate.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical estimate not found")
    return estimate

@router.post("/estimates", response_model=SurgicalEstimateSchema, status_code=status.HTTP_201_CREATED, summary="Create new surgical estimate")
async def create_estimate(
    estimate_data: SurgicalEstimateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new surgical estimate"""
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == estimate_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Validate procedure exists
    procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.id == estimate_data.procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical procedure not found")
    
    # Validate doctor exists
    doctor = db.query(User).filter(User.id == estimate_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    
    # Calculate total price
    base_price = estimate_data.base_price
    additional_fees = estimate_data.additional_fees or 0
    discount_amount = estimate_data.discount_amount or 0
    
    if estimate_data.discount_percentage and estimate_data.discount_percentage > 0:
        discount_amount = max(discount_amount, (base_price + additional_fees) * (estimate_data.discount_percentage / 100))
    
    total_price = base_price + additional_fees - discount_amount
    
    # Generate estimate number
    estimate_number = f"EST-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    estimate = SurgicalEstimate(
        **estimate_data.dict(),
        estimate_number=estimate_number,
        total_price=total_price,
        installment_value=total_price / estimate_data.installment_count if estimate_data.installment_count > 1 else None,
        created_by=current_user.id
    )
    
    db.add(estimate)
    db.commit()
    db.refresh(estimate)
    return estimate

@router.put("/estimates/{estimate_id}", response_model=SurgicalEstimateSchema, summary="Update surgical estimate")
async def update_estimate(
    estimate_id: int,
    estimate_data: SurgicalEstimateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a surgical estimate"""
    estimate = db.query(SurgicalEstimate).filter(SurgicalEstimate.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical estimate not found")
    
    update_data = estimate_data.dict(exclude_unset=True)
    
    # Recalculate total price if pricing fields are updated
    if any(field in update_data for field in ['base_price', 'additional_fees', 'discount_percentage', 'discount_amount']):
        base_price = update_data.get('base_price', estimate.base_price)
        additional_fees = update_data.get('additional_fees', estimate.additional_fees)
        discount_amount = update_data.get('discount_amount', estimate.discount_amount)
        
        if 'discount_percentage' in update_data and update_data['discount_percentage'] > 0:
            discount_amount = max(discount_amount, (base_price + additional_fees) * (update_data['discount_percentage'] / 100))
        
        total_price = base_price + additional_fees - discount_amount
        update_data['total_price'] = total_price
        
        # Update installment value if installment count changed
        installment_count = update_data.get('installment_count', estimate.installment_count)
        if installment_count > 1:
            update_data['installment_value'] = total_price / installment_count
        else:
            update_data['installment_value'] = None
    
    for field, value in update_data.items():
        setattr(estimate, field, value)
    
    db.commit()
    db.refresh(estimate)
    return estimate

@router.post("/estimates/{estimate_id}/approve", response_model=SurgicalEstimateSchema, summary="Approve surgical estimate")
async def approve_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a surgical estimate"""
    estimate = db.query(SurgicalEstimate).filter(SurgicalEstimate.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical estimate not found")
    
    if estimate.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending estimates can be approved"
        )
    
    estimate.status = "approved"
    db.commit()
    db.refresh(estimate)
    return estimate

@router.post("/estimates/{estimate_id}/reject", response_model=SurgicalEstimateSchema, summary="Reject surgical estimate")
async def reject_estimate(
    estimate_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a surgical estimate"""
    estimate = db.query(SurgicalEstimate).filter(SurgicalEstimate.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical estimate not found")
    
    if estimate.status not in ["pending", "draft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or draft estimates can be rejected"
        )
    
    estimate.status = "rejected"
    if reason:
        estimate.notes = f"{estimate.notes or ''}\nRejection reason: {reason}".strip()
    
    db.commit()
    db.refresh(estimate)
    return estimate

# Surgical Contracts endpoints
@router.get("/contracts", response_model=List[SurgicalContractSchema], summary="Get all surgical contracts")
async def get_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    procedure_id: Optional[int] = Query(None)
):
    """Get all surgical contracts with filtering options"""
    query = db.query(SurgicalContract)
    
    if status:
        query = query.filter(SurgicalContract.status == status)
    
    if patient_id:
        query = query.filter(SurgicalContract.patient_id == patient_id)
    
    if doctor_id:
        query = query.filter(SurgicalContract.doctor_id == doctor_id)
    
    if procedure_id:
        query = query.filter(SurgicalContract.procedure_id == procedure_id)
    
    contracts = query.offset(skip).limit(limit).all()
    return contracts

@router.get("/contracts/{contract_id}", response_model=SurgicalContractSchema, summary="Get surgical contract by ID")
async def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific surgical contract by ID"""
    contract = db.query(SurgicalContract).filter(SurgicalContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical contract not found")
    return contract

@router.post("/contracts", response_model=SurgicalContractSchema, status_code=status.HTTP_201_CREATED, summary="Create new surgical contract")
async def create_contract(
    contract_data: SurgicalContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new surgical contract"""
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == contract_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Validate procedure exists
    procedure = db.query(SurgicalProcedure).filter(SurgicalProcedure.id == contract_data.procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical procedure not found")
    
    # Validate doctor exists
    doctor = db.query(User).filter(User.id == contract_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    
    # Generate contract number
    contract_number = f"CON-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    contract = SurgicalContract(
        **contract_data.dict(),
        contract_number=contract_number,
        paid_amount=0,
        remaining_amount=contract_data.total_amount,
        created_by=current_user.id
    )
    
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

@router.put("/contracts/{contract_id}", response_model=SurgicalContractSchema, summary="Update surgical contract")
async def update_contract(
    contract_id: int,
    contract_data: SurgicalContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a surgical contract"""
    contract = db.query(SurgicalContract).filter(SurgicalContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical contract not found")
    
    update_data = contract_data.dict(exclude_unset=True)
    
    # Update remaining amount if total amount changed
    if 'total_amount' in update_data:
        update_data['remaining_amount'] = update_data['total_amount'] - contract.paid_amount
    
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    db.commit()
    db.refresh(contract)
    return contract

@router.post("/contracts/{contract_id}/sign", response_model=SurgicalContractSchema, summary="Sign contract")
async def sign_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sign a surgical contract"""
    contract = db.query(SurgicalContract).filter(SurgicalContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical contract not found")
    
    if contract.status != "pending_signature":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only contracts pending signature can be signed"
        )
    
    contract.patient_signed = True
    contract.patient_signature_date = datetime.utcnow()
    contract.status = "active"
    
    db.commit()
    db.refresh(contract)
    return contract

@router.post("/contracts/{contract_id}/approve", response_model=SurgicalContractSchema, summary="Approve contract")
async def approve_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a surgical contract"""
    contract = db.query(SurgicalContract).filter(SurgicalContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgical contract not found")
    
    if current_user.crm:  # Doctor approval
        contract.doctor_approved = True
        contract.doctor_approval_date = datetime.utcnow()
    elif current_user.is_superuser:  # Admin approval
        contract.admin_approved = True
        contract.admin_approval_date = datetime.utcnow()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors or administrators can approve contracts"
        )
    
    db.commit()
    db.refresh(contract)
    return contract

# Dashboard and Analytics endpoints
@router.get("/dashboard", response_model=CommercialDashboardStats, summary="Get commercial dashboard statistics")
async def get_commercial_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get commercial dashboard statistics"""
    # This would typically involve complex queries and calculations
    # For now, returning mock data - implement actual queries based on your needs
    
    stats = CommercialDashboardStats(
        total_procedures=db.query(SurgicalProcedure).filter(SurgicalProcedure.is_active == True).count(),
        active_estimates=db.query(SurgicalEstimate).filter(SurgicalEstimate.status == "pending").count(),
        pending_contracts=db.query(SurgicalContract).filter(SurgicalContract.status == "pending_signature").count(),
        monthly_revenue=0.0,  # Calculate from payments
        conversion_rate=0.0,  # Calculate from estimates to contracts
        average_contract_value=0.0,  # Calculate from contracts
        top_procedures=[],  # Query most requested procedures
        revenue_trend=[]  # Query revenue over time
    )
    
    return stats

@router.get("/analytics/estimates", response_model=EstimateAnalytics, summary="Get estimate analytics")
async def get_estimate_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get estimate analytics"""
    # Implement actual analytics queries
    analytics = EstimateAnalytics(
        total_estimates=0,
        converted_estimates=0,
        pending_estimates=0,
        expired_estimates=0,
        average_conversion_time_days=0.0,
        conversion_rate_by_procedure=[]
    )
    
    return analytics

@router.get("/analytics/contracts", response_model=ContractAnalytics, summary="Get contract analytics")
async def get_contract_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get contract analytics"""
    # Implement actual analytics queries
    analytics = ContractAnalytics(
        total_contracts=0,
        active_contracts=0,
        completed_contracts=0,
        cancelled_contracts=0,
        average_contract_value=0.0,
        payment_completion_rate=0.0,
        contracts_by_status=[]
    )
    
    return analytics
