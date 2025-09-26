"""
Advanced Secretarial Dashboard API
Patient queue management, real-time updates, and workflow optimization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, asc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.secretary import PatientCheckIn, WaitingPanel, DailyAgenda
from app.services.auth_service import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for API responses
class PatientQueueItem(BaseModel):
    id: int
    patient_name: str
    patient_id: int
    appointment_id: int
    check_in_time: datetime
    estimated_wait_time: int  # minutes
    priority: str  # low, medium, high, emergency
    status: str  # waiting, in_progress, completed, cancelled
    doctor_name: Optional[str] = None
    appointment_type: str
    insurance_status: str
    notes: Optional[str] = None

class QueueStats(BaseModel):
    total_patients: int
    waiting_patients: int
    in_progress_patients: int
    completed_today: int
    average_wait_time: int
    longest_wait_time: int
    doctors_available: int
    estimated_completion_time: Optional[datetime] = None

class DoctorSchedule(BaseModel):
    doctor_id: int
    doctor_name: str
    specialty: str
    current_patient: Optional[str] = None
    next_patient: Optional[str] = None
    patients_remaining: int
    estimated_end_time: Optional[datetime] = None
    status: str  # available, busy, break, offline

class DashboardSummary(BaseModel):
    queue_stats: QueueStats
    patient_queue: List[PatientQueueItem]
    doctor_schedules: List[DoctorSchedule]
    urgent_alerts: List[Dict[str, Any]]
    daily_metrics: Dict[str, Any]

# Dependency to get current user
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    token = auth_header.split(" ")[1]
    try:
        auth_service = AuthService(db)
        token_data = auth_service.verify_token(token)
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/dashboard", response_model=DashboardSummary)
async def get_secretarial_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive secretarial dashboard data
    """
    try:
        # Get queue statistics
        queue_stats = await get_queue_statistics(db)
        
        # Get patient queue
        patient_queue = await get_patient_queue(db)
        
        # Get doctor schedules
        doctor_schedules = await get_doctor_schedules(db)
        
        # Get urgent alerts
        urgent_alerts = await get_urgent_alerts(db)
        
        # Get daily metrics
        daily_metrics = await get_daily_metrics(db)
        
        return DashboardSummary(
            queue_stats=queue_stats,
            patient_queue=patient_queue,
            doctor_schedules=doctor_schedules,
            urgent_alerts=urgent_alerts,
            daily_metrics=daily_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting secretarial dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )

@router.get("/queue", response_model=List[PatientQueueItem])
async def get_patient_queue(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None
):
    """
    Get patient queue with optional filters
    """
    try:
        query = """
            SELECT 
                pc.id,
                p.full_name as patient_name,
                p.id as patient_id,
                a.id as appointment_id,
                pc.check_in_time,
                pc.estimated_wait_time,
                pc.priority,
                pc.status,
                u.full_name as doctor_name,
                a.appointment_type,
                pc.insurance_status,
                pc.notes
            FROM patient_checkins pc
            JOIN patients p ON pc.patient_id = p.id
            JOIN appointments a ON pc.appointment_id = a.id
            LEFT JOIN users u ON a.doctor_id = u.id
            WHERE pc.check_in_date = CURRENT_DATE
        """
        
        params = {}
        if status_filter:
            query += " AND pc.status = :status_filter"
            params["status_filter"] = status_filter
        if priority_filter:
            query += " AND pc.priority = :priority_filter"
            params["priority_filter"] = priority_filter
            
        query += " ORDER BY pc.priority DESC, pc.check_in_time ASC"
        
        cursor = db.execute(text(query), params)
        results = cursor.fetchall()
        
        queue_items = []
        for row in results:
            queue_items.append(PatientQueueItem(
                id=row.id,
                patient_name=row.patient_name,
                patient_id=row.patient_id,
                appointment_id=row.appointment_id,
                check_in_time=row.check_in_time,
                estimated_wait_time=row.estimated_wait_time,
                priority=row.priority,
                status=row.status,
                doctor_name=row.doctor_name,
                appointment_type=row.appointment_type,
                insurance_status=row.insurance_status,
                notes=row.notes
            ))
        
        return queue_items
        
    except Exception as e:
        logger.error(f"Error getting patient queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load patient queue: {str(e)}"
        )

