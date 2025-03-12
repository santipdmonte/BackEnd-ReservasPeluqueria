from fastapi import APIRouter, Depends
from uuid import UUID

from database import get_db
from schemas import UsuarioResponse, UsuarioBase, UsuarioUpdate
from services.usuarios import (
    create_usuario_service,
    get_usuario_service,
    update_usuario_service,
    get_usuario_by_phone_service,
    get_historial_del_usuario_service
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UsuarioResponse)
async def crear_usuario(usuario: UsuarioBase, db=Depends(get_db)):
    return await create_usuario_service(usuario, db)

@router.get("/{user_id}", response_model=UsuarioResponse)
async def get_usuario(user_id: UUID, db=Depends(get_db)):
    return await get_usuario_service(user_id, db)

@router.put("/", response_model=UsuarioResponse)
async def actualizar_usuario(usuario_new: UsuarioUpdate, db=Depends(get_db)):
    return await update_usuario_service(usuario_new, db)


@router.get("/telefono/{telefono}", response_model=UsuarioResponse)
async def obtener_usuario_by_phone_number(telefono: str, db=Depends(get_db)):
    return await get_usuario_by_phone_service(telefono, db)


@router.get("/historial/{user_id}")
async def obtener_historial_del_usuario(user_id: UUID, db=Depends(get_db)):
    return await get_historial_del_usuario_service(user_id, db)
