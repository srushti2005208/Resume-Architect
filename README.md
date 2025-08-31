# Resume Architect — Flask + MongoDB Backend

A simple, production-ready API for resume templates and user resumes.

## Features
- User signup/login with hashed passwords (Werkzeug)
- JWT auth with HttpOnly cookie (no tokens in localStorage)
- Resume CRUD (create, get, update, delete)
- List built-in templates
- CORS enabled for your frontend origin
- Environment-based config

## Quickstart

1) Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Copy `.env.example` to `.env` and set your values:
```bash
cp .env.example .env
```

3) Run the server:
```bash
flask --app app run --port 5000 --debug
```

4) Test endpoints (base URL defaults to `http://localhost:5000`):
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET  /api/auth/me`
- `POST /api/resumes`
- `GET  /api/resumes` (list current user's resumes)
- `GET  /api/resumes/<resume_id>`
- `PUT  /api/resumes/<resume_id>`
- `DELETE /api/resumes/<resume_id>`
- `GET  /api/templates` (static list; swap with DB if needed)

## Integrating with your frontend

- Set `FRONTEND_ORIGIN` in `.env` (e.g. `http://localhost:5173` for Vite).
- On fetch calls, include credentials so the HttpOnly cookie is sent:
  ```js
  fetch("http://localhost:5000/api/auth/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    credentials: "include",
    body: JSON.stringify({ email, password })
  })
  ```
- After login, call `/api/auth/me` to get the logged-in user's profile.

## Notes
- Passwords are hashed with `werkzeug.security`.
- JWT cookie is `HttpOnly; Secure` (Secure only when `FLASK_ENV=production`).
- Indexes are created for users and resumes on startup.
- Replace the in-file template list with a `templates` collection if preferred.