@router.post("/queue/{checkin_id}/update-status")
async def update_patient_status(
    checkin_id: int,
    new_status: str,
    notes: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update patient status in queue
    """
    try:
        # Validate status
        valid_statuses = ["waiting", "in_progress", "completed", "cancelled"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        # Update check-in status
        query = """
            UPDATE patient_checkins 
            SET status = :new_status, 
                updated_at = CURRENT_TIMESTAMP,
                notes = COALESCE(:notes, notes)
            WHERE id = :checkin_id
        """
        
        db.execute(text(query), {
            "new_status": new_status,
            "notes": notes,
            "checkin_id": checkin_id
        })
        db.commit()
        
        # Update appointment status if needed
        if new_status == "completed":
            appointment_query = """
                UPDATE appointments 
                SET status = 'completed', 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT appointment_id 
                    FROM patient_checkins 
                    WHERE id = :checkin_id
                )
            """
            db.execute(text(appointment_query), {"checkin_id": checkin_id})
            db.commit()
        
        return {"message": f"Patient status updated to {new_status}"}
        
    except Exception as e:
        logger.error(f"Error updating patient status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient status: {str(e)}"
        )

@router.post("/queue/{checkin_id}/priority")
async def update_patient_priority(
    checkin_id: int,
    priority: str,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update patient priority in queue
    """
    try:
        valid_priorities = ["low", "medium", "high", "emergency"]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {valid_priorities}"
            )
        
        query = """
            UPDATE patient_checkins 
            SET priority = :priority, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :checkin_id
        """
        
        db.execute(text(query), {
            "priority": priority,
            "checkin_id": checkin_id
        })
        db.commit()
        
        return {"message": f"Patient priority updated to {priority}"}
        
    except Exception as e:
        logger.error(f"Error updating patient priority: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient priority: {str(e)}"
        )

