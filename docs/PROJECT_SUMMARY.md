# Simple Hospital Information System (HIS) - Project Summary

## Overview

Simple HIS is a lightweight, staff-only Hospital Information System for small clinics, university projects, and local hospital workflow demonstrations. It is built with FastAPI, SQLite, Jinja2 templates, custom CSS, minimal JavaScript, and a Persian RTL interface.

The current implementation covers patient registration, admission, cashier payments, doctor visits, laboratory orders and results, radiology reports with image uploads, pharmacy inventory and dispensing, user administration, print views, async lookup APIs, and seed data for local testing.

The codebase uses direct `sqlite3` access through helpers in `database.py`. It does not use SQLAlchemy model classes. The Docker runtime is configured for one Uvicorn worker because the application uses a local SQLite database.

## Current Status

- Version: 3.0 documentation set
- Date: July 11, 2026
- Status: Complete for university and small-clinic HIS workflows
- Runtime: FastAPI served by Uvicorn
- Database: local SQLite file, `hospital.db`
- Data access: direct `sqlite3` helpers
- UI: server-rendered Jinja2 templates with custom CSS and minimal JavaScript
- Authentication: JWT cookie login with role-based route protection
- Container runtime: single Uvicorn worker, no reload process

## Project Statistics

- Tracked project files: 59
- Python files: 16
- HTML template files: 25
- CSS stylesheets: 4
- JavaScript files: 1
- Main documentation: `docs/README.md`, `docs/TESTING.md`, `docs/SRS.md`, `docs/DATA_MODEL.md`, `docs/DATA_STRUCTURE.md`, `docs/PROJECT_SUMMARY.md`

## Technology Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite
- Jinja2
- python-multipart
- Passlib with bcrypt
- python-jose with cryptography
- aiofiles
- python-dotenv
- Font Awesome through templates
- Custom CSS in `static/css`

## Roles

| Role | Purpose |
| --- | --- |
| `admin` | Full system access and user management |
| `reception` | Patient registration, admission, cashier |
| `doctor` | Paid doctor queue, patient file, clinical orders |
| `laboratory` | Lab order queue, sample collection, result entry, reports |
| `radiologist` | Paid radiology queue, report entry, image upload |
| `pharmacy` | Drug catalog, inventory, manual prescriptions, dispensing |

## Implemented Features

### Authentication and Authorization

- Login and logout flow with JWT access tokens stored in browser cookies.
- Password hashing with Passlib.
- Role-based route protection.
- Active and inactive user accounts.
- Admin user management.
- HTML requests without a valid login redirect to `/login`.

### User Interface

- Persian RTL layout.
- Dark/light mode support.
- Responsive templates for desktop and smaller screens.
- Shared base and panel layouts.
- Section templates for reception, doctor, laboratory, radiology, pharmacy, admin, print, and common pages.
- Custom styles under `static/css`.
- Shared JavaScript in `static/js/main.js` plus page-level scripts where needed.

### Reception and Cashier

- Patient search by national ID or phone.
- Full patient registration.
- Admission page with national ID lookup.
- Quick patient creation from the admission page.
- Admission creation for doctor, laboratory, and radiology services.
- Radiology admission type selection.
- Laboratory admission with selected lab tests and calculated lab order total.
- Cashier queues for admissions, prescriptions, and lab orders.
- Payment registration with generated receipt numbers.
- Cancellation for pending admissions, prescriptions, and lab orders.
- Admission pricing in `config.py`.
- Basic admission insurance plan calculation at cashier.

### Doctor Module

- Queue of paid doctor admissions.
- Patient file view for an active doctor admission.
- Recent prescriptions, lab orders, and radiology admissions in the patient file.
- Unified clinical ordering for prescriptions, lab tests, and radiology requests.
- Prescription totals calculated from selected drugs and quantities.
- Lab order totals calculated from selected lab tests.
- Doctor visits can be marked completed.

### Laboratory Module

- Lab order worklist for `waiting_payment`, `paid`, `collected`, and `resulted` orders.
- Sample collection status transition.
- Result entry per lab order item.
- Update support for existing result values.
- Automatic `low`, `normal`, or `high` flagging for numeric results when a parseable sex-specific normal range exists.
- Lab result report view available to laboratory users, doctors, and admins.

