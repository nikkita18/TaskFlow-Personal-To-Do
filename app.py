import os
from flask import Flask, jsonify
import config
import database
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.views import views_bp

def create_app(test_config=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        DATABASE=config.DATABASE_PATH
    )

    if test_config:
        app.config.update(test_config)

    # Auto-initialize database on startup
    with app.app_context():
        database.init_db(app.config.get("DATABASE"))
        # On Vercel serverless functions, auto-seed demo user so live link can be tested immediately
        if os.environ.get("VERCEL"):
            try:
                import models
                if not models.get_user_by_email("demo@taskflow.dev"):
                    u = models.create_user("demo@taskflow.dev", "Password123", "Demo Candidate")
                    from datetime import datetime, timezone, timedelta
                    now = datetime.now(timezone.utc)
                    yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
                    today = now.strftime("%Y-%m-%d")
                    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                    next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")
                    sample_tasks = [
                        ("Prepare slides for CN recruitment", "Walk through architecture and SQLite design", today, "high"),
                        ("Submit assignment report", "Review edge cases and test coverage", yesterday, "high"),
                        ("Refactor API auth middleware", "Ensure constant-time verification", yesterday, "medium"),
                        ("Design phone-first responsive layouts", "CSS media queries down to 360px viewport", today, "high"),
                        ("Write unit tests for task sorting", "Verify null due dates sort to the bottom", tomorrow, "medium"),
                        ("Clean up Git commit history", "Ensure small atomic commits over 24-hour cycle", next_week, "low"),
                    ]
                    for title, desc, due, prio in sample_tasks:
                        models.create_task(u["id"], title, desc, due, prio)
            except Exception:
                pass

    # Register DB connection teardown
    app.teardown_appcontext(database.close_db)

    # Register route blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.after_request
    def add_cache_headers(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app

app = create_app()

if __name__ == "__main__":
    print(f"Starting Task Tracker server on port {config.PORT}...")
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
