# Problem C2: Personal To-Do / Task Tracker with Login
## Comprehensive Specification & Implementation Plan

---

## 1. Project Overview & Rules Compliance

### A. Core Stack
* **Backend:** Python (Flask)
* **Database:** SQLite (file-based `task_tracker.db`, auto-initialized on first run with zero external services/Docker required)
* **Frontend:** Plain semantic HTML5, modern CSS3 (custom responsive styling, CSS variables, dark/light themes), and vanilla JavaScript (ES2020+). **Strictly NO React/Vue/jQuery/Bootstrap/Tailwind**.
* **Test Suite:** Standard library `unittest` (`python -m unittest discover tests`)
* **Port & Entry Point:** Starts with `python app.py`, listens on `PORT` environment variable (default: `3000`). Serves the UI at `/` and the REST API at `/api`.

---

## 2. Database Schema (SQLite)

### Table 1: `users`
* `id`: INTEGER PRIMARY KEY AUTOINCREMENT
* `email`: TEXT UNIQUE NOT NULL (stored in lowercase, max 120 chars)
* `password_hash`: TEXT NOT NULL (salted PBKDF2-HMAC-SHA256 with >= 100,000 iterations or `bcrypt`/`werkzeug.security`)
* `name`: TEXT (optional, max 80 chars)
* `created_at`: TEXT NOT NULL (ISO-8601 UTC timestamp)

### Table 2: `active_tokens` (For Session Invalidation on Logout)
* `token`: TEXT PRIMARY KEY
* `user_id`: INTEGER NOT NULL REFERENCES `users(id)` ON DELETE CASCADE
* `expires_at`: INTEGER NOT NULL (UNIX epoch timestamp, max 24 hours)

### Table 3: `tasks`
* `id`: INTEGER PRIMARY KEY AUTOINCREMENT
* `user_id`: INTEGER NOT NULL REFERENCES `users(id)` ON DELETE CASCADE
* `title`: TEXT NOT NULL (1–120 characters after trimming)
* `description`: TEXT DEFAULT '' (max 1000 characters)
* `due_date`: TEXT (nullable, format `YYYY-MM-DD`)
* `priority`: TEXT NOT NULL DEFAULT 'medium' (CHECK: `priority IN ('low', 'medium', 'high')`)
* `done`: INTEGER NOT NULL DEFAULT 0 (0 for false, 1 for true)
* `created_at`: TEXT NOT NULL (ISO-8601 UTC timestamp)

---

## 3. REST API Contract & Validation Rules

### Error Response Shapes
* **Validation Failure (400):**
  ```json
  {
    "errors": {
      "field_name": "Error description for this specific field"
    }
  }
  ```
  *(Must list EVERY bad field, not just the first one).*
* **General Errors (400, 401, 404, 409):**
  ```json
  {
    "error": "Descriptive message"
  }
  ```

---

### A. Authentication Endpoints

#### 1. `POST /api/auth/register`
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "Password123",
    "name": "Jane Doe"
  }
  ```
* **Validation:**
  - `email`: Required, valid email format (`x@y.z`), max 120 chars, normalized to lower case. Unique.
  - `password`: Required, 8–128 characters, must contain at least 1 letter and 1 digit.
  - `name`: Optional, max 80 characters.
* **Responses:**
  - `201 Created`: `{"id": 1, "email": "user@example.com"}` *(Never return password or hash)*.
  - `400 Bad Request`: `{"errors": {...}}`
  - `409 Conflict`: `{"error": "Email already exists"}`

#### 2. `POST /api/auth/login`
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "Password123"
  }
  ```
* **Validation & Security:**
  - Missing email or password returns `400 Bad Request`.
  - Unknown email or wrong password returns `401 Unauthorized` with the **EXACT SAME** message (e.g. `{"error": "Invalid email or password"}`) to prevent email enumeration.
* **Responses:**
  - `200 OK`: `{"token": "<secure_random_or_jwt_token>", "expiresIn": 86400}`
  - `400 / 401`: Error JSON

#### 3. `POST /api/auth/logout`
* **Headers:** `Authorization: Bearer <token>`
* **Behavior:** Invalidates the provided session token immediately. Does NOT log out the user's other sessions.
* **Responses:**
  - `204 No Content`
  - `401 Unauthorized`: Token missing, invalid, or expired.

#### 4. `GET /api/auth/me`
* **Headers:** `Authorization: Bearer <token>`
* **Responses:**
  - `200 OK`: `{"id": 1, "email": "user@example.com", "name": "Jane Doe"}`
  - `401 Unauthorized`

---

### B. Task Endpoints (All require `Authorization: Bearer <token>`)

#### 1. `GET /api/tasks`
* **Query Parameters:**
  - `status`: `all` (default) | `open` | `done`
  - `priority`: `low` | `medium` | `high` (optional filter)
  - `q`: case-insensitive substring search in `title` or `description`
  - `sort`: `createdAt` (default) | `dueDate` | `priority`
  - `order`: `desc` (default) | `asc`
