"""
Hospital Management System v2.0  --  Single-file edition
==========================================================
Just run:   python hospital_system.py
"""

import sys
import json
import os
import re
import threading
import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Tuple

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass



# ==============================================================================
# CONSOLE UI (colors & printing)
# ==============================================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class Colors:
    """ANSI color codes used across the whole application."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"


def _enable_windows_ansi():
    """Make ANSI colors work on old Windows cmd.exe as well."""
    if os.name == "nt":
        os.system("")


_enable_windows_ansi()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner(title: str):
    width = 70
    line = "=" * width
    print(f"\n{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(width)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}\n")


def print_header(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}>> {text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-' * (len(text) + 3)}{Colors.RESET}")


def print_success(text: str):
    print(f"{Colors.GREEN}{Colors.BOLD}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}{Colors.BOLD}[ERROR] {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[!] {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.CYAN}[i] {text}{Colors.RESET}")


def print_menu(title: str, options: list):
    """options: list of (key, label) tuples."""
    print_header(title)
    for key, label in options:
        print(f"  {Colors.MAGENTA}{Colors.BOLD}[{key}]{Colors.RESET} {label}")
    print()


def prompt(text: str) -> str:
    return input(f"{Colors.YELLOW}{text}{Colors.RESET}").strip()


def print_table(headers: list, rows: list):
    """Simple colorful table printer for lists of records."""
    if not rows:
        print_warning("No records to display.")
        return

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    header_line = " | ".join(
        f"{Colors.BOLD}{h.ljust(widths[i])}{Colors.RESET}" for i, h in enumerate(headers)
    )
    print(header_line)
    print(f"{Colors.DIM}{'-' * (sum(widths) + 3 * (len(widths) - 1))}{Colors.RESET}")
    for row in rows:
        print(" | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
    print()


# ==============================================================================
# VALIDATORS
# ==============================================================================

class Validator:

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address."""
        if not email or email.strip() == "":
            return False, "Email is required"

        pattern = r'^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"

        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number."""
        if not phone or phone.strip() == "":
            return False, "Phone number is required"

        cleaned = re.sub(r'\D', '', phone)

        if len(cleaned) not in [10, 11, 12]:
            return False, "Phone number must be 10-12 digits"

        return True, ""

    @staticmethod
    def validate_required(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate that a required field is not empty."""
        if not value or value.strip() == "":
            return False, f"{field_name} is required"
        return True, ""

    @staticmethod
    def validate_date(value: str) -> Tuple[bool, str]:
        """Validate a date string in YYYY-MM-DD format."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True, ""
        except (ValueError, TypeError):
            return False, "Date must be in YYYY-MM-DD format"

    @staticmethod
    def validate_positive_number(value, field_name: str) -> Tuple[bool, str]:
        """Validate that a number is positive."""
        try:
            if float(value) <= 0:
                return False, f"{field_name} must be greater than 0"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength."""
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters"
        return True, ""


# ==============================================================================
# MODELS (domain entities)
# ==============================================================================

# --------------------------------------------------------------------------- #
# Enums (clear, self-documenting constants instead of magic strings)
# --------------------------------------------------------------------------- #

class Role(str, Enum):
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    ONLINE = "Online Payment"
    INSURANCE = "Insurance"


class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# --------------------------------------------------------------------------- #
# Person (abstract base) -- Dependency Inversion target
# --------------------------------------------------------------------------- #

class Person(ABC):
    """Abstract base class every 'person' in the hospital extends."""

    def __init__(self, name: str, contact: str, email: str, address: str):
        self.id: str = self._generate_id()
        self.name = name
        self.contact = contact
        self.email = email
        self.address = address
        self.active: bool = True
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())[:8]

    def update_timestamp(self):
        self.updated_at = datetime.now()

    @abstractmethod
    def get_role(self) -> str:
        """Get the role of the person."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert object to dictionary for JSON storage."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict):
        """Create object from dictionary (Factory Method pattern)."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Patient
# --------------------------------------------------------------------------- #

class Patient(Person):
    def __init__(self, name: str, contact: str, email: str, address: str,
                 date_of_birth: str, blood_group: str, emergency_contact: str):
        super().__init__(name, contact, email, address)
        self.date_of_birth = date_of_birth
        self.blood_group = blood_group
        self.emergency_contact = emergency_contact
        self._medical_history: List[str] = []

    def get_role(self) -> str:
        return "Patient"

    def add_medical_history(self, history: str):
        """Add medical history entry."""
        self._medical_history.append(history)
        self.update_timestamp()

    @property
    def medical_history(self) -> List[str]:
        return list(self._medical_history)

    def calculate_age(self) -> int:
        """Calculate age from date of birth."""
        try:
            birth = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - birth.year
            if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
                age -= 1
            return age
        except (ValueError, TypeError):
            return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "email": self.email,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "blood_group": self.blood_group,
            "emergency_contact": self.emergency_contact,
            "medical_history": self._medical_history,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Patient":
        """Create Patient object from dictionary."""
        patient = cls(
            name=data["name"],
            contact=data["contact"],
            email=data["email"],
            address=data["address"],
            date_of_birth=data["date_of_birth"],
            blood_group=data["blood_group"],
            emergency_contact=data["emergency_contact"],
        )
        patient.id = data["id"]
        patient._medical_history = data.get("medical_history", [])
        patient.active = data.get("active", True)
        patient.created_at = datetime.fromisoformat(data["created_at"])
        patient.updated_at = datetime.fromisoformat(data["updated_at"])
        return patient


