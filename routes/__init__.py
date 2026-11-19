from functools import wraps
from flask import request, jsonify, g
import models

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication token required"}), 401

        token = auth_header[len("Bearer "):].strip()
        user = models.get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired session token"}), 401

        g.current_user = user
        g.token = token
        return f(*args, **kwargs)
    return decorated
