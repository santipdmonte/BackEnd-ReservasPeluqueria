from fastapi import APIRouter, Depends, HTTPException
from database import get_db

from uuid import UUID

from datetime import date, datetime, timedelta, time

router = APIRouter(prefix="/horarios", tags=["Horarios"])


@router.post("/generar_horrarios")
async def generar_horarios_semanales(db=Depends(get_db)):
    """
    Funcion recurrente que genera todos los horarios disponibles el domingo de cada semana
    """
    
    try:
        semanas_plazo = 1 
        dias_plazo = semanas_plazo * 7 + 2

        desplazamiento_dias  = {
                "L": 1 + dias_plazo,
                "M": 2 + dias_plazo,
                "X": 3 + dias_plazo,
                "J": 4 + dias_plazo,
                "V": 5 + dias_plazo,
                "S": 6 + dias_plazo,
                "D": 7 + dias_plazo
            }

        # Paso 1: Obtener los horarios de programacion_horarios
        programacion_horarios = await db.fetch("SELECT * FROM programacion_horarios")
        if not programacion_horarios:
            raise HTTPException(status_code=404, detail="No se encontró la programación de horarios")
        

        # Paso 2: Para cada registro de la programación, generar los horarios disponibles

        for horario_prog in programacion_horarios:

            dia_programado = horario_prog["dia"]
            hora_inicio  = horario_prog["hora_inicio"]
            hora_fin  = horario_prog["hora_fin"]
            intervalo = horario_prog["intervalo"] # En minutos
            empleado_id = horario_prog["empleado_id"]

            if dia_programado not in desplazamiento_dias:
                continue

            # Calcular la fecha destino según el día programado
            fecha = date.today() + timedelta(days=desplazamiento_dias[dia_programado])


            # Combinar la fecha con la hora de inicio y fin para trabajar con objetos datetime
            current_datetime = datetime.combine(fecha, hora_inicio)
            end_datetime = datetime.combine(fecha, hora_fin)

            while current_datetime  < end_datetime:
                await db.execute("""
                    INSERT INTO horarios_disponibles (fecha, hora, empleado_id, disponible)
                    VALUES ($1, $2, $3, TRUE)
                    ON CONFLICT DO NOTHING;
                """, fecha, current_datetime.time(), empleado_id)
                current_datetime += timedelta(minutes=intervalo)

            # Paso 3: Actualizar horarios que deban bloquearse según la tabla de bloqueos
            await db.execute("""
                UPDATE horarios_disponibles
                SET disponible = FALSE
                FROM bloqueos_horarios bh
                WHERE 
                    horarios_disponibles.empleado_id = bh.empleado_id
                    AND horarios_disponibles.fecha = bh.fecha
                    AND horarios_disponibles.hora >= bh.hora_inicio
                    AND horarios_disponibles.hora < bh.hora_fin
            """)

        return {"message": "Horarios generados y bloqueos aplicados correctamente"}
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/")
async def crear_programacion_horarios(
        empleado_id: UUID,
        dia: str,
        hora_inicio: time, 
        hora_fin: time,
        intervalo: int = 30,
        db=Depends(get_db)
    ):

    try:
        # Validar que el empleado exista
        if not await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id):
            raise HTTPException(status_code=404, detail="No se encontró al empleado")
        
        # Validar que la hora de inicio sea menor a la hora de fin
        if hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor a la hora de fin")

        # Validar que el intervalo sea mayor a 0
        if intervalo <= 0:
            raise HTTPException(status_code=400, detail="El intervalo debe ser mayor a 0")
        
        # Validar que el dia sea válido
        if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
            raise HTTPException(status_code=400, detail="El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
        
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
            """, empleado_id, dia, hora_fin, hora_inicio)
        
        if resultado:
            raise HTTPException(status_code=400, detail="Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programacion existente")

        # Insertar la programación
        programacion_horarios = await db.fetchrow(
            """
                INSERT INTO programacion_horarios (empleado_id, dia, hora_inicio, hora_fin, intervalo)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *;
            """, empleado_id, dia, hora_inicio, hora_fin, intervalo)
        
        return dict(programacion_horarios)

    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.get("/")
async def ver_programacion_horarios(
    empleado_id: UUID = None,
    dia: str = None,
    db=Depends(get_db)
):
    try:
        # Consulta base
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
            # Validar que el empleado exista
            empleado_existe = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
            if not empleado_existe:
                raise HTTPException(status_code=404, detail="No se encontró al empleado")
                
            filtros.append(f"e.id = ${contador_param}")
            parametros.append(empleado_id)
            contador_param += 1
            
        if dia:
            # Validar que el dia sea válido
            if dia not in ["L", "M", "X", "J", "V", "S", "D"]:
                raise HTTPException(status_code=400, detail="El día debe ser uno de los siguientes: L, M, X, J, V, S, D")
                
            filtros.append(f"programacion_horarios.dia = ${contador_param}")
            parametros.append(dia)
            contador_param += 1
            
        if filtros:
            query += " WHERE " + " AND ".join(filtros)

                # Agregamos ORDER BY con CASE para ordenar los días correctamente
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
            
        # Debug para ver la consulta y parámetros
        print(query)
        print(parametros)
        
        programacion_horarios = await db.fetch(query, *parametros)
        
        return [dict(ph) for ph in programacion_horarios]
        
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{id}")
async def actualizar_hora_programacion_horarios(
        id: UUID,
        hora_inicio: time = None, 
        hora_fin: time = None,
        intervalo: int = None,
        db=Depends(get_db)
    ):

    try:

        # Validar que se cargo al menos un campo
        if not hora_inicio and not hora_fin and not intervalo:
            raise HTTPException(status_code=400, detail="Debe ingresar al menos un campo para actualizar")

        # Validar que el registro exista
        programacion = await db.fetchrow("SELECT * FROM programacion_horarios WHERE id = $1;", id)
        if not programacion:
            raise HTTPException(status_code=404, detail="No se encontró la programación de horarios")
        
        if hora_inicio is None:
            hora_inicio = programacion["hora_inicio"]
        if hora_fin is None:
            hora_fin = programacion["hora_fin"]
        if intervalo is None:
            intervalo = programacion["intervalo"]

        # Validar que la hora de inicio sea menor a la hora de fin
        if hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor a la hora de fin")
        
        if intervalo <= 0:
            raise HTTPException(status_code=400, detail="El intervalo debe ser mayor a 0")

        # Validar que no se choque con horarios ya programados (con id diferente al actual)
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
            """, id, programacion["empleado_id"], programacion["dia"], hora_fin, hora_inicio)
        
        if resultado:
            raise HTTPException(status_code=400, detail="Ya existe una programación en ese horario, por favor elija otro horario o ajuste la programacion existente")        

        # Actualizar los campos
        programacion_actualizada = await db.fetchrow(
            """
                UPDATE programacion_horarios
                SET 
                    hora_inicio = $1, 
                    hora_fin = $2,
                    intervalo = $3
                WHERE id = $4 
                RETURNING *;
            """, hora_inicio, hora_fin, intervalo, id)
        
        return dict(programacion_actualizada)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{id}")
