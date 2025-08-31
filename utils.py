import os, datetime
import jwt

def _cookie_settings(is_prod: bool):
    return {
        "httponly": True,
        "secure": is_prod,
        "samesite": "None" if is_prod else "Lax",
        "path": "/",
        "max_age": 60 * 60 * 24 * 7,  # 7 days
    }

def make_jwt(payload: dict, secret: str):
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_jwt(token: str, secret: str):
    return jwt.decode(token, secret, algorithms=["HS256"])

def now_epoch():
    return int(datetime.datetime.utcnow().timestamp())

def cookie_args(env: str):
    return _cookie_settings(is_prod=(env == "production"))
