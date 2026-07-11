# Software Requirements Specification (SRS)

**Project Title:** Simple Hospital Information System (HIS)  
**Version:** 3.0  
**Date:** July 11, 2026  
**Prepared for:** Internal Hospital/Clinic and University Project Use

## 1. Introduction

### 1.1 Purpose

This document describes the implemented requirements for the Simple Hospital Information System. The system is a staff-only web application for managing patient registration, admissions, cashier payments, doctor consultations, laboratory orders and results, radiology reports and images, pharmacy inventory and dispensing, and administrative user management.

### 1.2 Scope

The system supports a small hospital or clinic workflow using a single FastAPI application and a local SQLite database. It is designed for simple deployment, local operation, and clear separation of role-based modules.

In scope:

- Staff authentication and role-based access control.
- Patient registration and lookup.
- Admissions for doctor, laboratory, and radiology services.
- Cashier payment processing for admissions, lab orders, and prescriptions.
- Doctor patient queue and unified clinical ordering.
- Laboratory order tracking, sample collection, result entry, and reports.
- Radiology report entry and image upload.
- Pharmacy drug catalog, stock tracking, manual prescriptions, and dispensing.
- Admin user management.
- Print-oriented prescription and lab report views.
- Persian RTL interface using server-rendered templates.

Out of scope:

- Appointment scheduling.
- Insurance contract management beyond basic cashier-side admission plan calculation.
- Patient portal.
- External laboratory/radiology device integration.
- Electronic claims.
- Advanced analytics.
- Multi-tenant hospital branches.

## 2. Overall Description

### 2.1 Product Perspective

The application is a monolithic FastAPI web application. It uses:

- `main.py` for application startup and router registration.
- `database.py` for SQLite connection helpers, schema initialization, and object hydration helpers.
- `auth.py` for password hashing, JWT token creation, cookie-based authentication, and role guards.
- `routers/` for feature modules.
- `templates/` for Jinja2 HTML views.
- `static/` for CSS, JavaScript, and assets.
- `uploads/` for uploaded radiology images.

### 2.2 User Classes

| Role | Main responsibilities |
| --- | --- |
| Admin | Manage users and access all modules |
| Reception | Register/search patients, create admissions, run cashier |
| Doctor | View paid doctor admissions, review patient history, create clinical orders |
| Laboratory | Track lab orders, collect samples, enter results, print reports |
| Radiologist | View paid radiology admissions, write reports, upload images |
| Pharmacy | Manage drugs and stock, create manual prescriptions, dispense paid prescriptions |

### 2.3 Operating Environment

- Python 3.10 or newer.
- SQLite database stored as `hospital.db`.
- Browser-based interface.
- Local filesystem access for `uploads/`.
- Can be run directly with Uvicorn or packaged for deployment with the included Docker/deployment resources.

### 2.4 Constraints

- The UI is implemented with Jinja2, custom CSS, and minimal JavaScript.
- No dedicated frontend framework is used.
- Database schema is initialized with SQL statements in `database.py`.
- The system uses SQLite, so write concurrency is limited compared with a server database.
- Uploaded files are stored on the local filesystem.

## 3. System Features

### 3.1 Authentication

Functional requirements:

- The system shall provide a login form at `/login`.
- The system shall authenticate active users by username and password.
- The system shall hash passwords before storage.
- The system shall create a JWT access token after successful login.
- The system shall store the access token in a browser cookie.
- The system shall redirect unauthenticated HTML requests to `/login`.
- The system shall allow logout by deleting the token cookie.
- The system shall protect feature routes by role.

Implemented notes:

- Token expiration is configured in `auth.py`.
- The current cookie settings are suitable for local development and should be hardened before production.

### 3.2 Administration

Functional requirements:

- Admin users shall view all users.
- Admin users shall create new users.
- Admin users shall edit full name and role.
- Admin users shall optionally reset a user's password.
- Admin users shall activate and deactivate users.

Main routes:

- `GET /admin/users`
- `GET|POST /admin/users/new`
- `GET|POST /admin/users/{user_id}/edit`
- `POST /admin/users/{user_id}/activate`
- `POST /admin/users/{user_id}/deactivate`

