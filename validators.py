import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email(email) -> str | None:
    if not isinstance(email, str):
        return "Email must be a string"
    email_clean = email.strip()
    if not email_clean:
        return "Email is required"
    if len(email_clean) > 120:
        return "Email must be at most 120 characters"
    if not EMAIL_REGEX.match(email_clean):
        return "Email must be a valid email address (e.g. user@example.com)"
    return None

def validate_password(password) -> str | None:
    if not isinstance(password, str):
        return "Password must be a string"
    if len(password) < 8 or len(password) > 128:
        return "Password must be between 8 and 128 characters"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "Password must contain at least one letter and one digit"
    return None

def validate_name(name) -> str | None:
    if name is not None and not isinstance(name, str):
        return "Name must be a string"
    if isinstance(name, str) and len(name.strip()) > 80:
        return "Name must be at most 80 characters"
    return None

def validate_registration(data: dict) -> dict[str, str]:
    """Validates user registration input and returns all errors."""
    errors = {}
    if not isinstance(data, dict):
        return {"body": "Invalid JSON object"}

    email_err = validate_email(data.get("email"))
    if email_err:
        errors["email"] = email_err

    pw_err = validate_password(data.get("password"))
    if pw_err:
        errors["password"] = pw_err

    if "name" in data:
        name_err = validate_name(data.get("name"))
        if name_err:
            errors["name"] = name_err

    return errors

def validate_due_date(due_date) -> str | None:
    if due_date is None or due_date == "":
        return None
    if not isinstance(due_date, str):
        return "dueDate must be a string in YYYY-MM-DD format or null"
    try:
        dt = datetime.strptime(due_date, "%Y-%m-%d")
        # Format back to ensure strict YYYY-MM-DD without unexpected prefixes
        if dt.strftime("%Y-%m-%d") != due_date:
            return "dueDate must be a valid calendar date in YYYY-MM-DD format"
    except ValueError:
        return "dueDate must be a valid calendar date in YYYY-MM-DD format"
    return None

def validate_priority(priority) -> str | None:
    if not isinstance(priority, str):
        return "priority must be a string"
    if priority.lower() not in ("low", "medium", "high"):
        return "priority must be one of: low, medium, high"
    return None

def validate_title(title, required=True) -> str | None:
    if title is None:
        return "title is required" if required else None
    if not isinstance(title, str):
        return "title must be a string"
    trimmed = title.strip()
    if required and len(trimmed) == 0:
        return "title cannot be empty"
    if len(trimmed) < 1 or len(trimmed) > 120:
        return "title must be between 1 and 120 characters"
    return None

def validate_description(description) -> str | None:
    if description is None:
        return None
    if not isinstance(description, str):
        return "description must be a string"
    if len(description) > 1000:
        return "description must be at most 1000 characters"
    return None

def validate_task_create(data: dict) -> dict[str, str]:
    """Validates task creation request and returns all errors."""
    errors = {}
    if not isinstance(data, dict):
        return {"body": "Invalid JSON object"}

    title_err = validate_title(data.get("title"), required=True)
    if title_err:
        errors["title"] = title_err

    if "description" in data:
        desc_err = validate_description(data.get("description"))
        if desc_err:
            errors["description"] = desc_err

    if "dueDate" in data:
        date_err = validate_due_date(data.get("dueDate"))
        if date_err:
            errors["dueDate"] = date_err

    if "priority" in data:
        priority_err = validate_priority(data.get("priority"))
        if priority_err:
            errors["priority"] = priority_err

    return errors

def validate_task_patch(data: dict) -> tuple[dict, dict[str, str], str | None]:
    """
    Validates task patch request.
    Returns (cleaned_updates, errors_dict, global_error_message).
    """
    if not isinstance(data, dict):
        return {}, {}, "Invalid JSON object"

    allowed_fields = {"title", "description", "dueDate", "priority", "done"}
    editable_present = {k: v for k, v in data.items() if k in allowed_fields}

    if not editable_present:
        return {}, {}, "No valid editable fields provided"

    errors = {}
    cleaned = {}

    if "title" in editable_present:
        err = validate_title(editable_present["title"], required=True)
        if err:
            errors["title"] = err
        else:
            cleaned["title"] = editable_present["title"].strip()

    if "description" in editable_present:
        err = validate_description(editable_present["description"])
        if err:
            errors["description"] = err
        else:
            cleaned["description"] = (editable_present["description"] or "").strip()

    if "dueDate" in editable_present:
        val = editable_present["dueDate"]
        if val == "" or val is None:
            cleaned["dueDate"] = None
        else:
            err = validate_due_date(val)
            if err:
                errors["dueDate"] = err
            else:
                cleaned["dueDate"] = val

    if "priority" in editable_present:
        err = validate_priority(editable_present["priority"])
        if err:
            errors["priority"] = err
        else:
            cleaned["priority"] = editable_present["priority"].lower()

    if "done" in editable_present:
        val = editable_present["done"]
        if not isinstance(val, bool):
            errors["done"] = "done must be a boolean"
        else:
            cleaned["done"] = val

    return cleaned, errors, None

def validate_query_params(params: dict) -> tuple[dict, str | None]:
    """Validates query parameters for GET /api/tasks."""
    status = params.get("status", "all")
    if status not in ("all", "open", "done"):
        return {}, "status must be one of: all, open, done"

    priority = params.get("priority")
    if priority and priority.lower() not in ("low", "medium", "high"):
        return {}, "priority must be one of: low, medium, high"

    sort = params.get("sort", "createdAt")
    if sort not in ("createdAt", "dueDate", "priority"):
        return {}, "sort must be one of: createdAt, dueDate, priority"

    order = params.get("order", "desc")
    if order.lower() not in ("asc", "desc"):
        return {}, "order must be one of: asc, desc"

    q = params.get("q")
    if q is not None and not isinstance(q, str):
        return {}, "q must be a string"

    return {
        "status": status,
        "priority": priority.lower() if priority else None,
        "sort": sort,
        "order": order.lower(),
        "q": q.strip() if q else None
    }, None
