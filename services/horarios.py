from uuid import UUID
from datetime import date, datetime, timedelta, time
from exception_handlers import AppException, NotFoundError, ValidationError, OperationError, try_except_closeCursor
from utils.helpers import fetchall_to_dict, fetchone_to_dict


@try_except_closeCursor
def generacion_horarios_semanales(db) -> dict:
    semanas_plazo = 0
    dias_plazo = semanas_plazo * 7 + 1

    desplazamiento_dias = {
        "L": 1 + dias_plazo,
        "M": 2 + dias_plazo,
        "X": 3 + dias_plazo,
        "J": 4 + dias_plazo,
        "V": 5 + dias_plazo,
        "S": 6 + dias_plazo,
        "D": 7 + dias_plazo
    }

    cursor = db.cursor()

    # Paso 1: Obtener la programación de horarios
    cursor.execute("SELECT * FROM programacion_horarios")
    programacion_horarios = fetchall_to_dict(cursor)
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
            cursor.execute(
                """
                INSERT INTO horarios_disponibles (fecha, hora, empleado_id, disponible)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING;
                """,
                (fecha, current_datetime.time(), empleado_id)
            )
            current_datetime += timedelta(minutes=intervalo)

        # Paso 3: Actualizar horarios que deban bloquearse según la tabla de bloqueos
        cursor.execute(
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
        db.commit()

    return {"message": "Horarios generados y bloqueos aplicados correctamente"}



@try_except_closeCursor
def crear_programacion_horarios(empleado_id: UUID, dia: str, hora_inicio: time, hora_fin: time, intervalo: int, db) -> dict:

    cursor = db.cursor()

    # Validar que el empleado exista
    cursor.execute("SELECT * FROM empleados WHERE id = %s;", (str(empleado_id),))
    if not fetchone_to_dict(cursor):
        raise NotFoundError("No se encontró al empleado")
    
    if hora_inicio >= hora_fin:
        raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
    
    if intervalo <= 0:
        raise ValidationError("El intervalo debe ser mayor a 0")
    
    if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
        raise ValidationError("El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
    
    # Validar que no se choque con horarios ya programados
    cursor.execute(
        """
        SELECT * 
        FROM programacion_horarios 
        WHERE 
            empleado_id = %s
            AND dia = %s
            AND hora_inicio < %s
            AND hora_fin > %s;
        """, (str(empleado_id), dia, hora_fin, hora_inicio)
    )
    resultado = fetchone_to_dict(cursor)
    if resultado:
        raise ValidationError("Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programación existente")
    
    # Insertar la programación
    cursor.execute(
        """
        INSERT INTO programacion_horarios (empleado_id, dia, hora_inicio, hora_fin, intervalo)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
        """, (str(empleado_id), dia, hora_inicio, hora_fin, intervalo)
    )
    programacion_horarios = fetchone_to_dict(cursor)
    db.commit()

    return programacion_horarios



@try_except_closeCursor
def obtener_programacion_horarios(db, empleado_id: UUID = None, dia: str = None) -> list:
    cursor = db.cursor()
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
    parametros = ()
    
    if empleado_id:

        cursor.execute("SELECT * FROM empleados WHERE id = %s;", (str(empleado_id),))
        if not fetchone_to_dict(cursor):
            raise NotFoundError(f"No se encontró al empleado con id: {empleado_id}")
        
        filtros.append(f"e.id = %s")
        parametros += (str(empleado_id),)
    
    if dia:
        if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
            raise ValidationError("El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
        
        filtros.append(f"programacion_horarios.dia = %s")
        parametros += (dia,)
    
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

    cursor.execute(query, parametros)
    programacion_horarios = fetchall_to_dict(cursor)

    return programacion_horarios


@try_except_closeCursor
def actualizar_programacion_horarios(id: UUID, hora_inicio: time = None, hora_fin: time = None, intervalo: int = None, db=None) -> dict:
    if not hora_inicio and not hora_fin and not intervalo:
        raise ValidationError("Debe ingresar al menos un campo para actualizar")
    
    cursor = db.cursor()

    cursor.execute("SELECT * FROM programacion_horarios WHERE id = %s;", (str(id),))
    programacion = fetchone_to_dict(cursor)

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

    cursor.execute(
        """
        SELECT * 
        FROM programacion_horarios 
        WHERE 
            id != %s
            AND empleado_id = %s
            AND dia = %s
            AND hora_inicio < %s
            AND hora_fin > %s;
        """, (str(id), str(programacion["empleado_id"]), programacion["dia"], hora_fin, hora_inicio)
    )
    if fetchone_to_dict(cursor):
        raise ValidationError("Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programación existente")
    
    cursor.execute(
        """
        UPDATE programacion_horarios
        SET hora_inicio = %s, hora_fin = %s, intervalo = %s
        WHERE id = %s
        RETURNING *;
        """, (hora_inicio, hora_fin, intervalo, str(id))
    )
    programacion_actualizada = fetchone_to_dict(cursor)
    db.commit()
    
    return programacion_actualizada


@try_except_closeCursor
def eliminar_programacion_horarios(id: UUID, db) -> dict:
        
    cursor = db.cursor()
    cursor.execute("DELETE FROM programacion_horarios WHERE id = %s RETURNING *;", (str(id),))
    resultado = fetchone_to_dict(cursor)
    if resultado == "DELETE 0":
        cursor.close()
        raise NotFoundError("Programación de horario no encontrada")
    db.commit()
    return {"mensaje": "Programación de horario eliminada correctamente"}


@try_except_closeCursor
def bloquear_horarios(empleado_id: UUID, fecha: date, hora_inicio: time, hora_fin: time, db) -> dict:
        
    cursor = db.cursor()
    cursor.execute("SELECT * FROM empleados WHERE id = %s;", (str(empleado_id),))
    if not fetchone_to_dict(cursor):
        raise NotFoundError(f"No se encontró el empleado con id {empleado_id}")
    
    if hora_inicio >= hora_fin:
        raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
    
    if fecha < date.today():
        raise ValidationError("La fecha no puede ser anterior a la fecha actual")
    
    cursor.execute("SELECT * FROM horarios_disponibles WHERE empleado_id = %s AND fecha = %s;", (str(empleado_id), fecha))
    horarios = fetchall_to_dict(cursor)
    if not horarios:
        cursor.execute(
            """
            INSERT INTO bloqueos_horarios (empleado_id, fecha, hora_inicio, hora_fin)
            VALUES (%s, %s, %s, %s);
            """, (str(empleado_id), fecha, hora_inicio, hora_fin)
        )
        db.commit()
        return {"mensaje": "bloqueo de horarios guardados correctamente"}
    
    horarios_con_turno = []
    for horario in horarios:
        if not horario["disponible"]:
            cursor.execute(
                """
                SELECT * FROM turnos 
                WHERE empleado_id = $1 AND fecha = $2 AND hora = $3 AND estado = 'confirmado';
                """, (str(empleado_id), fecha, horario["hora"])
            )
            turno = fetchone_to_dict(cursor)
            if turno:
                horarios_con_turno.append(horario)
    
    if horarios_con_turno:
        raise ValidationError(f"En el rango de horarios seleccionado los siguientes horarios están reservados: {horarios_con_turno}. Por favor cancelar los turnos antes de bloquear el horario")
    
    cursor.execute(
        """
        UPDATE horarios_disponibles
        SET disponible = FALSE
        WHERE 
            empleado_id = %s
            AND fecha = %s
            AND hora >= %s
            AND hora < %s;
        """, (str(empleado_id), fecha, hora_inicio, hora_fin)
    )
    db.commit()

    return {"mensaje": "Horarios bloqueados correctamente"}


@try_except_closeCursor
def desbloquear_horarios(empleado_id: UUID, fecha: date, hora_inicio: time, hora_fin: time, db) -> dict:

    cursor = db.cursor()
    cursor.execute("SELECT * FROM empleados WHERE id = %s;", (str(empleado_id),))
    empleado = fetchone_to_dict(cursor)
    if not empleado:
        raise NotFoundError(f"No se encontró el empleado con id {empleado_id}")
    
    if hora_inicio >= hora_fin:
        raise ValidationError("La hora de inicio debe ser menor a la hora de fin")
    
    cursor.execute(
        """
        SELECT * FROM horarios_disponibles 
        WHERE 
            empleado_id = %s 
            AND fecha = %s 
            AND hora >= %s 
            AND hora < %s
            AND disponible = FALSE;
        """, (str(empleado_id), fecha, hora_inicio, hora_fin)
    )
    horarios_bloqueados = fetchall_to_dict(cursor)
    
    if not horarios_bloqueados:

        cursor.execute(
            """
            SELECT * FROM bloqueos_horarios 
            WHERE 
                empleado_id = %s 
                AND fecha = %s
                AND hora >= %s
                AND hora < %s;
            """, (str(empleado_id), fecha, hora_inicio, hora_fin)
        )
        bloqueos = fetchall_to_dict(cursor)
        if bloqueos:
            for bloqueo in bloqueos:
                cursor.execute(
                    """
                    DELETE FROM bloqueos_horarios
                    WHERE id = %s;
                    """, (bloqueo["id"],)
                )
            db.commit()
            return {"mensaje": "Horarios desbloqueados correctamente"}
        else:
            return {"mensaje": "No hay horarios bloqueados en el rango seleccionado"}
    
    horarios_con_turno = []
    for horario in horarios_bloqueados:
        cursor.execute(
            """
            SELECT * FROM turnos 
            WHERE 
                empleado_id = %s
                AND fecha = %s 
                AND hora = %s 
                AND estado = 'confirmado';
            """, (str(empleado_id), fecha, horario["hora"])
        )
        turno = fetchone_to_dict(cursor)
        if turno:
            horarios_con_turno.append(horario["hora"])
    
    db.execute(
        """
        UPDATE horarios_disponibles
        SET disponible = TRUE
        WHERE 
            empleado_id = %s
            AND fecha = %s
            AND hora >= %s
            AND hora < %s
            AND hora NOT IN (
                SELECT hora FROM turnos 
                WHERE empleado_id = %s AND fecha = %s AND estado = 'confirmado'
            );
        """, (str(empleado_id), fecha, hora_inicio, hora_fin, str(empleado_id), fecha)
    )
    db.commit()
    
    if horarios_con_turno:
        return {
            "mensaje": f"Se desbloquearon los horarios sin turnos asignados. Los siguientes horarios mantienen el bloqueo por tener turnos asignados: {horarios_con_turno}"
        }
    else:
        return {"mensaje": "Todos los horarios seleccionados fueron desbloqueados correctamente"}