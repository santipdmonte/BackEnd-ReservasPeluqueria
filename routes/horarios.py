from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import date, time

from database import get_db
from services.horarios import (
    generacion_horarios_semanales,
    crear_programacion_horarios,
    obtener_programacion_horarios,
    actualizar_programacion_horarios,
    eliminar_programacion_horarios,
    bloquear_horarios,
    desbloquear_horarios
)

router = APIRouter(prefix="/horarios", tags=["Horarios"])

@router.post("/generar_horarios")
def generacion_horarios_semanales_endpoint(db=Depends(get_db)):
    return generacion_horarios_semanales(db)


@router.post("/")
def crear_programacion_horarios_endpoint(
    empleado_id: UUID,
    dia: str,
    hora_inicio: time,
    hora_fin: time,
    intervalo: int = 30,
    db=Depends(get_db)
):
    return crear_programacion_horarios(empleado_id, dia, hora_inicio, hora_fin, intervalo, db)


@router.get("/")
def obtener_programacion_horarios_endpoint(
    empleado_id: UUID = None,
    dia: str = None,
    db=Depends(get_db)
):
    return obtener_programacion_horarios(db, empleado_id, dia)


@router.put("/{id}")
def actualizar_programacion_horarios_endpoint(
    id: UUID,
    hora_inicio: time = None,
    hora_fin: time = None,
    intervalo: int = None,
    db=Depends(get_db)
):
    return actualizar_programacion_horarios(id, hora_inicio, hora_fin, intervalo, db)


@router.delete("/{id}")
def eliminar_programacion_horarios_endpoint(id: UUID, db=Depends(get_db)):
    return eliminar_programacion_horarios(id, db)


@router.post("/bloquear")
def bloquear_horarios_endpoint(
    empleado_id: UUID,
    fecha: date,
    hora_inicio: time = time(0, 0, 0),
    hora_fin: time = time(23, 59, 59),
    db=Depends(get_db)
):
    return bloquear_horarios(empleado_id, fecha, hora_inicio, hora_fin, db)


@router.post("/desbloquear")
def desbloquear_horarios_endpoint(
    empleado_id: UUID,
    fecha: date,
    hora_inicio: time = time(0, 0, 0),
    hora_fin: time = time(23, 59, 59),
    db=Depends(get_db)
):
    return desbloquear_horarios(empleado_id, fecha, hora_inicio, hora_fin, db)
