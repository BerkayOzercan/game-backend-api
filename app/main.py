from fastapi import FastAPI

from app.routers import auth, leaderboard, sessions

app = FastAPI(
    title="FastAPI Game Backend",
    description=(
        "REST API for a 3D physics-based medieval weapon game built in Godot 4. "
        "Handles player authentication, leaderboard data, and game session tracking."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(leaderboard.router)
app.include_router(sessions.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "project": "FastAPI Game Backend"}
