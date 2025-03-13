from fastapi import APIRouter, Depends
from uuid import UUID
from database import get_db
from schemas import EmpleadoResponse, EmpleadoBase, EmpleadoUpdate
from services.empleados import (
    get_empleados_service,
    create_empleado_service,
    update_empleado_service,
    delete_empleado_service,
    get_empleado_by_id_service
)

router = APIRouter(prefix="/empleados", tags=["Empleados"])

@router.get("/", response_model=list[EmpleadoResponse])
async def obtener_empleados(db=Depends(get_db)):
    return await get_empleados_service(db)   

@router.post("/", response_model=EmpleadoResponse)
async def crear_empleado(empleado: EmpleadoBase, db=Depends(get_db)):
    return await create_empleado_service(empleado, db)

@router.put("/{empleado_id}", response_model=EmpleadoResponse)
async def actualizar_datos_empleado(empleado_id: UUID, empleado: EmpleadoUpdate, db=Depends(get_db)):
    return await update_empleado_service(empleado_id, empleado, db)

@router.delete("/{empleado_id}")
async def eliminar_empleado(empleado_id: UUID, db=Depends(get_db)):
    return await delete_empleado_service(empleado_id, db)

@router.get("/{empleado_id}", response_model=EmpleadoResponse)
async def obtener_empleado_by_id(empleado_id: UUID, db=Depends(get_db)):
    return await get_empleado_by_id_service(empleado_id, db)
