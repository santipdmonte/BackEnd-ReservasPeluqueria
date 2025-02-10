from fastapi import APIRouter, Depends, HTTPException
from database import get_db

from schemas import TurnoBase, TurnoResponse, HorarioDisponible, HorarioDisponibleResponse
from uuid import UUID

from datetime import date

router = APIRouter(prefix="/turnos", tags=["Turnos"])

@router.post("/", response_model=TurnoResponse)
async def crear_turno(turno: TurnoBase, db=Depends(get_db)):

    async with db.transaction():

        # Verificar que el usuario exista
        usuario = await db.fetchrow("SELECT id FROM usuarios WHERE id = $1", turno.usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar que el empleado exista
        empleado = await db.fetchrow("SELECT id FROM empleados WHERE id = $1", turno.empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
        # Verificar que el servicio exista
        servicio = await db.fetchrow("SELECT id FROM servicios WHERE id = $1", turno.servicio_id)
        if not servicio:
            raise HTTPException(status_code=404, detail="Servicio no encontrado") 
        
        # Verifica que la fecha se mayor o igual a la actual
        if turno.fecha < date.today():
            raise HTTPException(status_code=400, detail="La fecha del turno no puede ser menor a la actual")

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

        nuevo_turno   = await db.fetchrow("""
            INSERT INTO turnos (usuario_id, empleado_id, servicio_id, fecha, hora, estado)
            VALUES ($1, $2, $3, $4, $5, 'confirmado')
            RETURNING id, usuario_id, empleado_id, servicio_id, fecha, hora, estado;
        """, turno.usuario_id, turno.empleado_id, turno.servicio_id, turno.fecha, turno.hora)
        
        if not nuevo_turno :
            raise HTTPException(status_code=500, detail="Error al crear el turno")
        
        horario_actualizado  = await db.fetchval("""
            UPDATE horarios_disponibles 
            SET disponible = FALSE 
            WHERE 
                fecha = $1 
                AND hora = $2 
                AND empleado_id = $3
            RETURNING id;
        """, turno.fecha, turno.hora, turno.empleado_id)
        
        if not horario_actualizado:
            raise HTTPException(status_code=400, detail="No se pudo reservar el horario seleccionado")
        
        return dict(nuevo_turno)
    

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


        # Validamos que el turno a editar exista
        turno_anterior = await db.fetchrow("""
            SELECT empleado_id, fecha, hora 
            FROM turnos 
            WHERE id = $1
                AND estado = 'confirmado';
        """, turno_id)
        
        if not turno_anterior:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        # Creamos el nuevo turno
        nuevo_turno = await crear_turno(nuevo_turno, db)

        # cancelamos el turno anterior
        await cancelar_turno(turno_id, db)
    
    return nuevo_turno

    

@router.get("/user/{user_id}", response_model=list[TurnoResponse])
async def obtener_turnos_by_user(user_id: UUID, db=Depends(get_db)):
    try:
        # Validar que el usuario exista
        usuario = await db.fetchrow("SELECT id FROM usuarios WHERE id = $1", user_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener los turnos del usuario
        turnos = await db.fetch("""
            SELECT * FROM turnos 
                WHERE usuario_id = $1 
                AND fecha >= CURRENT_DATE
                AND estado <> 'cancelado';
        """, user_id)

        return [dict(turno) for turno in turnos] if turnos else []
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




