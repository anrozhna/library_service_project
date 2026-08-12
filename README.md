# Library Service Project

Django REST Framework API for managing a library's books, users, borrowings, and payments, with Telegram notifications, background task scheduling, Docker support, and interactive Swagger documentation.

## Table of Contents

- [Features Implemented](#features-implemented)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running with Docker](#running-with-docker)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Telegram Notifications Setup](#telegram-notifications-setup)
- [Background Tasks (Celery)](#background-tasks-celery)
- [Stripe Payments](#stripe-payments)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)

---

## Features Implemented

### 📚 Books Service
- CRUD functionality for books (`Book` model: title, author, cover, inventory, daily fee)
- `cover` field implemented as `TextChoices` (`HARD` / `SOFT`)
- Read access open to everyone (including unauthenticated users)
- Create / update / delete restricted to admin users only (`IsAdminOrReadOnly` permission)
- JWT authentication applied to all book endpoints
- Registered in Django admin

### 👤 Users Service
- Custom `User` model with `email` as the username field (no `username` field)
- Custom `UserManager` with `create_user()` and `create_superuser()`
- JWT authentication via `djangorestframework-simplejwt`
- User registration endpoint
- Token obtain / refresh endpoints
- `users/me/` endpoint to retrieve and update the current user's profile

### 📖 Borrowings Service
- `Borrowing` model (borrow date, expected return date, actual return date, book, user)
- List and detail endpoints, filtered so non-admin users only see their own borrowings
- Filtering by `is_active` (returned / not returned) for all users
- Filtering by `user_id`, restricted to admin users
- Create endpoint with business logic:
  - Validates that the book has available inventory before creating a borrowing
  - Decreases book inventory by 1 on creation
  - Automatically attaches the current authenticated user (admins can create a borrowing on behalf of another user)
- Return endpoint (`POST /borrowings/<id>/return/`):
  - Sets the actual return date
  - Prevents returning the same borrowing twice
  - Increases book inventory by 1 on return
- Optimized queries with `select_related("book", "user")` to avoid N+1 queries

### 💳 Payments Service
- `Payment` model (status: PENDING/PAID, type: PAYMENT/FINE, linked borrowing, Stripe session data, amount)
- List and detail endpoints, restricted so non-admin users only see their own payments (via the related borrowing's owner)
- Optimized queries with `select_related` across `borrowing`, `borrowing__book`, `borrowing__user`

### 💰 Stripe Integration
- Stripe Python SDK installed and configured with test-mode API keys
- Automatic Stripe Checkout Session created for every new borrowing, with the total price calculated from the book's daily fee and the borrowing duration
- `Payment` record automatically created and linked to each Stripe session (`session_url`, `session_id`, amount)
- `payments` included as a nested field in the borrowing detail response
- `/payments/success/` endpoint marks a payment as `PAID` when Stripe redirects back after a successful checkout (idempotent — safe to call more than once)
- `/payments/cancel/` endpoint informs the user their Stripe session remains valid for 24 hours if payment wasn't completed
- **FINE payments**: if a book is returned after its expected return date, a second `Payment` (type `FINE`) is automatically created and a matching Stripe session generated, using a configurable `FINE_MULTIPLIER`

### 🔔 Telegram Notifications
- Helper function to send messages to a Telegram chat via the Bot API
- Automatic notification sent to Telegram whenever a new borrowing is created
- Daily background check for overdue borrowings, notifying about each one individually (or confirming none are overdue)

### ⏱ Background Tasks (Celery)
- Celery configured with Redis as the message broker
- `django-celery-beat` used to schedule the daily overdue-borrowings check via the database-backed scheduler

### 📄 API Documentation
- Interactive Swagger UI and Redoc documentation via `drf-spectacular`
- Auto-generated OpenAPI 3 schema for all endpoints

### 🐳 Docker
- Containerized with Docker and Docker Compose (app, Redis, Celery worker, Celery beat)

### ✅ Code Quality
- `black` for consistent code formatting
- `flake8` for linting
- `coverage` for test coverage reporting
- GitHub Actions CI running black, flake8, and the full test suite on every push/PR to `main`

---

## Tech Stack

- Python / Django
- Django REST Framework
- djangorestframework-simplejwt (JWT authentication)
- drf-spectacular (Swagger / OpenAPI documentation)
- Celery + Redis (background tasks and scheduling)
- django-celery-beat (periodic task scheduling)
- Stripe (payment processing)
- python-dotenv (environment variable management)
- requests (Telegram Bot API integration)
- Docker / Docker Compose
- SQLite (default database)
- black, flake8, coverage (code quality)

---

## Installation

### Option 1 — Local (without Docker)

```bash
git clone <repository-url>
cd library_service_project

python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root based on `.env.sample` (see [Environment Variables](#environment-variables)).

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000`.

To run background tasks locally, you also need Redis running (e.g. via Docker: `docker run -d -p 6379:6379 redis:7-alpine`) and two additional processes:

```bash
celery -A library_service_project worker --loglevel=info --pool=solo
celery -A library_service_project beat --loglevel=info
```

(`--pool=solo` is required on Windows; not needed on Linux/macOS or inside Docker)

### Option 2 — With Docker

See [Running with Docker](#running-with-docker) below.

---

## Running with Docker

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running

### Steps

1. Create a `.env` file in the project root based on `.env.sample` (see [Environment Variables](#environment-variables)).

   ⚠️ If any value in `.env` contains a `$` character (e.g. inside `DJANGO_SECRET_KEY`), escape it as `$$`, otherwise Docker Compose will try to interpret it as a variable substitution.

2. Build and start all services (app, Redis, Celery worker, Celery beat):

   ```bash
   docker-compose up --build
   ```

3. The API will be available at:

   ```
   http://localhost:8000
   ```

   (not `http://0.0.0.0:8000` — that address is only meaningful inside the container)

4. Create a superuser inside the running container:

   ```bash
   docker-compose exec app python manage.py createsuperuser
   ```

5. Stop all containers:

   ```bash
   docker-compose down
   ```

### Useful commands

```bash
docker-compose logs app              # view app logs
docker-compose logs celery_worker    # view Celery worker logs
docker-compose logs celery_beat      # view Celery beat logs
docker-compose ps                    # check container status
docker-compose exec app python manage.py test   # run tests inside the container
```

---

## Environment Variables

Create a `.env` file in the project root:

```
DJANGO_SECRET_KEY=your-django-secret-key
DEBUG=True

TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

STRIPE_SECRET_KEY=your-stripe-secret-key
FINE_MULTIPLIER=2
```

⚠️ When running via Docker, `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are overridden to use `redis://redis:6379/0` inside `docker-compose.yml` (containers reference each other by service name, not `localhost`).

See `.env.sample` for the template.

---

## API Endpoints

### Books
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/books/` | Everyone | List all books |
| POST | `/books/` | Admin only | Add a new book |
| GET | `/books/<id>/` | Everyone | Get book details |
| PUT/PATCH | `/books/<id>/` | Admin only | Update a book |
| DELETE | `/books/<id>/` | Admin only | Delete a book |

### Users
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/users/` | Everyone | Register a new user |
| POST | `/users/token/` | Everyone | Obtain JWT tokens (login) |
| POST | `/users/token/refresh/` | Everyone | Refresh access token |
| GET | `/users/me/` | Authenticated | Get current user's profile |
| PUT/PATCH | `/users/me/` | Authenticated | Update current user's profile |

### Borrowings
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/borrowings/` | Authenticated | List borrowings (own for regular users, all for admins). Supports `?is_active=true/false` and `?user_id=<id>` (admins only) |
| POST | `/borrowings/` | Authenticated | Create a new borrowing |
| GET | `/borrowings/<id>/` | Authenticated (owner or admin) | Get borrowing details |
| POST | `/borrowings/<id>/return/` | Authenticated | Return a borrowed book |

### Payments
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/payments/` | Authenticated | List payments (own for regular users, all for admins) |
| GET | `/payments/<id>/` | Authenticated (owner or admin) | Get payment details |
| GET | `/payments/success/?session_id=<id>` | Authenticated | Confirm a successful Stripe payment (marks it as `PAID`) |
| GET | `/payments/cancel/` | Authenticated | Inform the user a Stripe session was not completed |

### Documentation
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/schema/` | Raw OpenAPI 3 schema |
| GET | `/api/schema/swagger-ui/` | Interactive Swagger UI |
| GET | `/api/schema/redoc/` | Redoc documentation view |

---

## API Documentation (Swagger)

The project uses [`drf-spectacular`](https://github.com/tfranzel/drf-spectacular) to auto-generate an OpenAPI 3 schema and serve interactive documentation.

1. Start the server (locally or via Docker)
2. Open in your browser:

   ```
   http://localhost:8000/api/schema/swagger-ui/
   ```

3. To test protected endpoints, obtain a JWT token via `/users/token/`, then click **Authorize** in the top-right corner of the Swagger UI and enter:

   ```
   Bearer <your-access-token>
   ```

A Redoc-style alternative view is also available at `/api/schema/redoc/`.

---

## Telegram Notifications Setup

The project sends a Telegram notification whenever a new borrowing is created, and a daily notification about overdue borrowings.

### 1. Create a Telegram bot

1. Open Telegram and find **@BotFather**
2. Send `/newbot` and follow the instructions
3. Copy the bot token BotFather gives you

### 2. Get your chat ID

1. Start a chat with your bot and send it any message (e.g. "hi")
2. Open in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Find `"chat":{"id": ...}` in the response — this is your `TELEGRAM_CHAT_ID`

### 3. Configure environment variables

Add to your `.env` file:
```
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 4. Test the setup

```bash
python manage.py shell
```
```python
from borrowings.telegram_notifications import send_telegram_message
send_telegram_message("Test message")
```

If the message arrives in your Telegram chat, the setup is complete.

---

## Background Tasks (Celery)

The project uses **Celery** with **Redis** as the message broker to run background and scheduled tasks, and **django-celery-beat** to manage the schedule via the database.

### What runs in the background

- **Daily overdue borrowings check** (`borrowings.tasks.check_overdue_borrowings`) — scans for borrowings past their expected return date that haven't been returned yet, and sends a Telegram notification for each one. If nothing is overdue, it sends a single "No borrowings overdue today!" message.

### Running locally (without Docker)

Redis must be running:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Start the worker and the beat scheduler in two separate terminals:
```bash
celery -A library_service_project worker --loglevel=info --pool=solo
celery -A library_service_project beat --loglevel=info
```

> `--pool=solo` is required on Windows due to a known incompatibility between Celery's default prefork pool and Windows multiprocessing. It's not needed on Linux/macOS or inside Docker containers.

### Scheduling the task

The daily schedule is registered via a management command:
```bash
python manage.py schedule_overdue_check
```

You can inspect and modify the schedule anytime via Django admin → **Periodic Tasks**.

### Manually triggering the task (for testing)

```bash
python manage.py shell
```
```python
from borrowings.tasks import check_overdue_borrowings
check_overdue_borrowings.delay()
```

Check the worker terminal for the task result, or your Telegram chat for the notification(s).

---

## Stripe Payments

The project integrates with [Stripe](https://stripe.com) (in **test mode**) to handle borrowing payments and overdue fines.

### Setup

1. Create a Stripe account and switch to **Test mode** in the dashboard
2. Go to **Developers → API keys** and copy your **Secret key** (`sk_test_...`)
3. Add it to your `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   FINE_MULTIPLIER=2
   ```

### How it works

- **On borrowing creation**: the total price (`daily_fee × number of days`) is calculated, a Stripe Checkout Session is created, and a `Payment` (type `PAYMENT`, status `PENDING`) is saved with the session's `url` and `id`. The session URL is available in the borrowing's detail response, under the nested `payments` field.
- **On successful payment**: Stripe redirects the user to `/payments/success/?session_id=...`, which marks the matching `Payment` as `PAID`.
- **On a cancelled/abandoned checkout**: Stripe redirects to `/payments/cancel/`. The session remains valid for 24 hours, so the user can complete the payment later using the same `session_url`.
- **On an overdue return**: if a book is returned after its `expected_return_date`, a second `Payment` (type `FINE`, status `PENDING`) is created automatically, with the amount calculated as `overdue_days × daily_fee × FINE_MULTIPLIER`, along with its own Stripe Checkout Session.

### Testing a payment end-to-end

1. Create a borrowing via the API (`POST /borrowings/`)
2. Retrieve its details (`GET /borrowings/<id>/`) and copy the `session_url` from the nested `payments` field
3. Open `session_url` in your browser and pay with a Stripe test card:
   ```
   Card number: 4242 4242 4242 4242
   Expiry: any future date
   CVC: any 3 digits
   ```
4. You'll be redirected to `/payments/success/?session_id=...`, and the payment's status will update to `PAID`

### Manually creating a raw Checkout Session (for debugging)

```bash
python manage.py shell
```
```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{
        "price_data": {
            "currency": "usd",
            "product_data": {"name": "Library borrowing"},
            "unit_amount": 1400,  # amount in cents ($14.00)
        },
        "quantity": 1,
    }],
    mode="payment",
    success_url="http://localhost:8000/payments/success/",
    cancel_url="http://localhost:8000/payments/cancel/",
)

print(session.url)
```

---

## Running Tests

### Locally

```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test books
python manage.py test users
python manage.py test borrowings
python manage.py test payments
```

### With Docker

```bash
docker-compose exec app python manage.py test
```

### Test coverage

```bash
coverage run --source=. manage.py test
coverage report
```

HTML report:
```bash
coverage html
```
Open `htmlcov/index.html` in your browser.

---

## Code Quality

```bash
black .            # auto-format code
flake8 .           # lint for style issues
```

CI runs `black --check .`, `flake8 .`, and the full test suite (with a coverage threshold) on every push and pull request to `main` via GitHub Actions.

---
