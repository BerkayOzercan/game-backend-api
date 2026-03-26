# Regal Rust — Game Backend API (CLAUDE.md)

This file gives Claude full context about the Regal Rust game backend so it can assist without re-explaining the project every session.

---

## Project Overview

**Regal Rust Game Backend** is a REST API that serves as the game server for Regal Rust — a solo indie 3D physics-based medieval weapon game built in Godot 4.

The backend handles player authentication, persistent leaderboard data, and game session tracking. It is designed to be called directly from the Godot 4 client using HTTPRequest nodes.

**Public codename:** Project RR  
**Game engine:** Godot 4  
**Client → Server communication:** Godot HTTPRequest → FastAPI REST endpoints

---

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT via `python-jose` + `passlib[bcrypt]` |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Env vars | `python-dotenv` + `pydantic-settings` |

---

## Project Structure

```
regal-rust-backend/
├── app/
│   ├── main.py              # FastAPI app entry point, router registration
│   ├── database.py          # SQLAlchemy engine, SessionLocal, Base
│   ├── dependencies.py      # get_db, get_current_player shared dependencies
│   ├── config.py            # Settings loaded from .env via pydantic-settings
│   ├── models/
│   │   ├── player.py        # Player SQLAlchemy model
│   │   ├── score.py         # Score/leaderboard SQLAlchemy model
│   │   └── session.py       # GameSession SQLAlchemy model
│   ├── schemas/
│   │   ├── player.py        # PlayerCreate, PlayerOut, PlayerUpdate
│   │   ├── score.py         # ScoreCreate, ScoreOut, LeaderboardEntry
│   │   └── session.py       # SessionCreate, SessionOut, SessionEnd
│   ├── routers/
│   │   ├── auth.py          # POST /auth/register, POST /auth/login
│   │   ├── leaderboard.py   # GET /leaderboard, POST /scores
│   │   └── sessions.py      # POST /sessions/start, PUT /sessions/end
│   └── services/
│       ├── auth.py          # Password hashing, JWT creation/verification
│       └── leaderboard.py   # Score ranking logic, personal best checks
├── alembic/                 # Migration files
├── alembic.ini
├── .env                     # Secrets — never commit
├── .env.example             # Safe template to commit
├── requirements.txt
└── CLAUDE.md
```

---

## Environment Variables

```env
# .env.example
DATABASE_URL=postgresql://postgres:password@localhost:5432/regalrust
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Note: Token expiry is set to 1440 minutes (24 hours) since game clients should not need to re-login frequently.

Settings loaded in `app/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}

settings = Settings()
```

---

## Database Models (summary)

**Player**
- `id`, `username` (unique), `email` (unique), `hashed_password`
- `created_at`, `last_seen_at`
- `total_sessions` (int, default 0)

**Score**
- `id`, `player_id` (FK → Player)
- `score` (int) — total score for a run
- `gold_collected` (int) — gold gathered in the run
- `enemies_smashed` (int) — destructible objects hit
- `wave_reached` (int) — how far the player got
- `created_at`

**GameSession**
- `id`, `player_id` (FK → Player)
- `started_at`, `ended_at`
- `duration_seconds` (int, nullable — filled on session end)
- `status` — `active` | `completed` | `abandoned`
- `final_score_id` (FK → Score, nullable — linked on session end)

---

## API Endpoints

### Auth
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | ❌ | Register new player |
| POST | `/auth/login` | ❌ | Login, receive JWT token |
| GET | `/auth/me` | ✅ | Get current player profile |

### Leaderboard & Scores
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/leaderboard` | ❌ | Top 100 scores (global) |
| GET | `/leaderboard/me` | ✅ | Current player's personal best + rank |
| POST | `/scores` | ✅ | Submit a new score after a run |

### Game Sessions
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/sessions/start` | ✅ | Start a new game session |
| PUT | `/sessions/{id}/end` | ✅ | End session, link final score |
| GET | `/sessions/me` | ✅ | Get current player's session history |

---

## Auth Flow

- `POST /auth/register` — creates player, hashes password with bcrypt
- `POST /auth/login` — validates credentials, returns JWT access token
- Godot client stores token in memory and sends it as `Authorization: Bearer <token>` header on all protected requests
- `get_current_player` dependency decodes JWT and injects the Player object into route handlers
- Players can only access their own session history and scores

---

## Game Session Flow

```
Game starts
    → POST /sessions/start         (returns session_id)

Player plays the run...

Game ends
    → POST /scores                 (submit run stats, returns score_id)
    → PUT /sessions/{id}/end       (link score_id, mark session completed)
```

If the game crashes or closes mid-run, the session stays `active` — a cleanup job or login check can mark old active sessions as `abandoned`.

---

## Leaderboard Logic

- Global leaderboard is ranked by `score` descending
- Personal best is the player's highest single-run `score`
- `GET /leaderboard` returns: `rank`, `username`, `score`, `gold_collected`, `enemies_smashed`, `wave_reached`, `created_at`
- Pagination: `?limit=100&offset=0` query params
- Player rank is calculated with a subquery — no separate rank column stored

---

## Godot 4 Integration Notes

- All API calls from Godot use `HTTPRequest` node
- Base URL stored in a global Autoload singleton (`GameAPI.gd`)
- JWT token stored in the same singleton after login, attached to every request header
- Responses are parsed with `JSON.parse_string(response_body)`
- On session start, store `session_id` in the singleton for use at session end

Example Godot request pattern:
```gdscript
var headers = ["Content-Type: application/json", "Authorization: Bearer " + GameAPI.token]
http_request.request(GameAPI.base_url + "/leaderboard", headers, HTTPClient.METHOD_GET)
```

---

## Coding Conventions

- **Routers** handle HTTP only — no logic inside route functions
- **Services** contain all business logic (ranking queries, session state checks)
- **Schemas** are always separate from models — never return raw SQLAlchemy objects
- Use `response_model=` on every endpoint
- Return correct HTTP status codes: `201` for creates, `204` for deletes, `404` for not found, `403` for ownership violations
- All score submissions and session actions require JWT auth
- Use `Depends(get_db)` for DB sessions everywhere

---

## Running the Project

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Run dev server
uvicorn app.main:app --reload

# Swagger UI
http://localhost:8000/docs

# Run migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

---

## Build Order

1. [x] Folder structure + venv + dependencies installed
2. [x] `app/config.py` + `.env` setup
3. [x] `app/database.py` — DB connection
4. [x] `app/models/player.py` — Player model
5. [x] `app/schemas/player.py` — Pydantic schemas
6. [x] `app/services/auth.py` — password hashing + JWT logic
7. [x] `app/routers/auth.py` — register + login + /me
8. [x] `app/dependencies.py` — `get_current_player`
9. [x] Alembic setup + first migration
10. [x] `app/models/score.py` + score submission endpoint
11. [x] `app/models/session.py` + session start/end endpoints
12. [x] `app/routers/leaderboard.py` — global + personal leaderboard
13. [ ] Test full flow end-to-end in Swagger UI
14. [ ] Godot HTTPRequest integration (GameAPI.gd autoload)
15. [x] README.md with setup instructions + endpoint reference

---

## Portfolio Notes

- Swagger UI at `/docs` is the live demo — keep all endpoints well-described
- Add `summary=` and `description=` to every endpoint decorator
- Use realistic example data in Pydantic schemas via `json_schema_extra`
- README should show the full game session flow with example curl requests
- This backend directly supports a shipped indie game — strong portfolio talking point
