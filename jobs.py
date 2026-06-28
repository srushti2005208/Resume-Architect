# src/jobs.py
from flask import Blueprint, request, jsonify, current_app
from pymongo import MongoClient
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

# Mongo connection
mongo = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = mongo["resume_architect"]

# Config for job feed (replace with Apify / real source)
JOB_FEED_URL = os.getenv("JOB_FEED_URL", "https://api.example.com/jobs")
JOB_FEED_KEY = os.getenv("JOB_FEED_KEY", "")

def build_profile_text(skills, education):
    skills_text = " ".join(skills or [])
    edu_text = " ".join(
        f"{e.get('degree','')} {e.get('stream','')} {e.get('year','')}"
        for e in (education or [])
    )
    return f"{skills_text} {edu_text}"

def fetch_jobs_from_feed(query, location=None, limit=100):
    params = {"q": query, "limit": limit}
    if location: params["location"] = location
    headers = {}
    if JOB_FEED_KEY:
        headers["Authorization"] = f"Bearer {JOB_FEED_KEY}"
    r = requests.get(JOB_FEED_URL, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()  # expects a list of jobs

@jobs_bp.route("/suggest", methods=["POST"])
def suggest_jobs():
    """
    JSON body:
    {
      "user_id": "...", 
      "skills": ["python","flask"],
      "education": [{"degree":"B.E.","stream":"CS","year":"2024"}],
      "location": "Pune",
      "experience": 1
    }
    """
    data = request.json or {}
    skills = data.get("skills", [])
    education = data.get("education", [])
    location = data.get("location")

    profile_text = build_profile_text(skills, education)
    if not profile_text.strip():
        return jsonify({"error": "skills or education missing"}), 400

    try:
        jobs_raw = fetch_jobs_from_feed(" ".join(skills), location)
    except Exception as e:
        current_app.logger.exception("Error fetching jobs")
        return jsonify({"error": "Could not fetch job data", "detail": str(e)}), 502

    if not jobs_raw:
        return jsonify({"jobs": []})

    # Combine title+desc+skills of each job for TF-IDF
    job_texts = []
    jobs = []
    for j in jobs_raw:
        desc = " ".join([
            j.get("title",""),
            j.get("company",""),
            j.get("description",""),
            " ".join(j.get("skills", []))
        ])
        job_texts.append(desc)
        jobs.append(j)

    vect = TfidfVectorizer(max_features=1000, stop_words="english")
    docs = [profile_text] + job_texts
    tfidf = vect.fit_transform(docs)
    sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

    # Attach scores
    ranked_jobs = []
    for score, job in sorted(zip(sims, jobs), key=lambda x: x[0], reverse=True)[:20]:
        ranked_jobs.append({
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "skills": job.get("skills"),
            "url": job.get("url"),
            "score": float(score)
        })

    # Save suggestions to Mongo (optional)
    if data.get("user_id"):
        db.suggestions.insert_one({
            "user_id": data["user_id"],
            "profile": {"skills": skills, "education": education, "location": location},
            "results": ranked_jobs,
            "created_at": datetime.utcnow()
        })

    return jsonify({"jobs": ranked_jobs})
