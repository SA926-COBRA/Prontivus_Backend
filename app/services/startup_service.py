"""
Startup service for automatic database initialization
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.database.database import Base, get_engine, create_tables
from app.models import user, patient, appointment, medical_record, prescription, tenant, license, financial, secretary, audit

logger = logging.getLogger(__name__)

class DatabaseStartupService:
    """Service for automatic database initialization and management"""
    
    def __init__(self):
        self.engine = None
        self.database_exists = False
        self.tables_exist = False
        
    def check_database_connection(self) -> bool:
        """Check if database connection is available"""
        try:
            use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
            
            if use_sqlite:
                # For SQLite, check if file exists
                db_path = "./prontivus_offline.db"
                self.database_exists = os.path.exists(db_path)
                if self.database_exists:
                    logger.info("📱 SQLite database file found")
                else:
                    logger.info("📱 SQLite database file not found - will create")
            else:
                # For PostgreSQL, check connection
                db_url = settings.constructed_database_url
                logger.info(f"🔗 Using DATABASE_URL: {db_url}")
                try:
                    temp_engine = create_engine(db_url)
                    with temp_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    self.database_exists = True
                    logger.info("🌐 PostgreSQL database connection successful")
                except Exception as e:
                    self.database_exists = False
                    logger.warning(f"🌐 PostgreSQL database connection failed: {e}")
                    logger.info("🌐 Will attempt to create database")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection check failed: {e}")
            return False
    
    def check_tables_exist(self) -> bool:
        """Check if database tables exist"""
        try:
            if not self.database_exists:
                return False
                
            engine = get_engine()
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # Check for key tables
            required_tables = ['users', 'patients', 'appointments', 'medical_records', 'prescriptions', 'tenants']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.info(f"📊 Missing tables: {missing_tables}")
                self.tables_exist = False
                return False
            else:
                logger.info("📊 All required tables exist")
                self.tables_exist = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Error checking tables: {e}")
            self.tables_exist = False
            return False
    
    def create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist (PostgreSQL only)"""
        try:
            use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
            
            if use_sqlite:
                # SQLite databases are created automatically
                logger.info("📱 SQLite database will be created automatically")
                return True
            
            # For PostgreSQL, check if it's a managed service (like Render.com)
            db_url = settings.constructed_database_url
            if "render.com" in db_url or "heroku.com" in db_url or "aws.amazonaws.com" in db_url:
                # Managed database service - database already exists
                logger.info("🌐 Using managed PostgreSQL database (Render.com/Heroku/AWS)")
                logger.info("🌐 Database is managed externally - no creation needed")
                return True
            
            # For self-hosted PostgreSQL, try to create database
            try:
                # Parse database URL to get connection details
                db_url_parts = db_url.replace("postgresql://", "").split("/")
                db_name = db_url_parts[-1]
                connection_string = "/".join(db_url_parts[:-1])
                
                # Connect to PostgreSQL server (without specific database)
                server_engine = create_engine(f"postgresql://{connection_string}/postgres")
                
                with server_engine.connect() as conn:
                    # Check if database exists
                    result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
                    if result.fetchone():
                        logger.info(f"🌐 Database '{db_name}' already exists")
                        return True
                    
                    # Create database
                    conn.execute(text("COMMIT"))  # End any transaction
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"🌐 Database '{db_name}' created successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Failed to create PostgreSQL database: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False
    
    def create_tables_if_not_exist(self) -> bool:
        """Create tables if they don't exist"""
        try:
            logger.info("📊 Creating database tables...")
            
            # Import all models to ensure they're registered
            from app.models import user, patient, appointment, medical_record, prescription, tenant, license, financial, secretary, audit
            
            # Create tables with explicit transaction handling
            from app.database.database import get_engine, Base
            engine = get_engine()
            
            with engine.begin() as conn:
                # Create all tables in a single transaction
                Base.metadata.create_all(bind=conn)
                logger.info("✅ Database tables created successfully")
            
            # Verify tables were created
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            required_tables = ['users', 'patients', 'appointments', 'medical_records', 'prescriptions', 'tenants']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.warning(f"⚠️ Some tables still missing after creation: {missing_tables}")
                return False
            
            logger.info("✅ All required tables verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False
    
    def create_default_data_if_empty(self) -> bool:
        """Create default data if database is empty"""
        try:
            import time
            from app.database.database import get_session_local
            from app.models.user import User, Role, UserRole
            from app.models.patient import Patient
            from app.models.appointment import Appointment
            from app.models.medical_record import MedicalRecord
            from app.models.prescription import Prescription
            from app.models.tenant import Tenant
            from passlib.context import CryptContext
            from datetime import datetime
            from sqlalchemy import text
            
            # Small delay to ensure tables are fully committed
            time.sleep(0.5)
            
            SessionLocal = get_session_local()
            db = SessionLocal()
            
            try:
                # Check if any users exist using raw SQL to avoid ORM issues
                try:
                    result = db.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = result.scalar()
                    if user_count > 0:
                        logger.info(f"📊 Database already contains {user_count} users - skipping default data creation")
                        return True
                except Exception as e:
                    # If users table doesn't exist or has issues, proceed with data creation
                    logger.info("📊 Users table not accessible - proceeding with default data creation")
                
                logger.info("📊 Creating default data...")
                
                # Password hashing
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                # Create default tenant
                try:
                    tenant = Tenant(
                        name="Prontivus Clinic",
                        legal_name="Prontivus Clinic Ltda",
                        type="clinic",
                        status="active",
                        email="admin@prontivus.com",
                        phone="(11) 99999-9999",
                        website="https://prontivus.com",
                        address_line1="Rua das Flores, 123",
                        city="São Paulo",
                        state="SP",
                        postal_code="01234-567",
                        country="Brazil",
                        created_at=datetime.now()
                    )
                    db.add(tenant)
                    db.flush()
                    logger.info("✅ Created default tenant")
                except Exception as e:
                    logger.error(f"❌ Failed to create tenant: {e}")
                    # Try to get existing tenant or create a minimal one
                    try:
                        existing_tenant = db.query(Tenant).first()
                        if existing_tenant:
                            tenant = existing_tenant
                            logger.info("✅ Using existing tenant")
                        else:
                            raise Exception("No tenant available and cannot create one")
                    except Exception:
                        logger.error("❌ Cannot proceed without tenant - skipping default data creation")
                        return False
                
                # Create default roles
                roles_data = [
                    {"name": "admin", "description": "System Administrator", "permissions": ["*"]},
                    {"name": "doctor", "description": "Medical Doctor", "permissions": ["patients:read", "patients:update", "appointments:create", "appointments:read", "appointments:update", "medical_records:create", "medical_records:read", "medical_records:update", "prescriptions:create", "prescriptions:read", "prescriptions:update", "reports:read"]},
                    {"name": "secretary", "description": "Secretary/Receptionist", "permissions": ["patients:create", "patients:read", "patients:update", "appointments:create", "appointments:read", "appointments:update", "appointments:delete", "reports:read"]},
                    {"name": "patient", "description": "Patient with limited access to own data", "permissions": ["own_data:read", "appointments:read", "prescriptions:read"]}
                ]
                
                created_roles = {}
                for role_data in roles_data:
                    role = Role(**role_data)
                    db.add(role)
                    db.flush()
                    created_roles[role_data["name"]] = role
                    logger.info(f"✅ Created role: {role_data['name']}")
                
                # Create default users
                users_data = [
                    {
                        "email": "admin@prontivus.com",
                        "username": "admin",
                        "full_name": "System Administrator",
                        "hashed_password": pwd_context.hash("admin123"),
                        "is_active": True,
                        "is_verified": True,
                        "is_superuser": True,
                        "role": "admin"
                    },
                    {
                        "email": "doctor@prontivus.com",
                        "username": "doctor",
                        "full_name": "Dr. João Silva",
                        "hashed_password": pwd_context.hash("doctor123"),
                        "is_active": True,
                        "is_verified": True,
                        "is_superuser": False,
                        "crm": "12345",
                        "specialty": "Cardiologia",
                        "role": "doctor"
                    },
                    {
                        "email": "secretary@prontivus.com",
                        "username": "secretary",
                        "full_name": "Maria Santos",
                        "hashed_password": pwd_context.hash("secretary123"),
                        "is_active": True,
                        "is_verified": True,
                        "is_superuser": False,
                        "role": "secretary"
                    },
                    {
                        "email": "patient@prontivus.com",
                        "username": "patient",
                        "full_name": "Ana Costa",
                        "hashed_password": pwd_context.hash("patient123"),
                        "is_active": True,
                        "is_verified": True,
                        "is_superuser": False,
                        "cpf": "12345678901",
                        "phone": "(11) 99999-9999",
                        "role": "patient"
                    }
                ]
                
                created_users = {}
                for user_data in users_data:
                    user_role = user_data.pop("role")
                    user = User(**user_data)
                    db.add(user)
                    db.flush()
                    created_users[user_role] = user
                    logger.info(f"✅ Created {user_role}: {user_data['email']}")
                
                # Assign roles to users
                role_assignments = [
                    ("admin", "admin"),
                    ("doctor", "doctor"),
                    ("secretary", "secretary"),
                    ("patient", "patient")
                ]
                
                for user_role, role_name in role_assignments:
                    if user_role in created_users and role_name in created_roles:
                        user_role_assignment = UserRole(
                            user_id=created_users[user_role].id,
                            role_id=created_roles[role_name].id,
                            tenant_id=tenant.id,
                            created_at=datetime.now()
                        )
                        db.add(user_role_assignment)
                        logger.info(f"✅ Assigned {role_name} role to {user_role}")
                
                # Create sample patient record
                patient_data = {
                    "tenant_id": tenant.id,
                    "user_id": created_users["patient"].id,
                    "full_name": "Ana Costa",
                    "cpf": "12345678901",
                    "birth_date": "1985-03-15",
                    "gender": "F",
                    "phone": "(11) 99999-9999",
                    "address": "Rua das Flores, 123",
                    "insurance_company": "Unimed",
                    "insurance_number": "123456789"
                }
                
                patient = Patient(**patient_data)
                db.add(patient)
                db.flush()
                logger.info("✅ Created sample patient record")
                
                # Create sample appointment
                appointment_data = {
                    "tenant_id": tenant.id,
                    "patient_id": patient.id,
                    "doctor_id": created_users["doctor"].id,
                    "appointment_date": datetime(2024, 1, 20, 14, 0),  # Combined date and time
                    "type": "consultation",
                    "status": "scheduled",
                    "notes": "Consulta de rotina"
                }
                
                appointment = Appointment(**appointment_data)
                db.add(appointment)
                logger.info("✅ Created sample appointment")
                
                # Create sample medical record
                medical_record_data = {
                    "patient_id": patient.id,
                    "doctor_id": created_users["doctor"].id,
                    "date": "2024-01-20",
                    "type": "Consulta",
                    "diagnosis": "Hipertensão arterial",
                    "treatment": "Controle da pressão arterial",
                    "notes": "Paciente apresentou melhora significativa"
                }
                
                medical_record = MedicalRecord(**medical_record_data)
                db.add(medical_record)
                logger.info("✅ Created sample medical record")
                
                # Create sample prescription
                prescription_data = {
                    "patient_id": patient.id,
                    "doctor_id": created_users["doctor"].id,
                    "issued_date": "2024-01-20",
                    "medications": [
                        {
                            "name": "Paracetamol",
                            "dosage": "500mg",
                            "frequency": "3x ao dia",
                            "duration": "7 dias"
                        }
                    ],
                    "notes": "Tomar com alimentos",
                    "status": "active"
                }
                
                prescription = Prescription(**prescription_data)
                db.add(prescription)
                logger.info("✅ Created sample prescription")
                
                # Commit all changes
                db.commit()
                logger.info("✅ Default data created successfully!")
                
                return True
                
            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error creating default data: {e}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to create default data: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Complete database initialization process"""
        logger.info("🚀 Starting automatic database initialization...")
        logger.info("=" * 60)
        
        try:
            # Step 1: Check database connection
            logger.info("Step 1: Checking database connection...")
            if not self.check_database_connection():
                logger.error("❌ Database connection check failed")
                return False
            
            # Step 2: Create database if it doesn't exist (PostgreSQL only)
            logger.info("Step 2: Ensuring database exists...")
            if not self.create_database_if_not_exists():
                logger.error("❌ Database creation failed")
                return False
            
            # Step 3: Check if tables exist
            logger.info("Step 3: Checking database tables...")
            self.check_tables_exist()
            
            # Step 4: Create tables if they don't exist
            if not self.tables_exist:
                logger.info("Step 4: Creating database tables...")
                if not self.create_tables_if_not_exist():
                    logger.error("❌ Table creation failed")
                    return False
            else:
                logger.info("Step 4: Tables already exist - skipping creation")
            
            # Step 5: Create default data if database is empty (optional for deployment)
            logger.info("Step 5: Checking for default data...")
            try:
                self.create_default_data_if_empty()
                logger.info("✅ Default data creation completed")
            except Exception as e:
                logger.warning(f"⚠️ Default data creation skipped: {e}")
                logger.info("📊 Database is ready for deployment without default data")
            
            logger.info("=" * 60)
            logger.info("🎉 Database initialization completed successfully!")
            logger.info("")
            logger.info("Default credentials:")
            logger.info("Admin: admin@prontivus.com / admin123")
            logger.info("Doctor: doctor@prontivus.com / doctor123")
            logger.info("Secretary: secretary@prontivus.com / secretary123")
            logger.info("Patient: patient@prontivus.com / patient123")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False

def initialize_database_on_startup() -> bool:
    """Initialize database on application startup"""
    service = DatabaseStartupService()
    return service.initialize_database()