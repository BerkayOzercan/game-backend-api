from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_player
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerOut
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=PlayerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new player",
    description="Creates a new player account. Username and email must be unique.",
)
def register(player_data: PlayerCreate, db: Session = Depends(get_db)):
    if db.query(Player).filter(Player.username == player_data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    if db.query(Player).filter(Player.email == player_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    player = Player(
        username=player_data.username,
        email=player_data.email,
        hashed_password=hash_password(player_data.password),
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.post(
    "/login",
    summary="Login and receive a JWT token",
    description="Authenticate with username and password. Returns a Bearer token valid for 24 hours.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.username == form_data.username).first()
    if not player or not verify_password(form_data.password, player.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    player.last_seen_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({"sub": str(player.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=PlayerOut,
    summary="Get current player profile",
    description="Returns the authenticated player's profile data.",
)
def get_me(current_player: Player = Depends(get_current_player)):
    return current_player
