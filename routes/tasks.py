from flask import Blueprint, request, jsonify, g
import models
import validators
from routes import token_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")

@tasks_bp.route("", methods=["GET"])
@token_required
def list_tasks():
    cleaned_params, err = validators.validate_query_params(request.args)
    if err:
        return jsonify({"error": err}), 400

    tasks = models.get_tasks(
        user_id=g.current_user["id"],
        status=cleaned_params["status"],
        priority=cleaned_params["priority"],
        q=cleaned_params["q"],
        sort=cleaned_params["sort"],
        order=cleaned_params["order"]
    )
    return jsonify(tasks), 200

@tasks_bp.route("", methods=["POST"])
@token_required
def create_task():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON in request body"}), 400

    errors = validators.validate_task_create(data)
    if errors:
        return jsonify({"errors": errors}), 400

    task = models.create_task(
        user_id=g.current_user["id"],
        title=data["title"],
        description=data.get("description", ""),
        due_date=data.get("dueDate"),
        priority=data.get("priority", "medium")
    )
    return jsonify(task), 201

@tasks_bp.route("/<int:task_id>", methods=["GET"])
@token_required
def get_task(task_id: int):
    task = models.get_task(g.current_user["id"], task_id)
    if not task:
        # Crucial security rule: return 404 (not 403) so task existence is not revealed
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200

@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
@token_required
def patch_task(task_id: int):
    # Check if task exists and belongs to current user
    existing = models.get_task(g.current_user["id"], task_id)
    if not existing:
        return jsonify({"error": "Task not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed JSON in request body"}), 400

    cleaned_updates, errors, global_err = validators.validate_task_patch(data)
    if global_err:
        return jsonify({"error": global_err}), 400
    if errors:
        return jsonify({"errors": errors}), 400

    updated = models.update_task(g.current_user["id"], task_id, cleaned_updates)
    if not updated:
        return jsonify({"error": "Failed to update task"}), 400

    return jsonify(updated), 200

@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id: int):
    deleted = models.delete_task(g.current_user["id"], task_id)
    if not deleted:
        return jsonify({"error": "Task not found"}), 404
    return "", 204
