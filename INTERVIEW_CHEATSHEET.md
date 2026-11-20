# Interview & Live Code Change Cheatsheet

This cheatsheet is written for Python Flask and SQL developers. It explains exactly how every part of the project works and gives step-by-step instructions for live code changes during your recruitment interview.

---

## 1. Project Map (Where Everything Lives)

| What you want to do | Which file to open | What's inside |
| :--- | :--- | :--- |
| **Database Tables & Schema** | `database.py` | Standard SQL `CREATE TABLE` statements (just like MySQL). |
| **SQL Queries & Database Logic** | `models.py` | `INSERT`, `SELECT`, `UPDATE`, `DELETE` queries with parameters `?`. |
| **Input Validation Rules** | `validators.py` | Functions checking length, email regex, date formats. |
| **Flask API Routes** | `routes/tasks.py` and `routes/auth.py` | `@tasks_bp.route("/<id>", methods=["PATCH"])` etc. |
| **Web UI Structure** | `templates/index.html` | Plain HTML form inputs, buttons, and task cards. |
| **Frontend Logic (JavaScript)** | `static/js/app.js` | One single simple file (~250 lines) with plain functions. |

---

## 2. Typical Live Code Change Scenarios (Step-by-Step)

### Scenario 1: The Interviewer says:
> *"Add a `category` (or `notes`) field to tasks so users can categorize tasks like 'Work', 'Study', 'Personal'."*

Here is how you do it in 4 quick steps:

#### Step 1: Database (`database.py`)
In `database.py`, find `CREATE TABLE IF NOT EXISTS tasks (` around line 55. Add the column:
```sql
category TEXT DEFAULT 'General',
```
*(In SQLite / MySQL syntax, this adds a text column with a default value).*

#### Step 2: Database Models (`models.py`)
In `models.py`:
1. Find `serialize_task(row)` (around line 140) and add:
   ```python
   "category": row["category"] or "General",
   ```
2. Find `create_task(...)` (around line 150), add `category: str = "General"`, and include it in the `INSERT INTO tasks (..., category) VALUES (..., ?)`.
3. Find `update_task(...)` (around line 225) and add:
   ```python
   if "category" in updates:
       fields.append("category = ?")
       values.append(updates["category"].strip())
   ```

#### Step 3: Flask Route / Validator (`validators.py`)
In `validators.py`, in `validate_task_patch`:
Add `"category"` to `allowed_fields`:
```python
allowed_fields = {"title", "description", "dueDate", "priority", "done", "category"}
```

#### Step 4: HTML & JS (`templates/index.html` & `static/js/app.js`)
1. In `templates/index.html`, inside the task modal form, add:
   ```html
   <div class="form-group">
     <label for="task-category">Category</label>
     <input type="text" id="task-category" class="form-input" placeholder="Work, Personal, etc.">
   </div>
   ```
2. In `static/js/app.js`:
   - In `handleSaveTask`:
     ```javascript
     const category = document.getElementById("task-category").value.trim();
     const payload = { title, description, dueDate, priority, category };
     ```
   - In `renderTaskList`:
     Inside the card HTML template, add a category badge:
     ```html
     <span class="badge">${task.category}</span>
     ```

---

### Scenario 2: The Interviewer says:
> *"Change the password requirement so that passwords must be at least 10 characters instead of 8."*

1. Open **`validators.py`**.
2. Find `validate_password(password)`:
   ```python
   # Change 8 to 10:
   if len(password) < 10 or len(password) > 128:
       return "Password must be between 10 and 128 characters"
   ```
3. Done! Test it by trying to register with a 9-character password.

---

### Scenario 3: The Interviewer says:
> *"Change task sorting so tasks default to sorting by Priority instead of Creation Date."*

1. Open **`models.py`** or **`routes/tasks.py`**.
2. In `models.py`, find `get_tasks(...)` (around line 160):
   Change default argument from `sort: str = "createdAt"` to `sort: str = "priority"`.
3. In `templates/index.html`, change the default `<option selected>` in the sort dropdown.

---

### Scenario 4: The Interviewer asks:
> *"How does the token login work without external libraries like PyJWT?"*

**Your Answer:**
1. When the user logs in (`POST /api/auth/login`), the server verifies the password using salted PBKDF2 (`hashlib.pbkdf2_hmac` with 100,000 iterations).
2. It generates a cryptographically secure random token using Python's standard library `secrets.token_urlsafe(32)`.
3. It stores this token in the `active_tokens` SQLite table with an expiration timestamp (`expires_at = now + 86400`).
4. The client saves this token in `localStorage` and passes it in the HTTP header:
   `Authorization: Bearer <token>`.
5. When the user clicks **Logout**, the server removes that specific token from the `active_tokens` table. Any other sessions belonging to that user remain valid.

---

## 3. How to Run & Test During the Interview

1. **Start the server:**
   ```bash
   python app.py
   ```
   Opens on `http://127.0.0.1:3000`.

2. **Run the automated unit tests:**
   ```bash
   python -m unittest discover tests
   ```
   Runs 12 comprehensive tests in ~3 seconds.
