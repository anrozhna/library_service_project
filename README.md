# Library Service Project
 
Django REST Framework API for managing a library's books, users, and borrowings, with Telegram notifications, Docker support, and interactive Swagger documentation.
 
## Table of Contents
 
- [Features Implemented](#features-implemented)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running with Docker](#running-with-docker)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Telegram Notifications Setup](#telegram-notifications-setup)
- [Running Tests](#running-tests)
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
- Create endpoint with business logic:
  - Validates that the book has available inventory before creating a borrowing
  - Decreases book inventory by 1 on creation
  - Automatically attaches the current authenticated user (admins can create a borrowing on behalf of another user)
- Return endpoint (`POST /borrowings/<id>/return/`):
  - Sets the actual return date
  - Prevents returning the same borrowing twice
  - Increases book inventory by 1 on return
- Optimized queries with `select_related("book", "user")` to avoid N+1 queries
### 🔔 Telegram Notifications
- Helper function to send messages to a Telegram chat via the Bot API
- Automatic notification sent to Telegram whenever a new borrowing is created
### 📄 API Documentation
- Interactive Swagger UI and Redoc documentation via `drf-spectacular`
- Auto-generated OpenAPI 3 schema for all endpoints
### 🐳 Docker
- Containerized with Docker and Docker Compose for easy setup and deployment
---
 
## Tech Stack
 
- Python / Django
- Django REST Framework
- djangorestframework-simplejwt (JWT authentication)
- drf-spectacular (Swagger / OpenAPI documentation)
- python-dotenv (environment variable management)
- requests (Telegram Bot API integration)
- Docker / Docker Compose
- SQLite (default database)
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
 
### Option 2 — With Docker
 
See [Running with Docker](#running-with-docker) below.
 
---
 
## Running with Docker
 
### Prerequisites
 
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
### Steps
 
1. Create a `.env` file in the project root based on `.env.sample` (see [Environment Variables](#environment-variables)).
   ⚠️ If any value in `.env` contains a `$` character (e.g. inside `DJANGO_SECRET_KEY`), escape it as `$$`, otherwise Docker Compose will try to interpret it as a variable substitution.
2. Build and start the container:
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
 
5. Stop the container:
```bash
   docker-compose down
```
 
### Useful commands
 
```bash
docker-compose logs app          # view logs
docker-compose ps                # check container status
docker-compose exec app python manage.py test   # run tests inside the container
```
 
---
 
## Environment Variables
 
Create a `.env` file in the project root:
 
```
DJANGO_SECRET_KEY=your-django-secret-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
```
 
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
| GET | `/borrowings/` | Authenticated | List borrowings (own for regular users, all for admins) |
| POST | `/borrowings/` | Authenticated | Create a new borrowing |
| GET | `/borrowings/<id>/` | Authenticated (owner or admin) | Get borrowing details |
| POST | `/borrowings/<id>/return/` | Authenticated | Return a borrowed book |
 
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
 
The project sends a Telegram notification whenever a new borrowing is created.
 
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
```
 
### With Docker
 
```bash
docker-compose exec app python manage.py test
```
 
---