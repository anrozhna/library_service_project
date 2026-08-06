# Library Service Project
 
Django REST Framework API for managing a library's books, users, and borrowings, with Telegram notifications.
 
## Table of Contents
 
- [Features Implemented](#features-implemented)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
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
- List and detail endpoints
- Create endpoint with business logic:
  - Validates that the book has available inventory before creating a borrowing
  - Decreases book inventory by 1 on creation
  - Automatically attaches the current authenticated user (admins can create a borrowing on behalf of another user)
- Return endpoint (`POST /borrowings/<id>/return/`):
  - Sets the actual return date
  - Prevents returning the same borrowing twice
  - Increases book inventory by 1 on return
### 🔔 Telegram Notifications
- Helper function to send messages to a Telegram chat via the Bot API
- Automatic notification sent to Telegram whenever a new borrowing is created
---
 
## Tech Stack
 
- Python / Django
- Django REST Framework
- djangorestframework-simplejwt (JWT authentication)
- python-dotenv (environment variable management)
- requests (Telegram Bot API integration)
---
 
## Installation
 
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
| GET | `/borrowings/` | Authenticated | List all borrowings (no per-user restriction yet — see Roadmap) |
| POST | `/borrowings/` | Authenticated | Create a new borrowing |
| GET | `/borrowings/<id>/` | Authenticated (owner or admin) | Get borrowing details |
| POST | `/borrowings/<id>/return/` | Authenticated | Return a borrowed book |
 
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
 
```bash
python manage.py test
```
 
Run tests for a specific app:
```bash
python manage.py test books
python manage.py test users
python manage.py test borrowings
```
 
---
 
## Roadmap / Not Yet Implemented
 
- [ ] Borrowings filtering by `is_active` and `user_id`
- [ ] Daily overdue borrowings check with Telegram notifications
- [ ] Payments service (list/detail endpoints)
- [ ] Stripe payment session integration
- [ ] Payment success/cancel URLs
- [ ] FINE payments for overdue returns
- [ ] Docker Compose setup
 