from datetime import date
from uuid import UUID
from typing import Optional
from schemas import TurnoBase
from exception_handlers import transactional, NotFoundError, ValidationError, OperationError, AppException, try_except_closeCursor
from utils.helpers import fetchall_to_dict, fetchone_to_dict

@transactional
def crear_turno(turno: TurnoBase, db) -> dict:
  
    cursor = db.cursor()

    # Validar que la fecha no sea menor a la actual
    if turno.fecha < date.today():
        raise ValidationError("La fecha del turno no puede ser menor a la actual")

    # Verificar existencia de usuario, empleado y servicio
    cursor.execute("SELECT id FROM usuarios WHERE id = %s", (str(turno.usuario_id),))
    if not fetchone_to_dict(cursor):
        raise NotFoundError("Usuario no encontrado")

    cursor.execute("SELECT id FROM empleados WHERE id = %s", (str(turno.empleado_id),))
    if not fetchone_to_dict(cursor):
        raise NotFoundError("Empleado no encontrado")

    cursor.execute("SELECT id FROM servicios WHERE id = %s", (str(turno.servicio_id),))
    if not fetchone_to_dict(cursor):
        raise NotFoundError("Servicio no encontrado") 

    # Verificar disponibilidad del horario
    cursor.execute(
        """
        SELECT * FROM horarios_disponibles 
        WHERE fecha = %s 
            AND hora = %s 
            AND empleado_id = %s 
            AND disponible = TRUE
        """, (turno.fecha, turno.hora, str(turno.empleado_id))
    )
    disponible = fetchone_to_dict(cursor)

    if not disponible:
        raise ValidationError("El horario seleccionado no está disponible")

    # Insertar el nuevo turno
    cursor.execute(
        """
        INSERT INTO turnos (usuario_id, empleado_id, servicio_id, fecha, hora, estado)
        VALUES (%s, %s, %s, %s, %s, 'confirmado')
        RETURNING id, usuario_id, empleado_id, servicio_id, fecha, hora, estado;
        """, (str(turno.usuario_id), str(turno.empleado_id), str(turno.servicio_id), turno.fecha, turno.hora)
    )
    nuevo_turno = fetchone_to_dict(cursor)
    if not nuevo_turno:
        raise OperationError("Error al crear el turno")
    
    # Actualizar el horario a no disponible
    cursor.execute(
        """
        UPDATE horarios_disponibles 
        SET disponible = FALSE 
        WHERE fecha = %s 
            AND hora = %s 
            AND empleado_id = %s
        RETURNING id;
        """, (turno.fecha, turno.hora, str(turno.empleado_id))
    )
    horario_actualizado = fetchone_to_dict(cursor)
    if not horario_actualizado:
        raise OperationError("No se pudo reservar el horario seleccionado")
    
    return nuevo_turno


@try_except_closeCursor
def obtener_turnos_disponibles(fecha: date, empleado_id: Optional[UUID], db) -> list:
        
    if fecha < date.today():
        raise ValidationError("No se pueden consultar fechas pasadas")

    cursor = db.cursor()

    if empleado_id:
        cursor.execute(
            """
            SELECT 
                fecha,
                hora,
                empleado_id,
                e.nombre as nombre_empleado,
                horarios_disponibles.id as id_reserva,
                disponible
            FROM horarios_disponibles
            INNER JOIN empleados e ON horarios_disponibles.empleado_id = e.id
            WHERE 
                empleado_id = %s
                AND disponible = TRUE 
                AND fecha = %s;
            """, (str(empleado_id), fecha)
        )
        turnos = fetchall_to_dict(cursor)
        if not turnos:
            raise NotFoundError(f"No se encontraron turnos disponibles para el {fecha} con este empleado")
    else:
        cursor.execute(
            """
            SELECT 
                fecha,
                hora,
                empleado_id,
                e.nombre as nombre_empleado,
                horarios_disponibles.id as id_reserva,
                disponible
            FROM horarios_disponibles
            INNER JOIN empleados e ON horarios_disponibles.empleado_id = e.id
            WHERE disponible = TRUE 
                AND fecha = %s;
            """, (fecha,)
        )
        turnos = fetchall_to_dict(cursor)
        if not turnos:
            raise NotFoundError(f"No se encontraron turnos disponibles para el {fecha}")
    
    return turnos


