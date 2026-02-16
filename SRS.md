# Software Requirements Specification (SRS)  
**Project Title: Simple Hospital Information System (HIS)**  
**Version: 2.0**  
**Date: February 16, 2026**  
**Prepared for: Internal Hospital/Clinic Use**  

**Technology Stack:**  
- Backend: FastAPI (Python 3.10+)  
- Database: SQLite (via SQLAlchemy ORM) – zero-configuration  
- Frontend: Jinja2 templates (HTML), pure CSS (variables in `/static/css/vars.css`), minimal jQuery, Font Awesome 6 (free)  
- No UI frameworks (no Bootstrap, Tailwind, etc.)  
- All UI text: Persian (Farsi), full RTL layout  
- Logo: `/static/assets/logo.png`  

## 1. Introduction

### 1.1 Purpose
This document provides a complete and final specification for a lightweight, modern web-based Hospital Information System. The system manages patient registration, admission (doctor visit or radiology) with reason description, payment tracking (for admissions and prescriptions), doctor consultations with multi-drug prescriptions, radiology reporting with image upload, pharmacy inventory and prescription dispensing (including manual), role-based user management, and prescription printing/cancellation.

The application is simple, readable, maintainable, and deployable on a single server.

### 1.2 Scope
**In Scope:**
- Staff-only interface (Persian RTL)
- Full patient workflow: registration → admission with description → payment → service → prescription/report → dispensing/printing
- Unlimited drugs per prescription
- Prescription payment and cancellation
- Modern, clean UI with light gray background and blue primary color
- Print-friendly prescription invoice
- Login-protected (no self-registration)

**Out of Scope:**
- Appointment scheduling
- Insurance/billing complexity
- Patient portal
- Advanced analytics

### 1.3 Definitions
- Admission: Patient acceptance for doctor visit or radiology (with description/reason)
- Prescription: Doctor-written or manual, multi-drug, payable, printable

## 2. Overall Description

### 2.1 Product Functions Overview
1. User logs in → Home dashboard (logo-centered panel)
2. Reception: register/search patients, create admissions with description, record payments/cancellations
3. Doctor: view paid admissions, write multi-drug prescriptions (auto-calculate total), complete visit
4. Radiologist: view paid radiology admissions, write reports + upload images
5. Pharmacy: manage inventory, dispense/fill prescriptions, manual prescriptions, view/search old prescriptions
6. Cashier (Reception): handle payments for admissions and prescriptions, cancel transactions
7. Admin: manage users

### 2.2 User Classes and Roles

| Role              | Persian Name      | Allowed Modules/Pages                                                                 |
|-------------------|-------------------|---------------------------------------------------------------------------------------|
| Admin (مدیرکل)    | مدیرکل           | All + User management (create/edit/deactivate/change role)                            |
| Reception (پذیرش) | پذیرش            | Patient search/register, Admit (with description), Cashier (payments/cancellations)   |
| Doctor (پزشک)     | پزشک             | Paid doctor admissions list, Patient file (history, write prescription, complete)     |
| Radiologist (رادیولوژیست) | رادیولوژیست     | Paid radiology admissions list, Report form                                           |
| Pharmacy (داروخانه) | داروخانه        | Inventory, Drug register, Manual prescription, Dispense doctor prescriptions, Search old prescriptions |

All records include `created_at` and `created_by` (user ID).

### 2.3 Design Constraints
- **Colors** (defined in `/static/css/vars.css`):
  ```css
  :root {
      --bg: #efefef;           /* Very light gray background */
      --primary: #3698d4;      /* Main blue */
      --text: #333;
      --card-bg: #ffffff;
      --border: #ddd;
      --success: #28a745;
      --danger: #dc3545;
  }
  body.dark {
      --bg: #121212;
      --card-bg: #1e1e1e;
      --text: #e0e0e0;
      /* etc. */
  }
  ```
- Modern look: Card-based panels, subtle shadows, rounded corners, clean typography
- Background: `--bg` on `<body>`
- Primary buttons/links: `--primary`
- Fully responsive (mobile-first, flexbox/grid, no floats)
- Dark/light mode toggle in header
- Font Awesome 6 icons throughout
- Print styles for prescription invoice

### 2.4 Home & Layout
- **Home/Dashboard**: Clean panel with centered large logo, welcome message, no other content
- **Other Pages**: Same panel layout + role-specific content in main area
- **Common Layout** (`templates/layout/base.htm`):
  - RTL, Persian font
  - Header: Right = Logo → `/home`, Left = User dropdown + Dark/Light toggle
  - Sidebar: Role-based menu (collapses to hamburger on mobile)
  - Main content: Card-based panels
- All pages behind login (simple centered form)

## 3. Data Model (SQLite via SQLAlchemy)

