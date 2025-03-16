from uuid import UUID
from schemas import ServicioBase, ServicioUpdate
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError, try_except_closeCursor
from utils.helpers import fetchall_to_dict, fetchone_to_dict

@try_except_closeCursor
def obtener_servicios(db) -> list:

    cursor = db.cursor()
    cursor.execute("SELECT * FROM servicios;") # Where estado =...
    servicios = fetchall_to_dict(cursor)

    if not servicios:
        raise NotFoundError("No se encontraron servicios")
    
    return servicios

@try_except_closeCursor
def crear_servicio(servicio: ServicioBase, db) -> dict:

    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO servicios (nombre, duracion_minutos, precio)
        VALUES (%s, %s, %s)
        RETURNING *;
        """, (servicio.nombre, servicio.duracion_minutos, servicio.precio)
    )
    nuevo_servicio = fetchone_to_dict(cursor)
    db.commit()

    if not nuevo_servicio:
        raise OperationError("Error al crear el nuevo servicio")
    
    return nuevo_servicio


@try_except_closeCursor
def actualizar_servicio(servicio_id: UUID, servicio: ServicioUpdate, db) -> dict:
        
    cursor = db.cursor()
    cursor.execute("SELECT * FROM servicios WHERE id = %s;", (str(servicio_id),))
    servicio_anterior = fetchone_to_dict(cursor)
    if not servicio_anterior:
        raise NotFoundError(f"No se encontró al servicio con id {servicio_id}")

    # Completar campos faltantes con valores anteriores
    if not servicio.nombre:
        servicio.nombre = servicio_anterior["nombre"]
    if not servicio.duracion_minutos:
        servicio.duracion_minutos = servicio_anterior["duracion_minutos"]
    if not servicio.precio:
        servicio.precio = servicio_anterior["precio"]

    cursor.execute(
        """
        UPDATE servicios
        SET nombre = %s, duracion_minutos = %s, precio = %s
        WHERE id = %s
        RETURNING *;
        """, (servicio.nombre, servicio.duracion_minutos, servicio.precio, str(servicio_id))
    )
    servicio_actualizado = fetchone_to_dict(cursor)

    if not servicio_actualizado:
        raise OperationError(f"Error al actualizar el servicio con id {servicio_id}")
    
    db.commit()
    return servicio_actualizado


@try_except_closeCursor
def eliminar_servicio(servicio_id: UUID, db) -> dict:
    
    cursor = db.cursor()
    cursor.execute("DELETE FROM servicios WHERE id = %s;", (str(servicio_id),))
    filas_afectadas = cursor.rowcount

    if filas_afectadas == 0:
        raise NotFoundError("Servicio no encontrado")
    
    db.commit()

    return {"mensaje": "Servicio eliminado correctamente"}


@try_except_closeCursor
def obtener_servicio_by_id(servicio_id: UUID, db) -> dict:

    cursor = db.cursor()
    cursor.execute("SELECT * FROM servicios WHERE id = %s;", (str(servicio_id),))
    servicio = fetchone_to_dict(cursor)

    if not servicio:
        raise NotFoundError(f"No se encontró al servicio con id {servicio_id}")
    
    return servicio
