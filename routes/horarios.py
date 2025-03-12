from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import date, time

from database import get_db
from services.horarios import (
    generar_horarios_semanales_service,
    crear_programacion_horarios_service,
    ver_programacion_horarios_service,
    actualizar_programacion_horarios_service,
    eliminar_programacion_horarios_service,
    bloquear_horarios_service,
    desbloquear_horarios_service
)

router = APIRouter(prefix="/horarios", tags=["Horarios"])

@router.post("/generar_horarios")
async def generar_horarios(db=Depends(get_db)):
    return await generar_horarios_semanales_service(db)


@router.post("/")
async def crear_programacion(
    empleado_id: UUID,
    dia: str,
    hora_inicio: time,
    hora_fin: time,
    intervalo: int = 30,
    db=Depends(get_db)
):
    return await crear_programacion_horarios_service(empleado_id, dia, hora_inicio, hora_fin, intervalo, db)


@router.get("/")
async def ver_programacion(
    empleado_id: UUID = None,
    dia: str = None,
    db=Depends(get_db)
):
    return await ver_programacion_horarios_service(db, empleado_id, dia)


@router.put("/{id}")
async def actualizar_programacion(
    id: UUID,
    hora_inicio: time = None,
    hora_fin: time = None,
    intervalo: int = None,
    db=Depends(get_db)
):
    return await actualizar_programacion_horarios_service(id, hora_inicio, hora_fin, intervalo, db)


@router.delete("/{id}")
async def eliminar_programacion(id: UUID, db=Depends(get_db)):
    return await eliminar_programacion_horarios_service(id, db)


@router.post("/bloquear")
async def bloquear(
    empleado_id: UUID,
    fecha: date,
    hora_inicio: time = time(0, 0, 0),
    hora_fin: time = time(23, 59, 59),
    db=Depends(get_db)
):
    return await bloquear_horarios_service(empleado_id, fecha, hora_inicio, hora_fin, db)


@router.post("/desbloquear")
async def desbloquear(
    empleado_id: UUID,
    fecha: date,
    hora_inicio: time = time(0, 0, 0),
    hora_fin: time = time(23, 59, 59),
    db=Depends(get_db)
):
    return await desbloquear_horarios_service(empleado_id, fecha, hora_inicio, hora_fin, db)
