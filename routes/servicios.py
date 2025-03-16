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
def obtener_servicios_endpoint(db=Depends(get_db)):
    return obtener_servicios(db)

@router.post("/", response_model=ServicioResponse)
def crear_servicio_endpoint(servicio: ServicioBase, db=Depends(get_db)):
    return crear_servicio(servicio, db)

@router.put("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio_endpoint(servicio_id: UUID, servicio: ServicioUpdate, db=Depends(get_db)):
    return actualizar_servicio(servicio_id, servicio, db)

@router.delete("/{servicio_id}")
def eliminar_servicio_endpoint(servicio_id: UUID, db=Depends(get_db)):
    return eliminar_servicio(servicio_id, db)

@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio_by_id_endpoint(servicio_id: UUID, db=Depends(get_db)):
    return obtener_servicio_by_id(servicio_id, db)