### Radiology Module

- Radiology admission queue for paid and completed radiology admissions.
- Report creation and update per radiology admission.
- Multi-image upload.
- Image extension, MIME type, and size validation.
- UUID-based stored filenames.
- Uploaded files served from `/uploads`.
- Radiology admissions can be marked completed.

### Pharmacy and Inventory

- Drug catalog management.
- Drug editing.
- Restocking through stock transactions.
- Current stock calculated from stock transaction sums.
- Manual prescription creation for walk-in patients.
- Paid prescription dispensing queue.
- Stock availability checks before dispensing.
- Low-stock-after-dispense visibility.
- Dispensing creates negative stock transactions and marks prescriptions dispensed.
- Prescription search by prescription ID or patient national ID.
- Printable prescription view.

### Seeder Subsystem

- `seeder.py` populates testing and demo environments.
- Creates ready-to-use users for all major roles.
- Loads drug catalog data, laboratory test catalog data, sample patients, admissions, payments, prescriptions, and related workflow records.

## Main Workflows

### Patient Registration and Admission

1. Reception searches for a patient by national ID or phone.
2. If the patient exists, reception opens the admission page for that patient.
3. If the patient does not exist, reception creates the patient through the full form or quick-create modal.
4. Reception selects admission type: doctor, laboratory, or radiology.
5. For laboratory admission, reception selects one or more active lab tests.
6. For radiology admission, reception selects the radiology type.
7. The request is sent to the cashier queue or, for laboratory admission, a linked lab order is created and sent to cashier.

### Cashier Payment

1. Reception opens the cashier queue.
2. The cashier reviews pending admissions, prescriptions, and lab orders.
3. Admission payments can apply a basic insurance plan calculation.
4. The cashier records payment.
5. The system creates a `payments` row with a receipt number.
6. The payable item moves to the next workflow state.
7. Pending items can be cancelled before payment.

### Doctor Visit

1. Doctor opens the paid doctor admissions queue.
2. Doctor opens the patient file for an admission.
3. Doctor reviews recent prescriptions, lab orders, and radiology admissions.
4. Doctor creates any needed prescription, lab order, or radiology request.
5. New prescription, lab order, and radiology requests move to cashier for payment.
6. Doctor marks the doctor admission completed.

### Laboratory Order

1. Laboratory users view active lab orders.
2. Paid orders can be marked collected.
3. Laboratory users enter result values for each test.
4. The system flags numeric values when the normal range can be parsed.
5. When all ordered tests have results, the lab order becomes resulted.
6. Users with permission view the lab report page.

### Radiology Report

1. Radiologist views paid radiology admissions.
2. Radiologist opens the report form.
3. Radiologist writes or updates the report.
4. Radiologist uploads one or more valid image files when needed.
5. The system stores image metadata and UUID filenames.
6. Radiologist marks the radiology admission completed.

### Pharmacy Dispensing

1. Pharmacy user manages the drug catalog and stock ledger.
2. Doctor-created or manual prescriptions are sent to cashier.
3. After payment, prescriptions appear in the dispensing queue.
4. Pharmacy checks stock availability.
5. If stock is sufficient, dispensing creates negative stock transactions.
6. The prescription is marked dispensed.
7. Pharmacy can search prescriptions by prescription ID or patient national ID.

### Administration

1. Admin opens user management.
2. Admin creates staff users.
3. Admin edits user name, role, or password when needed.
4. Admin activates or deactivates accounts.

## User Stories

- As an admin, I can create and manage staff accounts so each department has role-appropriate access.
- As reception staff, I can search or register patients so admissions start from a reliable patient record.
- As reception staff, I can create doctor, lab, and radiology admissions so patients are routed to the right service.
- As a cashier, I can see pending admissions, prescriptions, and lab orders so payments are handled from one queue.
- As a cashier, I can cancel pending items so incorrect requests do not continue through the workflow.
- As a doctor, I can view paid patients and their recent clinical history so I can make informed orders.
- As a doctor, I can create prescriptions, lab orders, and radiology requests from one patient file so clinical work stays in one screen.
- As a laboratory user, I can collect samples and enter results so lab orders progress to a report.
- As a laboratory user, I can see result flags so abnormal numeric values are visible.
- As a radiologist, I can write reports and upload images so imaging results are stored with the admission.
- As a pharmacy user, I can manage stock and dispense only paid prescriptions so inventory and billing stay consistent.
- As a pharmacy user, I can create manual prescriptions for walk-in patients so non-doctor prescription workflows are supported.