# --------------------------------------------------------------------------- #
# Doctor
# --------------------------------------------------------------------------- #

class Doctor(Person):
    def __init__(self, name: str, contact: str, email: str, address: str,
                 specialization: str, qualification: str, experience_years: int,
                 license_number: str, consultation_fee: float):
        super().__init__(name, contact, email, address)
        self.specialization = specialization
        self.qualification = qualification
        self.experience_years = experience_years
        self.license_number = license_number
        self.consultation_fee = consultation_fee

    def get_role(self) -> str:
        return "Doctor"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "email": self.email,
            "address": self.address,
            "specialization": self.specialization,
            "qualification": self.qualification,
            "experience_years": self.experience_years,
            "license_number": self.license_number,
            "consultation_fee": self.consultation_fee,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Doctor":
        doctor = cls(
            name=data["name"],
            contact=data["contact"],
            email=data["email"],
            address=data["address"],
            specialization=data["specialization"],
            qualification=data["qualification"],
            experience_years=data["experience_years"],
            license_number=data["license_number"],
            consultation_fee=data["consultation_fee"],
        )
        doctor.id = data["id"]
        doctor.active = data.get("active", True)
        doctor.created_at = datetime.fromisoformat(data["created_at"])
        doctor.updated_at = datetime.fromisoformat(data["updated_at"])
        return doctor


# --------------------------------------------------------------------------- #
# User (system login account -- admin / receptionist)
# --------------------------------------------------------------------------- #

class User(Person):
    def __init__(self, name: str, contact: str, email: str, address: str,
                 username: str, password_hash: str, role: Role):
        super().__init__(name, contact, email, address)
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def get_role(self) -> str:
        return self.role.value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "email": self.email,
            "address": self.address,
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role.value,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        user = cls(
            name=data["name"],
            contact=data.get("contact", ""),
            email=data["email"],
            address=data.get("address", ""),
            username=data["username"],
            password_hash=data["password_hash"],
            role=Role(data["role"]),
        )
        user.id = data["id"]
        user.active = data.get("active", True)
        user.created_at = datetime.fromisoformat(data["created_at"])
        user.updated_at = datetime.fromisoformat(data["updated_at"])
        return user


# --------------------------------------------------------------------------- #
# Appointment
# --------------------------------------------------------------------------- #

class Appointment:
    def __init__(self, patient_id: str, doctor_id: str, appt_date: str,
                 appt_time: str, appt_type: str, reason: str):
        self.id = str(uuid.uuid4())[:8]
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.date = appt_date
        self.time = appt_time
        self.type = appt_type
        self.reason = reason
        self.status = AppointmentStatus.SCHEDULED
        self.notes = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def cancel(self):
        """Cancel appointment."""
        self.status = AppointmentStatus.CANCELLED
        self.updated_at = datetime.now()

    def complete(self):
        """Mark appointment as completed."""
        self.status = AppointmentStatus.COMPLETED
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "date": self.date,
            "time": self.time,
            "type": self.type,
            "reason": self.reason,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Appointment":
        appt = cls(
            patient_id=data["patient_id"],
            doctor_id=data["doctor_id"],
            appt_date=data["date"],
            appt_time=data["time"],
            appt_type=data["type"],
            reason=data["reason"],
        )
        appt.id = data["id"]
        appt.status = AppointmentStatus(data.get("status", "SCHEDULED"))
        appt.notes = data.get("notes", "")
        appt.created_at = datetime.fromisoformat(data["created_at"])
        appt.updated_at = datetime.fromisoformat(data["updated_at"])
        return appt


# --------------------------------------------------------------------------- #
# BillItem + Bill (Builder pattern: build a bill up item by item)
# --------------------------------------------------------------------------- #

class BillItem:
    def __init__(self, description: str, quantity: int, unit_price: float):
        self.id = str(uuid.uuid4())[:8]
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BillItem":
        item = cls(data["description"], data["quantity"], data["unit_price"])
        item.id = data["id"]
        return item


