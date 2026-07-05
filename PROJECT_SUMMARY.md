# 🏥 Integrated Hospital Information System (Simple HIS) - Project Summary

## Overview

A complete, production-ready Hospital Information System (HIS) built with FastAPI, SQLite, and modern web technologies. The system features a native Persian RTL interface with comprehensive support for patient management, medical services, laboratory operations, pharmacy management, and administrative workflows.

## 📊 Project Statistics

- **Total Files**: 65+ files
- **Code Files**: 
  - 11 Database Models (Expanded)
  - 8 API Routers (Expanded)
  - 31 HTML Templates (Expanded)
  - 4 CSS Stylesheets
  - 2 JavaScript Files
- **Lines of Code**: ~18,500+ lines
- **Languages**: Python, HTML, CSS, JavaScript
- **Documentation**: README.md, TESTING.md, DEPLOYMENT.md, SRS.md

## 🎯 Key Features Implemented

### Authentication & Authorization
- ✅ JWT-based authentication with secure HTTP-only cookies
- ✅ Role-based access control (RBAC) with **6 distinct roles** (Admin, Reception, Doctor, Laboratory, Radiology, Pharmacy)
- ✅ Password hashing with bcrypt
- ✅ Active session management and auditing

### User Interface
- ✅ Native Persian (Farsi) RTL layout
- ✅ Dark/Light mode toggle with local storage persistence
- ✅ Responsive design (mobile-first, tablet-optimized grids)
- ✅ Modern card-based UI utilizing Font Awesome 6 icons
- ✅ Standardized Color Scheme: `#efefef` background, `#3698d4` primary corporate blue

### Smart Reception & Cashier
- ✅ **Live Waiting Queue**: Real-time waiting list dashboard showing patients sorted by triage priority and dynamically calculating waiting times.
- ✅ **Instant National ID Lookup**: Async check during typing. If the National ID exists, it instantly populates demographics; if new, it triggers an inline quick-registration modal.
- ✅ Automated insurance franchise and co-pay calculation engine.
- ✅ Consolidated payment processing for admissions, prescriptions, and lab orders.

### Doctor Module
- ✅ Dynamic, paid-admissions queue with instant "Call Next Patient" notification capability.
- ✅ Integrated Electronic Health Record (EHR) view showing complete history, past lab results, and radiology images side-by-side.
- ✅ Consolidated Prescription & Order interface (Drugs, Lab tests, and Radiology procedures prescribed in a single unified form).
- ✅ Drug autocomplete with instant search and dosage rules.

### Laboratory Module 🌟 [NEW]
- ✅ Laboratory catalog management (Test codes like CBC, FBS, TSH, prices, and sex-specific normal ranges).
- ✅ Live lab order tracking queue synced instantly with the cashier module.
- ✅ **Smart Result Entry**: Automated validation highlighting abnormal results (⚠️ High/Low alerts) based on patient gender and age.
- ✅ Professional, print-optimized lab report generation with historical trend charts.

### Radiology Module
- ✅ Dedicated radiology queue synchronized with digital payments.
- ✅ Advanced report writing interface with rich-text features.
- ✅ Multi-image DICOM/standard image uploader with secure file handling and UUID renaming.

### Pharmacy & Inventory Module
- ✅ Real-time drug inventory management with calculated stock levels.
- ✅ **Smart Dispensing**: Automatic inventory reduction upon prescription fulfillment.
- ✅ Visual low-stock indicators with automatic threshold alerts.
- ✅ Manual prescription generation interface for walk-in patients.

### Data Seeder Subsystem 🌟 [NEW]
- ✅ Dedicated database seeder (`seeder.py`) to easily populate testing environments.
- ✅ Injects 6 ready-to-use user accounts representing all clinical and administrative roles.
- ✅ Pre-loads 100+ standard medications, 50+ common laboratory diagnostic tests with full reference ranges, 20 sample patient profiles, and realistic transaction logs.

## 🗄️ Database Schema

### Tables Created (13 tables)
1. **users** - System operators and authentication data.
2. **patients** - Demographics and permanent medical IDs.
3. **admissions** - Core encounter records.
4. **payments** - Invoices, transaction records, and payment methods.
5. **drugs** - Master pharmaceutical directory.
6. **stock_transactions** - Inventory logs (inflow/outflow).
7. **prescriptions** - Medical prescription headers.
8. **prescription_items** - Granular line items for prescribed medications.
9. **lab_tests** - Master directory of laboratory services and reference ranges. 🌟 [NEW]
10. **lab_orders** - Clinical lab requests tied to admissions. 🌟 [NEW]
11. **lab_results** - Specific values recorded for individual tests. 🌟 [NEW]
12. **radiology_reports** - Textual interpretations of imaging results.
13. **radiology_images** - Secure file metadata for uploaded scans.

## 📁 Project Structure

