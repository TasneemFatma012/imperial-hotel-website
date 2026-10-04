# Imperial Hotel

A Django hotel website with a royal-inspired design, room information, guest
accounts, contact and FAQ pages, date-based room booking, and Razorpay checkout.

## Requirements

- Python 3.11
- Django 4.2
- Razorpay test API credentials to try the online checkout

The project currently uses SQLite, so no separate database server is needed.

## Run locally on Windows

Open PowerShell in the project folder:

```powershell
cd C:\Users\tasne\hotel
```

Create and activate a virtual environment, then install Django:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "Django>=4.2,<5.0"
```

If PowerShell prevents activation, allow scripts for this terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Apply database migrations and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser. Stop the server with `Ctrl+C`.

## Razorpay test checkout

Checkout requires Razorpay API credentials. Create test-mode keys in your
Razorpay account and set them in the same PowerShell window before starting
Django:

```powershell
$env:RAZORPAY_KEY_ID = "rzp_test_your_key_id"
$env:RAZORPAY_KEY_SECRET = "your_test_key_secret"
python manage.py runserver
```

Keep the secret private; do not commit it or paste it into source files. These
environment variables apply only to the current PowerShell window. Without
both credentials, new bookings cannot be submitted for online payment.

## Booking behavior

- Select arrival and checkout dates; checkout must be after arrival.
- The current displayed rate is ₹2,500 per night for each room category.
- A pending payment temporarily holds its dates for 15 minutes. Confirmed
  bookings prevent overlapping bookings.
- Each room category is currently treated as one reservable unit. Update the
  inventory logic before using the site for categories with multiple physical
  rooms.
- Payments are confirmed server-side after verifying the Razorpay signature
  and checking the captured payment details. If a late payment arrives after
  its room dates have been rebooked, the site requests a refund and records its
  refund status.

## Useful commands

```powershell
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py createsuperuser
```

The Django admin is available at <http://127.0.0.1:8000/admin/> after creating
a superuser.

## Project layout

- `app/` — Django models, forms, views, routes, migrations, and tests
- `hotel/` — project settings and root URL configuration
- `templates/` — HTML pages
- `static/` — CSS, JavaScript, and images
- `manage.py` — Django management commands

## Production note

The checked-in Django settings are for local development. Before deployment,
configure a private `DJANGO_SECRET_KEY` environment variable, disable `DEBUG`,
configure `ALLOWED_HOSTS`, serve static files appropriately, and use production
Razorpay credentials only in a secure environment. If `DJANGO_SECRET_KEY` is
not set locally, Django generates a temporary key when the server starts.

For example, set a persistent key in the PowerShell session before starting
Django:

```powershell
$env:DJANGO_SECRET_KEY = "paste-a-newly-generated-secret-key-here"
python manage.py runserver
```

Generate a secure key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
