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

    return app

app = create_app()

if __name__ == "__main__":
    print(f"Starting Task Tracker server on port {config.PORT}...")
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
