# Software Requirements Specification (SRS)  
**Project Title: Simple Hospital Information System (HIS)**  
**Version: 2.0**  
**Date: February 16, 2026**  
**Prepared for: Internal Hospital/Clinic Use**  

**Technology Stack:**  
- Backend: FastAPI (Python 3.10+)  
- Database: SQLite (via SQLAlchemy ORM) – zero-configuration deployment  
- Frontend: Jinja2 templates (HTML), pure CSS (variables in `/static/css/vars.css`), minimal jQuery, Font Awesome 6 (free)  
- No external UI frameworks  
- All UI text: Persian (Farsi), full RTL layout  
- Logo: `/static/assets/logo.png`

## 1. Introduction

### 1.1 Purpose
This document provides a complete and detailed specification for a lightweight, web-based Hospital Information System (HIS). The system automates core workflows of a small hospital/clinic: patient registration, admission for doctor visits or radiology (with notes), cash payment tracking for both services and prescriptions, doctor consultations with multi-drug prescription writing, radiology reporting with image upload, pharmacy inventory management and prescription dispensing, role-based user management, prescription search, and printable invoices.

The application emphasizes simplicity, readability, maintainability, and minimal dependencies.

### 1.2 Scope
**In Scope:**
- Staff-only web interface
- Patient registration → admission (with description) → payment (services) → service delivery
- Prescription writing (unlimited drugs per prescription) → pricing → payment → dispensing
- Radiology reporting with image upload
- Pharmacy inventory with drug details
- Prescription search and printable invoice
- Transaction cancellation in cashier
- Role-based access control (5 roles)
- Dark/light mode, fully responsive, Persian RTL UI

**Out of Scope:**
- Online appointments
- Insurance integration
- Advanced analytics
- Patient portal
- Multi-branch support

### 1.3 Definitions
- **Admission**: Registration for doctor visit or radiology service
- **Prescription**: List of drugs (doctor-written or manual), with total price, payable separately
- **Cashier**: Unified payment point for admissions (services) and prescriptions (drugs)

## 2. Overall Description

### 2.1 Product Functions Overview
1. User login → role-based dashboard
2. Reception: register/search patient, create admission with description/notes, record payments/cancellations
3. Doctor: view paid admissions, review history, write multi-drug prescriptions (auto-price calculation)
4. Radiologist: view paid radiology admissions, write report + upload images
5. Pharmacy: manage drug inventory, dispense prescriptions (reduce stock), manual prescriptions
6. Admin: manage users/roles
7. Common: search prescriptions by ID, print invoice, cancel transactions

All records include `created_at` timestamp and `created_by` user ID.

### 2.2 User Classes and Roles

| Role              | Persian Name      | Key Permissions                                                                      |
|-------------------|-------------------|--------------------------------------------------------------------------------------|
| Admin (مدیرکل)    | مدیرکل           | Full access + user management (create/edit/role change/deactivate)                   |
| Reception (پذیرش) | پذیرش            | Patient CRUD, admission creation, cashier (payments/cancellations for services & prescriptions) |
| Doctor (پزشک)     | پزشک             | View paid doctor admissions, patient file, write prescriptions                      |
| Radiologist (رادیولوژیست) | رادیولوژیست     | View paid radiology admissions, write reports + upload images                        |
| Pharmacy (داروخانه) | داروخانه        | Drug inventory, manual prescriptions, dispense doctor prescriptions                  |

### 2.3 Design Constraints
- Pure CSS with all colors in `/static/css/vars.css` (light/dark variants)
- Layout: Flexbox/Grid only (no floats)
- Responsive: Mobile-first, sidebar → hamburger menu on ≤768px
- Icons: Font Awesome 6
- JS: jQuery only for dark mode, mobile menu, minor interactions (e.g., add/remove drug rows)
- File uploads: Radiology images only → `/uploads/` with unique names
- Printing: Browser-printable invoice page (CSS @media print)

### 2.4 Folder Structure

```
/project-root
├── main.py
├── database.py
├── auth.py
├── routers/
│   ├── reception.py
│   ├── doctor.py
│   ├── radiology.py
│   ├── pharmacy.py
│   ├── admin.py
│   └── common.py
├── models/
├── schemas/
├── templates/
│   ├── layout/
│   │   ├── base.htm
│   │   └── panel.htm
│   ├── reception/
│   ├── doctor/
│   ├── radiology/
│   ├── pharmacy/
│   ├── user/
│   └── common/
│       ├── login.htm
│       ├── prescription_search.htm
│       └── prescription_print.htm
├── static/
│   ├── css/
│   │   ├── vars.css
│   │   ├── style.css
│   │   └── print.css
│   ├── js/
│   │   └── main.js
│   └── assets/
│       └── logo.png
└── uploads/
```

## 3. Data Model (SQLite via SQLAlchemy)

