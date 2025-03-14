from uuid import UUID
from schemas import EmpleadoBase, EmpleadoUpdate
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError

async def obtener_empleados(db) -> list:
    try:
        empleados = await db.fetch("SELECT * FROM empleados;")
        if not empleados:
            raise NotFoundError("No se encontraron empleados")
        return [dict(empleado) for empleado in empleados]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def crear_empleado(empleado: EmpleadoBase, db) -> dict:
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
            raise OperationError("Error al crear el nuevo empleado")
        return dict(nuevo_empleado)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def actualizar_empleado(empleado_id: UUID, empleado: EmpleadoUpdate, db) -> dict:
    try:
        empleado_anterior = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado_anterior:
            raise NotFoundError(f"No se encontró al empleado con id {empleado_id}")
        
        # Completar los campos que no se actualizan
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
            raise OperationError(f"Error al actualizar el empleado con id {empleado_id}")
        return dict(empleado_actualizado)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def eliminar_empleado(empleado_id: UUID, db) -> dict:
    try:
        resultado = await db.execute("DELETE FROM empleados WHERE id = $1;", empleado_id)
        if resultado == "DELETE 0":
            raise NotFoundError("Empleado no encontrado")
        return {"mensaje": "Empleado eliminado correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def obtener_empleado_by_id(empleado_id: UUID, db) -> dict:
    try:
        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise NotFoundError(f"No se encontró al empleado con id {empleado_id}")
        return dict(empleado)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")