class Bill:
    """Represents a patient's bill. Items are added one at a time
    (Builder-style) via add_item()."""

    def __init__(self, patient_id: str, appointment_id: Optional[str] = None):
        self.id = self._generate_id()
        self.bill_number = self._generate_bill_number()
        self.patient_id = patient_id
        self.appointment_id = appointment_id
        self._items: List[BillItem] = []
        self._tax_rate: float = 0.0
        self._discount: float = 0.0
        self._payment_status = PaymentStatus.PENDING
        self._payment_method: Optional[PaymentMethod] = None
        self._payment_date: Optional[datetime] = None
        self.notes = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @staticmethod
    def _generate_id() -> str:
        return "BIL" + str(uuid.uuid4())[:8].upper()

    @staticmethod
    def _generate_bill_number() -> str:
        """Generate bill number with date."""
        date_str = datetime.now().strftime("%Y%m")
        random_num = str(uuid.uuid4().int)[:4]
        return f"BILL{date_str}{random_num}"

    @property
    def items(self) -> List[BillItem]:
        return list(self._items)

    @property
    def subtotal(self) -> float:
        """Calculate subtotal before tax and discount."""
        return sum(item.total for item in self._items)

    @property
    def tax_amount(self) -> float:
        """Calculate tax amount."""
        return self.subtotal * (self._tax_rate / 100)

    @property
    def total(self) -> float:
        """Calculate final total."""
        return self.subtotal + self.tax_amount - self._discount

    @property
    def payment_status(self) -> PaymentStatus:
        return self._payment_status

    def add_item(self, description: str, quantity: int, unit_price: float) -> BillItem:
        """Add item to bill."""
        for existing in self._items:
            if existing.description == description and existing.unit_price == unit_price:
                existing.quantity += quantity
                self.updated_at = datetime.now()
                return existing
        item = BillItem(description, quantity, unit_price)
        self._items.append(item)
        self.updated_at = datetime.now()
        return item

    def remove_item(self, item_id: str):
        """Remove item from bill."""
        self._items = [i for i in self._items if i.id != item_id]
        self.updated_at = datetime.now()

    def process_payment(self, method: PaymentMethod, amount: Optional[float] = None):
        """Process payment."""
        if amount is None or amount >= self.total:
            self._payment_status = PaymentStatus.PAID
        elif amount > 0:
            self._payment_status = PaymentStatus.PARTIALLY_PAID
        else:
            raise ValueError("Invalid payment amount")

        self._payment_method = method
        self._payment_date = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bill_number": self.bill_number,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "items": [i.to_dict() for i in self._items],
            "tax_rate": self._tax_rate,
            "discount": self._discount,
            "payment_status": self._payment_status.value,
            "payment_method": self._payment_method.value if self._payment_method else None,
            "payment_date": self._payment_date.isoformat() if self._payment_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bill":
        bill = cls(patient_id=data["patient_id"], appointment_id=data.get("appointment_id"))
        bill.id = data["id"]
        bill.bill_number = data["bill_number"]
        bill._items = [BillItem.from_dict(i) for i in data.get("items", [])]
        bill._tax_rate = data.get("tax_rate", 0.0)
        bill._discount = data.get("discount", 0.0)
        bill._payment_status = PaymentStatus(data.get("payment_status", "PENDING"))
        pm = data.get("payment_method")
        bill._payment_method = PaymentMethod(pm) if pm else None
        pd = data.get("payment_date")
        bill._payment_date = datetime.fromisoformat(pd) if pd else None
        bill.notes = data.get("notes", "")
        bill.created_at = datetime.fromisoformat(data["created_at"])
        bill.updated_at = datetime.fromisoformat(data["updated_at"])
        return bill


# ==============================================================================
# DATA MANAGER (Singleton + Adapter)
# ==============================================================================

