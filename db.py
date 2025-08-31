import os
from flask import current_app
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

client = None
db = None

def init_db(app):
    global client, db
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/resume_architect")
    client = MongoClient(uri, uuidRepresentation="standard")
    db_name = uri.rsplit("/", 1)[-1] if "/" in uri else "resume_architect"
    db = client.get_database(db_name)

    # Create indexes
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.resumes.create_index([("user_id", ASCENDING)])

    # Attach to app for shell access
    app.mongo_client = client
    app.db = db

def to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    return ObjectId(str(value))
