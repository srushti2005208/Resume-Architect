from flask import Blueprint, request, jsonify, current_app, send_file
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from src.db import db
import jwt
import datetime
import secrets
import os

auth_bp = Blueprint("auth", __name__)

# Password reset token storage (in production, use a DB or Redis)
reset_tokens = {}

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    if not email or not password or not name:
        return jsonify({"error": "Missing fields"}), 400
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 409
    hashed = generate_password_hash(password)
    db.users.insert_one({"email": email, "password": hashed, "name": name})
    return jsonify({"message": "Signup successful"}), 201

# Password reset request
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")
    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "Email not found"}), 404
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "email": email,
        "expires": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    # Send email (requires Flask-Mail config)
    mail = current_app.extensions.get('mail')
    if mail:
        msg = Message(
            subject="Password Reset Request",
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=[email],
            body=f"Click the link to reset your password: {request.url_root}reset-password?token={token}"
        )
        mail.send(msg)
    return jsonify({"success": True, "message": "Password reset email sent"})

# Verify reset token
@auth_bp.route("/verify-reset-token", methods=["POST"])
def verify_reset_token():
    data = request.json
    token = data.get("token")
    info = reset_tokens.get(token)
    if not info or info["expires"] < datetime.datetime.utcnow():
        return jsonify({"success": False, "message": "Invalid or expired token"}), 400
    return jsonify({"success": True, "message": "Token is valid"})

# Serve reset password page
@auth_bp.route("/reset-password", methods=["GET"])
def serve_reset_page():
    # Serve the reset_password.html file from the frontend directory
    return send_file(os.path.join('..', 'FRONTEND', 'reset_password.html'))

# Password reset
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    token = data.get("token")
    new_password = data.get("new_password")
    info = reset_tokens.get(token)
    if not info or info["expires"] < datetime.datetime.utcnow():
        return jsonify({"success": False, "message": "Invalid or expired token"}), 400
    email = info["email"]
    hashed = generate_password_hash(new_password)
    db.users.update_one({"email": email}, {"$set": {"password": hashed}})
    del reset_tokens[token]
    return jsonify({"success": True, "message": "Password has been reset"})

# Update last_login on successful login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    user = db.users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    # Send welcome email only for new users (first login)
    if not user.get("last_login"):
        mail = current_app.extensions.get('mail')
        if mail:
            msg = Message(
                subject="Welcome to Resume Architect",
                sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
                recipients=[email],
                body=f"{user['name']}, welcome to the Resume Architect website!"
            )
            try:
                mail.send(msg)
            except Exception as e:
                # Log the error but don't fail the login
                print(f"Failed to send welcome email: {e}")

    # Update last_login timestamp
    db.users.update_one({"email": email}, {"$set": {"last_login": datetime.datetime.utcnow()}})
    token = jwt.encode({
        "user_id": str(user["_id"]),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": token, "name": user["name"]})

# Admin endpoint to get user login info
@auth_bp.route("/admin/users", methods=["GET"])
def admin_get_users():
    users = list(db.users.find({}, {"name": 1, "email": 1, "last_login": 1}))
    for u in users:
        u["_id"] = str(u["_id"])
        if "last_login" in u and u["last_login"]:
            u["last_login"] = u["last_login"].strftime("%Y-%m-%d %H:%M")
        else:
            u["last_login"] = "Never"
    return jsonify(users)