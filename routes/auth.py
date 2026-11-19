from flask import Blueprint, request, jsonify, g
import models
import validators
from routes import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON in request body"}), 400

    errors = validators.validate_registration(data)
    if errors:
        return jsonify({"errors": errors}), 400

    email = data["email"].strip().lower()
    existing = models.get_user_by_email(email)
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    try:
        user = models.create_user(
            email=email,
            password=data["password"],
            name=data.get("name", "")
        )
        return jsonify({"id": user["id"], "email": user["email"]}), 201
    except Exception:
        return jsonify({"error": "Failed to create user account"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON in request body"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    client_ip = request.remote_addr or "unknown"
    rate_limit_key = f"{client_ip}:{email.strip().lower()}"

    if models.is_login_rate_limited(rate_limit_key):
        return jsonify({"error": "Too many failed attempts. Account temporarily locked."}), 429

    user = models.get_user_by_email(email)
    # Timing safe: always evaluate password hash verification logic
    if not user or not models.verify_password(user["password_hash"], password):
        models.record_login_attempt(rate_limit_key)
        # CRITICAL: Identical 401 error message for non-existent email and bad password
        return jsonify({"error": "Invalid email or password"}), 401

    models.clear_login_attempts(rate_limit_key)
    token, expires_in = models.create_session(user["id"])
    return jsonify({"token": token, "expiresIn": expires_in}), 200

@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    models.delete_session(g.token)
    return "", 204

@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    return jsonify({
        "id": g.current_user["id"],
        "email": g.current_user["email"],
        "name": g.current_user["name"] or ""
    }), 200

@auth_bp.route("/change-password", methods=["POST"])
@token_required
def change_password():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON"}), 400

    old_pw = data.get("oldPassword")
    new_pw = data.get("newPassword")

    if not old_pw or not new_pw:
        return jsonify({"error": "Both oldPassword and newPassword are required"}), 400

    user = models.get_user_by_id(g.current_user["id"])
    if not user or not models.verify_password(user["password_hash"], old_pw):
        return jsonify({"error": "Current password is incorrect"}), 400

    err = validators.validate_password(new_pw)
    if err:
        return jsonify({"errors": {"newPassword": err}}), 400

    models.update_user_password(user["id"], new_pw)
    return jsonify({"message": "Password updated successfully"}), 200