### 3.3 Patient Registration and Lookup

Functional requirements:

- Reception shall search patients by national ID or phone.
- Reception shall register a new patient.
- Reception shall open admission for an existing patient.
- The admission page shall support async patient lookup by national ID.
- The admission page shall support quick patient creation.

Main routes:

- `GET /reception/patients`
- `GET|POST /reception/patients/new`
- `GET|POST /reception/admit`
- `GET /api/patients/lookup`
- `POST /api/patients/quick-create`

### 3.4 Admissions

Functional requirements:

- Reception shall create admissions with a patient, type, and description.
- Supported admission types shall include `doctor`, `laboratory`, and `radiology`.
- Radiology admissions may include `radiology_type`.
- Doctor and radiology admissions shall start as `waiting_payment`.
- Laboratory admissions shall create a linked lab order with selected tests and send that lab order to cashier.
- Laboratory admission records are marked `completed` when the linked lab order is created.

Admission statuses:

- `waiting_payment`
- `paid`
- `completed`
- `cancelled`

### 3.5 Cashier and Payments

Functional requirements:

- Reception shall view unpaid admissions, prescriptions, and lab orders.
- Reception shall mark admissions as paid and create a payment row.
- Reception shall mark prescriptions as paid and create a payment row.
- Reception shall mark lab orders as paid and create a payment row.
- Reception shall cancel pending admissions, prescriptions, and lab orders.
- The system shall generate receipt numbers with type-specific prefixes.

Payment payable types:

- `admission`
- `prescription`
- `lab_order`

Main routes:

- `GET /reception/cashier`
- `POST /reception/cashier/pay-admission`
- `POST /reception/cashier/pay-prescription`
- `POST /reception/cashier/pay-lab-order`
- `POST /reception/cashier/cancel-admission`
- `POST /reception/cashier/cancel-prescription`
- `POST /reception/cashier/cancel-lab-order`

### 3.6 Doctor Module

Functional requirements:

- Doctors shall view paid doctor admissions.
- Doctors shall open a patient file for a paid doctor admission.
- The patient file shall show recent prescriptions, lab orders, and radiology admissions.
- Doctors shall create drug prescriptions.
- Doctors shall create lab orders.
- Doctors shall create radiology requests.
- Doctors shall complete the visit.

Main routes:

- `GET /doctor/patients`
- `GET /doctor/patient/{patient_id}/admission/{admission_id}`
- `POST /doctor/orders/create`
- `POST /doctor/prescription/create`
- `POST /doctor/complete/{admission_id}`

### 3.7 Laboratory Module

Functional requirements:

- Laboratory users shall view active lab orders.
- Laboratory users shall mark paid lab orders as collected.
- Laboratory users shall enter result values per ordered test.
- The system shall flag numeric result values as `low`, `normal`, or `high` when a parseable normal range is available.
- A lab order shall become `resulted` when all order items have results.
- Lab reports shall be viewable by laboratory users, doctors, and admins.

Lab order statuses:

- `waiting_payment`
- `paid`
- `collected`
- `resulted`
- `cancelled`

Main routes:

- `GET /lab/orders`
- `POST /lab/orders/{order_id}/collect`
- `GET|POST /lab/orders/{order_id}/results`
- `GET /lab/orders/{order_id}/report`

### 3.8 Radiology Module

Functional requirements:

- Radiologists shall view paid and completed radiology admissions.
- Radiologists shall create or update a report for an admission.
- Radiologists shall upload one or more image files.
- The system shall validate uploaded image files.
- The system shall store uploaded images using UUID filenames.
- Radiologists shall complete radiology admissions.

Main routes:

- `GET /radiology/admissions`
- `GET|POST /radiology/report/{admission_id}`
- `POST /radiology/complete/{admission_id}`

### 3.9 Pharmacy Module

Functional requirements:

