from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_player
from app.models.player import Player
from app.models.score import Score
from app.models.session import GameSession
from app.schemas.player import PlayerOut

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Inline schemas ────────────────────────────────────────────────────────────

class AdminPlayerUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class AdminScoreUpdate(BaseModel):
    score: Optional[int] = None
    gold_collected: Optional[int] = None
    enemies_smashed: Optional[int] = None
    wave_reached: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="Get dashboard stats",
    description="Returns aggregate stats: total players, scores, and session counts.",
)
def get_stats(
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    total_players = db.query(func.count(Player.id)).scalar() or 0
    total_scores = db.query(func.count(Score.id)).scalar() or 0
    active_sessions = db.query(func.count(GameSession.id)).filter(GameSession.status == "active").scalar() or 0
    completed_sessions = db.query(func.count(GameSession.id)).filter(GameSession.status == "completed").scalar() or 0
    top_score = db.query(func.max(Score.score)).scalar() or 0

    return {
        "total_players": total_players,
        "total_scores": total_scores,
        "active_sessions": active_sessions,
        "completed_sessions": completed_sessions,
        "top_score": top_score,
    }


@router.get(
    "/players",
    response_model=list[PlayerOut],
    summary="List all players",
    description="Returns all registered players ordered by registration date descending.",
)
def list_players(
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    return db.query(Player).order_by(Player.created_at.desc()).all()


@router.put(
    "/players/{player_id}",
    response_model=PlayerOut,
    summary="Update a player",
    description="Update a player's username and/or email.",
)
def update_player(
    player_id: int,
    data: AdminPlayerUpdate,
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    if data.username is not None:
        conflict = db.query(Player).filter(Player.username == data.username, Player.id != player_id).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        player.username = data.username

    if data.email is not None:
        conflict = db.query(Player).filter(Player.email == data.email, Player.id != player_id).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        player.email = data.email

    db.commit()
    db.refresh(player)
    return player


@router.get(
    "/scores",
    summary="List all scores",
    description="Returns all score records with player username, ordered by score descending.",
)
def list_scores(
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    rows = (
        db.query(Score, Player.username)
        .join(Player, Score.player_id == Player.id)
        .order_by(Score.score.desc())
        .all()
    )
    return [
        {
            "id": score.id,
            "player_id": score.player_id,
            "username": username,
            "score": score.score,
            "gold_collected": score.gold_collected,
            "enemies_smashed": score.enemies_smashed,
            "wave_reached": score.wave_reached,
            "created_at": score.created_at,
        }
        for score, username in rows
    ]


@router.put(
    "/scores/{score_id}",
    summary="Update a score",
    description="Update any fields on a score record.",
)
def update_score(
    score_id: int,
    data: AdminScoreUpdate,
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    score = db.get(Score, score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    if data.score is not None:
        score.score = data.score
    if data.gold_collected is not None:
        score.gold_collected = data.gold_collected
    if data.enemies_smashed is not None:
        score.enemies_smashed = data.enemies_smashed
    if data.wave_reached is not None:
        score.wave_reached = data.wave_reached

    db.commit()
    db.refresh(score)
    return score