async def eliminar_programacion_horarios(id: UUID, db=Depends(get_db)):

    # Validar que el registro exista
    try:

        resultado = await db.execute( "DELETE FROM programacion_horarios WHERE id = $1;", id)
        
        if resultado == "DELETE 0":  # Si no se eliminó ningún registro
            raise HTTPException(status_code=404, detail=f"Programacion de horario no encontrada")
        
        return {"mensaje": "Programacion de horario eliminada correctamente"}
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# @router.put("/")
# async def cancelar_turnos():
#     pass

@router.post("/bloquear")
async def bloquear_horarios(
        empleado_id: UUID,
        fecha: date,
        hora_inicio: time = time(0, 0, 0),
        hora_fin: time = time(23, 59, 59),
        db=Depends(get_db)
    ):
    
    try:

        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail=f"No se encontró el empleado con id {empleado_id}")

        if hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor a la hora de fin")
        
        if fecha < date.today():
            raise HTTPException(status_code=400, detail="La fecha no puede ser anterior a la fecha actual")
        

        horarios = await db.fetch("SELECT * FROM horarios_disponibles WHERE empleado_id = $1 AND fecha = $2;", empleado_id, fecha)

        # Validar que los horarios ya esten generados
        if not horarios:
            await db.execute(
            """
                INSERT INTO bloqueos_horarios (empleado_id, fecha, hora_inicio, hora_fin)
                VALUES ($1, $2, $3, $4);
            """, empleado_id, fecha, hora_inicio, hora_fin)

            return {"mensaje": "Horarios de bloqueados guardados correctamente"}
        
        # Validar que los horarios no estén previamente bloqueados
        horarios_con_turno = []
        for horario in horarios:
            if not horario["disponible"] and await db.fetchrow("SELECT * FROM turnos WHERE empleado_id = $1 AND fecha = $2 AND hora = $3 AND estado = 'confirmado';", empleado_id, fecha, horario["hora"]):
                horarios_con_turno.append(horario)
                
        if horarios_con_turno:
            raise HTTPException(status_code=400, detail=f"En el rango de horarios seleccionado los siguientes horarios estan reservados: {horarios_con_turno}. Porfavor cancelar los turnos antes de bloquear el horario")
    
        # Bloquear los horarios
        await db.execute(
            """
            UPDATE horarios_disponibles
            SET disponible = FALSE
            WHERE 
                empleado_id = $1
                AND fecha = $2
                AND hora >= $3
                AND hora < $4;
            """, empleado_id, fecha, hora_inicio, hora_fin)
        
        return {"mensaje": "Horarios bloqueados correctamente"}

    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.post("/desbloquear")