```python
class User(Base):
    id: int (PK)
    username: str (unique)
    password_hash: str
    full_name: str
    role: Enum('admin', 'reception', 'doctor', 'radiologist', 'pharmacy')
    is_active: bool = True
    created_at: datetime
    created_by: int (FK User.id, nullable for initial admin)

class Patient(Base):
    id: int (PK)
    national_id: str (unique, indexed)
    full_name: str
    phone: str
    birth_date: date
    gender: Enum('male', 'female', 'other')
    address: str (optional)
    created_at: datetime
    created_by: int (FK User.id)

class Admission(Base):
    id: int (PK)
    patient_id: int (FK Patient.id)
    admission_type: Enum('doctor', 'radiology')
    description: str              # New: reason for visit / radiology details (e.g., "درد کمر - MRI")
    radiology_type: str (optional)
    status: Enum('waiting_payment', 'paid', 'completed', 'cancelled')
    created_at: datetime
    created_by: int (FK User.id)
    paid_at: datetime (nullable)
    paid_by: int (FK User.id, nullable)
    completed_at: datetime (nullable)
    cancelled_at: datetime (nullable)

class Payment(Base):
    id: int (PK)
    payable_type: Enum('admission', 'prescription')   # New: unified payment
    payable_id: int                                   # FK to Admission.id or Prescription.id
    amount: decimal
    receipt_number: str (optional)
    status: Enum('completed', 'cancelled')
    created_at: datetime
    created_by: int (FK User.id)

class Drug(Base):
    id: int (PK)
    name: str
    company: str
    form: str                    # e.g., "قرص", "شربت"
    dosage: str                  # e.g., "500mg"
    default_instructions: str    # e.g., "روزي ۲ عدد بعد غذا"
    price: decimal
    min_threshold: int = 10
    created_at: datetime
    created_by: int (FK User.id)

class StockTransaction(Base):
    id: int (PK)
    drug_id: int (FK Drug.id)
    quantity_change: int
    reason: str
    created_at: datetime
    created_by: int (FK User.id)

class Prescription(Base):
    id: int (PK)
    patient_id: int (FK Patient.id)
    admission_id: int (FK Admission.id, nullable)   # linked if from doctor visit
    is_manual: bool = False
    total_amount: decimal                           # calculated from items
    status: Enum('waiting_payment', 'paid', 'dispensed', 'cancelled')
    created_at: datetime
    created_by: int (FK User.id)
    paid_at: datetime (nullable)
    dispensed_at: datetime (nullable)

class PrescriptionItem(Base):
    id: int (PK)
    prescription_id: int (FK Prescription.id)
    drug_id: int (FK Drug.id)
    quantity: int
    instructions: str               # defaults from Drug.default_instructions, editable

class RadiologyReport(Base):
    id: int (PK)
    admission_id: int (FK Admission.id, unique)
    report_text: str
    created_at: datetime
    created_by: int (FK User.id)

class RadiologyImage(Base):
    id: int (PK)
    report_id: int (FK RadiologyReport.id)
    filename: str
    uploaded_at: datetime
```

Current stock = SUM(StockTransaction.quantity_change) per drug.

## 4. Functional Requirements

### 4.1 Authentication & Common UI
- Login/logout with Persian labels
- Base layout: RTL, header (logo right, user dropdown left, dark/light toggle), collapsible sidebar
- Dashboard with role-specific menu
- Prescription search page (by prescription ID or patient national ID)

### 4.2 Reception Module
- Patient search/register
- Admission creation:
  - Required description field (reason for visit or specific radiology request)
  - Status → waiting_payment
- Cashier (unified):
  - List of waiting_payment admissions and prescriptions
  - Register payment → update status to paid
  - Cancel transaction → mark admission/prescription as cancelled (with reason)

### 4.3 Doctor Module
- Patient list: paid, non-completed doctor admissions
- Patient file:
  - History tabs
  - Prescription form: dynamic rows (add/remove drugs)
    - Drug search/select → auto-fill company, form, dosage, default_instructions, price
    - Quantity input → auto-calculate line total
    - Instructions editable (pre-filled with default)
    - Unlimited drugs
    - Total amount calculated and saved
  - Complete visit button

### 4.4 Radiology Module
- Patient list: paid radiology admissions
- Report form with image uploads
- Submit → mark admission completed

### 4.5 Pharmacy Module
- Inventory view with low-stock highlighting
- Drug registration (all fields including price and default instructions)
- Manual prescription creation (same multi-drug form as doctor)
- Dispense doctor/manual prescriptions (after paid) → reduce stock

### 4.6 Prescription Features
- Search by prescription ID → view details
- Print invoice page: clean layout with hospital logo, patient info, drug table (name, company, form, dosage, quantity, instructions, price), total amount, timestamps
- CSS @media print for printer-friendly output

## 5. Non-Functional Requirements
- Responsive across devices
- Dark/light mode (CSS variables + localStorage)
- Persian RTL layout and text
- Simple, clean, well-commented code
- Input validation + Persian error messages
- Image upload size limit (≤5MB)
- Browser print support for invoices

## 6. Detailed Development Plan

**Phase 1: Setup & Auth (2-3 days)**  
1. Project structure, FastAPI + Jinja2 + SQLite  
2. User model, initial admin script  
3. Login/logout, session, role checks  

**Phase 2: Layout & Common (2 days)**  
1. `base.htm`, header, sidebar, dark/light toggle, RTL styling  
2. Dashboard, prescription search page  

**Phase 3: Patient & Admission (3 days)**  
1. Patient + Admission models (with description)  
2. Search/register/admit forms  
3. Unified Payment model  

**Phase 4: Doctor & Prescription Core (4 days)**  
1. Prescription models (multi-item, pricing)  
2. Dynamic prescription form (jQuery add rows, auto-fill, calculation)  
3. Doctor patient list and file  

**Phase 5: Cashier & Cancellation (2 days)**  
1. Unified cashier page  
2. Payment registration and cancellation logic  

**Phase 6: Radiology (2 days)**  
1. Report + multi-image upload  

**Phase 7: Pharmacy & Drugs (3 days)**  
1. Drug model with extended fields  
2. Inventory, manual prescription, dispensing  

**Phase 8: Print & Polish (2-3 days)**  
1. Prescription print page + print.css  
2. Full Persian text, validation, responsive testing  
3. End-to-end workflow testing  

**Total estimated: 20-25 days**

This SRS is now complete, consistent, and ready for implementation.