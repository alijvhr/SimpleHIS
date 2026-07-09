#!/usr/bin/env python3
"""Seed catalog data for local HIS testing.

Usage:
    python seeder.py
"""

from decimal import Decimal

from database import SessionLocal, init_db
from models.drug import Drug
from models.lab_test import LabTest
from models.stock import StockTransaction
from models.user import User, UserRole


USERS = [
    ("admin", "System Admin", UserRole.admin),
    ("reception", "Reception User", UserRole.reception),
    ("doctor", "Doctor User", UserRole.doctor),
    ("laboratory", "Laboratory User", UserRole.laboratory),
    ("radiology", "Radiology User", UserRole.radiologist),
    ("pharmacy", "Pharmacy User", UserRole.pharmacy),
]

DEFAULT_PASSWORD_HASH = "$2b$12$hIxdXLiBf79n2d2ynD1B1uatgwB/l0w9XwIDwLzjVvPd2.NJpw5YG"
ADMIN_PASSWORD_HASH = "$2b$12$YIxB/2ydoOiIHv4HL2m30u5JMgOX3V3EYNCd7wn46X3MdWuwq1H6i"

DRUGS = [
    ("Acetaminophen", "Pars Darou", "Tablet", "500mg", "1 tablet every 8 hours as needed", 12000, 30),
    ("Ibuprofen", "Hakim", "Tablet", "400mg", "1 tablet every 8 hours after food", 18000, 25),
    ("Naproxen", "Sobhan", "Tablet", "250mg", "1 tablet every 12 hours after food", 22000, 20),
    ("Diclofenac", "Darou Pakhsh", "Tablet", "50mg", "1 tablet every 12 hours after food", 16000, 20),
    ("Amoxicillin", "Farabi", "Capsule", "500mg", "1 capsule every 8 hours", 28000, 30),
    ("Co-Amoxiclav", "Exir", "Tablet", "625mg", "1 tablet every 8 hours", 65000, 20),
    ("Azithromycin", "Tehran Chemie", "Tablet", "250mg", "1 tablet daily", 55000, 20),
    ("Cephalexin", "Jaber", "Capsule", "500mg", "1 capsule every 6 hours", 32000, 25),
    ("Ciprofloxacin", "Amin", "Tablet", "500mg", "1 tablet every 12 hours", 42000, 20),
    ("Metronidazole", "Rouz Darou", "Tablet", "250mg", "1 tablet every 8 hours", 17000, 25),
    ("Loratadine", "Abidi", "Tablet", "10mg", "1 tablet daily", 15000, 20),
    ("Cetirizine", "Sobhan", "Tablet", "10mg", "1 tablet at night", 14000, 20),
    ("Diphenhydramine", "Darou Pakhsh", "Syrup", "12.5mg/5ml", "5 ml at night as needed", 24000, 15),
    ("Omeprazole", "Farabi", "Capsule", "20mg", "1 capsule before breakfast", 26000, 25),
    ("Pantoprazole", "Exir", "Tablet", "40mg", "1 tablet before breakfast", 30000, 25),
    ("Famotidine", "Hakim", "Tablet", "20mg", "1 tablet every 12 hours", 18000, 20),
    ("Metformin", "Amin", "Tablet", "500mg", "1 tablet twice daily with food", 19000, 30),
    ("Glibenclamide", "Jaber", "Tablet", "5mg", "1 tablet daily with breakfast", 16000, 20),
    ("Insulin Regular", "Novo", "Vial", "100IU/ml", "Use according to physician order", 145000, 10),
    ("Insulin NPH", "Novo", "Vial", "100IU/ml", "Use according to physician order", 150000, 10),
    ("Amlodipine", "Abidi", "Tablet", "5mg", "1 tablet daily", 21000, 25),
    ("Losartan", "Sobhan", "Tablet", "25mg", "1 tablet daily", 19000, 25),
    ("Valsartan", "Exir", "Tablet", "80mg", "1 tablet daily", 38000, 20),
    ("Atenolol", "Darou Pakhsh", "Tablet", "50mg", "1 tablet daily", 17000, 20),
    ("Furosemide", "Farabi", "Tablet", "40mg", "1 tablet morning", 15000, 20),
    ("Atorvastatin", "Amin", "Tablet", "20mg", "1 tablet at night", 34000, 25),
    ("Rosuvastatin", "Hakim", "Tablet", "10mg", "1 tablet at night", 47000, 20),
    ("Aspirin", "Darou Pakhsh", "Tablet", "80mg", "1 tablet daily", 9000, 30),
    ("Clopidogrel", "Jaber", "Tablet", "75mg", "1 tablet daily", 52000, 15),
    ("Warfarin", "Orchid", "Tablet", "5mg", "Use according to INR", 18000, 15),
    ("Salbutamol", "Caspian", "Inhaler", "100mcg", "1-2 puffs as needed", 85000, 10),
    ("Budesonide", "Caspian", "Inhaler", "200mcg", "Use according to physician order", 125000, 10),
    ("Montelukast", "Exir", "Tablet", "10mg", "1 tablet at night", 45000, 15),
    ("Prednisolone", "Abidi", "Tablet", "5mg", "Use according to physician order", 16000, 20),
    ("Dexamethasone", "Darou Pakhsh", "Ampoule", "8mg/2ml", "Use according to physician order", 22000, 15),
    ("Ondansetron", "Amin", "Tablet", "4mg", "1 tablet every 8 hours as needed", 39000, 15),
    ("Metoclopramide", "Farabi", "Tablet", "10mg", "1 tablet before meals as needed", 13000, 20),
    ("ORS", "Toliddaru", "Sachet", "Standard", "Dissolve in 1 liter water", 8000, 30),
    ("Ferrous Sulfate", "Rouz Darou", "Tablet", "50mg", "1 tablet daily", 12000, 25),
    ("Folic Acid", "Darou Pakhsh", "Tablet", "1mg", "1 tablet daily", 7000, 25),
    ("Vitamin D3", "Zahravi", "Pearl", "50000IU", "1 pearl weekly", 26000, 20),
    ("Calcium D", "Abidi", "Tablet", "500mg", "1 tablet daily", 30000, 20),
    ("Levothyroxine", "Iran Hormone", "Tablet", "50mcg", "1 tablet fasting", 15000, 25),
    ("Methimazole", "Iran Hormone", "Tablet", "5mg", "Use according to physician order", 18000, 15),
    ("Sertraline", "Sobhan", "Tablet", "50mg", "1 tablet daily", 42000, 15),
    ("Fluoxetine", "Farabi", "Capsule", "20mg", "1 capsule daily", 28000, 15),
    ("Alprazolam", "Loghman", "Tablet", "0.5mg", "Use according to physician order", 20000, 10),
    ("Carbamazepine", "Amin", "Tablet", "200mg", "Use according to physician order", 24000, 15),
    ("Phenytoin", "Darou Pakhsh", "Capsule", "100mg", "Use according to physician order", 22000, 15),
    ("Levetiracetam", "Orchid", "Tablet", "500mg", "Use according to physician order", 68000, 10),
]

