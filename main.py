from fastapi import FastAPI, HTTPException, Depends, APIRouter
from pydantic import BaseModel, EmailStr
from enum import Enum as PyEnum
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional
import os

# Cargar variables de entorno si existe .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Configuración de la base de datos
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Instancia principal de la aplicación
app = FastAPI(title="Servicio de Estudiantes")

# Enumeración de roles
class Role(PyEnum):
    Estudiante = "Estudiante"
    Profesor = "Profesor"

# Modelo de base de datos
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(SqlEnum(Role, name='role_enum'), nullable=False, default=Role.Estudiante)
    password = Column(String, nullable=False)  # texto plano solo para pruebas
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Modelos Pydantic
class UserCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    bio: Optional[str] = None
    role: Optional[Role] = Role.Estudiante

class UserUpdate(BaseModel):
    nombre: Optional[str]
    apellido: Optional[str]
    bio: Optional[str]
    role: Optional[Role]

class UserOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    bio: Optional[str]
    role: Role
    created_at: datetime

    class Config:
        orm_mode = True

# Dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# Router específico de estudiantes
# -------------------------------
router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

@router.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = UserDB(
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        password=user.password,
        bio=user.bio,
        role=user.role
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
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/users/{user_id}", response_model=UserOut)
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
    if updates.role is not None:
        user.role = updates.role
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users

# Registrar el router en la app principal
app.include_router(router)
