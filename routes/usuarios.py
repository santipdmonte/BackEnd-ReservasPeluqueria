from fastapi import APIRouter, Depends
from uuid import UUID

from database import get_db
from schemas import UsuarioResponse, UsuarioBase, UsuarioUpdate
from services.usuarios import (
    crear_usuario,
    obtener_usuario,
    actualizar_usuario,
    obtener_usuario_por_telefono,
    obtener_historial_usuario
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UsuarioResponse)
def crear_usuario_endpoint(usuario: UsuarioBase, db=Depends(get_db)):
    return crear_usuario(usuario, db)

@router.get("/{user_id}", response_model=UsuarioResponse)
def obtener_usuario_endpoint(user_id: UUID, db=Depends(get_db)):
    return obtener_usuario(user_id, db)

@router.put("/", response_model=UsuarioResponse)
def actualizar_usuario_endpoint(user_id: UUID,usuario_new: UsuarioUpdate, db=Depends(get_db)):
    return actualizar_usuario(user_id, usuario_new, db)


@router.get("/telefono/{telefono}", response_model=UsuarioResponse)
def obtener_usuario_por_telefono_endpoint(telefono: str, db=Depends(get_db)):
    return obtener_usuario_por_telefono(telefono, db)


@router.get("/historial/{user_id}")
def obtener_historial_usuario_endpoint(user_id: UUID, db=Depends(get_db)):
    return obtener_historial_usuario(user_id, db)