async def desbloquear_horarios(
        empleado_id: UUID,
        fecha: date,
        hora_inicio: time = time(0, 0, 0),
        hora_fin: time = time(23, 59, 59),
        db=Depends(get_db)
    ):
    
    try:
        # Verificar que el empleado existe
        empleado = await db.fetchrow("SELECT * FROM empleados WHERE id = $1;", empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail=f"No se encontró el empleado con id {empleado_id}")

        # Validar horas
        if hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor a la hora de fin")
        
        # Verificar bloqueos existentes
        horarios_bloqueados = await db.fetch(
            """
            SELECT * FROM horarios_disponibles 
            WHERE 
                empleado_id = $1 
                AND fecha = $2 
                AND hora >= $3 
                AND hora < $4
                AND disponible = FALSE;
            """, 
            empleado_id, fecha, hora_inicio, hora_fin
        )
        
        if not horarios_bloqueados:
            # Verificar en la tabla de bloqueos_horarios
            bloqueos = await db.fetch(
                """
                SELECT * FROM bloqueos_horarios 
                WHERE 
                    empleado_id = $1 
                    AND fecha = $2
                    AND hora >= $3
                    AND hora < $4;
                """, 
                empleado_id, fecha, hora_inicio, hora_fin
            )
            
            if bloqueos:
                for bloqueo in bloqueos:
                    await db.execute(
                    """
                        DELETE FROM bloqueos_horarios
                        WHERE id = $1;
                    """, bloqueo["id"])
                
                return {"mensaje": "Horarios desbloqueados correctamente"}
            else:
                return {"mensaje": "No hay horarios bloqueados en el rango seleccionado"}
        
        # Buscar horarios que tienen turnos asignados
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
                """, 
                empleado_id, fecha, horario["hora"]
            )
            if turno:
                horarios_con_turno.append(horario["hora"])
        
        # Desbloquear solo los horarios sin turnos asignados
        await db.execute(
            """
            UPDATE horarios_disponibles
            SET disponible = TRUE
            WHERE 
                empleado_id = $1
                AND fecha = $2
                AND hora >= $3
                AND hora < $4
                AND hora NOT IN (SELECT hora FROM turnos WHERE empleado_id = $1 AND fecha = $2 AND estado = 'confirmado');
            """, 
            empleado_id, fecha, hora_inicio, hora_fin
        )
        
        # Informar si algunos horarios no se pudieron desbloquear por tener turnos
        if horarios_con_turno:
            return {
                "mensaje": f"Se desbloquearon los horarios sin turnos asignados. Los siguientes horarios mantienen el bloqueo por tener turnos asignados: {horarios_con_turno}"
            }
        else:
            return {"mensaje": "Todos los horarios seleccionados fueron desbloqueados correctamente"}

    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")