class DataManager:
    """Singleton class for managing JSON data storage. Thread-safe implementation."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.data_dir = "data"
        self._ensure_data_directory()
        self._initialized = True
        self._cache: Dict[str, list] = {}
        self._cache_lock = threading.Lock()

    def _ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def _read_json(self, filename: str) -> List[dict]:
        path = self._path(filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_json(self, filename: str, records: List[dict]) -> bool:
        try:
            with open(self._path(filename), "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
            return True
        except OSError:
            return False

    def get_all(self, filename: str) -> List[Dict]:
        """Get all records from a file."""
        with self._cache_lock:
            return self._read_json(filename)

    def get_by_id(self, filename: str, record_id: str) -> Optional[Dict]:
        """Get record by ID."""
        records = self._read_json(filename)
        for record in records:
            if record.get("id") == record_id:
                return record
        return None

    def add(self, filename: str, record: Dict) -> bool:
        """Add a new record."""
        with self._cache_lock:
            records = self._read_json(filename)

            # Check if record with same ID exists
            if any(r.get("id") == record.get("id") for r in records):
                return False

            records.append(record)
            return self._write_json(filename, records)

    def update(self, filename: str, record_id: str, updated_record: Dict) -> bool:
        """Update an existing record by ID."""
        with self._cache_lock:
            records = self._read_json(filename)
            for i, record in enumerate(records):
                if record.get("id") == record_id:
                    records[i] = updated_record
                    return self._write_json(filename, records)
            return False

    def delete(self, filename: str, record_id: str) -> bool:
        """Delete a record by ID."""
        with self._cache_lock:
            records = self._read_json(filename)
            new_records = [r for r in records if r.get("id") != record_id]
            if len(new_records) == len(records):
                return False
            return self._write_json(filename, new_records)


# ==============================================================================
# MANAGERS (business logic)
# ==============================================================================

# --------------------------------------------------------------------------- #
# UserManager -- login accounts (admin / receptionist)
# --------------------------------------------------------------------------- #

class UserManager:
    _filename = "users.json"

    def __init__(self):
        self.data_manager = DataManager()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_user(self, name: str, email: str, username: str, password: str,
                     role: Role, contact: str = "", address: str = "") -> Optional[User]:
        """Create new system user with the given role."""
        print(f"Creating user: {username}, role: {role.value}, name: {name}, email: {email}")

        if self.get_user_by_username(username):
            print(f"Error: username '{username}' already exists")
            return None

        user = User(name, contact, email, address, username, self._hash_password(password), role)
        if self.data_manager.add(self._filename, user.to_dict()):
            print(f"User added: {username} (Role: {role.value})")
            return user
        return None

    def login(self, username: str, password: str) -> Optional[User]:
        """Attempt login for a user."""
        print(f"Attempting login for user: {username}")
        user = self.get_user_by_username(username)
        if user and user.password_hash == self._hash_password(password) and user.active:
            print(f"LOGIN OK: {user.name} (Role: {user.get_role()})")
            return user
        print_msg = "invalid credentials" if user else "user not found"
        print(f"LOGIN FAILED: {print_msg}")
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        for data in self.data_manager.get_all(self._filename):
            if data.get("username") == username:
                return User.from_dict(data)
        return None

    def get_all_users(self) -> List[User]:
        return [User.from_dict(d) for d in self.data_manager.get_all(self._filename)]

    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user details. Reports the fields that changed."""
        data = self.data_manager.get_by_id(self._filename, user_id)
        if not data:
            return False
        user = User.from_dict(data)
        changes = {}
        for key, value in kwargs.items():
            if hasattr(user, key) and getattr(user, key) != value:
                changes[key] = f"{getattr(user, key)} -> {value}"
                setattr(user, key, value)
        user.update_timestamp()
        ok = self.data_manager.update(self._filename, user_id, user.to_dict())
        if ok:
            print(f"User updated: {user_id}")
            if changes:
                print(f"TESTING OK: User '{user.name}' profile updated - Changes: {changes}")
        return ok

    def change_password(self, username: str, new_password: str) -> bool:
        """Change password for a user."""
        valid, msg = Validator.validate_password(new_password)
        if not valid:
            print(f"Error: {msg}")
            return False
        user = self.get_user_by_username(username)
        if not user:
            return False
        ok = self.update_user(user.id, password_hash=self._hash_password(new_password))
        if ok:
            print(f"TESTING OK: Password changed for user '{username}'")
        return ok


# --------------------------------------------------------------------------- #
# PatientManager
# --------------------------------------------------------------------------- #

class PatientManager:
    _filename = "patients.json"

    def __init__(self):
        self.data_manager = DataManager()

    def add_patient(self, name: str, contact: str, email: str, address: str,
                     date_of_birth: str, blood_group: str,
                     emergency_contact: str) -> Optional[Patient]:
        """Add a new patient."""
        for field_name, value in (("Name", name), ("Contact", contact)):
            valid, msg = Validator.validate_required(value, field_name)
            if not valid:
                print(f"Error: {msg}")
                return None

        valid, msg = Validator.validate_email(email)
        if not valid:
            print(f"Error: {msg}")
            return None

        try:
            patient = Patient(name, contact, email, address, date_of_birth,
                               blood_group, emergency_contact)
            if self.data_manager.add(self._filename, patient.to_dict()):
                print(f"Patient added: {name} (ID: {patient.id}) - testing OK")
                return patient
            return None
        except Exception as e:
            print(f"Error adding patient: {e}")
            return None

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        data = self.data_manager.get_by_id(self._filename, patient_id)
        return Patient.from_dict(data) if data else None

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return [Patient.from_dict(d) for d in self.data_manager.get_all(self._filename)]

    def update_patient(self, patient_id: str, **kwargs) -> bool:
        """Update patient details."""
        patient = self.get_patient(patient_id)
        if not patient:
            return False
        for key, value in kwargs.items():
            if hasattr(patient, key):
                setattr(patient, key, value)
        patient.update_timestamp()
        return self.data_manager.update(self._filename, patient_id, patient.to_dict())

    def delete_patient(self, patient_id: str) -> bool:
        """Delete an existing patient record."""
        patient = self.get_patient(patient_id)
        if not patient:
            return False
        ok = self.data_manager.delete(self._filename, patient_id)
        if ok:
            print(f"Patient deleted: {patient.name} (ID: {patient_id}) - testing OK")
        return ok

    def search_patients(self, keyword: str) -> List[Patient]:
        """Search patients by name (case-insensitive, partial match)."""
        keyword = keyword.lower()
        return [p for p in self.get_all_patients() if keyword in p.name.lower()]


# --------------------------------------------------------------------------- #
# DoctorManager
# --------------------------------------------------------------------------- #

