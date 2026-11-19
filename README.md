# TaskFlow — Personal Task Tracker with Secure Token Authentication

A robust, phone-first full-stack task tracker web application built for the **CN Club Recruitment (Track C — Problem C2)**.

---

## 1. Quick Start (Single Command)

### Prerequisites
* Python 3.10+ (Standard library + Flask)

### Installation & Run
```bash
# 1. (Optional) Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application (Single documented command)
python app.py
```

The application will start on **`http://localhost:3000`** (or the port specified by the `PORT` environment variable).
* **Web UI:** `http://localhost:3000/`
* **REST API:** `http://localhost:3000/api`

### (Optional) Load Sample Data
To quickly test and demo with realistic tasks and a pre-configured user:
```bash
python seed.py
```
* **Demo Email:** `demo@taskflow.dev`
* **Demo Password:** `Password123`

---

## 2. Architecture & Design Overview

TaskFlow follows a strictly **layered architecture** to ensure separation of concerns, testability, and clean code hygiene:

```
┌─────────────────────────────────────────────────────────────┐
│                       Browser Client                        │
│   (Semantic HTML5 + Handcrafted CSS3 + Vanilla ES2020+ JS)  │
│   • api.js (HTTP / Tokens)   • state.js (Reactive Store)    │
│   • app.js (XSS-Safe DOM)    • manifest.json (PWA)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON REST API (Bearer Token)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Flask Backend                        │
│   • app.py (App Factory, Port/Env Setup, Global Error Handlers)
│   • routes/auth.py (Registration, PBKDF2 Login, Sessions)   │
│   • routes/tasks.py (Tasks CRUD, Filters, Dynamic Sorting)  │
│   • routes/views.py (SPA View & PWA Assets)                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│        validators.py         │ │          models.py          │
│ • Comprehensive Multi-field  │ │ • PBKDF2 Password Hashing   │
│   validation & error mapping │ │ • Token & Session Store     │
│ • Safe type & range checks   │ │ • Query & Sort logic        │
└──────────────────────────────┘ └──────────────┬──────────────┘
                                                │
                                                ▼
                               ┌───────────────────────────────┐
                               │     database.py (SQLite)      │
                               │ • Auto-creates tables on start│
                               │ • Foreign keys enforced       │
                               │ • Zero external services/DB   │
                               └───────────────────────────────┘
```

### Module Responsibilities
* **`app.py`**: Flask application factory. Manages configuration from environment variables, registers blueprints, auto-initializes the database, and enforces standard JSON error handlers.
* **`database.py`**: Connection management and SQLite schema definitions. Runs `init_db()` automatically on app launch, creating `users`, `active_tokens`, `tasks`, and `login_attempts` tables if they don't already exist.
* **`models.py`**: Storage abstraction layer. Handles salted PBKDF2 password hashing (100,000 iterations), token generation and validation, brute-force rate-limiting, and SQL query generation for filtering and sorting.
* **`validators.py`**: Pure validation layer. Enforces strict input rules and compiles multi-field error maps (`{"errors": {"field": "reason"}}`) so clients receive all issues at once.
* **`routes/auth.py`**: Endpoints for user onboarding, authentication, session termination, and profile retrieval.
* **`routes/tasks.py`**: Endpoints for task creation, retrieval, partial updates, and deletion with strict user ownership isolation.
* **`static/`**: Vanilla frontend built phone-first without any third-party UI libraries (No React/Vue, No Bootstrap/Tailwind). All DOM nodes are rendered safely with `textContent` to ensure total immunity against XSS.

---

## 3. Database Schema

The database is a single self-contained file (`task_tracker.db` by default) managed via SQLite:

```sql
-- 1. Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT COLLATE NOCASE UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- 2. Active Sessions (Allows individual session invalidation on logout)
CREATE TABLE active_tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);

-- 3. Tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    due_date TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- 4. Login Attempt Log (For brute-force rate limiting bonus)
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL,
    attempt_time INTEGER NOT NULL
);
```

---

## 4. API Contract & Endpoints

