from flask import Blueprint, jsonify

templates_bp = Blueprint("templates", __name__)

@templates_bp.route("/", methods=["GET"])
def get_templates():
    templates = [
        {"key": "modern", "name": "Modern Template"},
        {"key": "classic", "name": "Classic Template"},
        {"key": "minimal", "name": "Minimal Template"},
        {"key": "creative", "name": "Creative Template"},
    ]
    return jsonify(templates)