LAB_TESTS = [
    ("CBC", "Complete Blood Count", "Hematology", "Whole blood", 90000, "13.5-17.5", "12.0-15.5", "g/dL"),
    ("FBS", "Fasting Blood Sugar", "Biochemistry", "Serum", 70000, "70-100", "70-100", "mg/dL"),
    ("BUN", "Blood Urea Nitrogen", "Biochemistry", "Serum", 65000, "7-20", "7-20", "mg/dL"),
    ("CR", "Creatinine", "Biochemistry", "Serum", 65000, "0.74-1.35", "0.59-1.04", "mg/dL"),
    ("ALT", "Alanine Aminotransferase", "Biochemistry", "Serum", 75000, "7-56", "7-45", "U/L"),
    ("AST", "Aspartate Aminotransferase", "Biochemistry", "Serum", 75000, "10-40", "9-32", "U/L"),
    ("TSH", "Thyroid Stimulating Hormone", "Hormone", "Serum", 160000, "0.4-4.0", "0.4-4.0", "mIU/L"),
    ("T4", "Thyroxine", "Hormone", "Serum", 145000, "5.0-12.0", "5.0-12.0", "ug/dL"),
    ("UA", "Urinalysis", "Urine", "Urine", 80000, "Normal", "Normal", None),
    ("CRP", "C-Reactive Protein", "Immunology", "Serum", 110000, "<10", "<10", "mg/L"),
]


def get_seed_user(db):
    user = db.query(User).filter(User.username == "admin").first()
    if user:
        return user

    user = User(
        username="admin",
        password_hash=ADMIN_PASSWORD_HASH,
        full_name="System Admin",
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_users(db, admin_id):
    for username, full_name, role in USERS:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.full_name = full_name
            user.role = role
            user.is_active = True
            continue
        db.add(User(
            username=username,
            password_hash=DEFAULT_PASSWORD_HASH,
            full_name=full_name,
            role=role,
            is_active=True,
            created_by=admin_id,
        ))


def seed_drugs(db, admin_id):
    created = 0
    for name, manufacturer, form, dosage, instructions, price, min_threshold in DRUGS:
        drug = db.query(Drug).filter(
            Drug.name == name,
            Drug.dosage == dosage,
            Drug.form == form,
        ).first()
        if not drug:
            drug = Drug(
                name=name,
                manufacturer=manufacturer,
                form=form,
                dosage=dosage,
                default_instructions=instructions,
                price=Decimal(price),
                min_threshold=min_threshold,
                created_by=admin_id,
            )
            db.add(drug)
            db.flush()
            db.add(StockTransaction(
                drug_id=drug.id,
                quantity_change=100,
                reason="Seeder initial stock",
                created_by=admin_id,
            ))
            created += 1
            continue

        drug.manufacturer = manufacturer
        drug.default_instructions = instructions
        drug.price = Decimal(price)
        drug.min_threshold = min_threshold
    return created


def seed_lab_tests(db):
    created = 0
    for code, name, category, sample_type, price, male_range, female_range, unit in LAB_TESTS:
        test = db.query(LabTest).filter(LabTest.code == code).first()
        if not test:
            db.add(LabTest(
                code=code,
                name=name,
                category=category,
                sample_type=sample_type,
                price=Decimal(price),
                male_normal_range=male_range,
                female_normal_range=female_range,
                unit=unit,
                is_active=True,
            ))
            created += 1
            continue

        test.name = name
        test.category = category
        test.sample_type = sample_type
        test.price = Decimal(price)
        test.male_normal_range = male_range
        test.female_normal_range = female_range
        test.unit = unit
        test.is_active = True
    return created


def main():
    init_db()
    db = SessionLocal()
    try:
        admin = get_seed_user(db)
        db.flush()
        seed_users(db, admin.id)
        drug_count = seed_drugs(db, admin.id)
        lab_count = seed_lab_tests(db)
        db.commit()
        print("Seeder completed.")
        print(f"Users available: {len(USERS)} (password: 123456, admin may use admin123 if newly created)")
        print(f"Drugs in seed set: {len(DRUGS)}; newly created: {drug_count}")
        print(f"Lab tests in seed set: {len(LAB_TESTS)}; newly created: {lab_count}")
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
