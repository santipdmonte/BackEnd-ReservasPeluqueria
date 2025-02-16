from fastapi import APIRouter, Depends, HTTPException
from database import get_db

from schemas import EmpleadoResponse, EmpleadoBase
from uuid import UUID

from datetime import date

router = APIRouter(prefix="/empleados", tags=["Empleados"])


@router.get("/", response_model=list[EmpleadoResponse])
async def obtener_empleados(db=Depends(get_db)):
    
    try:
        empleados = await db.fetch("SELECT * FROM empleados;")

        if not empleados:
            raise HTTPException(status_code=404, detail=f"No se encontraron empleados")
        
        return [dict(empleado) for empleado in empleados]
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.post("/", response_model=EmpleadoResponse)
async def crear_empleados (empleado: EmpleadoBase ,db=Depends(get_db)):
    
    try:

        nuevo_empleado = await db.fetchrow(
        """
            INSERT INTO empleados (nombre, especialidad)
            VALUES ($1, $2)
            RETURNING *;
        """, empleado.nombre, empleado.especialidad)    

        if not nuevo_empleado:
            raise HTTPException(status_code=404, detail=f"Error al crear el nuevo empleado")
        
        return dict(nuevo_empleado)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.put("/", response_model=EmpleadoResponse)
async def actualizar_datos_empleado(empleado: EmpleadoResponse, db=Depends(get_db)):
    
    try:
        
        if not await db.fetchrow(" SELECT * FROM empleados where id = $1;", empleado.id):
            raise HTTPException(status_code=404, detail=f"No se encontraro al empleado con id {empleado.id}")

        empleado_actualizado = await db.fetchrow(
        """
            UPDATE empleados
            SET 
                nombre = $1, 
                especialidad = $2
            WHERE id = $3 
            RETURNING *;
        """, empleado.nombre, empleado.especialidad, empleado.id)

        if not empleado_actualizado:
            raise HTTPException(status_code=404, detail=f"Error al actualizar el empleado con id {empleado.id}")
        
        return dict(empleado_actualizado)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.delete("/")
async def eliminar_empleado(empleado_id: UUID, db=Depends(get_db)):
    
    try:

        resultado = await db.execute(
            "DELETE FROM empleados WHERE id = $1;",
            empleado_id
        )
        
        if resultado == "DELETE 0":  # Si no se eliminó ningún registro
            raise HTTPException(status_code=404, detail=f"Empleado no encontrado")
        
        return {"mensaje": "Empleado eliminado correctamente"}
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{empleado_id}", response_model=EmpleadoResponse)
async def obtener_empleado_by_id(empleado_id: UUID, db=Depends(get_db)):
    
    try:
        empleado = await db.fetchrow(" SELECT * FROM empleados where id = $1; ", empleado_id)

        if not empleado:
            raise HTTPException(status_code=404, detail=f"No se encontraro al empleado con id {empleado_id}")
        
        return dict(empleado)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

