# HABA Safety Management System

## Description
Production-ready Django based HSE management system.

## Core Architecture
- Django `User` + `Employee` profile model
- Hierarchical `Department` (unlimited depth with parent-child structure)
- Master data via admin only: `Department`, `Position`, `Location`
- Role management via Django `Group`

## Role Groups
- `system_admin`
- `hse_manager`
- `department_head`
- `employee`

## Employee Management Rules
- Employee creation/edit is done only in Django admin (`/admin/`)
- Frontend employee page is read-only list
- Excel import is removed from the system

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Tests
```bash
python manage.py test
```