* **Sorting Rules:**
  - Priority ordering: `low` < `medium` < `high`.
  - When sorting by `dueDate` ascending, tasks without a `dueDate` (`null`) must come **last**.
  - Secondary tie-break: `id` asc/desc for stable pagination and ordering.
* **Responses:**
  - `200 OK`: `[ { "id": 1, "title": "...", "description": "...", "dueDate": "...", "priority": "...", "done": false, "createdAt": "..." }, ... ]`
  - `400 Bad Request`: Invalid filter/sort query value.

#### 2. `POST /api/tasks`
* **Request Body:**
  ```json
  {
    "title": "Complete CN project",
    "description": "Write clean code and tests",
    "dueDate": "2026-11-25",
    "priority": "high"
  }
  ```
* **Validation:**
  - `title`: Required, trimmed 1–120 characters.
  - `description`: Optional (default `""`), max 1000 characters.
  - `dueDate`: Optional (default `null`), valid calendar date `YYYY-MM-DD` (past dates allowed).
  - `priority`: Optional, must be `low`, `medium`, or `high` (default `medium`).
* **Responses:**
  - `201 Created`: Complete created task object.
  - `400 Bad Request`: `{"errors": {...}}`

#### 3. `GET /api/tasks/:id`
* **Security/Ownership:** If task does not exist OR belongs to another user, return `404 Not Found` (never `403`, to avoid leaking task IDs).
* **Responses:**
  - `200 OK`: Task object.
  - `404 Not Found`: `{"error": "Task not found"}`

#### 4. `PATCH /api/tasks/:id`
* **Request Body:** Any subset of `{"title", "description", "dueDate", "priority", "done"}`.
* **Rules:**
  - Ignore unknown or read-only fields (`id`, `createdAt`).
  - If no valid editable field is provided, return `400 Bad Request`.
  - If validation fails on any provided field, return `400 {"errors": {...}}`.
  - If task doesn't exist or belongs to another user, return `404`.
* **Responses:**
  - `200 OK`: Updated task object.
  - `400 Bad Request`
  - `404 Not Found`

#### 5. `DELETE /api/tasks/:id`
* **Responses:**
  - `204 No Content`
  - `404 Not Found`

---

## 4. UI/UX Design & Architecture

### Phone-First Principles (360px to 1280px)
* **Touch Targets:** Minimum 44px × 44px for buttons, inputs, checkboxes.
* **Semantic Elements:** `<main>`, `<nav>`, `<header>`, `<section>`, `<label>`, `<button>`, etc.
* **XSS Prevention:** All user-provided strings rendered strictly via `.textContent` or safe DOM node creation. Never raw `innerHTML`.

### UI Screens & State Flow
1. **Auth View (Register / Login Modal or Card):**
   - Toggle between "Sign In" and "Create Account".
   - Input validations with inline error messages (e.g., password criteria, duplicate email alert).
   - "Remember Me" / session persistence explanation.
2. **Dashboard / Task View (Logged In):**
   - Top Header: User avatar/name, theme toggle (Dark/Light), Logout button.
   - Quick Add Bar / FAB: Floating action button for phone view; inline fast entry on desktop.
   - Filter & Search Bar:
     - Search input (debounced).
     - Filter tabs/pills: All, Active (Open), Completed (Done).
     - Priority filter dropdown.
     - Sort dropdown (`Created (Newest)`, `Due Date`, `Priority`).
   - Task List:
     - Task item card with custom checkbox (`done` toggle).
     - Priority badge (Color coded: Red = High, Amber = Medium, Gray/Blue = Low).
     - Due date badge with **Overdue Alert** (bold red highlight if `dueDate < today` and not done).
     - Edit & Delete buttons with delete confirmation.
   - Empty, Loading, and Network Error states.

---

## 5. Testing & Verification Strategy

1. **Automated Backend Tests (`tests/test_api.py`):**
   - User registration (valid, invalid password, duplicate email).
   - User login (successful, wrong password, unknown email with identical 401 error).
   - Session logout & token invalidation.
   - Task CRUD operations.
   - Strict cross-user isolation (User A cannot read, edit, or delete User B's task -> 404).
   - Task filters (status, priority, search `q`, sorting with null due dates last).
   - Error format validations (multiple field errors in 400 response).
2. **Manual & Browser Testing:**
   - Responsive check at 360px mobile width.
   - Token expiry and 401 redirect behavior.
   - Accessibility audit (tab navigation, labels, contrast).

---

## 6. Bonus Features Checklist
* [x] Brute-force rate limiting on failed login attempts (`429 Too Many Requests`).
* [x] Change password endpoint (`POST /api/auth/change-password`).
* [x] Task tags / categories support.
* [x] Light / Dark theme toggle.
* [x] Web App Manifest (`manifest.json`) for installable PWA.
