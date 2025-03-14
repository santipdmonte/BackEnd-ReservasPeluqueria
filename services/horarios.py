from uuid import UUID
from datetime import date, datetime, timedelta, time
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError

async def generacion_horarios_semanales(db) -> dict:
    try:
        semanas_plazo = 2
        dias_plazo = semanas_plazo * 7

        desplazamiento_dias = {
            "L": 1 + dias_plazo,
            "M": 2 + dias_plazo,
            "X": 3 + dias_plazo,
            "J": 4 + dias_plazo,
            "V": 5 + dias_plazo,
            "S": 6 + dias_plazo,
            "D": 7 + dias_plazo
        }

        # Paso 1: Obtener la programación de horarios
        programacion_horarios = await db.fetch("SELECT * FROM programacion_horarios")
        if not programacion_horarios:
            raise NotFoundError("No se encontró la programación de horarios")

        # Paso 2: Para cada registro, generar los horarios disponibles
        for horario_prog in programacion_horarios:
            dia_programado = horario_prog["dia"]
            hora_inicio = horario_prog["hora_inicio"]
            hora_fin = horario_prog["hora_fin"]
            intervalo = horario_prog["intervalo"]  # en minutos
            empleado_id = horario_prog["empleado_id"]

            if dia_programado not in desplazamiento_dias:
                continue

            # Calcular la fecha destino según el día programado
            fecha = date.today() + timedelta(days=desplazamiento_dias[dia_programado])
            current_datetime = datetime.combine(fecha, hora_inicio)
            end_datetime = datetime.combine(fecha, hora_fin)

            while current_datetime < end_datetime:
                await db.execute(
                    """
                    INSERT INTO horarios_disponibles (fecha, hora, empleado_id, disponible)
                    VALUES ($1, $2, $3, TRUE)
                    ON CONFLICT DO NOTHING;
                    """,
                    fecha, current_datetime.time(), empleado_id
                )
                current_datetime += timedelta(minutes=intervalo)

            # Paso 3: Actualizar horarios que deban bloquearse según la tabla de bloqueos
            await db.execute(
                """
                UPDATE horarios_disponibles
                SET disponible = FALSE
                FROM bloqueos_horarios bh
                WHERE 
                    horarios_disponibles.empleado_id = bh.empleado_id
                    AND horarios_disponibles.fecha = bh.fecha
                    AND horarios_disponibles.hora >= bh.hora_inicio
                    AND horarios_disponibles.hora < bh.hora_fin
                """
            )

        return {"message": "Horarios generados y bloqueos aplicados correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def crear_programacion_horarios(empleado_id: UUID, dia: str, hora_inicio: time, hora_fin: time, intervalo: int, db) -> dict:
    try:
        # Validar que el empleado exista
        if not await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id):
            raise NotFoundError("No se encontró al empleado")
        
        if hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
        
        if intervalo <= 0:
            raise ValidationError("El intervalo debe ser mayor a 0")
        
        if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
            raise ValidationError("El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
        
        # Validar que no se choque con horarios ya programados
        resultado = await db.fetch(
            """
            SELECT * 
            FROM programacion_horarios 
            WHERE 
                empleado_id = $1
                AND dia = $2
                AND hora_inicio < $3
                AND hora_fin > $4;
            """, empleado_id, dia, hora_fin, hora_inicio
        )
        if resultado:
            raise ValidationError("Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programación existente")
        
        # Insertar la programación
        programacion_horarios = await db.fetchrow(
            """
            INSERT INTO programacion_horarios (empleado_id, dia, hora_inicio, hora_fin, intervalo)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *;
            """, empleado_id, dia, hora_inicio, hora_fin, intervalo
        )
        
        return dict(programacion_horarios)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_programacion_horarios(db, empleado_id: UUID = None, dia: str = None) -> list:
    try:
        query = """
            SELECT 
                programacion_horarios.id,
                e.id as empleado_id,
                e.nombre as nombre_empleado, 
                programacion_horarios.dia as dia,
                programacion_horarios.hora_inicio as hora_inicio,
                programacion_horarios.hora_fin as hora_fin,
                programacion_horarios.intervalo as intervalo
            FROM programacion_horarios
            INNER JOIN empleados e ON e.id = programacion_horarios.empleado_id
            """
        
        filtros = []
        parametros = []
        contador_param = 1
        
        if empleado_id:
            empleado_existe = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
            if not empleado_existe:
                raise NotFoundError("No se encontró al empleado")
            filtros.append(f"e.id = ${contador_param}")
            parametros.append(empleado_id)
            contador_param += 1
        
        if dia:
            if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
                raise ValidationError("El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
            filtros.append(f"programacion_horarios.dia = ${contador_param}")
            parametros.append(dia)
            contador_param += 1
        
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        
        query += """
            ORDER BY 
                CASE 
                    WHEN programacion_horarios.dia = 'L' THEN 1
                    WHEN programacion_horarios.dia = 'M' THEN 2
                    WHEN programacion_horarios.dia = 'X' THEN 3
                    WHEN programacion_horarios.dia = 'J' THEN 4
                    WHEN programacion_horarios.dia = 'V' THEN 5
                    WHEN programacion_horarios.dia = 'S' THEN 6
                    WHEN programacion_horarios.dia = 'D' THEN 7
                END,
                programacion_horarios.hora_inicio
            """
        
        programacion_horarios = await db.fetch(query, *parametros)
        return [dict(ph) for ph in programacion_horarios]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def actualizar_programacion_horarios(id: UUID, hora_inicio: time = None, hora_fin: time = None, intervalo: int = None, db=None) -> dict:
    try:
        if not hora_inicio and not hora_fin and not intervalo:
            raise ValidationError("Debe ingresar al menos un campo para actualizar")
        
        programacion = await db.fetchrow("SELECT * FROM programacion_horarios WHERE id = $1;", id)
        if not programacion:
            raise NotFoundError("No se encontró la programación de horarios")
        
        if hora_inicio is None:
            hora_inicio = programacion["hora_inicio"]
        if hora_fin is None:
            hora_fin = programacion["hora_fin"]
        if intervalo is None:
            intervalo = programacion["intervalo"]
        
        if hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
        if intervalo <= 0:
            raise ValidationError("El intervalo debe ser mayor a 0")
        
        resultado = await db.fetch(
            """
            SELECT * 
            FROM programacion_horarios 
            WHERE 
                id != $1
                AND empleado_id = $2
                AND dia = $3
                AND hora_inicio < $4
                AND hora_fin > $5;
            """, id, programacion["empleado_id"], programacion["dia"], hora_fin, hora_inicio
        )
        if resultado:
            raise ValidationError("Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programación existente")
        
        programacion_actualizada = await db.fetchrow(
            """
            UPDATE programacion_horarios
            SET hora_inicio = $1, hora_fin = $2, intervalo = $3
            WHERE id = $4
            RETURNING *;
            """, hora_inicio, hora_fin, intervalo, id
        )
        
        return dict(programacion_actualizada)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def eliminar_programacion_horarios(id: UUID, db) -> dict:
    try:
        resultado = await db.execute("DELETE FROM programacion_horarios WHERE id = $1;", id)
        if resultado == "DELETE 0":
            raise NotFoundError("Programación de horario no encontrada")
        return {"mensaje": "Programación de horario eliminada correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def bloquear_horarios(empleado_id: UUID, fecha: date, hora_inicio: time, hora_fin: time, db) -> dict:
    try:
        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise NotFoundError(f"No se encontró el empleado con id {empleado_id}")
        
        if hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
        
        if fecha < date.today():
            raise ValidationError("La fecha no puede ser anterior a la fecha actual")
        
        horarios = await db.fetch("SELECT * FROM horarios_disponibles WHERE empleado_id = $1 AND fecha = $2;", empleado_id, fecha)
        if not horarios:
            await db.execute(
                """
                INSERT INTO bloqueos_horarios (empleado_id, fecha, hora_inicio, hora_fin)
                VALUES ($1, $2, $3, $4);
                """, empleado_id, fecha, hora_inicio, hora_fin
            )
            return {"mensaje": "Horarios bloqueados guardados correctamente"}
        
        horarios_con_turno = []
        for horario in horarios:
            if not horario["disponible"]:
                turno = await db.fetchrow(
                    """
                    SELECT * FROM turnos 
                    WHERE empleado_id = $1 AND fecha = $2 AND hora = $3 AND estado = 'confirmado';
                    """, empleado_id, fecha, horario["hora"]
                )
                if turno:
                    horarios_con_turno.append(horario)
        
        if horarios_con_turno:
            raise ValidationError(f"En el rango de horarios seleccionado los siguientes horarios están reservados: {horarios_con_turno}. Por favor cancelar los turnos antes de bloquear el horario")
        
        await db.execute(
            """
            UPDATE horarios_disponibles
            SET disponible = FALSE
            WHERE 
                empleado_id = $1
                AND fecha = $2
                AND hora >= $3
                AND hora < $4;
            """, empleado_id, fecha, hora_inicio, hora_fin
        )
        return {"mensaje": "Horarios bloqueados correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def desbloquear_horarios(empleado_id: UUID, fecha: date, hora_inicio: time, hora_fin: time, db) -> dict:
    try:
        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise NotFoundError(f"No se encontró el empleado con id {empleado_id}")
        
        if hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
        
        horarios_bloqueados = await db.fetch(
            """
            SELECT * FROM horarios_disponibles 
            WHERE 
                empleado_id = $1 
                AND fecha = $2 
                AND hora >= $3 
                AND hora < $4
                AND disponible = FALSE;
            """, empleado_id, fecha, hora_inicio, hora_fin
        )
        
        if not horarios_bloqueados:
            bloqueos = await db.fetch(
                """
                SELECT * FROM bloqueos_horarios 
                WHERE 
                    empleado_id = $1 
                    AND fecha = $2
                    AND hora >= $3
                    AND hora < $4;
                """, empleado_id, fecha, hora_inicio, hora_fin
            )
            if bloqueos:
                for bloqueo in bloqueos:
                    await db.execute(
                        """
                        DELETE FROM bloqueos_horarios
                        WHERE id = $1;
                        """, bloqueo["id"]
                    )
                return {"mensaje": "Horarios desbloqueados correctamente"}
            else:
                return {"mensaje": "No hay horarios bloqueados en el rango seleccionado"}
        
        horarios_con_turno = []
        for horario in horarios_bloqueados:
            turno = await db.fetchrow(
                """
                SELECT * FROM turnos 
                WHERE 
                    empleado_id = $1 
                    AND fecha = $2 
                    AND hora = $3 
                    AND estado = 'confirmado';
                """, empleado_id, fecha, horario["hora"]
            )
            if turno:
                horarios_con_turno.append(horario["hora"])
        
        await db.execute(
            """
            UPDATE horarios_disponibles
            SET disponible = TRUE
            WHERE 
                empleado_id = $1
                AND fecha = $2
                AND hora >= $3
                AND hora < $4
                AND hora NOT IN (
                    SELECT hora FROM turnos 
                    WHERE empleado_id = $1 AND fecha = $2 AND estado = 'confirmado'
                );
            """, empleado_id, fecha, hora_inicio, hora_fin
        )
        
        if horarios_con_turno:
            return {
                "mensaje": f"Se desbloquearon los horarios sin turnos asignados. Los siguientes horarios mantienen el bloqueo por tener turnos asignados: {horarios_con_turno}"
            }
        else:
            return {"mensaje": "Todos los horarios seleccionados fueron desbloqueados correctamente"}
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")
