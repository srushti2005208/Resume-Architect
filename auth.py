import os, re, datetime
from flask import Blueprint, request, jsonify, current_app, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from .db import db
from .utils import make_jwt, decode_jwt, now_epoch, cookie_args

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _get_user_from_token():
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        data = decode_jwt(token, current_app.config["SECRET_KEY"])
        uid = data.get("sub")
        if not uid:
            return None
        user = db.users.find_one({"_id": ObjectId(uid)}, {"password": 0})
        return user
    except Exception:
        return None

@auth_bp.post("/signup")
def signup():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "invalid email"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 chars"}), 400

    hashed = generate_password_hash(password)
    user_doc = {
        "name": name,
        "email": email,
        "password": hashed,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    try:
        result = db.users.insert_one(user_doc)
    except DuplicateKeyError:
        return jsonify({"error": "email already registered"}), 409

    uid = str(result.inserted_id)
    token = make_jwt({"sub": uid, "iat": now_epoch()}, current_app.config["SECRET_KEY"])
    resp = make_response(jsonify({"_id": uid, "name": name, "email": email}))
    resp.set_cookie("access_token", token, **cookie_args(current_app.config["ENV"]))
    return resp, 201

@auth_bp.post("/login")
def login():
    body = request.get_json(force=True, silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    user = db.users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "invalid email or password"}), 401

    uid = str(user["_id"])
    token = make_jwt({"sub": uid, "iat": now_epoch()}, current_app.config["SECRET_KEY"])
    resp = make_response(jsonify({"_id": uid, "name": user["name"], "email": user["email"]}))
    resp.set_cookie("access_token", token, **cookie_args(current_app.config["ENV"]))
    return resp

@auth_bp.post("/logout")
def logout():
    resp = make_response(jsonify({"ok": True}))
    # Clear cookie
    resp.set_cookie("access_token", "", max_age=0, path="/")
    return resp

@auth_bp.get("/me")
def me():
    user = _get_user_from_token()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    user["_id"] = str(user["_id"])
    return jsonify(user)
