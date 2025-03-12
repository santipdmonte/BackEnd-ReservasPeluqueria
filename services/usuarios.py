from fastapi import HTTPException
from uuid import UUID
from schemas import UsuarioResponse, UsuarioBase, UsuarioUpdate

async def create_usuario_service(usuario: UsuarioBase, db) -> dict:
    # Verificar que no exista un usuario con el mismo número de teléfono
    existe_telefono = await db.fetchval(
        """
        SELECT EXISTS (
            SELECT 1 FROM usuarios 
            WHERE telefono = $1
        );
        """, usuario.telefono
    )
    if existe_telefono:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese número de teléfono")
    
    # Verificar que no exista un usuario con el mismo email
    if usuario.email and usuario.email.strip() and usuario.email != "":
        existe_mail = await db.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM usuarios 
                WHERE email = $1
            );
            """, usuario.email
        )
        if existe_mail:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    else:
        usuario.email = None  # Se asigna None si no se provee email válido
    
    # Crear el usuario
    result = await db.fetchrow(
        """
        INSERT INTO usuarios (nombre, telefono, email)
        VALUES ($1, $2, $3)
        RETURNING id, nombre, telefono, email;
        """, usuario.nombre, usuario.telefono, usuario.email
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear el usuario")
        
    return dict(result)


async def update_usuario_service(usuario_new: UsuarioUpdate, db) -> dict:
    try:
        # Buscar el usuario a actualizar
        usuario = await db.fetchrow("SELECT * FROM usuarios WHERE id = $1;", usuario_new.id)
        if not usuario:
            raise HTTPException(status_code=400, detail=f"No existe usuario con el id ({usuario_new.id})")
        
        if not usuario_new.nombre and not usuario_new.email:
            raise HTTPException(status_code=400, detail="Debe enviar al menos un campo para actualizar")
        
        email_actual = usuario.get('email')
        
        # Validar si el email es diferente y no está vacío
        if usuario_new.email and (usuario_new.email != email_actual or email_actual is None):
            existe_email = await db.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM usuarios 
                    WHERE email = $1
                );
                """, usuario_new.email
            )
            if existe_email:
                raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
        
        if not usuario_new.nombre:
            usuario_new.nombre = usuario['nombre']
        
        # Actualizar el usuario
        result = await db.fetchrow(
            """
            UPDATE usuarios 
            SET 
                nombre = $1, 
                email = $2
            WHERE 
                id = $3
            RETURNING *;
            """, usuario_new.nombre, usuario_new.email, usuario_new.id
        )
            
        return dict(result)
    
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_usuario_by_phone_service(telefono: str, db) -> dict:
    query = "SELECT * FROM usuarios WHERE telefono = $1"
    user = await db.fetchrow(query, telefono)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user)


async def get_historial_del_usuario_service(user_id: UUID, db) -> list:
    # Validar que el usuario exista
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
