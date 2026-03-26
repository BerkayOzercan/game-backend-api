from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_player
from app.models.player import Player
from app.models.score import Score
from app.schemas.score import ScoreCreate, ScoreOut, LeaderboardEntry
from app.services.leaderboard import get_global_leaderboard, get_personal_best

router = APIRouter(tags=["Leaderboard & Scores"])


@router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntry],
    summary="Get global leaderboard",
    description="Returns the top scores across all players, ranked by score descending.",
)
def global_leaderboard(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return get_global_leaderboard(db, limit=limit, offset=offset)


@router.get(
    "/leaderboard/me",
    response_model=LeaderboardEntry,
    summary="Get personal best and rank",
    description="Returns the authenticated player's highest score and their global rank.",
)
def personal_leaderboard(
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    entry = get_personal_best(db, current_player.id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No scores found for this player")
    return entry


@router.post(
    "/scores",
    response_model=ScoreOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new score",
    description="Submit the stats from a completed run. Requires authentication.",
)
def submit_score(
    score_data: ScoreCreate,
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    score = Score(
        player_id=current_player.id,
        score=score_data.score,
        gold_collected=score_data.gold_collected,
        enemies_smashed=score_data.enemies_smashed,
        wave_reached=score_data.wave_reached,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score