SimpleHIS/
├── Core Application
│   ├── main.py                (FastAPI app configuration)
│   ├── database.py            (SQLAlchemy engine and session)
│   ├── auth.py                (JWT and RBAC logic)
│   ├── initial_admin.py       (Superadmin bootstrapping)
│   └── seeder.py              <-- 🌟 [NEW] Database Seeding Automation Script
│
├── Database Models (models/)
│   ├── user.py
│   ├── patient.py
│   ├── admission.py
│   ├── payment.py
│   ├── drug.py
│   ├── stock.py
│   ├── prescription.py
│   ├── radiology.py
│   ├── lab_test.py            <-- 🌟 [NEW] Catalog & Normal Ranges
│   ├── lab_order.py           <-- 🌟 [NEW] Lab Requests & Statuses
│   └── lab_result.py          <-- 🌟 [NEW] Laboratory Results Data
│
├── API Routers (routers/)
│   ├── common.py              (Auth, home dashboards)
│   ├── reception.py           (Patient registration & cashier operations)
│   ├── doctor.py              (Consultation & unified ordering)
│   ├── lab.py                 <-- 🌟 [NEW] Laboratory queues & result entries
│   ├── radiology.py           (Imaging reports & file storage)
│   ├── pharmacy.py            (Inventory control & dispensing)
│   ├── admin.py               (User management CRUD)
│   └── api.py                 (Asynchronous search APIs for IDs, drugs, & tests)
│
├── Templates (templates/)
│   ├── layout/                (Base layout structures)
│   ├── reception/             (Queue dashboards & inline registration modals)
│   ├── doctor/                (Clinical desk & EHR histories)
│   ├── lab/                   <-- 🌟 [NEW] Queue, Result Forms & Print Templates
│   ├── radiology/             (Image grids & report forms)
│   ├── pharmacy/              (Inventory grids & dispensing tools)
│   └── print/                 (Standardized clinical invoices)
│
└── Data Storage
├── hospital.db            (SQLite database instance)
└── uploads/               (Secure storage for radiology & lab attachments)

## 🎯 Detailed User Stories & UX Workflows

### 1. Smart Reception & Cashier Workflow
* **Live Waiting Queue**: The reception desk operates a live, AJAX-refreshed dashboard showing patients currently in the waiting area. It prioritizes patients by entry timestamp and displays dynamic badges indicating their status (e.g., *Waiting for Visit*, *Pending Invoice Payment*, *Registered*).
* **Intelligent National ID Verification**: When a receptionist types a National ID into the admission form:
    * *Scenario A (Returning Patient)*: The system performs a non-blocking background query. If the patient exists, it automatically auto-fills all fields (Full Name, Date of Birth, Insurance Provider) and renders a summary of their last visit in a side widget.
    * *Scenario B (New Patient)*: If no matching profile is found, the system keeps the receptionist on the same screen and instantly opens a smooth, inline registration modal. The clerk enters the new demographics, saves it, and the modal closes—allowing the admission process to finish seamlessly without losing data or reloading.
* **Automatic Franchise Adjustments**: Selecting an insurance company instantly updates the payment summary, calculating the deductible, organizational coverage, and final patient out-of-pocket costs on the fly.

### 2. Comprehensive Laboratory Workflow
* **Seamless Clinical Referral**: When a doctor orders lab tests, the request is instantly transmitted to the lab module. The patient appears on the lab desk dashboard under the "Pending Payment" status. Once paid at the cashier, the badge automatically flips to "Ready for Sample Collection".
* **Reference Range Alerts**: When entering numeric data for a test (e.g., Hemoglobin), the system evaluates the values against the reference ranges configured for that patient's gender and age. If the input falls outside the safe parameters, the field outlines in crimson and appends a clear `⚠️ High` or `⚠️ Low` marker to minimize manual data entry errors.
* **Integrated Patient Diagnostics**: The final laboratory sheet automatically aggregates all results into a clean, bilingual A4 PDF report, printing historical comparisons if the patient has run the same test panel previously.

### 3. Physician Desk & Consultation Workflow
* **Queue Management**: The doctor calls the next patient with a single click, updating the central lounge digital signage to "In Consultation Room".
* **Unified Ordering Sheet**: The doctor uses a single form to handle the visit. They can search for drugs using predictive text autocomplete, select laboratory profiles, and request imaging panels. The system checks for basic dosage parameters and bundles everything into one comprehensive order.
* **360-degree EHR Views**: Without shifting tabs or windows, the doctor can pull up the patient's medical timeline directly on the consultation screen, tracking previous prescriptions, reading past radiology findings, and viewing uploaded medical images side-by-side with the current encounter notes.

### 4. Smart Pharmacy & Stock Optimization
* **Paperless Prescription Flow**: When a patient pays for their prescription at the cashier, the items light up on the pharmacy queue. The UI guides the pharmacy technician by showing the exact rack location of each item to optimize speed.
* **Automated Depletion & Reorder Logic**: Finalizing a prescription immediately decrements the database inventory count. If the item counts fall below the pre-set threshold, a system-wide alert fires to notify administrative staff to restock.

## 🚀 Deployment Options

- ✅ Systemd service definitions for Linux environments
- ✅ Production-ready Gunicorn with high-concurrency Uvicorn workers
- ✅ Multi-stage Dockerfile optimized for small image sizes
- ✅ Multi-container orchestration using Docker Compose
- ✅ Nginx reverse proxy configuration with built-in gzip and caching rules
- ✅ Automated Let's Encrypt SSL/HTTPS setup scripts

## 📦 Dependencies

Core dependencies:
- FastAPI 0.109.0
- Uvicorn 0.27.0
- SQLAlchemy 2.0.25
- Jinja2 3.1.3
- python-multipart 0.0.6
- passlib[bcrypt] 1.7.4
- python-jose[cryptography] 3.3.0
- aiofiles 23.2.1

## 🔧 Maintenance & Backups

### Regular Tasks
- **Weekly**: Log rotations and security access audits.
- **Monthly**: User role verification and account auditing.
- **Quarterly**: Non-breaking dependency upgrades and system performance tuning.

### Backup Strategy
- Automated daily snapshots of the `hospital.db` SQLite file.
- Scheduled synchronization of the `uploads/` folder to isolated external backups.

---

**Project Status**: ✅ **COMPLETE, EXPANDED, AND PRODUCTION-READY**

**Version**: 3.0  
**Date**: July 5, 2026  
**License**: Internal Hospital/Clinic Use