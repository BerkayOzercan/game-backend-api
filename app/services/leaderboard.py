from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.score import Score
from app.schemas.score import LeaderboardEntry


def get_global_leaderboard(db: Session, limit: int = 100, offset: int = 0) -> list[LeaderboardEntry]:
    rank_subquery = (
        db.query(
            Score.id,
            func.rank().over(order_by=desc(Score.score)).label("rank"),
        )
        .subquery()
    )

    rows = (
        db.query(Score, Player.username, rank_subquery.c.rank)
        .join(Player, Score.player_id == Player.id)
        .join(rank_subquery, Score.id == rank_subquery.c.id)
        .order_by(rank_subquery.c.rank)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        LeaderboardEntry(
            rank=rank,
            username=username,
            score=score.score,
            gold_collected=score.gold_collected,
            enemies_smashed=score.enemies_smashed,
            wave_reached=score.wave_reached,
            created_at=score.created_at,
        )
        for score, username, rank in rows
    ]


def get_personal_best(db: Session, player_id: int) -> LeaderboardEntry | None:
    best_score = (
        db.query(Score)
        .filter(Score.player_id == player_id)
        .order_by(desc(Score.score))
        .first()
    )

    if not best_score:
        return None

    rank_subquery = (
        db.query(func.count(Score.id).label("rank"))
        .filter(Score.score > best_score.score)
        .scalar()
    )

    player = db.query(Player).filter(Player.id == player_id).first()

    return LeaderboardEntry(
        rank=rank_subquery + 1,
        username=player.username,
        score=best_score.score,
        gold_collected=best_score.gold_collected,
        enemies_smashed=best_score.enemies_smashed,
        wave_reached=best_score.wave_reached,
        created_at=best_score.created_at,
    )