```python
class User(Base):
    id: int (PK)
    username: str (unique)
    password_hash: str
    full_name: str
    role: Enum('admin','reception','doctor','radiologist','pharmacy')
    is_active: bool = True
    created_at: datetime
    created_by: int (FK User.id, nullable)

class Patient(Base):
    id: int (PK)
    national_id: str (unique, indexed)
    full_name: str
    phone: str
    birth_date: date
    gender: Enum('male','female','other')
    address: str (optional)
    created_at: datetime
    created_by: int (FK User.id)

class Admission(Base):
    id: int (PK)
    patient_id: int (FK Patient.id)
    admission_type: Enum('doctor','radiology')
    description: str              # Reason/complaint (e.g., "درد کمر - MRI کمر")
    radiology_type: str (optional)
    status: Enum('waiting_payment','paid','completed','cancelled')
    created_at: datetime
    created_by: int (FK User.id)
    paid_at: datetime (nullable)
    paid_by: int (FK User.id, nullable)
    completed_at: datetime (nullable)

class Payment(Base):
    id: int (PK)
    payable_type: Enum('admission','prescription') 
    payable_id: int               # FK to Admission.id or Prescription.id
    amount: decimal
    receipt_number: str (optional)
    status: Enum('paid','cancelled')
    created_at: datetime
    created_by: int (FK User.id)

class Drug(Base):
    id: int (PK)
    name: str
    manufacturer: str
    form: str (e.g., "قرص", "شربت")
    dosage: str (e.g., "500mg")
    default_instructions: str (e.g., "روزي ۲ عدد بعد غذا")
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
    admission_id: int (FK Admission.id, nullable)  # null for manual
    is_manual: bool = False
    total_amount: decimal         # Auto-calculated
    status: Enum('waiting_payment','paid','dispensed','cancelled')
    created_at: datetime
    created_by: int (FK User.id)
    dispensed_at: datetime (nullable)
    dispensed_by: int (FK User.id, nullable)

class PrescriptionItem(Base):
    id: int (PK)
    prescription_id: int (FK Prescription.id)
    drug_id: int (FK Drug.id)
    quantity: int
    instructions: str             # Default from Drug, editable

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

### 4.1 Authentication
- Simple centered login page (username/password, Persian labels)
- No registration page – users created by Admin only
- Session via secure cookie
- Role-based access and menu

### 4.2 Common UI
- Home: Full-screen card with centered logo + "خوش آمدید"
- All pages: Card layout with subtle shadow, rounded corners, `--primary` accents
- Prescription Print: Dedicated printable page (A4-friendly, @media print styles)

### 4.3 Reception & Cashier
- Patient search/register (as before)
- Admit: Form with description field (mandatory)
- Cashier:
  - List waiting_payment items (admissions + prescriptions)
  - Register payment → create Payment record, update status to paid
  - Cancel transaction → mark as cancelled, optional note

### 4.4 Doctor Module
- Patient list: Paid non-completed doctor admissions
- Patient file:
  - History tabs
  - Prescription form: Add unlimited drugs (dynamic rows)
    - Drug search → auto-fill manufacturer, form, dosage, default_instructions, price
    - Quantity + editable instructions
    - Auto-calculate total_amount
  - Submit → create Prescription (waiting_payment), items
  - Complete visit button

### 4.5 Radiology Module
- Unchanged except status flow

### 4.6 Pharmacy Module
- Inventory with calculated stock, low-stock highlight
- Drug register/restock
- Manual prescription: Same form as doctor, creates waiting_payment prescription
- Dispense: List paid prescriptions → reduce stock → mark dispensed
- Search old prescriptions by ID/patient → view details + print button

### 4.7 Prescription Printing
- Button on prescription view/dispense → opens print-friendly page with:
  - Hospital logo, patient info, drug table (name, manufacturer, form, dosage, quantity, instructions, price), total amount
  - Clean layout, Persian text

### 4.8 Admin Module
- Full user CRUD (no self-registration)

## 5. Non-Functional Requirements
- Modern card-based UI with specified colors
- Fully responsive
- Dark/light mode
- Persian RTL throughout
- Print-friendly prescription
- Basic validation + Persian error messages
- Secure password hashing, role checks

## 6. Folder Structure (Recommended)
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
│   ├── common/
│   │   ├── login.htm
│   │   └── home.htm          # Logo-centered
│   ├── reception/...
│   ├── doctor/...
│   ├── pharmacy/...
│   └── print/
│       └── prescription.htm  # Print template
├── static/
│   ├── css/
│   │   ├── vars.css
│   │   ├── style.css
│   │   ├── responsive.css
│   │   └── print.css
│   ├── js/
│   │   └── main.js           # Dynamic prescription rows, etc.
│   └── assets/
│       └── logo.png
└── uploads/
```

This SRS is now complete, incorporating all previous requirements and new updates. Ready for implementation guidance (e.g., with Copilot).

## 7. Detailed Development Plan

### Phase 1: Setup & Auth (2-3 days)
1. Project structure + FastAPI + SQLite + Jinja2
2. User model + initial admin script
3. Simple login page + session auth
4. Base layout with modern CSS vars (#efefef bg, #3698d4 primary)

### Phase 2: Layout & Home (1-2 days)
1. Home page (centered logo)
2. Full panel layout + responsive sidebar + dark mode
3. Role-based menu rendering

### Phase 3: Patient & Reception (3-4 days)
1. Patient + Admission models (add description)
2. Search/register/admit forms
3. Cashier with payment + cancellation

### Phase 4: Drug & Prescription Core (3 days)
1. Enhanced Drug model
2. Multi-drug prescription form (shared component)
3. Total calculation + waiting_payment status

### Phase 5: Doctor Module (2-3 days)
1. Patient list + file page
2. Integrate prescription form

### Phase 6: Pharmacy Module (4 days)
1. Inventory + drug CRUD
2. Manual prescription + dispense workflow
3. Prescription search + printable invoice template

### Phase 7: Radiology & Admin (3 days)
1. Radiology report + uploads
2. Admin user management

### Phase 8: Polish & Testing (4 days)
1. Full Persian RTL text
2. Modern styling refinements
3. Print invoice testing
4. End-to-end workflow testing
5. Security & responsiveness check

**Total estimated: 22-28 days**