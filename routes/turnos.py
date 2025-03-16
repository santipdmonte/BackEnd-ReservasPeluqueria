from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import date
from typing import Optional

from database import get_db
from schemas import TurnoBase, TurnoResponse
from services.turnos import (
    crear_turno,
    obtener_turnos_disponibles,
    obtener_turno,
    cancelar_turno,
    modificar_turno,
    obtener_turnos_por_usuario,
    obtener_turnos_agendados_por_fecha
)

router = APIRouter(prefix="/turnos", tags=["Turnos"])

@router.post("/", response_model=TurnoResponse)
async def crear_turno_endpoint(turno: TurnoBase):
    return crear_turno(turno)


@router.get("/disponibles")
async def obtener_turnos_disponibles_endpoint(fecha: date, empleado_id: Optional[UUID] = None, db=Depends(get_db)):
    return obtener_turnos_disponibles(fecha, empleado_id, db)


@router.get("/{turno_id}", response_model=TurnoResponse)
async def obtener_turno(turno_id: UUID, db=Depends(get_db)):
    return obtener_turno(turno_id, db)


@router.delete("/{turno_id}")
async def cancelar_turno_endpoint(turno_id: UUID, db=Depends(get_db)):
    return cancelar_turno(turno_id, db)


@router.put("/{turno_id}", response_model=TurnoResponse)
async def modificar_turno_endpoint(turno_id: UUID, nuevo_turno: TurnoBase, db=Depends(get_db)):
    return modificar_turno(turno_id, nuevo_turno, db)


@router.get("/user/{user_id}", response_model=list[TurnoResponse])
def obtener_turnos_por_usuario_endpoint(user_id: UUID, db=Depends(get_db)):
    return obtener_turnos_por_usuario(user_id, db)


@router.get("/agendados/{fecha}")
def obtener_turnos_agendados_por_fecha_endpoint(fecha: date, db=Depends(get_db)):
    return obtener_turnos_agendados_por_fecha(fecha, db)
