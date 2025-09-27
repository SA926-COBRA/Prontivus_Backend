#!/usr/bin/env python3
"""
Script to check users and permissions in the Prontivus database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def check_database_connection():
    """Check if we can connect to the database"""
    try:
        # Use the same database URL as the application
        engine = create_engine(settings.constructed_database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def check_users_table(engine):
    """Check the users table structure and data"""
    print("\n" + "="*60)
    print("USERS TABLE ANALYSIS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)).fetchone()
            
            if not result[0]:
                print("❌ Users table does not exist!")
                return
            
            print("✅ Users table exists")
            
            # Get table structure
            print("\n📋 Table Structure:")
            columns = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """)).fetchall()
            
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  • {col[0]}: {col[1]} {nullable}{default}")
            
            # Count total users
            count = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            print(f"\n👥 Total users: {count}")
            
            if count == 0:
                print("⚠️  No users found in the database!")
                return
            
            # Get all users with their basic info
            print("\n👤 User Details:")
            users = conn.execute(text("""
                SELECT 
                    id, email, username, full_name, cpf, crm,
                    is_active, is_verified, is_superuser,
                    created_at, last_login
                FROM users 
                ORDER BY id;
            """)).fetchall()
            
            for user in users:
                print(f"\n  ID: {user[0]}")
                print(f"  Email: {user[1]}")
                print(f"  Username: {user[2] or 'N/A'}")
                print(f"  Full Name: {user[3]}")
                print(f"  CPF: {user[4] or 'N/A'}")
                print(f"  CRM: {user[5] or 'N/A'}")
                print(f"  Active: {'✅' if user[6] else '❌'}")
                print(f"  Verified: {'✅' if user[7] else '❌'}")
                print(f"  Superuser: {'✅' if user[8] else '❌'}")
                print(f"  Created: {user[9]}")
                print(f"  Last Login: {user[10] or 'Never'}")
                
    except Exception as e:
        print(f"❌ Error checking users table: {e}")

def check_roles_table(engine):
    """Check the roles table structure and data"""
    print("\n" + "="*60)
    print("ROLES TABLE ANALYSIS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Check if roles table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'roles'
                );
            """)).fetchone()
            
            if not result[0]:
                print("❌ Roles table does not exist!")
                return
            
            print("✅ Roles table exists")
            
            # Get all roles
            roles = conn.execute(text("""
                SELECT id, name, description, permissions, created_at
                FROM roles 
                ORDER BY id;
            """)).fetchall()
            
            print(f"\n🔐 Available Roles ({len(roles)}):")
            for role in roles:
                print(f"\n  ID: {role[0]}")
                print(f"  Name: {role[1]}")
                print(f"  Description: {role[2]}")
                print(f"  Permissions: {role[3]}")
                print(f"  Created: {role[4]}")
                
    except Exception as e:
        print(f"❌ Error checking roles table: {e}")

def check_user_roles_table(engine):
    """Check the user_roles table (many-to-many relationship)"""
    print("\n" + "="*60)
    print("USER-ROLE ASSIGNMENTS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Check if user_roles table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_roles'
                );
            """)).fetchone()
            
            if not result[0]:
                print("❌ User_roles table does not exist!")
                return
            
            print("✅ User_roles table exists")
            
            # Get user-role assignments
            assignments = conn.execute(text("""
                SELECT 
                    u.id, u.email, u.full_name, r.name as role_name, ur.created_at
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.id
                JOIN roles r ON ur.role_id = r.id
                ORDER BY u.id, r.name;
            """)).fetchall()
            
            if not assignments:
                print("⚠️  No role assignments found!")
                return
            
            print(f"\n👥 User-Role Assignments ({len(assignments)}):")
            current_user = None
            for assignment in assignments:
                if current_user != assignment[0]:
                    current_user = assignment[0]
                    print(f"\n  User: {assignment[2]} ({assignment[1]})")
                print(f"    • Role: {assignment[3]} (assigned: {assignment[4]})")
                
    except Exception as e:
        print(f"❌ Error checking user_roles table: {e}")

def check_user_permissions(engine, user_email=None):
    """Check permissions for a specific user or all users"""
    print("\n" + "="*60)
    print("USER PERMISSIONS ANALYSIS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Build query based on whether we're checking a specific user
            if user_email:
                query = text("""
                    SELECT 
                        u.id, u.email, u.full_name, u.is_superuser,
                        r.name as role_name, r.permissions
                    FROM users u
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    WHERE u.email = :email
                    ORDER BY u.id, r.name;
                """)
                params = {"email": user_email}
                print(f"🔍 Checking permissions for: {user_email}")
            else:
                query = text("""
                    SELECT 
                        u.id, u.email, u.full_name, u.is_superuser,
                        r.name as role_name, r.permissions
                    FROM users u
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    ORDER BY u.id, r.name;
                """)
                params = {}
                print("🔍 Checking permissions for all users")
            
            results = conn.execute(query, params).fetchall()
            
            if not results:
                print("❌ No users found!")
                return
            
            current_user = None
            for result in results:
                if current_user != result[0]:
                    if current_user is not None:
                        print()  # Add spacing between users
                    current_user = result[0]
                    print(f"\n👤 User: {result[2]} ({result[1]})")
                    print(f"   ID: {result[0]}")
                    print(f"   Superuser: {'✅' if result[3] else '❌'}")
                
                if result[4]:  # If role exists
                    print(f"   🔐 Role: {result[4]}")
                    print(f"   📋 Permissions: {result[5]}")
                else:
                    print("   ⚠️  No roles assigned (treated as patient)")
                    
    except Exception as e:
        print(f"❌ Error checking user permissions: {e}")

def main():
    """Main function"""
    print("🔍 Prontivus Database User & Permission Checker")
    print("=" * 60)
    
    # Check database connection
    engine = check_database_connection()
    if not engine:
        return
    
    # Check all tables and data
    check_users_table(engine)
    check_roles_table(engine)
    check_user_roles_table(engine)
    check_user_permissions(engine)
    
    # Check specific user if provided as argument
    if len(sys.argv) > 1:
        user_email = sys.argv[1]
        check_user_permissions(engine, user_email)
    
    print("\n" + "="*60)
    print("✅ Analysis complete!")
    print("\n💡 Tips:")
    print("  • Use 'python check_users_and_permissions.py user@example.com' to check specific user")
    print("  • Default users: admin@prontivus.com, doctor@prontivus.com, secretary@prontivus.com, patient@prontivus.com")
    print("  • Default passwords: admin123, doctor123, secretary123, patient123")

if __name__ == "__main__":
    main()