## API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/drugs/search` | Drug autocomplete with price, default instructions, stock, and threshold data |
| `GET /api/lab-tests/search` | Active lab test autocomplete with catalog and reference-range data |
| `GET /api/patients/lookup` | National ID patient lookup with last-visit payload |
| `POST /api/patients/quick-create` | Quick patient creation for reception |

## Main Routes

| Area | Routes |
| --- | --- |
| Common | `/`, `/login`, `/logout`, `/home`, `/print/prescription/{id}` |
| Reception | `/reception/patients`, `/reception/patients/new`, `/reception/admit`, `/reception/cashier` |
| Doctor | `/doctor/patients`, `/doctor/patient/{patient_id}/admission/{admission_id}`, `/doctor/orders/create`, `/doctor/complete/{admission_id}` |
| Laboratory | `/lab/orders`, `/lab/orders/{order_id}/collect`, `/lab/orders/{order_id}/results`, `/lab/orders/{order_id}/report` |
| Radiology | `/radiology/admissions`, `/radiology/report/{admission_id}`, `/radiology/complete/{admission_id}` |
| Pharmacy | `/pharmacy/inventory`, `/pharmacy/drug/new`, `/pharmacy/drug/{drug_id}/edit`, `/pharmacy/restock`, `/pharmacy/manual-prescription`, `/pharmacy/dispense`, `/pharmacy/search` |
| Admin | `/admin/users`, `/admin/users/new`, `/admin/users/{user_id}/edit` |
| API | `/api/drugs/search`, `/api/lab-tests/search`, `/api/patients/lookup`, `/api/patients/quick-create` |

## Database Schema

The database schema is created by `init_db()` in `database.py`.

Implemented tables:

1. `users`
2. `patients`
3. `admissions`
4. `payments`
5. `drugs`
6. `stock_transactions`
7. `prescriptions`
8. `prescription_items`
9. `radiology_reports`
10. `radiology_images`
11. `lab_tests`
12. `lab_orders`
13. `lab_order_items`
14. `lab_results`

Important database notes:

- `hospital.db` is initialized automatically at application startup.
- SQLite tables use application-level logical foreign keys rather than declared SQLite foreign key constraints.
- `payments.payable_type` and `payments.payable_id` form a polymorphic payment reference.
- Current drug stock is calculated from `stock_transactions`; it is not stored directly on `drugs`.
- Prescription totals are calculated at creation time from drug price and quantity.
- Lab order totals are calculated at creation time from selected lab test prices.
- Uploaded radiology files are stored in `uploads/` and referenced by generated filenames.
- SQLite is appropriate for this small-clinic and university deployment scope, but write concurrency is limited.

## Workflow State Transitions

### Admission

```text
waiting_payment -> paid -> completed
waiting_payment -> cancelled
laboratory admission -> completed after creating linked lab_order
```

### Prescription

```text
waiting_payment -> paid -> dispensed
waiting_payment -> cancelled
```

### Lab Order

```text
waiting_payment -> paid -> collected -> resulted
waiting_payment -> cancelled
```

### Payment

```text
created as paid
```

Cashier cancellation routes cancel the payable item. They do not create reversal ledger rows.

## Project Structure

