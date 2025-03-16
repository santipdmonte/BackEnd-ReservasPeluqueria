from uuid import UUID
from schemas import EmpleadoBase, EmpleadoUpdate
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError, try_except_closeCursor
from utils.helpers import fetchall_to_dict, fetchone_to_dict

@try_except_closeCursor
def obtener_empleados(db) -> list:

    cursor = db.cursor()
    cursor.execute("SELECT * FROM empleados;")
    empleados = fetchall_to_dict(cursor)
    
    if not empleados:
        raise NotFoundError("No se encontraron empleados")

    return empleados
    
@try_except_closeCursor
def crear_empleado(empleado: EmpleadoBase, db) -> dict:
    
    # Validaciones de datos

    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO empleados (nombre, especialidad)
        VALUES (%s, %s)
        RETURNING *;
        """,
        (empleado.nombre, empleado.especialidad)
    )
    nuevo_empleado = fetchone_to_dict(cursor)
    db.commit()

    if not nuevo_empleado:
        raise OperationError("Error al crear el nuevo empleado")

    return nuevo_empleado

@try_except_closeCursor
def actualizar_empleado(empleado_id: UUID, empleado: EmpleadoUpdate, db) -> dict:
    
    empleado_id = str(empleado_id)

    cursor = db.cursor()
    cursor.execute("SELECT * FROM empleados WHERE id = %s;", (empleado_id,))
    empleado_anterior = fetchone_to_dict(cursor)

    if not empleado_anterior:
        raise NotFoundError(f"No se encontró al empleado con id {empleado_id}")

    # Completar los campos que no se actualizan
    empleado.nombre = empleado.nombre or empleado_anterior["nombre"]
    empleado.especialidad = empleado.especialidad or empleado_anterior["especialidad"]

    cursor.execute(
        """
        UPDATE empleados
        SET nombre = %s, especialidad = %s
        WHERE id = %s
        RETURNING *;
        """,
        (empleado.nombre, empleado.especialidad, empleado_id)
    )

    empleado_actualizado = fetchone_to_dict(cursor)
    db.commit()

    if not empleado_actualizado:
        raise OperationError(f"Error al actualizar el empleado con id {empleado_id}")

    return empleado_actualizado

@try_except_closeCursor
def eliminar_empleado(empleado_id: UUID, db) -> dict:

    cursor = db.cursor()
    cursor.execute("DELETE FROM empleados WHERE id = %s;", (str(empleado_id),))
    filas_afectadas = cursor.rowcount

    if filas_afectadas == 0:
        raise NotFoundError("Empleado no encontrado")
    
    db.commit()

    return {"mensaje": "Empleado eliminado correctamente"}

@try_except_closeCursor
def obtener_empleado_by_id(empleado_id: UUID, db) -> dict:
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM empleados WHERE id = %s;", (str(empleado_id),))
    empleado = fetchone_to_dict(cursor)

    if not empleado:
        raise NotFoundError(f"No se encontró al empleado con id {empleado_id}")

    return empleado

