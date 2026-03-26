from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    gold_collected: Mapped[int] = mapped_column(Integer, default=0)
    enemies_smashed: Mapped[int] = mapped_column(Integer, default=0)
    wave_reached: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    player: Mapped["Player"] = relationship("Player", back_populates="scores")
