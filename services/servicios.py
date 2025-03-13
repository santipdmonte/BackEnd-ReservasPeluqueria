from uuid import UUID
from schemas import ServicioBase, ServicioUpdate
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError

async def get_servicios_service(db) -> list:
    try:
        servicios = await db.fetch("SELECT * FROM servicios;")
        if not servicios:
            raise NotFoundError("No se encontraron servicios")
        return [dict(servicio) for servicio in servicios]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def create_servicio_service(servicio: ServicioBase, db) -> dict:
    try:
        nuevo_servicio = await db.fetchrow(
            """
            INSERT INTO servicios (nombre, duracion_minutos, precio)
            VALUES ($1, $2, $3)
            RETURNING *;
            """, servicio.nombre, servicio.duracion_minutos, servicio.precio
        )
        if not nuevo_servicio:
            raise OperationError("Error al crear el nuevo servicio")
        return dict(nuevo_servicio)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def update_servicio_service(servicio_id: UUID, servicio: ServicioUpdate, db) -> dict:
    try:
        servicio_anterior = await db.fetchrow("SELECT * FROM servicios WHERE id = $1;", servicio_id)
        if not servicio_anterior:
            raise NotFoundError(f"No se encontró al servicio con id {servicio_id}")

        # Completar campos faltantes con valores anteriores
        if not servicio.nombre:
            servicio.nombre = servicio_anterior["nombre"]
        if not servicio.duracion_minutos:
            servicio.duracion_minutos = servicio_anterior["duracion_minutos"]
        if not servicio.precio:
            servicio.precio = servicio_anterior["precio"]

        servicio_actualizado = await db.fetchrow(
            """
            UPDATE servicios
            SET nombre = $1, duracion_minutos = $2, precio = $3
            WHERE id = $4
            RETURNING *;
            """, servicio.nombre, servicio.duracion_minutos, servicio.precio, servicio_id
        )
        if not servicio_actualizado:
            raise OperationError(f"Error al actualizar el servicio con id {servicio_id}")
        return dict(servicio_actualizado)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def delete_servicio_service(servicio_id: UUID, db) -> dict:
    try:
        resultado = await db.execute("DELETE FROM servicios WHERE id = $1;", servicio_id)
        if resultado == "DELETE 0":
            raise NotFoundError("Servicio no encontrado")
        return {"mensaje": "Servicio eliminado correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")

async def get_servicio_by_id_service(servicio_id: UUID, db) -> dict:
    try:
        servicio = await db.fetchrow("SELECT * FROM servicios WHERE id = $1;", servicio_id)
        if not servicio:
            raise NotFoundError(f"No se encontró al servicio con id {servicio_id}")
        return dict(servicio)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")
