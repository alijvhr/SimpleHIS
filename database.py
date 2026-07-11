import sqlite3
from datetime import datetime, timezone

DATABASE_NAME = "hospital.db"


class ValueStr(str):
    @property
    def value(self):
        return str(self)


class DateTimeStr(str):
    def _datetime(self):
        value = str(self)
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

    def strftime(self, date_format):
        parsed = self._datetime()
        return parsed.strftime(date_format) if parsed else str(self)

    def isoformat(self):
        parsed = self._datetime()
        return parsed.isoformat() if parsed else str(self)


class Obj:
    def __init__(self, **items):
        for key, value in items.items():
            if key in ("role", "gender", "status", "admission_type", "payable_type"):
                value = ValueStr(value) if value is not None else None
            elif key.endswith("_at"):
                value = DateTimeStr(value) if value is not None else None
            setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


def now():
    return datetime.now(timezone.utc).isoformat()


async def get_db():
    db = sqlite3.connect(DATABASE_NAME)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def one(db, sql, params=()):
    row = db.execute(sql, params).fetchone()
    return Obj(**dict(row)) if row else None


def all_rows(db, sql, params=()):
    return [Obj(**dict(row)) for row in db.execute(sql, params).fetchall()]


def execute(db, sql, params=()):
    cur = db.execute(sql, params)
    db.commit()
    return cur


def get_user(db, user_id):
    return one(db, "SELECT * FROM users WHERE id = ?", (user_id,))


def get_patient(db, patient_id):
    return one(db, "SELECT * FROM patients WHERE id = ?", (patient_id,))


def get_admission(db, admission_id):
    admission = one(db, "SELECT * FROM admissions WHERE id = ?", (admission_id,))
    if admission:
        admission.patient = get_patient(db, admission.patient_id)
        admission.radiology_report = get_radiology_report(db, admission.id)
    return admission


def get_lab_test(db, test_id):
    return one(db, "SELECT * FROM lab_tests WHERE id = ?", (test_id,))


def get_drug(db, drug_id):
    return one(db, "SELECT * FROM drugs WHERE id = ?", (drug_id,))


def get_prescription_items(db, prescription_id):
    items = all_rows(db, "SELECT * FROM prescription_items WHERE prescription_id = ?", (prescription_id,))
    for item in items:
        item.drug = get_drug(db, item.drug_id)
    return items


def get_prescription(db, prescription_id):
    prescription = one(db, "SELECT * FROM prescriptions WHERE id = ?", (prescription_id,))
    if prescription:
        prescription.patient = get_patient(db, prescription.patient_id)
        prescription.admission = get_admission(db, prescription.admission_id) if prescription.admission_id else None
        prescription.items = get_prescription_items(db, prescription.id)
    return prescription


def get_lab_order_items(db, order_id):
    items = all_rows(db, "SELECT * FROM lab_order_items WHERE order_id = ?", (order_id,))
    for item in items:
        item.test = get_lab_test(db, item.test_id)
        item.result = one(db, "SELECT * FROM lab_results WHERE order_item_id = ?", (item.id,))
    return items


def get_lab_order(db, order_id):
    order = one(db, "SELECT * FROM lab_orders WHERE id = ?", (order_id,))
    if order:
        order.patient = get_patient(db, order.patient_id)
        order.admission = get_admission(db, order.admission_id)
        order.items = get_lab_order_items(db, order.id)
    return order


def get_radiology_report(db, admission_id):
    report = one(db, "SELECT * FROM radiology_reports WHERE admission_id = ?", (admission_id,))
    if report:
        report.images = all_rows(db, "SELECT * FROM radiology_images WHERE report_id = ?", (report.id,))
    return report


def stock_for_drug(db, drug_id):
    row = db.execute(
        "SELECT SUM(quantity_change) AS stock FROM stock_transactions WHERE drug_id = ?",
        (drug_id,),
    ).fetchone()
    return row["stock"] or 0


def init_db():
    db = sqlite3.connect(DATABASE_NAME)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER
        );
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            admission_type TEXT NOT NULL,
            description TEXT NOT NULL,
            radiology_type TEXT,
            status TEXT DEFAULT 'waiting_payment',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL,
            paid_at TEXT,
            paid_by INTEGER,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payable_type TEXT NOT NULL,
            payable_id INTEGER NOT NULL,
            amount NUMERIC NOT NULL,
            receipt_number TEXT,
            status TEXT DEFAULT 'paid',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            form TEXT NOT NULL,
            dosage TEXT NOT NULL,
            default_instructions TEXT NOT NULL,
            price NUMERIC NOT NULL,
            min_threshold INTEGER DEFAULT 10,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INTEGER NOT NULL,
            quantity_change INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            admission_id INTEGER,
            is_manual INTEGER DEFAULT 0,
            total_amount NUMERIC NOT NULL,
            status TEXT DEFAULT 'waiting_payment',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL,
            dispensed_at TEXT,
            dispensed_by INTEGER
        );
        CREATE TABLE IF NOT EXISTS prescription_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL,
            drug_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            instructions TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS radiology_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER UNIQUE NOT NULL,
            report_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS radiology_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS lab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            sample_type TEXT,
            price NUMERIC NOT NULL DEFAULT 0,
            male_normal_range TEXT,
            female_normal_range TEXT,
            unit TEXT,
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS lab_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            admission_id INTEGER NOT NULL,
            total_amount NUMERIC NOT NULL DEFAULT 0,
            status TEXT DEFAULT 'waiting_payment',
            clinical_note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL,
            paid_at TEXT,
            paid_by INTEGER,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS lab_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            price NUMERIC NOT NULL DEFAULT 0,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id INTEGER UNIQUE NOT NULL,
            value TEXT NOT NULL,
            flag TEXT,
            entered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            entered_by INTEGER NOT NULL
        );
        """
    )
    db.commit()
    db.close()
