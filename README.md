# Hospital Information System (HIS)

A simple Hospital Information System built with FastAPI, SQLite, Jinja2 templates, and a Persian right-to-left user interface.

> [!WARNING]
> This repository is a university project created for learning, demonstration, and coursework purposes. It is not designed, audited, or approved for production hospital, clinic, billing, legal, or patient-care use.

## Overview

This project implements a small staff-only HIS workflow for educational use. It demonstrates common hospital information system modules such as patient registration, admission, cashier payments, doctor visits, laboratory orders, radiology reports, pharmacy inventory, and user administration.

The application uses server-rendered pages with FastAPI and Jinja2, direct SQLite access through helper functions, and a local `hospital.db` database file. It is intentionally lightweight and suitable for local demos, university presentations, and controlled testing environments.

## Key Features

- Staff authentication with JWT cookies
- Role-based access for admin, reception, doctor, laboratory, radiology, and pharmacy users
- Persian RTL web interface
- Patient search, registration, and admission
- Cashier queue for admissions, prescriptions, and lab orders
- Doctor patient file with prescriptions, lab orders, and radiology requests
- Laboratory order collection, result entry, and result reports
- Radiology report entry with image uploads
- Pharmacy drug catalog, stock ledger, manual prescriptions, and dispensing
- Admin user management
- Printable prescription views
- Demo data seeding for local testing

## Technology Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite
- Jinja2
- Passlib and bcrypt
- python-jose
- python-dotenv
- Custom CSS and minimal JavaScript

## Project Status

The project is complete for its university demonstration scope. It is not production ready.

Known limitations include:

- SQLite-based local storage
- No production security hardening
- No external device, insurance, claims, or hospital system integrations
- No appointment scheduling or patient portal
- Limited concurrency and operational tooling
- No formal clinical, regulatory, privacy, or security audit

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd HIS
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the initial admin user

```bash
python initial_admin.py
```

Default prompt values:

| Field | Value |
| --- | --- |
| Username | `admin` |
| Password | `admin123` |
| Full name | `System Admin` |

### 5. Optional: load demo data

```bash
python seeder.py
```

Demo accounts created by the seeder:

| Username | Role | Password |
| --- | --- | --- |
| `admin` | `admin` | `admin123` or the existing admin password |
| `reception` | `reception` | `123456` |
| `doctor` | `doctor` | `123456` |
| `laboratory` | `laboratory` | `123456` |
| `radiology` | `radiologist` | `123456` |
| `pharmacy` | `pharmacy` | `123456` |

### 6. Run the application

```bash
python main.py
```

Or run it directly with Uvicorn:

```bash
uvicorn main:app --reload
```

Open the application at:

```text
http://localhost:8000
```

## Quick Start Scripts

The repository includes convenience scripts:

```bash
quick-start.bat
quick-start.sh
```

Use the script that matches your operating system. Review the script before running it if you want to understand the exact setup steps.

## User Roles

| Role | Access |
| --- | --- |
| `admin` | User management and full system access |
| `reception` | Patient registration, admissions, and cashier workflow |
| `doctor` | Paid patient queue, patient file, prescriptions, lab orders, and radiology requests |
| `laboratory` | Lab order queue, sample collection, result entry, and reports |
| `radiologist` | Radiology queue, reports, image uploads, and completion |
| `pharmacy` | Drug catalog, inventory, manual prescriptions, and dispensing |

## Main Workflows

### Reception and Cashier

Reception staff can search or create patients, create admissions, select laboratory tests or radiology types, and process pending payments from the cashier queue.

### Doctor

Doctors can view paid admissions, open a patient file, review recent clinical activity, create prescriptions, request lab tests, request radiology services, and complete visits.

### Laboratory

Laboratory users can view active lab orders, collect samples, enter test results, update result values, and generate lab reports.

### Radiology

Radiology users can write and update reports, upload related images, and mark radiology admissions as completed.

### Pharmacy

Pharmacy users can manage the drug catalog, restock inventory, create manual prescriptions, dispense paid prescriptions, and search prescriptions.

### Administration

Administrators can create, edit, activate, and deactivate staff accounts.

## API Endpoints

| Endpoint | Description |
| --- | --- |
| `GET /api/drugs/search` | Drug autocomplete with price, instructions, stock, and threshold data |
| `GET /api/lab-tests/search` | Active lab test autocomplete with catalog and reference-range data |
| `GET /api/patients/lookup` | Patient lookup by national ID |
| `POST /api/patients/quick-create` | Quick patient creation for reception |

## Project Structure

```text
.
|-- main.py
|-- database.py
|-- auth.py
|-- config.py
|-- initial_admin.py
|-- seeder.py
|-- requirements.txt
|-- quick-start.bat
|-- quick-start.sh
|-- docker/
|   `-- Dockerfile
|-- docs/
|   |-- DATA_MODEL.md
|   |-- DATA_STRUCTURE.md
|   |-- DOCUMENTATION.md
|   |-- SRS.md
|   |-- diagrams/
|-- routers/
|-- templates/
|-- static/
|-- uploads/
`-- utils/
```

## Documentation

Additional project documentation is available in the `docs/` directory:

- `docs/DOCUMENTATION.md`
- `docs/SRS.md`
- `docs/DATA_MODEL.md`
- `docs/DATA_STRUCTURE.md`
- `docs/diagrams/`

The diagrams directory contains UML and database diagrams for activity flow, components, classes, sequence flow, entity relationships, and workflow states.

## Docker

A Dockerfile is available in `docker/Dockerfile`.

The container runs Uvicorn with a single worker because the current application uses a local SQLite database:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

## Security Notice

This project uses simple local-development defaults. Before any real deployment, it would require substantial changes, including but not limited to:

- Replacing development secrets
- Enforcing HTTPS
- Securing cookies
- Restricting CORS
- Adding proper logging and monitoring
- Reviewing authentication and authorization behavior
- Moving from local SQLite to a production database where appropriate
- Implementing reliable backup and recovery procedures
- Performing privacy, clinical safety, and security reviews

Do not use this application with real patient data.

## License

This project is provided for university coursework and educational demonstration. Check the repository license or contact the project owner before reusing it.
