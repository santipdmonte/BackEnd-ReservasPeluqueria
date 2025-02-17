from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from schemas import UsuarioResponse, UsuarioBase
from uuid import UUID

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UsuarioResponse)
async def crear_usuario(usuario: UsuarioBase, db=Depends(get_db)):
    
    # Verificar que no exista un usuraio con el mismo numero de telefono
    existe_telefono = await db.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM usuarios 
            WHERE telefono = $1
        );
    """, usuario.telefono)

    if existe_telefono:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese número de teléfono")

    # Verificar que no exista un usuraio con el mismo email
    if usuario.email and usuario.email.strip() and usuario.email != "":
        existe_mail = await db.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM usuarios 
            WHERE email = $1
        );
        """, usuario.email)

        if existe_mail:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    else:
        usuario.email =  None # Validar si es necesario

    # Crear el usuario
    result  = await db.fetchrow("""
        INSERT INTO usuarios (nombre, telefono, email)
        VALUES ($1, $2, $3)
        RETURNING id, nombre, telefono, email;
    """, usuario.nombre, usuario.telefono, usuario.email)
    
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear el usuario")
        
    return dict(result)
    


@router.get("/telefono/{telefono}", response_model=UsuarioResponse)
async def obtener_usuario_by_phone_number(telefono: str, db=Depends(get_db)):
    query = "SELECT * FROM usuarios WHERE telefono = $1"
    user = await db.fetchrow(query, telefono)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user)

@router.get("/historial/{user_id}")
async def obtener_historial_del_usuario(user_id: UUID, db=Depends(get_db)):

    if not await db.fetchrow("SELECT * FROM usuarios WHERE id = $1", user_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    query = """
        SELECT
            turnos.id       as turno_id,
            turnos.fecha    as fecha,
            turnos.hora     as hora,
            u.id            as usuario_id,
            u.nombre        as usuario,
            e.id            as empleado_id,
            e.nombre        as empleado,
            s.id            as servicio_id,
            s.nombre        as servicio
        FROM turnos 
        LEFT JOIN usuarios u ON turnos.usuario_id = u.id
        LEFT JOIN servicios s ON turnos.servicio_id = s.id 
        LEFT JOIN empleados e ON turnos.empleado_id = e.id 
        WHERE  
            turnos.usuario_id = $1
            AND turnos.estado <> 'cancelado'
            AND turnos.fecha < CURRENT_DATE
        ORDER BY turnos.fecha DESC
        LIMIT 6;
    """

    historial_turnos = await db.fetch(query, user_id)
    if not historial_turnos:
        raise HTTPException(status_code=404, detail="El usuario no tiene turnos anteriores")
    
    return [dict(turno) for turno in historial_turnos]