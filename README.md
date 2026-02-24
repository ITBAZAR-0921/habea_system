# HABA Safety Management System

## Description
Web-based workplace HSE management system for employee safety instruction tracking.

## Tech Stack
- Django 6
- SQLite (default) or PostgreSQL via environment variables
- Bootstrap 5

## Current Features
- Department and Employee management
- Employee Excel import (`.xlsx`)
- Safety instruction library
- Employee instruction record with validity period
- Dashboard with key HSE indicators
- Report page for overdue and expiring instruction records
- Role-based access levels

## Employee Excel Import
`/employees/upload/` хуудсаар импорт хийнэ.

### Recommended columns
- `last_name` (required)
- `first_name` (required)
- `register_number` (required)
- `phone`
- `department`
- `is_head` (`TRUE/FALSE`, `1/0`, `yes/no`, `тийм/үгүй`)
- `username` (empty байж болно, автоматаар үүсгэнэ)
- `password` (empty бол default password хэрэглэнэ)

### Optional extra columns
- `position`
- `email`
- `hired_date` (`YYYY-MM-DD`)

## Role Levels
- `system_admin`: тохиргоо, эрх оноолт, бүх хэсэг
- `hse_manager`: ажилтан Excel импорт, үндсэн хяналт
- `department_head`: тайлан харах
- `employee`: суурь хандалт

Role assignment: `/settings/`

## Environment Variables (optional)
Use these when running with PostgreSQL:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Django settings:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`

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
