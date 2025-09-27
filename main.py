from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # texto plano para pruebas
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    nombre: Optional[str]
    apellido: Optional[str]
    bio: Optional[str]

class UserOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    bio: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = UserDB(
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        password=user.password,  # sin hash, solo para pruebas!
        bio=user.bio
    )
    db.add(db_user) 
    try:
        db.commit()
        db.refresh(db_user)
        return {"message": "Usuario creado", "id": db_user.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email ya registrado")
    except Exception as e:
        db.rollback()
        print(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, updates: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if updates.nombre is not None:
        user.nombre = updates.nombre
    if updates.apellido is not None:
        user.apellido = updates.apellido
    if updates.bio is not None:
        user.bio = updates.bio
    db.commit()
    db.refresh(user)
    return user

@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users