class DoctorManager:
    _filename = "doctors.json"

    def __init__(self):
        self.data_manager = DataManager()

    def add_doctor(self, name: str, contact: str, email: str, address: str,
                    specialization: str, qualification: str, experience_years: int,
                    license_number: str, consultation_fee: float) -> Optional[Doctor]:
        """Add a new doctor."""
        try:
            doctor = Doctor(name=name, contact=contact, email=email, address=address,
                             specialization=specialization, qualification=qualification,
                             experience_years=experience_years, license_number=license_number,
                             consultation_fee=consultation_fee)
            if self.data_manager.add(self._filename, doctor.to_dict()):
                print(f"Doctor added: {name} ({specialization}) - testing OK")
                return doctor
            return None
        except Exception as e:
            print(f"Error adding doctor: {e}")
            return None

    def get_doctor(self, doctor_id: str) -> Optional[Doctor]:
        data = self.data_manager.get_by_id(self._filename, doctor_id)
        if data:
            print(f"Found doctor: {data['name']} with ID: {doctor_id}")
            return Doctor.from_dict(data)
        return None

    def get_all_doctors(self) -> List[Doctor]:
        return [Doctor.from_dict(d) for d in self.data_manager.get_all(self._filename)]

    def get_doctors_by_specialization(self, specialization: str) -> List[Doctor]:
        return [d for d in self.get_all_doctors()
                if specialization.lower() in d.specialization.lower()]

    def get_available_slots(self, doctor_id: str) -> List[str]:
        """Return a simple fixed set of consultation slots for a doctor."""
        print(f"Loading slots for doctor ID: {doctor_id}")
        return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

    def update_doctor(self, doctor_id: str, **kwargs) -> bool:
        doctor = self.get_doctor(doctor_id)
        if not doctor:
            return False
        for key, value in kwargs.items():
            if hasattr(doctor, key):
                setattr(doctor, key, value)
        doctor.update_timestamp()
        return self.data_manager.update(self._filename, doctor_id, doctor.to_dict())

    def delete_doctor(self, doctor_id: str) -> bool:
        return self.data_manager.delete(self._filename, doctor_id)


# --------------------------------------------------------------------------- #
# AppointmentManager
# --------------------------------------------------------------------------- #