@try_except_closeCursor
def obtener_turno(turno_id: UUID, db) -> dict:

    cursor = db.cursor()
    cursor.execute("SELECT * FROM turnos WHERE id = %s", (str(turno_id),))
    turno = fetchone_to_dict(cursor)    
    if not turno:
        raise NotFoundError("Turno no encontrado")
    return turno


@transactional
def cancelar_turno(turno_id: UUID, db) -> any:

    cursor = db.cursor()

    # Verificar si el turno existe y su estado
    cursor.execute("SELECT * FROM turnos WHERE id = %s;", (str(turno_id),))
    turno = fetchone_to_dict(cursor)
    if not turno:
        raise NotFoundError("Turno no encontrado")
    if turno["estado"] == "cancelado":
        raise ValidationError("El turno ya fue cancelado")

    # Cancelar el turno
    cursor.execute(
        """
        UPDATE turnos
        SET estado = 'cancelado'
        WHERE id = %s;
        """, (str(turno_id),)
    )
    deleted_turno = fetchone_to_dict(cursor)
    if not deleted_turno:
        raise OperationError("Error al eliminar el turno")
    
    # Liberar el horario reservado
    cursor.execute(
        """
        UPDATE horarios_disponibles
        SET disponible = TRUE
        WHERE fecha = %s 
            AND hora = %s 
            AND empleado_id = %s;
        """, (turno["fecha"], turno["hora"], str(turno["empleado_id"]))
    )

    return deleted_turno


@transactional
def modificar_turno(turno_id: UUID, nuevo_turno: TurnoBase, db) -> dict:

    cursor = db.cursor()

    # Validar que el turno a editar exista y esté confirmado
    cursor.execute(
        """
        SELECT empleado_id, fecha, hora 
        FROM turnos 
        WHERE id = %s
            AND estado = 'confirmado';
        """, (str(turno_id),)
    )
    turno_anterior = fetchone_to_dict(cursor)
    if not turno_anterior:
        raise NotFoundError("Turno no encontrado")

    # Crear el nuevo turno
    nuevo_turno = crear_turno(nuevo_turno, db)
    if not nuevo_turno:
        raise OperationError("Error al asignar el nuevo turno")

    # Cancelar el turno anterior
    cancelar_turno(turno_id, db)

    return nuevo_turno


@try_except_closeCursor
def obtener_turnos_por_usuario(user_id: UUID, db) -> list:
        
    cursor = db.cursor()

    # Verificar que el usuario exista
    cursor.execute("SELECT id FROM usuarios WHERE id = %s", (str(user_id),))
    usuario = fetchone_to_dict(cursor)
    if not usuario:
        raise NotFoundError("Usuario no encontrado")
    
    # Obtener turnos del usuario
    cursor.execute(
        """
        SELECT * FROM turnos 
        WHERE usuario_id = %s 
            AND fecha >= CURRENT_DATE
            AND estado <> 'cancelado';
        """, (str(user_id),)
    )
    turnos = fetchall_to_dict(cursor)
    if not turnos:
        raise NotFoundError("No se encontraron turnos para este usuario")

    return turnos


@try_except_closeCursor
def obtener_turnos_agendados_por_fecha(fecha: date, db) -> list:
    if fecha < date.today():
        raise ValidationError("No se pueden consultar fechas pasadas")

    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            usuario_id, 
            u.telefono,
            u.email,
            hora,
            u.nombre as nombre_usuario,
            s.nombre as servicio,
            e.nombre as nombre_empleado
        FROM turnos
        LEFT JOIN usuarios u ON turnos.usuario_id = u.id 
        LEFT JOIN servicios s ON turnos.servicio_id = s.id
        LEFT JOIN empleados e ON turnos.empleado_id = e.id
        WHERE fecha = %s
            AND estado = 'confirmado'
        ORDER BY hora;
        """, (fecha,)
    )
    turnos = fetchall_to_dict(cursor)
    if not turnos:
        raise NotFoundError(f"No se encontraron turnos agendados para el {fecha}")
    return turnos
