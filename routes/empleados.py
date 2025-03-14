from fastapi import APIRouter, Depends
from uuid import UUID
from database import get_db
from schemas import EmpleadoResponse, EmpleadoBase, EmpleadoUpdate
from services.empleados import (
    obtener_empleados,
    crear_empleado,
    actualizar_empleado,
    eliminar_empleado,
    obtener_empleado_by_id
)

router = APIRouter(prefix="/empleados", tags=["Empleados"])

@router.get("/", response_model=list[EmpleadoResponse])
async def obtener_empleados_endpoint(db=Depends(get_db)):
    return await obtener_empleados(db)   

@router.post("/", response_model=EmpleadoResponse)
async def crear_empleado_endpoint(empleado: EmpleadoBase, db=Depends(get_db)):
    return await crear_empleado(empleado, db)

@router.put("/{empleado_id}", response_model=EmpleadoResponse)
async def actualizar_empleado_endpoint(empleado_id: UUID, empleado: EmpleadoUpdate, db=Depends(get_db)):
    return await actualizar_empleado(empleado_id, empleado, db)

@router.delete("/{empleado_id}")
async def eliminar_empleado_endpoint(empleado_id: UUID, db=Depends(get_db)):
    return await eliminar_empleado(empleado_id, db)

@router.get("/{empleado_id}", response_model=EmpleadoResponse)
async def obtener_empleado_by_id_endpoint(empleado_id: UUID, db=Depends(get_db)):
    return await obtener_empleado_by_id(empleado_id, db)
