from fastapi import APIRouter, Depends
from uuid import UUID
from database import get_db
from schemas import ServicioBase, ServicioResponse, ServicioUpdate
from services.servicios import (
    obtener_servicios,
    crear_servicio,
    actualizar_servicio,
    eliminar_servicio,
    obtener_servicio_by_id
)

router = APIRouter(prefix="/servicios", tags=["Servicios"])

@router.get("/", response_model=list[ServicioResponse])
async def obtener_servicios_endpoint(db=Depends(get_db)):
    return await obtener_servicios(db)

@router.post("/", response_model=ServicioResponse)
async def crear_servicio_endpoint(servicio: ServicioBase, db=Depends(get_db)):
    return await crear_servicio(servicio, db)

@router.put("/{servicio_id}", response_model=ServicioResponse)
async def actualizar_servicio_endpoint(servicio_id: UUID, servicio: ServicioUpdate, db=Depends(get_db)):
    return await actualizar_servicio(servicio_id, servicio, db)

@router.delete("/{servicio_id}")
async def eliminar_servicio_endpoint(servicio_id: UUID, db=Depends(get_db)):
    return await eliminar_servicio(servicio_id, db)

@router.get("/{servicio_id}", response_model=ServicioResponse)
async def obtener_servicio_by_id_endpoint(servicio_id: UUID, db=Depends(get_db)):
    return await obtener_servicio_by_id(servicio_id, db)
