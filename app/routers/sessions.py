from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_player
from app.models.player import Player
from app.models.score import Score
from app.models.session import GameSession
from app.schemas.session import SessionCreate, SessionEnd, SessionOut

router = APIRouter(prefix="/sessions", tags=["Game Sessions"])


@router.post(
    "/start",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new game session",
    description="Creates an active session for the authenticated player. Store the returned session ID in your client.",
)
def start_session(
    _: SessionCreate = SessionCreate(),
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    session = GameSession(player_id=current_player.id)
    current_player.total_sessions += 1
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put(
    "/{session_id}/end",
    response_model=SessionOut,
    summary="End a game session",
    description="Marks the session as completed and links the final score. Duration is calculated automatically.",
)
def end_session(
    session_id: int,
    body: SessionEnd,
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.player_id != current_player.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")

    score = db.query(Score).filter(Score.id == body.score_id, Score.player_id == current_player.id).first()
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    now = datetime.now(timezone.utc)
    session.ended_at = now
    session.duration_seconds = int((now - session.started_at).total_seconds())
    session.status = "completed"
    session.final_score_id = body.score_id

    db.commit()
    db.refresh(session)
    return session


@router.get(
    "/me",
    response_model=list[SessionOut],
    summary="Get session history",
    description="Returns all game sessions for the authenticated player, newest first.",
)
def my_sessions(
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    return (
        db.query(GameSession)
        .filter(GameSession.player_id == current_player.id)
        .order_by(GameSession.started_at.desc())
        .all()
    )