- Pharmacy users shall view the drug inventory and calculated stock.
- Pharmacy users shall create and edit drugs.
- Pharmacy users shall create restock transactions.
- Pharmacy users shall create manual prescriptions for patients.
- Pharmacy users shall view paid prescriptions ready for dispensing.
- The system shall block dispensing when stock is insufficient.
- Dispensing shall create negative stock transactions.
- Dispensing shall mark prescriptions as `dispensed`.
- Pharmacy users shall search prescriptions by prescription ID or patient national ID.

Prescription statuses:

- `waiting_payment`
- `paid`
- `dispensed`
- `cancelled`

Main routes:

- `GET /pharmacy/inventory`
- `GET|POST /pharmacy/drug/new`
- `GET|POST /pharmacy/drug/{drug_id}/edit`
- `GET|POST /pharmacy/restock`
- `GET|POST /pharmacy/manual-prescription`
- `GET /pharmacy/dispense`
- `GET /pharmacy/dispense/{prescription_id}`
- `POST /pharmacy/dispense/{prescription_id}/complete`
- `GET /pharmacy/search`
- `GET /pharmacy/prescription/{prescription_id}`

### 3.10 Print Views

Functional requirements:

- Authenticated users shall print prescriptions through `/print/prescription/{prescription_id}`.
- Lab reports shall have report pages suitable for review and printing.
- Print CSS shall be maintained in `static/css/print.css`.

## 4. Data Requirements

The implemented schema has 14 tables:

- `users`
- `patients`
- `admissions`
- `payments`
- `drugs`
- `stock_transactions`
- `prescriptions`
- `prescription_items`
- `radiology_reports`
- `radiology_images`
- `lab_tests`
- `lab_orders`
- `lab_order_items`
- `lab_results`

The complete data dictionary, relation list, and diagram guidance are maintained in [DATA_MODEL.md](DATA_MODEL.md).

## 5. Non-Functional Requirements

### 5.1 Usability

- The interface shall use a Persian RTL layout.
- The interface shall support dark/light mode styling.
- The interface shall be responsive for common desktop, tablet, and mobile widths.
- Forms shall use clear role-specific workflows.

### 5.2 Performance

- The application shall be suitable for small clinic workloads on SQLite.
- Search APIs shall limit autocomplete result counts.
- Inventory stock shall be calculated from stock transactions when needed.

### 5.3 Security

- Passwords shall be stored as hashes.
- Feature routes shall require authentication.
- Role guards shall protect module routes.
- Uploaded image files shall be validated.
- Production deployments shall replace development secrets and cookie settings.

### 5.4 Maintainability

- Feature code shall remain grouped by router.
- Templates shall remain grouped by module.
- Schema changes shall be reflected in `database.py`, `SRS.md`, `README.md`, and `DATA_MODEL.md`.

### 5.5 Backup and Recovery

- `hospital.db` shall be backed up regularly.
- `uploads/` shall be backed up with the database.
- Restoring a backup requires both the SQLite file and uploaded images.

## 6. External Interfaces

### 6.1 Browser Interface

The application is primarily server-rendered HTML with forms and selected async JSON calls.

### 6.2 File Interface

Radiology uploads are written to `uploads/` and exposed through FastAPI static file mounting.

### 6.3 Database Interface

The application uses SQLite through the Python standard `sqlite3` module. `database.py` provides:

- connection generator
- schema initialization
- row-to-object wrappers
- common lookup helpers
- stock calculation helper

## 7. Assumptions and Dependencies

- Users are internal staff.
- All access occurs through trusted staff accounts.
- The system runs in one deployment environment against one SQLite database file.
- The deployment operator is responsible for backups, HTTPS, secret management, and filesystem permissions.

## 8. Acceptance Criteria

- A new admin can be created with `python initial_admin.py`.
- The application starts with `python main.py` and initializes missing tables.
- Seed data can be loaded with `python seeder.py`.
- Reception can create a patient, admission, and payment.
- A doctor can process a paid admission and create prescription/lab/radiology orders.
- Cashier can pay a prescription and a lab order.
- Laboratory can collect a sample, enter results, and view a report.
- Radiology can write a report and upload images.
- Pharmacy can restock, dispense a paid prescription, and reduce stock.
- Admin can create, edit, activate, and deactivate users.
