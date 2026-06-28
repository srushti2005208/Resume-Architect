from flask import Blueprint, request, jsonify
from bson import ObjectId
from src.db import db

resumes_bp = Blueprint("resumes", __name__)

@resumes_bp.route("/", methods=["GET"])
def get_resumes():
    user_id = request.args.get("user_id")
    resumes = list(db.resumes.find({"user_id": user_id}))
    for r in resumes:
        r["_id"] = str(r["_id"])
    return jsonify(resumes)

@resumes_bp.route("/", methods=["POST"])
def create_resume():
    data = request.json
    user_id = data.get("user_id")
    resume_data = data.get("resume")
    result = db.resumes.insert_one({"user_id": user_id, "resume": resume_data})
    return jsonify({"_id": str(result.inserted_id)}), 201

@resumes_bp.route("/<resume_id>", methods=["PUT"])
def update_resume(resume_id):
    data = request.json
    db.resumes.update_one({"_id": ObjectId(resume_id)}, {"$set": {"resume": data.get("resume")}})
    return jsonify({"message": "Resume updated"})

@resumes_bp.route("/<resume_id>", methods=["DELETE"])
def delete_resume(resume_id):
    db.resumes.delete_one({"_id": ObjectId(resume_id)})
    return jsonify({"message": "Resume deleted"})