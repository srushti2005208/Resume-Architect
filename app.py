from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from src.db import init_db
from src.auth import auth_bp
from src.resume import resumes_bp
from src.templates import templates_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["ENV"] = os.getenv("FLASK_ENV", "development")

    # CORS — allow only your frontend origin
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(app, supports_credentials=True, resources={
        r"/api/*": {"origins": [frontend_origin]}
    })

    # DB
    init_db(app)

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(resumes_bp, url_prefix="/api/resumes")
    app.register_blueprint(templates_bp, url_prefix="/api/templates")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
