from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.player import Player
from app.services.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_player(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Player:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    player_id: int = payload.get("sub")
    if player_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    player = db.query(Player).filter(Player.id == int(player_id)).first()
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Player not found")

    return player
