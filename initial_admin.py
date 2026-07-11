#!/usr/bin/env python3

from auth import get_password_hash
from database import get_db, init_db, now, one


def create_initial_admin():
    init_db()
    db = next(get_db())

    existing_admin = one(db, "SELECT * FROM users WHERE role = 'admin' LIMIT 1")
    if existing_admin:
        print("An admin user already exists. Updating password...")
        password = input("Enter new password (default: admin123): ").strip() or "admin123"
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (get_password_hash(password), existing_admin.id))
        db.commit()
        print("Admin password updated successfully.")
        print(f"Username: {existing_admin.username}")
        print(f"Full Name: {existing_admin.full_name}")
        db.close()
        return

    print("=" * 50)
    print("Create Initial Admin User")
    print("=" * 50)

    username = input("Enter username (default: admin): ").strip() or "admin"
    full_name = input("Enter full name (default: System Admin): ").strip() or "System Admin"
    password = input("Enter password (default: admin123): ").strip() or "admin123"

    db.execute(
        """
        INSERT INTO users (username, password_hash, full_name, role, is_active, created_at, created_by)
        VALUES (?, ?, ?, 'admin', 1, ?, NULL)
        """,
        (username, get_password_hash(password), full_name, now()),
    )
    db.commit()
    db.close()

    print("Admin user created successfully.")
    print(f"Username: {username}")
    print(f"Full Name: {full_name}")


if __name__ == "__main__":
    create_initial_admin()