```text
/
|-- main.py
|-- database.py
|-- auth.py
|-- config.py
|-- initial_admin.py
|-- seeder.py
|-- requirements.txt
|-- quick-start.bat
|-- quick-start.sh
|-- hospital.db
|-- docker/
|   `-- Dockerfile
|-- docs/
|   |-- README.md
|   |-- PROJECT_SUMMARY.md
|   |-- SRS.md
|   |-- SRS.docx
|   |-- DATA_MODEL.md
|   |-- DATA_STRUCTURE.md
|   |-- TESTING.md
|   `-- diagrams/
|       |-- ActivityUML.png
|       |-- ClassUML.png
|       |-- ComponentUML.png
|       |-- EER.png
|       |-- SequenceUML.png
|       |-- StateAdmissionUML.png
|       `-- StateLabOrderUML.png
|-- routers/
|   |-- common.py
|   |-- reception.py
|   |-- doctor.py
|   |-- lab.py
|   |-- radiology.py
|   |-- pharmacy.py
|   |-- admin.py
|   `-- api.py
|-- templates/
|   |-- admin/
|   |-- common/
|   |-- doctor/
|   |-- lab/
|   |-- layout/
|   |-- pharmacy/
|   |-- print/
|   |-- radiology/
|   `-- reception/
|-- static/
|   |-- assets/
|   |-- css/
|   `-- js/
|-- uploads/
|-- utils/
```

## Diagrams

The project diagrams are stored under `docs/diagrams/` and support architecture, database, and workflow review:

| Diagram | File | Purpose |
| --- | --- | --- |
| Activity UML | `docs/diagrams/ActivityUML.png` | Shows the main end-to-end HIS workflow across reception, cashier, doctor, laboratory, radiology, and pharmacy actions. |
| Class UML | `docs/diagrams/ClassUML.png` | Summarizes the main domain entities, attributes, and relationships used by the application data model. |
| Component UML | `docs/diagrams/ComponentUML.png` | Shows the high-level application components, including routers, templates, static assets, database helpers, and supporting modules. |
| EER | `docs/diagrams/EER.png` | Documents the database entities, relationships, and cardinalities for the SQLite schema. |
| Sequence UML | `docs/diagrams/SequenceUML.png` | Describes request flow between users, FastAPI routes, database helpers, and workflow modules. |
| Admission State UML | `docs/diagrams/StateAdmissionUML.png` | Shows admission lifecycle states such as waiting payment, paid, completed, and cancelled. |
| Lab Order State UML | `docs/diagrams/StateLabOrderUML.png` | Shows lab order lifecycle states from waiting payment through collection and resulted completion. |

## Deployment

### Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Create or update the initial admin user:

```bash
python initial_admin.py
```

Optionally load demo data:

```bash
python seeder.py
```

Run locally:

```bash
python main.py
```

or:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker

The Dockerfile uses Python 3.12 slim and starts the app with one Uvicorn worker:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

The single-worker setting is intentional for the current SQLite-based architecture. The app also avoids Uvicorn reload mode in the container.

## Runtime Threading Notes

The app is configured to avoid SQLite cross-thread connection errors:

- `database.get_db` is an async FastAPI dependency.
- `routers/api.py` uses an async local database dependency.
- Auth dependencies are async.
- Docker runs Uvicorn with `--workers 1`.
- `main.py` runs Uvicorn with `workers=1` when started directly.

This keeps SQLite connections on the request execution path where they are created and avoids FastAPI's synchronous dependency threadpool for database connection creation.

## Dependencies

Core dependencies from `requirements.txt`:

- FastAPI 0.109.1
- Uvicorn 0.27.0
- Jinja2 3.1.3
- python-multipart 0.0.22
- Passlib with bcrypt 1.7.4
- bcrypt 4.1.3
- python-jose with cryptography 3.3.0
- aiofiles 23.2.1
- python-dotenv 1.0.0

## Maintenance and Backups

Recommended operational tasks:

- Back up `hospital.db` regularly.
- Back up the `uploads/` directory with the database.
- Rotate and review logs in production deployments.
- Replace the development `SECRET_KEY` in `auth.py` before production use.
- Use HTTPS and secure cookie flags in production.
- Restrict CORS origins before exposing the app outside a trusted network.

## Known Scope Limits

- No appointment scheduling.
- No patient portal.
- No external laboratory or radiology device integration.
- No electronic claims.
- No advanced analytics.
- No multi-tenant branch support.
- Insurance support is limited to basic cashier-side admission calculation.

## License

Internal hospital/clinic and university project use.
