from fastapi import APIRouter, Depends, HTTPException
from database import get_db

from schemas import TurnoBase, TurnoResponse, HorarioDisponible, HorarioDisponibleResponse
from uuid import UUID

from datetime import date

router = APIRouter(prefix="/turnos", tags=["Turnos"])

@router.post("/", response_model=TurnoResponse)
async def crear_turno(turno: TurnoBase, db=Depends(get_db)):
    async with db.transaction():

        # Verificar que el horario esté disponible
        disponible = await db.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM horarios_disponibles 
                WHERE fecha = $1 
                AND hora = $2 
                AND empleado_id = $3 
                AND disponible = TRUE
            );
        """, turno.fecha, turno.hora, turno.empleado_id)

        if not disponible:
            raise HTTPException(status_code=400, detail="El horario seleccionado no está disponible")

        result  = await db.fetchrow("""
            INSERT INTO turnos (usuario_id, empleado_id, servicio_id, fecha, hora, estado)
            VALUES ($1, $2, $3, $4, $5, 'confirmado')
            RETURNING id, usuario_id, empleado_id, servicio_id, fecha, hora, estado;
        """, turno.usuario_id, turno.empleado_id, turno.servicio_id, turno.fecha, turno.hora)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al crear el turno")
        
        result_update_horarios  = await db.fetchval("""
            UPDATE horarios_disponibles 
            SET disponible = FALSE 
            WHERE 
                fecha = $1 
                AND hora = $2 
                AND empleado_id = $3;
        """, turno.fecha, turno.hora, turno.empleado_id)
        
        if result_update_horarios == 0:
            raise HTTPException(status_code=400, detail="El horario no está disponible")
        
        return dict(result)
    

@router.get("/{turno_id}", response_model=TurnoResponse)
async def obtener_turno(turno_id: UUID, db=Depends(get_db)):
    query = "SELECT * FROM turnos WHERE id = $1"
    turno = await db.fetchrow(query, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return dict(turno)


@router.put("/{turno_id}")#, response_model=TurnoResponse)
async def cancelar_turno(turno_id: UUID, db=Depends(get_db)):
    async with db.transaction():

        # Verificar si el turno existe
        turno = await db.fetchrow("""
            SELECT * FROM turnos WHERE id = $1;
        """, turno_id)

        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        if turno["estado"] == "cancelado":
            raise HTTPException(status_code=400, detail="El turno ya fue cancelado")

        # Cancelar el turno
        deleted_turno = await db.execute("""
            UPDATE turnos
            SET estado = 'cancelado'
            WHERE id = $1;
        """, turno_id)

        if deleted_turno == 0:
            raise HTTPException(status_code=400, detail="Error al eliminar el turno")
        
        # Liberar el horario del turno
        await db.execute("""
            UPDATE horarios_disponibles
            SET disponible = TRUE
            WHERE fecha = $1 
                AND hora = $2 
                AND empleado_id = $3;
        """, turno["fecha"], turno["hora"], turno["empleado_id"])

        return deleted_turno

@router.get("/disponibles/{fecha}", response_model=list[HorarioDisponibleResponse])
async def horarios_disponibles_by_date(fecha: date, db=Depends(get_db)):
    
    if fecha < date.today():
        raise HTTPException( status_code=400, detail="No se pueden consultar fechas pasadas")

    turnos = await db.fetch("""
        SELECT * FROM horarios_disponibles 
        WHERE  
            disponible = TRUE 
            AND fecha = $1;
    """
    , fecha)

    if not turnos:
        raise HTTPException(status_code=404, detail=f"No se encontraron turnos disponibles para el {fecha}")
    
    return [dict(turno) for turno in turnos]


@router.put("/edit/{turno_id}", response_model=TurnoResponse)
async def modificar_turno(turno_id: UUID, nuevo_turno: TurnoBase, db=Depends(get_db)):
    async with db.transaction():

        # Obtenemos el turno a editar
        turno_anterior = await db.fetchrow("""
            SELECT empleado_id, fecha, hora 
            FROM turnos 
            WHERE id = $1
                AND estado = 'confirmado';
        """, turno_id)
        
        if not turno_anterior:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        # Validamos si el nuevo horario esta disponible
        disponible = await db.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM horarios_disponibles 
                WHERE fecha = $1 
                AND hora = $2 
                AND empleado_id = $3 
                AND disponible = TRUE
            );
        """, nuevo_turno.fecha, nuevo_turno.hora, nuevo_turno.empleado_id)
        
        if not disponible:
            raise HTTPException(status_code=400, detail="El horario seleccionado no está disponible")
        
        # cancelamos el turno anterior
        await db.execute("""
            UPDATE turnos
            SET estado = 'cancelado'
            WHERE id = $1;
        """,turno_id)
        
        # Actualizamos el horario del turno anterior como disponible
        await db.execute("""
            UPDATE horarios_disponibles 
            SET disponible = TRUE 
            WHERE fecha = $1 
            AND hora = $2 
            AND empleado_id = $3;
        """, turno_anterior["fecha"], turno_anterior["hora"], turno_anterior["empleado_id"])

        # Creamos el nuevo turno
        result  = await db.fetchrow("""
            INSERT INTO turnos (usuario_id, empleado_id, servicio_id, fecha, hora, estado)
            VALUES ($1, $2, $3, $4, $5, 'confirmado')
            RETURNING id, usuario_id, empleado_id, servicio_id, fecha, hora, estado;
        """, nuevo_turno.usuario_id, nuevo_turno.empleado_id, nuevo_turno.servicio_id, nuevo_turno.fecha, nuevo_turno.hora)
        
        # Actualizamos el horario del nuevo turno como no disponible
        await db.execute("""
            UPDATE horarios_disponibles 
            SET disponible = FALSE 
            WHERE fecha = $1 
            AND hora = $2 
            AND empleado_id = $3;
        """, nuevo_turno.fecha, nuevo_turno.hora, nuevo_turno.empleado_id)
    
    return await obtener_turno(result["id"], db)


    

@router.get("/user/{user_id}", response_model=list[TurnoResponse])
async def obtener_turnos_by_user(user_id: UUID, db=Depends(get_db)):
    query = "SELECT * FROM turnos WHERE usuario_id = $1 AND estado <> 'cancelado';"
    turnos = await db.fetch(query, user_id)
    if not turnos:
        raise HTTPException(status_code=404, detail="No se encontraron turnos para el usuario")
    return [dict(turno) for turno in turnos]




