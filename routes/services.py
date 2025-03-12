from fastapi import APIRouter, Depends
from uuid import UUID
from database import get_db
from schemas import ServicioBase, ServicioResponse, ServicioUpdate
from services.servicios import (
    get_servicios_service,
    create_servicio_service,
    update_servicio_service,
    delete_servicio_service,
    get_servicio_by_id_service
)

router = APIRouter(prefix="/servicios", tags=["Servicios"])

@router.get("/", response_model=list[ServicioResponse])
async def obtener_servicios(db=Depends(get_db)):
    return await get_servicios_service(db)

@router.post("/", response_model=ServicioResponse)
async def crear_servicio(servicio: ServicioBase, db=Depends(get_db)):
    return await create_servicio_service(servicio, db)

@router.put("/{servicio_id}", response_model=ServicioResponse)
async def actualizar_datos_servicio(servicio_id: UUID, servicio: ServicioUpdate, db=Depends(get_db)):
    return await update_servicio_service(servicio_id, servicio, db)

@router.delete("/{servicio_id}")
async def eliminar_servicio(servicio_id: UUID, db=Depends(get_db)):
    return await delete_servicio_service(servicio_id, db)

@router.get("/{servicio_id}", response_model=ServicioResponse)
async def obtener_servicio_by_id(servicio_id: UUID, db=Depends(get_db)):
    return await get_servicio_by_id_service(servicio_id, db)
