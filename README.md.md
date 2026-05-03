# ⚡ TaskFlow — Team Task Management App

A clean, full-featured team task management web application built with Django. Think simplified Trello/Asana — built for real teams, deployable in minutes.

---

## 🎯 Features

| Feature | Details |
|---|---|
| **Auth** | Signup, Login, Logout with session management |
| **Projects** | Create projects, add/remove members, role management |
| **Tasks** | Create tasks with title, description, priority, due date, assignment |
| **Kanban Board** | Visual To Do / In Progress / Done board per project |
| **Roles** | Admin (full control) vs Member (assigned tasks only) |
| **Dashboard** | Stats: total tasks, by status, overdue tasks, project count |
| **REST API** | Full JWT-authenticated API for all resources |

---

## 🏗️ Project Structure

```
taskflow/               ← Django project config
│  settings.py
│  urls.py
│  wsgi.py
core/                   ← Main app
│  models.py            ← Project, ProjectMember, Task
│  views.py             ← Template + API views
│  serializers.py       ← DRF serializers
│  urls.py              ← All URL routes
│  admin.py
│  context_processors.py
templates/
│  base.html            ← Sidebar layout
│  dashboard.html
│  auth/
│     login.html
│     signup.html
│  projects/
│     list.html, create.html, detail.html, confirm_delete.html
│  tasks/
│     create.html, detail.html, confirm_delete.html
static/
│  css/main.css         ← Full design system
requirements.txt
Procfile                ← Railway deployment
```

---

## ⚡ Quick Start (Local)

```bash
# 1. Clone and enter the project
git clone https://github.com/yourname/taskflow.git
cd taskflow

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and set SECRET_KEY

# 5. Run migrations
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Run the server
python manage.py runserver

# Visit: http://127.0.0.1:8000/
```

---

## 🔐 Role-Based Access

| Action | Admin | Member |
|---|---|---|
| Create project | ✅ | ❌ |
| Add/remove members | ✅ | ❌ |
| Create tasks | ✅ | ❌ |
| See all project tasks | ✅ | ❌ |
| See own assigned tasks | ✅ | ✅ |
| Update task status | ✅ | ✅ (own tasks) |
| Edit task details | ✅ | ❌ |
| Delete task/project | ✅ | ❌ |

---

## 🌐 REST API Reference

### Auth

```
POST /api/auth/register/          Register new user
POST /api/auth/token/             Get JWT token (login)
POST /api/auth/token/refresh/     Refresh JWT token
```

### Projects

```
GET    /api/projects/             List user's projects
POST   /api/projects/             Create project
GET    /api/projects/{id}/        Get project detail
PUT    /api/projects/{id}/        Update project
DELETE /api/projects/{id}/        Delete project
POST   /api/projects/{id}/members/add/              Add member
DELETE /api/projects/{id}/members/{user_id}/remove/ Remove member
```

### Tasks

```
GET    /api/projects/{id}/tasks/  List tasks in project
POST   /api/projects/{id}/tasks/  Create task
GET    /api/tasks/{id}/           Get task detail
PUT    /api/tasks/{id}/           Update task
DELETE /api/tasks/{id}/           Delete task
```

### Dashboard

```
GET    /api/dashboard/            Stats (task counts, overdue)
```

---

## 📮 Sample API Requests (Postman)

### 1. Register
```json
POST /api/auth/register/
{
  "username": "sanchit",
  "email": "sanchit@example.com",
  "password": "SecurePass@1",
  "password2": "SecurePass@1",
  "first_name": "Sanchit"
}
```

### 2. Login
```json
POST /api/auth/token/
{
  "username": "sanchit",
  "password": "SecurePass@1"
}
```
Response: `{ "access": "eyJ...", "refresh": "eyJ..." }`

### 3. Create Project
```json
POST /api/projects/
Authorization: Bearer <access_token>
{
  "name": "Website Redesign",
  "description": "Q3 redesign sprint"
}
```

### 4. Create Task
```json
POST /api/projects/1/tasks/
Authorization: Bearer <access_token>
{
  "title": "Design wireframes",
  "description": "Create low-fi wireframes for all pages",
  "priority": "high",
  "due_date": "2024-12-31",
  "assigned_to_id": 2
}
```

### 5. Update Task Status
```json
PATCH /api/tasks/1/
Authorization: Bearer <access_token>
{
  "status": "in_progress"
}
```

### 6. Dashboard Stats
```
GET /api/dashboard/
Authorization: Bearer <access_token>
```

---

## 🚂 Deploy to Railway

### One-time setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link your GitHub repo or deploy from CLI
railway up
```

### Environment Variables (set in Railway dashboard)

```
SECRET_KEY=your-very-long-random-secret-key
DEBUG=False
```

Railway auto-detects the `Procfile` and runs:
- `release`: `python manage.py migrate` (on each deploy)
- `web`: `gunicorn taskflow.wsgi --bind 0.0.0.0:$PORT`

### Generate a strong SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 📌 Database Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration status
python manage.py showmigrations
```

---

## 🐙 GitHub Push Steps

```bash
# 1. Initialize git repo (first time)
git init
git add .
git commit -m "Initial commit: TaskFlow app"

# 2. Create repo on GitHub then link it
git remote add origin https://github.com/yourname/taskflow.git
git branch -M main
git push -u origin main

# For subsequent updates
git add .
git commit -m "Your descriptive commit message"
git push
```

---

## 🛠️ Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Auth**: Django sessions (UI) + JWT via SimpleJWT (API)
- **Database**: SQLite (dev) — swap to PostgreSQL for production
- **Frontend**: Django Templates + custom CSS design system
- **Static Files**: WhiteNoise
- **Deployment**: Railway (Gunicorn + Procfile)

---

## 🔑 Default Admin Credentials

After running `createsuperuser`, access Django admin at `/admin/`.

---

## 📝 License

MIT — build freely.
