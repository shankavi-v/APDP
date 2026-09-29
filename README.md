# Hospital Management System v2.0

A console-based Hospital Management System written in Python (single-file edition).

**Student:** Shankavi Vigneswaran | **Student ID:** 2600157
**Unit:** Unit 20 - Advanced Programming (APDP) | **Institute:** BCAS Campus, Jaffna

## How to run

1. Install Python 3.8 or above.
2. Open a terminal in this folder.
3. Run:

```bash
python hospital_system.py
```

## Default login (first run only)

| Username | Password |
|----------|----------|
| admin    | admin123 |

Please change the password after your first login.

## Features

- Patient management (add, list, search, delete)
- Doctor management (add, list, available slots)
- Appointment scheduling (schedule, cancel, complete)
- Billing (create bills, add items, process payments)
- User login with role-based access (Admin / Receptionist)
- Built-in test suite (main menu option 7)

## Notes

- No external libraries needed, only the Python standard library.
- A `data/` folder with JSON files is created automatically on first run.
- Design patterns used: Singleton (DataManager), Factory Method (`from_dict`), Builder-style bills, abstract base class (`Person`).