@router.get("/statistics", response_model=QueueStats)
async def get_queue_statistics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get queue statistics and metrics
    """
    try:
        # Get basic counts
        stats_query = """
            SELECT 
                COUNT(*) as total_patients,
                COUNT(CASE WHEN status = 'waiting' THEN 1 END) as waiting_patients,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_patients,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_today,
                AVG(estimated_wait_time) as average_wait_time,
                MAX(estimated_wait_time) as longest_wait_time
            FROM patient_checkins 
            WHERE check_in_date = CURRENT_DATE
        """
        
        cursor = db.execute(text(stats_query))
        stats = cursor.fetchone()
        
        # Get available doctors count
        doctors_query = """
            SELECT COUNT(*) as doctors_available
            FROM users u
            WHERE u.is_active = true 
            AND u.crm IS NOT NULL 
            AND u.id IN (
                SELECT DISTINCT doctor_id 
                FROM appointments 
                WHERE appointment_date = CURRENT_DATE
            )
        """
        
        cursor = db.execute(text(doctors_query))
        doctors_count = cursor.fetchone().doctors_available
        
        # Calculate estimated completion time
        estimated_completion = None
        if stats.waiting_patients > 0 and doctors_count > 0:
            avg_time_per_patient = 30  # minutes
            total_time_needed = (stats.waiting_patients * avg_time_per_patient) / doctors_count
            estimated_completion = datetime.now() + timedelta(minutes=total_time_needed)
        
        return QueueStats(
            total_patients=stats.total_patients or 0,
            waiting_patients=stats.waiting_patients or 0,
            in_progress_patients=stats.in_progress_patients or 0,
            completed_today=stats.completed_today or 0,
            average_wait_time=int(stats.average_wait_time or 0),
            longest_wait_time=int(stats.longest_wait_time or 0),
            doctors_available=doctors_count,
            estimated_completion_time=estimated_completion
        )
        
    except Exception as e:
        logger.error(f"Error getting queue statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load statistics: {str(e)}"
        )

async def get_queue_statistics(db: Session) -> QueueStats:
    """Helper function to get queue statistics"""
    # Implementation similar to the endpoint above
    pass

async def get_patient_queue(db: Session) -> List[PatientQueueItem]:
    """Helper function to get patient queue"""
    # Implementation similar to the endpoint above
    pass

async def get_doctor_schedules(db: Session) -> List[DoctorSchedule]:
    """Helper function to get doctor schedules"""
    try:
        query = """
            SELECT 
                u.id as doctor_id,
                u.full_name as doctor_name,
                u.specialty,
                COUNT(a.id) as patients_remaining,
                MAX(a.appointment_date + INTERVAL '1 hour') as estimated_end_time
            FROM users u
            LEFT JOIN appointments a ON u.id = a.doctor_id 
                AND a.appointment_date = CURRENT_DATE 
                AND a.status IN ('scheduled', 'in_progress')
            WHERE u.is_active = true AND u.crm IS NOT NULL
            GROUP BY u.id, u.full_name, u.specialty
            ORDER BY patients_remaining DESC
        """
        
        cursor = db.execute(text(query))
        results = cursor.fetchall()
        
        schedules = []
        for row in results:
            schedules.append(DoctorSchedule(
                doctor_id=row.doctor_id,
                doctor_name=row.doctor_name,
                specialty=row.specialty,
                current_patient=None,  # Would need additional logic
                next_patient=None,    # Would need additional logic
                patients_remaining=row.patients_remaining,
                estimated_end_time=row.estimated_end_time,
                status="available"  # Would need additional logic
            ))
        
        return schedules
        
    except Exception as e:
        logger.error(f"Error getting doctor schedules: {e}")
        return []

async def get_urgent_alerts(db: Session) -> List[Dict[str, Any]]:
    """Helper function to get urgent alerts"""
    alerts = []
    
    try:
        # Check for patients waiting too long
        long_wait_query = """
            SELECT 
                pc.id,
                p.full_name,
                pc.check_in_time,
                pc.estimated_wait_time
            FROM patient_checkins pc
            JOIN patients p ON pc.patient_id = p.id
            WHERE pc.status = 'waiting' 
            AND pc.check_in_time < CURRENT_TIMESTAMP - INTERVAL '2 hours'
            AND pc.check_in_date = CURRENT_DATE
        """
        
        cursor = db.execute(text(long_wait_query))
        long_waits = cursor.fetchall()
        
        for row in long_waits:
            alerts.append({
                "type": "long_wait",
                "severity": "high",
                "message": f"Patient {row.full_name} has been waiting for over 2 hours",
                "patient_id": row.id,
                "timestamp": row.check_in_time
            })
        
        # Check for emergency priority patients
        emergency_query = """
            SELECT 
                pc.id,
                p.full_name,
                pc.check_in_time
            FROM patient_checkins pc
            JOIN patients p ON pc.patient_id = p.id
            WHERE pc.priority = 'emergency' 
            AND pc.status = 'waiting'
            AND pc.check_in_date = CURRENT_DATE
        """
        
        cursor = db.execute(text(emergency_query))
        emergencies = cursor.fetchall()
        
        for row in emergencies:
            alerts.append({
                "type": "emergency",
                "severity": "critical",
                "message": f"Emergency patient {row.full_name} is waiting",
                "patient_id": row.id,
                "timestamp": row.check_in_time
            })
        
    except Exception as e:
        logger.error(f"Error getting urgent alerts: {e}")
    
    return alerts

async def get_daily_metrics(db: Session) -> Dict[str, Any]:
    """Helper function to get daily metrics"""
    try:
        metrics_query = """
            SELECT 
                COUNT(*) as total_appointments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_appointments,
                COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_appointments,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/60) as avg_appointment_duration
            FROM appointments 
            WHERE appointment_date = CURRENT_DATE
        """
        
        cursor = db.execute(text(metrics_query))
        metrics = cursor.fetchone()
        
        return {
            "total_appointments": metrics.total_appointments or 0,
            "completed_appointments": metrics.completed_appointments or 0,
            "cancelled_appointments": metrics.cancelled_appointments or 0,
            "completion_rate": round(
                (metrics.completed_appointments / metrics.total_appointments * 100) 
                if metrics.total_appointments > 0 else 0, 2
            ),
            "average_duration_minutes": round(metrics.avg_appointment_duration or 0, 1)
        }
        
    except Exception as e:
        logger.error(f"Error getting daily metrics: {e}")
        return {
            "total_appointments": 0,
            "completed_appointments": 0,
            "cancelled_appointments": 0,
            "completion_rate": 0,
            "average_duration_minutes": 0
        }
