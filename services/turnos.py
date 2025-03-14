from datetime import date
from uuid import UUID
from typing import Optional
from schemas import TurnoBase
from exception_handlers import NotFoundError, ValidationError, OperationError, AppException

async def crear_turno(turno: TurnoBase, db) -> dict:
    try:
        async with db.transaction():
            # Validar que la fecha no sea menor a la actual
            if turno.fecha < date.today():
                raise ValidationError("La fecha del turno no puede ser menor a la actual")

            # Verificar existencia de usuario, empleado y servicio
            usuario = await db.fetchrow("SELECT id FROM usuarios WHERE id = $1", turno.usuario_id)
            if not usuario:
                raise NotFoundError("Usuario no encontrado")

            empleado = await db.fetchrow("SELECT id FROM empleados WHERE id = $1", turno.empleado_id)
            if not empleado:
                raise NotFoundError("Empleado no encontrado")

            servicio = await db.fetchrow("SELECT id FROM servicios WHERE id = $1", turno.servicio_id)
            if not servicio:
                raise NotFoundError("Servicio no encontrado") 

            # Verificar disponibilidad del horario
            disponible = await db.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM horarios_disponibles 
                    WHERE fecha = $1 
                      AND hora = $2 
                      AND empleado_id = $3 
                      AND disponible = TRUE
                );
                """, turno.fecha, turno.hora, turno.empleado_id
            )
            if not disponible:
                raise ValidationError("El horario seleccionado no está disponible")

            # Insertar el nuevo turno
            nuevo_turno = await db.fetchrow(
                """
                INSERT INTO turnos (usuario_id, empleado_id, servicio_id, fecha, hora, estado)
                VALUES ($1, $2, $3, $4, $5, 'confirmado')
                RETURNING id, usuario_id, empleado_id, servicio_id, fecha, hora, estado;
                """, turno.usuario_id, turno.empleado_id, turno.servicio_id, turno.fecha, turno.hora
            )
            if not nuevo_turno:
                raise OperationError("Error al crear el turno")
            
            # Actualizar el horario a no disponible
            horario_actualizado = await db.fetchval(
                """
                UPDATE horarios_disponibles 
                SET disponible = FALSE 
                WHERE fecha = $1 
                  AND hora = $2 
                  AND empleado_id = $3
                RETURNING id;
                """, turno.fecha, turno.hora, turno.empleado_id
            )
            if not horario_actualizado:
                raise OperationError("No se pudo reservar el horario seleccionado")
            
            return dict(nuevo_turno)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_turnos_disponibles(fecha: date, empleado_id: Optional[UUID], db) -> list:
    try:
        if fecha < date.today():
            raise ValidationError("No se pueden consultar fechas pasadas")

        if empleado_id:
            turnos = await db.fetch(
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
                    empleado_id = $1
                    AND disponible = TRUE 
                    AND fecha = $2;
                """, empleado_id, fecha
            )
            if not turnos:
                raise NotFoundError(f"No se encontraron turnos disponibles para el {fecha} con este empleado")
        else:
            turnos = await db.fetch(
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
                  AND fecha = $1;
                """, fecha
            )
            if not turnos:
                raise NotFoundError(f"No se encontraron turnos disponibles para el {fecha}")
        
        return [dict(turno) for turno in turnos]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_turno(turno_id: UUID, db) -> dict:
    try:
        query = "SELECT * FROM turnos WHERE id = $1"
        turno = await db.fetchrow(query, turno_id)
        if not turno:
            raise NotFoundError("Turno no encontrado")
        return dict(turno)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def cancelar_turno(turno_id: UUID, db) -> any:
    try:
        async with db.transaction():
            # Verificar si el turno existe y su estado
            turno = await db.fetchrow("SELECT * FROM turnos WHERE id = $1;", turno_id)
            if not turno:
                raise NotFoundError("Turno no encontrado")
            if turno["estado"] == "cancelado":
                raise ValidationError("El turno ya fue cancelado")

            # Cancelar el turno
            deleted_turno = await db.execute(
                """
                UPDATE turnos
                SET estado = 'cancelado'
                WHERE id = $1;
                """, turno_id
            )
            if deleted_turno == 0:
                raise OperationError("Error al eliminar el turno")
            
            # Liberar el horario reservado
            await db.execute(
                """
                UPDATE horarios_disponibles
                SET disponible = TRUE
                WHERE fecha = $1 
                  AND hora = $2 
                  AND empleado_id = $3;
                """, turno["fecha"], turno["hora"], turno["empleado_id"]
            )

            return deleted_turno
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def modificar_turno(turno_id: UUID, nuevo_turno: TurnoBase, db) -> dict:
    try:
        async with db.transaction():
            # Validar que el turno a editar exista y esté confirmado
            turno_anterior = await db.fetchrow(
                """
                SELECT empleado_id, fecha, hora 
                FROM turnos 
                WHERE id = $1
                  AND estado = 'confirmado';
                """, turno_id
            )
            if not turno_anterior:
                raise NotFoundError("Turno no encontrado")

            # Crear el nuevo turno
            nuevo = await crear_turno(nuevo_turno, db)
            if not nuevo:
                raise OperationError("Error al asignar el nuevo turno")

            # Cancelar el turno anterior
            await cancelar_turno(turno_id, db)

            return nuevo
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_turnos_por_usuario(user_id: UUID, db) -> list:
    try:
        # Verificar que el usuario exista
        usuario = await db.fetchrow("SELECT id FROM usuarios WHERE id = $1", user_id)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")
        
        # Obtener turnos del usuario
        turnos = await db.fetch(
            """
            SELECT * FROM turnos 
            WHERE usuario_id = $1 
              AND fecha >= CURRENT_DATE
              AND estado <> 'cancelado';
            """, user_id
        )
        return [dict(turno) for turno in turnos] if turnos else []
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_turnos_agendados_por_fecha(fecha: date, db) -> list:
    try:
        if fecha < date.today():
            raise ValidationError("No se pueden consultar fechas pasadas")

        turnos = await db.fetch(
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
            WHERE fecha = $1
              AND estado = 'confirmado'
            ORDER BY hora;
            """, fecha
        )
        if not turnos:
            raise NotFoundError(f"No se encontraron turnos agendados para el {fecha}")
        return [dict(turno) for turno in turnos]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")
