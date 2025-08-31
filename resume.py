import datetime
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from .db import db, to_object_id
from .auth import _get_user_from_token

resumes_bp = Blueprint("resumes", __name__)

def _require_user():
    user = _get_user_from_token()
    if not user:
        return None, (jsonify({"error": "unauthorized"}), 401)
    return user, None

@resumes_bp.post("")
def create_resume():
    user, err = _require_user()
    if err: return err
    body = request.get_json(force=True, silent=True) or {}
    title = (body.get("title") or "Untitled").strip()
    template_key = (body.get("template_key") or "classic").strip()
    sections = body.get("sections") or {}

    doc = {
        "user_id": user["_id"],
        "title": title,
        "template_key": template_key,
        "sections": sections,  # arbitrary JSON your frontend sends
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    result = db.resumes.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["user_id"] = str(doc["user_id"])
    return jsonify(doc), 201

@resumes_bp.get("")
def list_resumes():
    user, err = _require_user()
    if err: return err
    items = []
    for r in db.resumes.find({"user_id": user["_id"]}).sort("updated_at", -1):
        r["_id"] = str(r["_id"]); r["user_id"] = str(r["user_id"])
        items.append(r)
    return jsonify(items)

@resumes_bp.get("/<resume_id>")
def get_resume(resume_id):
    user, err = _require_user()
    if err: return err
    r = db.resumes.find_one({"_id": ObjectId(resume_id), "user_id": user["_id"]})
    if not r: return jsonify({"error": "not found"}), 404
    r["_id"] = str(r["_id"]); r["user_id"] = str(r["user_id"])
    return jsonify(r)

@resumes_bp.put("/<resume_id>")
def update_resume(resume_id):
    user, err = _require_user()
    if err: return err
    body = request.get_json(force=True, silent=True) or {}
    updates = {
        "updated_at": datetime.datetime.utcnow()
    }
    for key in ["title", "template_key", "sections"]:
        if key in body:
            updates[key] = body[key]
    result = db.resumes.find_one_and_update(
        {"_id": ObjectId(resume_id), "user_id": user["_id"]},
        {"$set": updates},
        return_document=True
    )
    if not result: return jsonify({"error": "not found"}), 404
    result["_id"] = str(result["_id"]); result["user_id"] = str(result["user_id"])
    return jsonify(result)

@resumes_bp.delete("/<resume_id>")
def delete_resume(resume_id):
    user, err = _require_user()
    if err: return err
    res = db.resumes.delete_one({"_id": ObjectId(resume_id), "user_id": user["_id"]})
    if res.deleted_count == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"ok": True})
