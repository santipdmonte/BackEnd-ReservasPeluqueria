from fastapi import HTTPException
from uuid import UUID
from schemas import EmpleadoBase, EmpleadoUpdate

async def get_empleados_service(db) -> list:
    try:
        empleados = await db.fetch("SELECT * FROM empleados;")
        if not empleados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return [dict(empleado) for empleado in empleados]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def create_empleado_service(empleado: EmpleadoBase, db) -> dict:
    try:
        nuevo_empleado = await db.fetchrow(
            """
            INSERT INTO empleados (nombre, especialidad)
            VALUES ($1, $2)
            RETURNING *;
            """,
            empleado.nombre, empleado.especialidad
        )
        if not nuevo_empleado:
            raise HTTPException(status_code=404, detail="Error al crear el nuevo empleado")
        return dict(nuevo_empleado)
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def update_empleado_service(empleado_id: UUID, empleado: EmpleadoUpdate, db) -> dict:
    try:
        empleado_anterior = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado_anterior:
            raise HTTPException(status_code=404, detail=f"No se encontró al empleado con id {empleado_id}")
        
        if not empleado.nombre:
            empleado.nombre = empleado_anterior["nombre"]
        if not empleado.especialidad:
            empleado.especialidad = empleado_anterior["especialidad"]
        
        empleado_actualizado = await db.fetchrow(
            """
            UPDATE empleados
            SET nombre = $1, especialidad = $2
            WHERE id = $3
            RETURNING *;
            """,
            empleado.nombre, empleado.especialidad, empleado_id
        )
        if not empleado_actualizado:
            raise HTTPException(status_code=404, detail=f"Error al actualizar el empleado con id {empleado_id}")
        return dict(empleado_actualizado)
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def delete_empleado_service(empleado_id: UUID, db) -> dict:
    try:
        resultado = await db.execute("DELETE FROM empleados WHERE id = $1;", empleado_id)
        if resultado == "DELETE 0":
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return {"mensaje": "Empleado eliminado correctamente"}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def get_empleado_by_id_service(empleado_id: UUID, db) -> dict:
    try:
        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail=f"No se encontró al empleado con id {empleado_id}")
        return dict(empleado)
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
