#!/usr/bin/env python3
"""
Script to create the initial admin user for the Hospital Information System.
Run this script after setting up the database.

Usage:
    python initial_admin.py
"""

from database import SessionLocal, init_db
from models.user import User, UserRole
from auth import get_password_hash

def create_initial_admin():
    """Create the first admin user"""
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
        if existing_admin:
            print("ℹ️  An admin user already exists. Updating password...")
            password = input("Enter new password (default: admin123): ").strip() or "admin123"
            existing_admin.password_hash = get_password_hash(password)
            db.commit()
            print("✅ Admin password updated successfully!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Full Name: {existing_admin.full_name}")
            return
        
        # Get admin details
        print("=" * 50)
        print("Create Initial Admin User")
        print("=" * 50)
        
        username = input("Enter username (default: admin): ").strip() or "admin"
        full_name = input("Enter full name (default: مدیر سیستم): ").strip() or "مدیر سیستم"
        password = input("Enter password (default: admin123): ").strip() or "admin123"
        
        # Create admin user
        admin = User(
            username=username,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=UserRole.admin,
            is_active=True,
            created_by=None  # First user has no creator
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"Username: {admin.username}")
        print(f"Full Name: {admin.full_name}")
        print(f"Role: مدیرکل (Admin)")
        print("\nYou can now login to the system at: http://localhost:8000")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()
