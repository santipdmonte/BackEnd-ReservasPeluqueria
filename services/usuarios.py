from uuid import UUID
from schemas import UsuarioBase, UsuarioUpdate
from exception_handlers import NotFoundError, ValidationError, OperationError, AppException

async def crear_usuario(usuario: UsuarioBase, db) -> dict:
    try:
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
            raise ValidationError("Ya existe un usuario con ese número de teléfono")
        
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
                raise ValidationError("Ya existe un usuario con ese email")
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
            raise OperationError("Error al crear el usuario")
            
        return dict(result)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_usuario(user_id: UUID, db) -> dict:
    try:
        query = "SELECT * FROM usuarios WHERE id = $1"
        user = await db.fetchrow(query, user_id)
        if not user:
            raise NotFoundError("Usuario no encontrado")
        return dict(user)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def actualizar_usuario(usuario_new: UsuarioUpdate, db) -> dict:
    try:
        # Buscar el usuario a actualizar
        usuario = await db.fetchrow("SELECT * FROM usuarios WHERE id = $1;", usuario_new.id)
        if not usuario:
            raise NotFoundError(f"No existe usuario con el id ({usuario_new.id})")
        
        if not usuario_new.nombre and not usuario_new.email:
            raise ValidationError("Debe enviar al menos un campo para actualizar")
        
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
                raise ValidationError("Ya existe un usuario con ese email")
        
        if not usuario_new.nombre:
            usuario_new.nombre = usuario['nombre']
        
        # Actualizar el usuario
        result = await db.fetchrow(
            """
            UPDATE usuarios 
            SET nombre = $1, email = $2
            WHERE id = $3
            RETURNING *;
            """, usuario_new.nombre, usuario_new.email, usuario_new.id
        )
        if not result:
            raise OperationError("Error al actualizar el usuario")
        return dict(result)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_usuario_por_telefono(telefono: str, db) -> dict:
    try:
        query = "SELECT * FROM usuarios WHERE telefono = $1"
        user = await db.fetchrow(query, telefono)
        if not user:
            raise NotFoundError("Usuario no encontrado")
        return dict(user)
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")


async def obtener_historial_usuario(user_id: UUID, db) -> list:
    try:
        # Validar que el usuario exista
        if not await db.fetchrow("SELECT * FROM usuarios WHERE id = $1", user_id):
            raise NotFoundError("Usuario no encontrado")
        
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
            raise NotFoundError("El usuario no tiene turnos anteriores")
        
        return [dict(turno) for turno in historial_turnos]
    except AppException as ae:
        raise ae
    except Exception as e:
        raise OperationError(f"Error interno: {str(e)}")
