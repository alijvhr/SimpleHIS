# Simple Hospital Information System (HIS)

A modern, lightweight, Persian (Farsi) web-based Hospital Information System built with FastAPI and SQLite.

> **🔒 Security Update (Feb 16, 2026)**: All dependencies updated to patched versions to fix critical vulnerabilities. See [SECURITY_UPDATE.md](SECURITY_UPDATE.md) for details.

## Features

- **Persian RTL Interface**: Full right-to-left layout with Persian text
- **Dark/Light Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Role-Based Access Control**: Admin, Reception, Doctor, Radiologist, Pharmacy
- **Patient Management**: Search, register, and track patients
- **Admission System**: Accept patients for doctor visits or radiology with descriptions
- **Doctor Module**: View patients, write multi-drug prescriptions, complete visits
- **Radiology Module**: Write reports and upload images
- **Pharmacy Module**: 
  - Drug inventory management with low-stock alerts
  - Manual and doctor prescriptions
  - Prescription dispensing with stock tracking
  - Search old prescriptions
- **Payment System**: Track payments for admissions and prescriptions
- **Prescription Printing**: Print-friendly prescription invoices

## Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 Templates, Pure CSS, Minimal jQuery
- **Icons**: Font Awesome 6 (Free)
- **Authentication**: JWT with secure cookies

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository** (or extract the files)

```bash
cd SimpleHIS
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Create the first admin user**

```bash
python initial_admin.py
```

Follow the prompts to create your admin account. Default credentials:
- Username: `admin`
- Password: `admin123`
- Full Name: `مدیر سیستم`

4. **Run the application**

```bash
uvicorn main:app --reload
```

Or simply:

```bash
python main.py
```

5. **Access the system**

Open your browser and navigate to:
```
http://localhost:8000
```

Login with the admin credentials you created.

## Default Port

The application runs on port **8000** by default. If you need to change the port:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## User Roles

| Role | Persian Name | Access |
|------|-------------|--------|
| Admin | مدیرکل | Full access to all modules including user management |
| Reception | پذیرش | Patient registration, admissions, cashier (payments) |
| Doctor | پزشک | View patients, write prescriptions, complete visits |
| Radiologist | رادیولوژیست | View radiology admissions, write reports, upload images |
| Pharmacy | داروخانه | Inventory, manual prescriptions, dispense prescriptions |

## Workflow

### 1. Reception Workflow
1. Search for existing patient or register new patient
2. Admit patient (doctor visit or radiology) with description/reason
3. Cashier pays for admission → status changes to "paid"

### 2. Doctor Workflow
1. View list of paid doctor admissions
2. Open patient file
3. Write prescription with unlimited drugs
4. System auto-calculates total amount
5. Complete visit when done

### 3. Radiology Workflow
1. View list of paid radiology admissions
2. Write report and upload images
3. Complete admission

### 4. Pharmacy Workflow
1. **Inventory**: View stock levels, add new drugs, restock
2. **Manual Prescription**: Create prescriptions for walk-in customers
3. **Dispense**: View paid prescriptions and dispense them (reduces stock)
4. **Search**: Find old prescriptions by ID or patient national ID

### 5. Prescription Payment & Printing
1. Prescriptions go to cashier for payment
2. After payment, pharmacy can dispense
3. Print prescription invoice from multiple locations

## Database Schema

The system uses SQLite database (`hospital.db`) with the following main tables:

- **users**: System users with roles
- **patients**: Patient demographics
- **admissions**: Patient admissions (doctor/radiology)
- **payments**: Payment records for admissions and prescriptions
- **drugs**: Drug master data
- **stock_transactions**: Track drug inventory changes
- **prescriptions**: Prescription headers
- **prescription_items**: Individual drugs in prescriptions
- **radiology_reports**: Radiology reports
- **radiology_images**: Uploaded radiology images

## Project Structure

```
SimpleHIS/
├── main.py                 # FastAPI application entry point
├── database.py             # Database configuration
├── auth.py                 # Authentication utilities
├── initial_admin.py        # Script to create first admin user
├── requirements.txt        # Python dependencies
├── models/                 # Database models
│   ├── user.py
│   ├── patient.py
│   ├── admission.py
│   ├── payment.py
│   ├── drug.py
│   ├── stock.py
│   ├── prescription.py
│   └── radiology.py
├── routers/                # API route handlers
│   ├── common.py
│   ├── reception.py
│   ├── doctor.py
│   ├── radiology.py
│   ├── pharmacy.py
│   └── admin.py
├── templates/              # Jinja2 HTML templates
│   ├── layout/
│   ├── common/
│   ├── reception/
│   ├── doctor/
│   ├── radiology/
│   ├── pharmacy/
│   ├── admin/
│   └── print/
├── static/                 # Static files
│   ├── css/
│   ├── js/
│   └── assets/
└── uploads/                # Uploaded files (radiology images)
```

## Color Scheme

The application uses a modern color scheme defined in CSS variables:

**Light Mode:**
- Background: `#efefef` (very light gray)
- Primary: `#3698d4` (blue)
- Card Background: `#ffffff` (white)
- Text: `#333` (dark gray)

**Dark Mode:**
- Background: `#121212` (very dark)
- Primary: `#3698d4` (blue)
- Card Background: `#1e1e1e` (dark)
- Text: `#e0e0e0` (light gray)

## Features in Detail

### Dynamic Prescription Form
- Add unlimited drugs to a prescription
- Auto-complete drug search
- Auto-fill drug details (manufacturer, form, dosage, price)
- Auto-calculate total amount
- Editable instructions for each drug

### Stock Management
- Real-time stock calculation from transactions
- Low-stock highlighting (below minimum threshold)
- Stock reduced automatically when dispensing prescriptions

### Print-Friendly Invoices
- Clean, professional prescription printouts
- Includes hospital logo, patient info, drug table
- Optimized for A4 paper
- Auto-print on page load

## Security Notes

⚠️ **Important for Production:**

1. Change the `SECRET_KEY` in `auth.py` to a secure random string
2. Use HTTPS in production
3. Configure proper firewall rules
4. Regular database backups
5. Keep Python packages updated

## Customization

### Adding a Logo

Replace `/static/assets/logo.png` with your hospital logo.

### Changing Colors

Edit `/static/css/vars.css` to customize colors for both light and dark modes.

### Adding More Roles

1. Edit `models/user.py` to add new role to `UserRole` enum
2. Update sidebar menu logic in `templates/layout/panel.htm`
3. Create new router and templates for the role

## Troubleshooting

### Database Issues

If you encounter database errors, delete `hospital.db` and restart:

```bash
rm hospital.db
python initial_admin.py
python main.py
```

### Port Already in Use

If port 8000 is busy, use a different port:

```bash
uvicorn main:app --port 8080 --reload
```

### Static Files Not Loading

Make sure the `static` and `uploads` directories exist and have proper permissions.

## Support

For issues, questions, or contributions, please contact the development team.

## License

This project is developed for internal hospital/clinic use.

---

**Version:** 2.0  
**Date:** February 16, 2026  
**Prepared for:** Internal Hospital/Clinic Use
