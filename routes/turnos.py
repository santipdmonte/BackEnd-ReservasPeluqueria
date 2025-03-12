from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import date
from typing import Optional

from database import get_db
from schemas import TurnoBase, TurnoResponse
from services.turnos import (
    create_turno_service,
    get_horarios_disponibles,
    get_turno,
    cancel_turno,
    modify_turno,
    get_turnos_by_user,
    get_turnos_agendados_by_date
)

router = APIRouter(prefix="/turnos", tags=["Turnos"])

@router.post("/", response_model=TurnoResponse)
async def crear_turno(turno: TurnoBase, db=Depends(get_db)):
    return await create_turno_service(turno, db)


@router.get("/disponibles")
async def horarios_disponibles_by_date_employee(fecha: date, empleado_id: Optional[UUID] = None, db=Depends(get_db)):
    return await get_horarios_disponibles(fecha, empleado_id, db)


@router.get("/{turno_id}", response_model=TurnoResponse)
async def obtener_turno(turno_id: UUID, db=Depends(get_db)):
    return await get_turno(turno_id, db)


@router.put("/{turno_id}")
async def cancelar_turno_endpoint(turno_id: UUID, db=Depends(get_db)):
    return await cancel_turno(turno_id, db)


@router.put("/edit/{turno_id}", response_model=TurnoResponse)
async def modificar_turno_endpoint(turno_id: UUID, nuevo_turno: TurnoBase, db=Depends(get_db)):
    return await modify_turno(turno_id, nuevo_turno, db)


@router.get("/user/{user_id}", response_model=list[TurnoResponse])
async def obtener_turnos_by_user_endpoint(user_id: UUID, db=Depends(get_db)):
    return await get_turnos_by_user(user_id, db)


@router.get("/agendados/{fecha}")
async def turnos_agendados_by_date_endpoint(fecha: date, db=Depends(get_db)):
    return await get_turnos_agendados_by_date(fecha, db)