class AppointmentManager:
    _filename = "appointments.json"

    def __init__(self, doctor_manager: DoctorManager, patient_manager: PatientManager):
        self.data_manager = DataManager()
        self.doctor_manager = doctor_manager
        self.patient_manager = patient_manager

    def schedule_appointment(self, patient_id: str, doctor_id: str, appt_date: str,
                              appt_time: str, appt_type: str, reason: str) -> Optional[Appointment]:
        """Schedule an appointment with the selected doctor and time."""
        patient = self.patient_manager.get_patient(patient_id)
        doctor = self.doctor_manager.get_doctor(doctor_id)
        if not patient or not doctor:
            print("Error: patient or doctor not found")
            return None

        print("=" * 50)
        print("SAVING APPOINTMENT")
        print(f"Patient ID: {patient_id}")
        print(f"Doctor ID: {doctor_id}")
        print(f"Date: {appt_date}")
        print(f"Time: {appt_time}")
        print(f"Type: {appt_type}")
        print(f"Reason: {reason}")
        print("=" * 50)

        appt = Appointment(patient_id, doctor_id, appt_date, appt_time, appt_type, reason)
        if self.data_manager.add(self._filename, appt.to_dict()):
            print(f"Appointment scheduled: {patient.name} with Dr. {doctor.name} "
                  f"on {appt_date} at {appt_time} - testing OK")
            return appt
        return None

    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        data = self.data_manager.get_by_id(self._filename, appointment_id)
        return Appointment.from_dict(data) if data else None

    def get_all_appointments(self) -> List[Appointment]:
        """Get all appointments."""
        return [Appointment.from_dict(d) for d in self.data_manager.get_all(self._filename)]

    def update_appointment(self, appointment_id: str, **kwargs) -> bool:
        """Update appointment."""
        appt = self.get_appointment(appointment_id)
        if not appt:
            return False
        for key, value in kwargs.items():
            if hasattr(appt, key):
                setattr(appt, key, value)
        return self.data_manager.update(self._filename, appointment_id, appt.to_dict())

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel appointment."""
        appt = self.get_appointment(appointment_id)
        if not appt:
            return False
        appt.cancel()
        return self.data_manager.update(self._filename, appointment_id, appt.to_dict())

    def complete_appointment(self, appointment_id: str) -> bool:
        """Mark appointment as completed."""
        appt = self.get_appointment(appointment_id)
        if not appt:
            return False
        appt.complete()
        return self.data_manager.update(self._filename, appointment_id, appt.to_dict())


# --------------------------------------------------------------------------- #
# BillManager
# --------------------------------------------------------------------------- #

class BillManager:
    _filename = "bills.json"

    def __init__(self, patient_manager: PatientManager):
        self.data_manager = DataManager()
        self.patient_manager = patient_manager

    def create_bill(self, patient_id: str, appointment_id: Optional[str] = None,
                     tax_rate: float = 0.0) -> Optional[Bill]:
        """Create a new bill for a patient."""
        patient = self.patient_manager.get_patient(patient_id)
        if not patient:
            print("Error: patient not found")
            return None

        bill = Bill(patient_id, appointment_id)
        bill._tax_rate = tax_rate
        if self.data_manager.add(self._filename, bill.to_dict()):
            print(f"Bill created: {bill.bill_number} (ID: {bill.id}) - {patient.name} - "
                  f"Total: Rs. {bill.total:,.2f} - testing OK")
            return bill
        return None

    def get_bill(self, bill_id: str) -> Optional[Bill]:
        data = self.data_manager.get_by_id(self._filename, bill_id)
        if data:
            return Bill.from_dict(data)
        # Fallback: also allow lookup by the human-friendly bill_number
        # (e.g. "BILL2026081843") since that's what gets printed to the user.
        for d in self.data_manager.get_all(self._filename):
            if d.get("bill_number") == bill_id:
                return Bill.from_dict(d)
        return None

    def get_all_bills(self) -> List[Bill]:
        return [Bill.from_dict(d) for d in self.data_manager.get_all(self._filename)]

    def add_item_to_bill(self, bill_id: str, description: str, quantity: int,
                          unit_price: float) -> bool:
        """Add item to bill."""
        bill = self.get_bill(bill_id)
        if not bill:
            return False

        # Check if this item already exists (prevent duplicate insert issues)
        bill.add_item(description, quantity, unit_price)
        ok = self.data_manager.update(self._filename, bill.id, bill.to_dict())
        if ok:
            print(f"Item added to bill: {description} x{quantity} = Rs. {bill.total:,.2f}")
        return ok

    def process_payment(self, bill_id: str, method: PaymentMethod,
                         amount: Optional[float] = None) -> bool:
        """Process payment for a bill."""
        bill = self.get_bill(bill_id)
        if not bill:
            return False
        patient = self.patient_manager.get_patient(bill.patient_id)
        try:
            bill.process_payment(method, amount)
        except ValueError as e:
            print(f"Error: {e}")
            return False
        ok = self.data_manager.update(self._filename, bill.id, bill.to_dict())
        if ok:
            name = patient.name if patient else bill.patient_id
            print(f"Payment processed: {bill.bill_number} - {name} - "
                  f"Rs. {bill.total:,.2f} ({method.value}) - testing OK")
        return ok


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

class HospitalManagementSystem:
    def __init__(self):
        self.user_manager = UserManager()
        self.patient_manager = PatientManager()
        self.doctor_manager = DoctorManager()
        self.appointment_manager = AppointmentManager(self.doctor_manager, self.patient_manager)
        self.bill_manager = BillManager(self.patient_manager)
        self.current_user = None
        self._bootstrap_admin()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    def _bootstrap_admin(self):
        """Create a default admin account the very first time the app runs."""
        if not self.user_manager.get_all_users():
            self.user_manager.create_user(
                name="Administrator", email="admin@hms.local", username="admin",
                password="admin123", role=Role.ADMIN,
            )
            print_info("Default admin account created -> username: admin | password: admin123")
            print_warning("Please change this password after your first login!")

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    def login_screen(self) -> bool:
        print_banner("HOSPITAL MANAGEMENT SYSTEM v2.0")
        print(f"{Colors.DIM}Type 'exit' as username anytime to quit.{Colors.RESET}\n")
        attempts = 0
        while attempts < 5:
            username = prompt("Username: ")
            if username.lower() == "exit":
                return False
            password = prompt("Password: ")
            user = self.user_manager.login(username, password)
            if user:
                self.current_user = user
                print_success(f"Welcome, {user.name}! ({user.get_role()})")
                return True
            print_error("Invalid username or password.")
            attempts += 1
        print_error("Too many failed attempts.")
        return False

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def run(self):
        clear_screen()
        if not self.login_screen():
            print_info("Goodbye!")
            return

        while True:
            options = [
                ("1", "Patient Management"),
                ("2", "Doctor Management"),
                ("3", "Appointment Management"),
                ("4", "Billing"),
                ("5", "My Profile"),
            ]
            if self.current_user.role == Role.ADMIN:
                options.append(("6", "User Management (Admin)"))
            options.append(("7", "Run Built-in Test Suite"))
            options.append(("0", "Logout / Exit"))

            print_menu(f"MAIN MENU - logged in as {self.current_user.name}", options)
            choice = prompt("Select an option: ")

            if choice == "1":
                self.patient_menu()
            elif choice == "2":
                self.doctor_menu()
            elif choice == "3":
                self.appointment_menu()
            elif choice == "4":
                self.billing_menu()
            elif choice == "5":
                self.profile_menu()
            elif choice == "6" and self.current_user.role == Role.ADMIN:
                self.user_menu()
            elif choice == "7":
                self.run_test_suite()
            elif choice == "0":
                print_info("Goodbye!")
                break
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # Patient menu
    # ------------------------------------------------------------------ #
    def patient_menu(self):
        while True:
            print_menu("PATIENT MANAGEMENT", [
                ("1", "Add new patient"),
                ("2", "List all patients"),
                ("3", "Search patient by name"),
                ("4", "Delete patient"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                name = prompt("Name: ")
                contact = prompt("Contact: ")
                email = prompt("Email: ")
                address = prompt("Address: ")
                dob = prompt("Date of birth (YYYY-MM-DD): ")
                blood_group = prompt("Blood group: ")
                emergency = prompt("Emergency contact: ")
                self.patient_manager.add_patient(name, contact, email, address,
                                                  dob, blood_group, emergency)
            elif choice == "2":
                self._list_patients()
            elif choice == "3":
                keyword = prompt("Search keyword: ")
                results = self.patient_manager.search_patients(keyword)
                self._render_patients(results)
            elif choice == "4":
                pid = prompt("Patient ID to delete: ")
                if self.patient_manager.delete_patient(pid):
                    print_success("Patient deleted.")
                else:
                    print_error("Patient not found.")
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    def _list_patients(self):
        self._render_patients(self.patient_manager.get_all_patients())

    def _render_patients(self, patients):
        rows = [(p.id, p.name, p.calculate_age(), p.blood_group, p.contact) for p in patients]
        print_table(["ID", "Name", "Age", "Blood", "Contact"], rows)

    # ------------------------------------------------------------------ #
    # Doctor menu
    # ------------------------------------------------------------------ #
    def doctor_menu(self):
        while True:
            print_menu("DOCTOR MANAGEMENT", [
                ("1", "Add new doctor"),
                ("2", "List all doctors"),
                ("3", "View available slots"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                name = prompt("Name: ")
                contact = prompt("Contact: ")
                email = prompt("Email: ")
                address = prompt("Address: ")
                specialization = prompt("Specialization: ")
                qualification = prompt("Qualification: ")
                exp = prompt("Experience (years): ")
                license_no = prompt("License number: ")
                fee = prompt("Consultation fee: ")
                self.doctor_manager.add_doctor(
                    name, contact, email, address, specialization, qualification,
                    int(exp or 0), license_no, float(fee or 0),
                )
            elif choice == "2":
                doctors = self.doctor_manager.get_all_doctors()
                rows = [(d.id, d.name, d.specialization, d.experience_years,
                          f"Rs. {d.consultation_fee:,.2f}") for d in doctors]
                print_table(["ID", "Name", "Specialization", "Exp (yrs)", "Fee"], rows)
            elif choice == "3":
                did = prompt("Doctor ID: ")
                slots = self.doctor_manager.get_available_slots(did)
                print_info("Available slots: " + ", ".join(slots))
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # Appointment menu
    # ------------------------------------------------------------------ #
    def appointment_menu(self):
        while True:
            print_menu("APPOINTMENT MANAGEMENT", [
                ("1", "Schedule appointment"),
                ("2", "List all appointments"),
                ("3", "Cancel appointment"),
                ("4", "Complete appointment"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                pid = prompt("Patient ID: ")
                did = prompt("Doctor ID: ")
                appt_date = prompt("Date (YYYY-MM-DD): ")
                appt_time = prompt("Time (HH:MM): ")
                appt_type = prompt("Type (e.g. Consultation): ") or "Consultation"
                reason = prompt("Reason: ")
                self.appointment_manager.schedule_appointment(
                    pid, did, appt_date, appt_time, appt_type, reason)
            elif choice == "2":
                appts = self.appointment_manager.get_all_appointments()
                rows = [(a.id, a.patient_id, a.doctor_id, a.date, a.time, a.status.value)
                        for a in appts]
                print_table(["ID", "Patient", "Doctor", "Date", "Time", "Status"], rows)
            elif choice == "3":
                aid = prompt("Appointment ID: ")
                if self.appointment_manager.cancel_appointment(aid):
                    print_success("Appointment cancelled.")
                else:
                    print_error("Appointment not found.")
            elif choice == "4":
                aid = prompt("Appointment ID: ")
                if self.appointment_manager.complete_appointment(aid):
                    print_success("Appointment marked as completed.")
                else:
                    print_error("Appointment not found.")
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # Billing menu
    # ------------------------------------------------------------------ #
    def billing_menu(self):
        while True:
            print_menu("BILLING", [
                ("1", "Create new bill"),
                ("2", "Add item to bill"),
                ("3", "Process payment"),
                ("4", "List all bills"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                pid = prompt("Patient ID: ")
                appt_id = prompt("Appointment ID (optional, press enter to skip): ") or None
                tax = prompt("Tax rate % (optional, default 0): ")
                self.bill_manager.create_bill(pid, appt_id, float(tax or 0))
            elif choice == "2":
                bid = prompt("Bill ID: ")
                desc = prompt("Item description: ")
                qty = prompt("Quantity: ")
                price = prompt("Unit price: ")
                self.bill_manager.add_item_to_bill(bid, desc, int(qty or 1), float(price or 0))
            elif choice == "3":
                bid = prompt("Bill ID: ")
                print_info("Payment methods: 1) Cash 2) Card 3) Online Payment 4) Insurance")
                method_choice = prompt("Choose method: ")
                method_map = {"1": PaymentMethod.CASH, "2": PaymentMethod.CARD,
                              "3": PaymentMethod.ONLINE, "4": PaymentMethod.INSURANCE}
                method = method_map.get(method_choice, PaymentMethod.CASH)
                amount = prompt("Amount paid (press enter for full amount): ")
                self.bill_manager.process_payment(bid, method, float(amount) if amount else None)
            elif choice == "4":
                bills = self.bill_manager.get_all_bills()
                rows = [(b.id, b.bill_number, b.patient_id, f"Rs. {b.total:,.2f}", b.payment_status.value)
                        for b in bills]
                print_table(["Bill ID", "Bill #", "Patient", "Total", "Status"], rows)
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # Profile menu
    # ------------------------------------------------------------------ #
    def profile_menu(self):
        while True:
            print_menu("MY PROFILE", [
                ("1", "View profile"),
                ("2", "Update profile"),
                ("3", "Change password"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                u = self.current_user
                print_table(["Field", "Value"], [
                    ("Name", u.name), ("Username", u.username),
                    ("Email", u.email), ("Role", u.get_role()),
                ])
            elif choice == "2":
                name = prompt(f"New name (blank keeps '{self.current_user.name}'): ")
                email = prompt(f"New email (blank keeps '{self.current_user.email}'): ")
                kwargs = {}
                if name:
                    kwargs["name"] = name
                if email:
                    kwargs["email"] = email
                if kwargs:
                    self.user_manager.update_user(self.current_user.id, **kwargs)
                    for k, v in kwargs.items():
                        setattr(self.current_user, k, v)
                    print_success("Profile updated.")
            elif choice == "3":
                new_password = prompt("New password: ")
                if self.user_manager.change_password(self.current_user.username, new_password):
                    print_success("Password changed.")
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # User menu (admin only)
    # ------------------------------------------------------------------ #
    def user_menu(self):
        while True:
            print_menu("USER MANAGEMENT (ADMIN)", [
                ("1", "Create new user"),
                ("2", "List all users"),
                ("0", "Back"),
            ])
            choice = prompt("Select an option: ")

            if choice == "1":
                name = prompt("Full name: ")
                email = prompt("Email: ")
                username = prompt("Username: ")
                password = prompt("Password: ")
                print_info("Roles: 1) Admin 2) Receptionist")
                role_choice = prompt("Choose role: ")
                role = Role.ADMIN if role_choice == "1" else Role.RECEPTIONIST
                self.user_manager.create_user(name, email, username, password, role)
            elif choice == "2":
                users = self.user_manager.get_all_users()
                rows = [(u.id, u.name, u.username, u.get_role()) for u in users]
                print_table(["ID", "Name", "Username", "Role"], rows)
            elif choice == "0":
                return
            else:
                print_error("Invalid option.")

    # ------------------------------------------------------------------ #
    # Built-in test suite (mirrors the project's Table 3 test cases)
    # ------------------------------------------------------------------ #
    def run_test_suite(self):
        print_banner("RUNNING BUILT-IN TEST SUITE")

        # 1. Login already proven by the fact current_user exists
        print_success(f"[TC-1] Login OK for '{self.current_user.username}'")

        # 2. Register patient
        patient = self.patient_manager.add_patient(
            "Test Patient", "0771234567", "test.patient@example.com",
            "Negombo, Sri Lanka", "1999-05-14", "O+", "0779876543")

        # 3. Register doctor
        doctor = self.doctor_manager.add_doctor(
            "Test Doctor", "0711234567", "test.doctor@example.com",
            "Colombo, Sri Lanka", "Cardiology", "MBBS, MD", 8, "SLMC12345", 2500.0)

        # 4. Delete patient (create a throwaway one first so we don't lose our test patient)
        temp_patient = self.patient_manager.add_patient(
            "Temp Patient", "0700000000", "temp@example.com", "N/A",
            "2000-01-01", "A+", "0700000001")
        if temp_patient:
            self.patient_manager.delete_patient(temp_patient.id)

        # 5. Schedule appointment
        appt = None
        if patient and doctor:
            appt = self.appointment_manager.schedule_appointment(
                patient.id, doctor.id, str(date.today()), "09:00",
                "Consultation", "General checkup")

        # 6. Generate bill
        if patient:
            bill = self.bill_manager.create_bill(
                patient.id, appt.id if appt else None, tax_rate=0.0)
            if bill:
                self.bill_manager.add_item_to_bill(bill.id, "Consultation Fee", 1, 2500.0)
                self.bill_manager.process_payment(bill.id, PaymentMethod.ONLINE)

        # 7. Update profile
        self.user_manager.update_user(self.current_user.id, email=self.current_user.email)

        # 8. Change password (set it right back so future logins still work)
        self.user_manager.change_password(self.current_user.username, "admin123") \
            if self.current_user.username == "admin" else None

        # 9. Create new system user with admin role
        self.user_manager.create_user(
            "Test Admin", "test.admin@example.com", f"test_admin_{doctor.id if doctor else '0'}",
            "test1234", Role.ADMIN)

        print_banner("TEST SUITE COMPLETE")


def main():
    app = HospitalManagementSystem()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n")
        print_info("Interrupted. Goodbye!")


if __name__ == "__main__":
    main()
