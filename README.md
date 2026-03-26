
![Regal Rust](src/thumbnail.png)

# Regal Rust — Game Backend API

REST API backend for **Regal Rust**, a solo indie 3D physics-based medieval weapon game built in Godot 4.

Handles player authentication, persistent leaderboard data, and game session tracking. Designed to be called directly from the Godot 4 client via `HTTPRequest` nodes.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT (python-jose + passlib bcrypt) |
| Validation | Pydantic v2 |
| Server | Uvicorn |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/regalrust
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Create the database

```sql
CREATE DATABASE regalrust;
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Swagger UI: `http://localhost:8000/docs`

---

## API Reference

### Auth

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register a new player |
| POST | `/auth/login` | No | Login, receive JWT token |
| GET | `/auth/me` | Yes | Get current player profile |

### Leaderboard & Scores

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/leaderboard` | No | Top 100 scores (global) |
| GET | `/leaderboard/me` | Yes | Personal best + global rank |
| POST | `/scores` | Yes | Submit a new score after a run |

### Game Sessions

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/sessions/start` | Yes | Start a new game session |
| PUT | `/sessions/{id}/end` | Yes | End session, link final score |
| GET | `/sessions/me` | Yes | Get current player's session history |

---

## Game Session Flow

```
1. POST /auth/login              → receive token
2. POST /sessions/start          → receive session_id
3. Player plays the run...
4. POST /scores                  → receive score_id
5. PUT /sessions/{id}/end        → link score, mark completed
```

### Example with curl

**Register**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "dragonslayer99", "email": "player@example.com", "password": "secret123"}'
```

**Login**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dragonslayer99&password=secret123"
```

**Start session**
```bash
curl -X POST http://localhost:8000/sessions/start \
  -H "Authorization: Bearer <token>"
```

**Submit score**
```bash
curl -X POST http://localhost:8000/scores \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"score": 4200, "gold_collected": 310, "enemies_smashed": 47, "wave_reached": 12}'
```

**End session**
```bash
curl -X PUT http://localhost:8000/sessions/1/end \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"score_id": 1}'
```

**Global leaderboard**
```bash
curl http://localhost:8000/leaderboard
```

---

## Godot 4 Integration

All requests use the `HTTPRequest` node. Store the token in a global `GameAPI.gd` autoload after login.

```gdscript
# GameAPI.gd (AutoLoad singleton)
extends Node

var base_url := "http://localhost:8000"
var token := ""
var session_id := 0
```

```gdscript
# Example authenticated request
var headers = [
    "Content-Type: application/json",
    "Authorization: Bearer " + GameAPI.token
]
http_request.request(GameAPI.base_url + "/leaderboard", headers, HTTPClient.METHOD_GET)
```

---

## Project Structure

```
regal-rust-backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy engine + Base
│   ├── dependencies.py      # get_db, get_current_player
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # Route handlers
│   └── services/            # Business logic
├── alembic/                 # Migrations
├── alembic.ini
├── requirements.txt
└── .env.example
```
