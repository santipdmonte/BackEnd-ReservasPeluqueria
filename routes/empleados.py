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
def obtener_empleados_endpoint(db=Depends(get_db)):
    return obtener_empleados(db)   

@router.post("/", response_model=EmpleadoResponse)
def crear_empleado_endpoint(empleado: EmpleadoBase, db=Depends(get_db)):
    return crear_empleado(empleado, db)

@router.put("/{empleado_id}", response_model=EmpleadoResponse)
def actualizar_empleado_endpoint(empleado_id: UUID, empleado: EmpleadoUpdate, db=Depends(get_db)):
    return actualizar_empleado(empleado_id, empleado, db)

@router.delete("/{empleado_id}")
def eliminar_empleado_endpoint(empleado_id: UUID, db=Depends(get_db)):
    return eliminar_empleado(empleado_id, db)

@router.get("/{empleado_id}", response_model=EmpleadoResponse)
def obtener_empleado_by_id_endpoint(empleado_id: UUID, db=Depends(get_db)):
    return obtener_empleado_by_id(empleado_id, db)
