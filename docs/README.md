# Simple Hospital Information System (HIS)

A lightweight web-based Hospital Information System built with FastAPI, SQLite, Jinja2 templates, and a Persian RTL user interface. The current implementation covers reception, cashier, doctor, laboratory, radiology, pharmacy, administration, print views, async lookup APIs, and seed data for local testing.

## Current Status

- Version: 3.0
- Date: July 11, 2026
- Database: local SQLite file, `hospital.db`
- Data access style: direct `sqlite3` helpers in `database.py`
- UI: server-rendered Jinja2 templates with custom CSS and minimal JavaScript
- Authentication: JWT cookie login with role checks

## Implemented Features

### Authentication and Roles

- Login/logout flow with JWT access token stored in a browser cookie.
- Password hashing through Passlib.
- Role-based route protection.
- Active/inactive user accounts.
- Admin user management.

Implemented roles:

| Role | Purpose |
| --- | --- |
| `admin` | Full system access and user management |
| `reception` | Patient registration, admission, cashier |
| `doctor` | Paid doctor queue, patient file, clinical orders |
| `laboratory` | Lab order queue, sample collection, result entry, reports |
| `radiologist` | Paid radiology queue, report entry, image upload |
| `pharmacy` | Drug catalog, inventory, manual prescriptions, dispensing |

### Reception and Cashier

- Patient search by national ID or phone.
- Patient registration and quick-create API from the admission screen.
- Smart patient lookup by national ID.
- Admission creation for doctor, laboratory, and radiology services.
- Laboratory admission can create a lab order with selected tests.
- Cashier queue for admissions, prescriptions, and lab orders.
- Payment registration with receipt numbers.
- Cancellation for pending admissions, prescriptions, and lab orders.
- Admission pricing in `config.py`.
- Basic insurance plan calculation for admission payments.

### Doctor Module

- Queue of paid doctor admissions.
- Patient file view with recent prescriptions, lab orders, and radiology admissions.
- Unified clinical ordering:
  - Drug prescriptions
  - Laboratory test orders
  - Radiology requests
- Prescription totals are calculated from selected drugs and quantities.
- Doctor visits can be marked completed.

### Laboratory Module

- Lab order worklist for pending, paid, collected, and resulted orders.
- Sample collection status transition.
- Result entry per lab order item.
- Automatic low/normal/high flagging for numeric results based on sex-specific normal ranges.
- Printable/report-oriented lab result view.

### Radiology Module

- Radiology admission queue for paid and completed radiology admissions.
- Report creation and update per radiology admission.
- Multi-image upload with validation and UUID-based stored filenames.
- Uploaded files are served from `/uploads`.
- Radiology admissions can be marked completed.

### Pharmacy and Inventory

- Drug catalog management.
- Restocking through stock transactions.
- Current stock is calculated from stock transaction sums.
- Manual prescription creation for walk-in patients.
- Paid prescription dispensing queue.
- Stock availability checks before dispensing.
- Dispensing creates negative stock transactions and marks prescriptions dispensed.
- Prescription search by prescription ID or patient national ID.
- Printable prescription view.

### API Endpoints

- `/api/drugs/search`: drug autocomplete and stock payload.
- `/api/lab-tests/search`: active lab test autocomplete.
- `/api/patients/lookup`: national ID patient lookup.
- `/api/patients/quick-create`: quick patient creation for reception.

## Technology Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite
- Jinja2
- python-multipart
- Passlib
- python-jose
- aiofiles
- python-dotenv
- Font Awesome 6 through templates
- Custom CSS in `static/css`

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create or update the initial admin user:

```bash
python initial_admin.py
```

Default prompt values:

- Username: `admin`
- Password: `admin123`
- Full name: `System Admin`

3. Optional: load testing catalog data and sample users:

```bash
python seeder.py
```

Seeder accounts:

| Username | Role | Password |
| --- | --- | --- |
| `admin` | admin | `admin123` for newly created admin, or existing admin password |
| `reception` | reception | `123456` |
| `doctor` | doctor | `123456` |
| `laboratory` | laboratory | `123456` |
| `radiology` | radiologist | `123456` |
| `pharmacy` | pharmacy | `123456` |

4. Run the app:

```bash
python main.py
```

or:

```bash
uvicorn main:app --reload
```

5. Open:

```text
http://localhost:8000
```

## Main Routes

| Area | Routes |
| --- | --- |
| Common | `/`, `/login`, `/logout`, `/home`, `/print/prescription/{id}` |
| Reception | `/reception/patients`, `/reception/patients/new`, `/reception/admit`, `/reception/cashier` |
| Doctor | `/doctor/patients`, `/doctor/patient/{patient_id}/admission/{admission_id}`, `/doctor/orders/create` |
| Laboratory | `/lab/orders`, `/lab/orders/{order_id}/results`, `/lab/orders/{order_id}/report` |
| Radiology | `/radiology/admissions`, `/radiology/report/{admission_id}` |
| Pharmacy | `/pharmacy/inventory`, `/pharmacy/drug/new`, `/pharmacy/restock`, `/pharmacy/manual-prescription`, `/pharmacy/dispense`, `/pharmacy/search` |
| Admin | `/admin/users` |
| API | `/api/drugs/search`, `/api/lab-tests/search`, `/api/patients/lookup`, `/api/patients/quick-create` |

## Data Model

The database schema is created by `init_db()` in `database.py`. The implemented tables are:

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

See [DATA_MODEL.md](DATA_MODEL.md) for the full table structure, relationships, cardinalities, and diagram notes for UML and EER diagrams.

## Project Structure

```text
HIS/
|-- main.py
|-- database.py
|-- auth.py
|-- config.py
|-- initial_admin.py
|-- seeder.py
|-- requirements.txt
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
|-- docker/
`-- hospital.db
```

## Important Notes

- `hospital.db` is a local SQLite database file and is initialized automatically at app startup.
- `uploads/` stores radiology images by generated UUID filenames.
- Current stock is not stored directly on `drugs`; it is calculated from `stock_transactions`.
- `payments.payable_id` is a polymorphic reference. Use `payments.payable_type` to determine whether the row points to an admission, prescription, or lab order.
- For production, replace `SECRET_KEY` in `auth.py`, enable HTTPS, set secure cookie flags, restrict CORS, and back up both `hospital.db` and `uploads/`.

## Useful Commands

```bash
python initial_admin.py
python seeder.py
python main.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## License

Internal hospital/clinic and university project use.
