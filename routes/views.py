from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import models
import validators

views_bp = Blueprint("views", __name__)

def get_logged_in_user():
    """Helper to get currently logged in user from session, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return models.get_user_by_id(user_id)

@views_bp.route("/")
def index():
    """Home route: redirect to /tasks if logged in, else /login."""
    if session.get("user_id"):
        return redirect(url_for("views.tasks_view"))
    return redirect(url_for("views.login_view"))

@views_bp.route("/login", methods=["GET", "POST"])
def login_view():
    """Display login page or process login form."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html", email=email, active_tab="login")

        user = models.get_user_by_email(email)
        if not user or not models.verify_password(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html", email=email, active_tab="login")

        # Save user id into Flask session (pure server-side session)
        session["user_id"] = user["id"]
        return redirect(url_for("views.tasks_view"))

    return render_template("login.html", active_tab="login")

@views_bp.route("/register", methods=["GET", "POST"])
def register_view():
    """Display register page or process registration form."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = validators.validate_registration({"name": name, "email": email, "password": password})
        if errors:
            flash(" ".join(errors.values()), "error")
            return render_template("login.html", name=name, email=email, active_tab="register")

        if models.get_user_by_email(email):
            flash("Email already registered.", "error")
            return render_template("login.html", name=name, email=email, active_tab="register")

        user = models.create_user(email=email, password=password, name=name)
        session["user_id"] = user["id"]
        return redirect(url_for("views.tasks_view"))

    return render_template("login.html", active_tab="register")

@views_bp.route("/logout")
def logout_view():
    """Clear session and redirect to login."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("views.login_view"))

@views_bp.route("/tasks")
def tasks_view():
    """Display task workspace with search, filters, and sorting."""
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("views.login_view"))

    # Read filter query parameters
    status = request.args.get("status", "all")
    priority = request.args.get("priority", "")
    sort = request.args.get("sort", "createdAt")
    order = request.args.get("order", "desc")
    q = request.args.get("q", "").strip()

    # Query tasks from SQLite database
    tasks = models.get_tasks(
        user_id=user["id"],
        status=status,
        priority=priority if priority else None,
        q=q if q else None,
        sort=sort,
        order=order
    )

    # Compute task summary stats
    all_user_tasks = models.get_tasks(user_id=user["id"], status="all")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    total_count = len(all_user_tasks)
    completed_count = sum(1 for t in all_user_tasks if t["done"])
    open_count = total_count - completed_count
    overdue_count = sum(1 for t in all_user_tasks if t["dueDate"] and t["dueDate"] < today_str and not t["done"])

    return render_template(
        "tasks.html",
        user=user,
        tasks=tasks,
        today_str=today_str,
        status=status,
        priority=priority,
        sort=sort,
        order=order,
        q=q,
        total_count=total_count,
        open_count=open_count,
        completed_count=completed_count,
        overdue_count=overdue_count
    )

@views_bp.route("/tasks/new", methods=["POST"])
def add_task_view():
    """Create a new task from submitted form."""
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("views.login_view"))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("dueDate", "").strip() or None
    priority = request.form.get("priority", "medium")

    if not title:
        flash("Task title is required.", "error")
        return redirect(url_for("views.tasks_view"))

    models.create_task(
        user_id=user["id"],
        title=title,
        description=description,
        due_date=due_date,
        priority=priority
    )
    flash("Task created successfully!", "success")
    return redirect(url_for("views.tasks_view"))

@views_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task_view(task_id):
    """Toggle a task between done and open."""
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("views.login_view"))

    task = models.get_task(user["id"], task_id)
    if task:
        models.update_task(user["id"], task_id, {"done": not task["done"]})

    return redirect(url_for("views.tasks_view"))

@views_bp.route("/tasks/<int:task_id>/edit", methods=["POST"])
def edit_task_view(task_id):
    """Update a task's title, description, due date, and priority."""
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("views.login_view"))

    updates = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "dueDate": request.form.get("dueDate", "").strip() or None,
        "priority": request.form.get("priority", "medium")
    }
    models.update_task(user["id"], task_id, updates)
    flash("Task updated!", "success")
    return redirect(url_for("views.tasks_view"))

@views_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task_view(task_id):
    """Delete a task."""
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("views.login_view"))

    models.delete_task(user["id"], task_id)
    flash("Task deleted.", "info")
    return redirect(url_for("views.tasks_view"))
