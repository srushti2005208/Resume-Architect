from flask import Blueprint, jsonify

templates_bp = Blueprint("templates", __name__)

# Replace with DB-based templates if needed. `key` should match what your frontend expects.
BUILTIN_TEMPLATES = [
    {
        "key": "classic",
        "name": "Classic",
        "preview_url": "/static/previews/classic.png",
        "sections": ["header", "summary", "experience", "education", "skills", "projects"]
    },
    {
        "key": "modern",
        "name": "Modern",
        "preview_url": "/static/previews/modern.png",
        "sections": ["header", "summary", "experience", "education", "skills", "projects"]
    }
]

@templates_bp.get("")
def list_templates():
    return jsonify(BUILTIN_TEMPLATES)