### Authentication (`/api/auth`)
| Method | Path | Auth Required | Description | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | No | Register new user `{email, password, name?}` | `201`, `400`, `409` |
| `POST` | `/api/auth/login` | No | Login with `{email, password}` | `200`, `400`, `401`, `429` |
| `POST` | `/api/auth/logout` | Yes (`Bearer`) | Invalidate caller's session token | `204`, `401` |
| `GET` | `/api/auth/me` | Yes (`Bearer`) | Retrieve current user profile `{id, email, name}` | `200`, `401` |
| `POST` | `/api/auth/change-password` | Yes (`Bearer`) | Change account password | `200`, `400`, `401` |

### Tasks (`/api/tasks`)
*All task endpoints require `Authorization: Bearer <token>`.*

| Method | Path | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks` | List caller's tasks (supports `status`, `priority`, `q`, `sort`, `order`) | `200`, `400`, `401` |
| `POST` | `/api/tasks` | Create a task `{title, description?, dueDate?, priority?}` | `201`, `400`, `401` |
| `GET` | `/api/tasks/:id` | Get single task | `200`, `401`, `404` |
| `PATCH` | `/api/tasks/:id` | Partial update of task attributes | `200`, `400`, `401`, `404` |
| `DELETE` | `/api/tasks/:id` | Delete task | `204`, `401`, `404` |

### Error Response Shapes
1. **Validation Errors (`400 Bad Request`):**
   ```json
   {
     "errors": {
       "title": "title cannot be empty",
       "dueDate": "dueDate must be a valid calendar date in YYYY-MM-DD format"
     }
   }
   ```
2. **General Errors (`400`, `401`, `404`, `409`, `429`):**
   ```json
   {
     "error": "Descriptive message"
   }
   ```

---

## 5. Security Decisions & Token Storage Trade-offs

### Token Storage Strategy
* **Implementation:** The client stores the bearer authentication token in browser storage (`localStorage` by default for seamless return sessions, with automatic session fallback).
* **Security Analysis & Trade-off:**
  - *Storage Options considered:*
    1. **`localStorage` vs `sessionStorage`:** `localStorage` persists across tab closures and reloads, delivering superior UX for personal task tracking on mobile. However, any script running on the same origin could theoretically inspect storage if an XSS flaw existed.
    2. **XSS Mitigation:** To eliminate XSS vulnerabilities, TaskFlow **strictly forbids raw `innerHTML`**. All user inputs (titles, descriptions, email strings) are injected into the DOM exclusively using `.textContent` and safe DOM node creation methods.
    3. **Session Invalidation:** The server persists active tokens in SQLite. When `/api/auth/logout` is called, the specific session token is removed from `active_tokens` instantly. Other active sessions belonging to the same user remain unaffected.
  - *Identical 401 Responses:* To defend against account enumeration attacks, `POST /api/auth/login` emits the exact same 401 error message (`{"error": "Invalid email or password"}`) whether the email does not exist or the password is incorrect.
  - *Rate Limiting:* Failed login attempts trigger automatic rate-limiting (`429 Too Many Requests`) after 5 failed tries within 5 minutes.

---

## 6. Running Automated Tests

All tests are implemented using the Python standard library `unittest` framework:

```bash
python -m unittest discover tests
```

### Test Coverage Highlights
* **Authentication:** Registration success, multi-field error reporting, duplicate email collisions, identical 401 login responses, multi-session independence, logout token invalidation.
* **Task CRUD:** Creation validations, patch updates, safe deletion.
* **Data Isolation:** User B cannot read, patch, or delete User A's tasks (returns `404 Not Found` to prevent revealing resource existence).
* **Filters & Complex Sorting:** Verified filtering by `status`, `priority`, substring `q`, and custom sorting (null due dates sorted last when ascending; high > medium > low priority sorting).

---

## 7. Assumptions & Edge Cases Handled

1. **Sorting with Null Due Dates:** When sorting by `dueDate` ascending, tasks without a due date (`null`) appear at the very end of the list.
2. **Case Insensitivity:** Emails are normalized to lower case; search queries match case-insensitively across both title and description.
3. **Empty Data State:** A fresh checkout starts with no database file. On first start, SQLite auto-generates tables cleanly without requiring manual migrations.
4. **Touch Accessibility:** Every button, tab, and form control satisfies the 44px minimum touch target guideline for mobile usability.
