from uuid import UUID
from schemas import UsuarioBase, UsuarioUpdate
from exception_handlers import NotFoundError, ValidationError, OperationError, AppException, try_except_closeCursor
from utils.helpers import fetchall_to_dict, fetchone_to_dict

@try_except_closeCursor
def crear_usuario(usuario: UsuarioBase, db) -> dict:
        
    # Verificar que no exista un usuario con el mismo número de teléfono
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT * FROM usuarios 
        WHERE telefono = %s;
        """, (usuario.telefono,)
    )
    existe_telefono = fetchone_to_dict(cursor)
    if existe_telefono:
        raise ValidationError("Ya existe un usuario con ese número de teléfono")
    
    # Verificar que no exista un usuario con el mismo email
    if usuario.email and usuario.email.strip() and usuario.email != "":
        cursor.execute(
            """
            SELECT * FROM usuarios 
            WHERE email = %s;
            """, (usuario.email,)
        )
        existe_mail = fetchone_to_dict(cursor)
        if existe_mail:
            raise ValidationError("Ya existe un usuario con ese email")
    else:
        usuario.email = None  # Se asigna None si no se provee email válido
    
    # Crear el usuario
    cursor.execute(
        """
        INSERT INTO usuarios (nombre, telefono, email)
        VALUES (%s, %s, %s)
        RETURNING id, nombre, telefono, email;
        """, (usuario.nombre, usuario.telefono, usuario.email)
    )
    result = fetchone_to_dict(cursor)
    
    db.commit()
    
    if not result:
        raise OperationError("Error al crear el usuario")
        
    return result


@try_except_closeCursor
def obtener_usuario(user_id: UUID, db) -> dict:
        
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = %s;", (str(user_id),))
    user = fetchone_to_dict(cursor)

    if not user:
        raise NotFoundError("Usuario no encontrado")
    return user


@try_except_closeCursor
def actualizar_usuario(user_id: UUID, usuario_new: UsuarioUpdate, db) -> dict:
        
    # Buscar el usuario a actualizar
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = %s;", (str(user_id),))
    usuario = fetchone_to_dict(cursor)
    
    if not usuario:
        raise NotFoundError(f"No existe usuario con el id ({user_id})")
    
    if not usuario_new.nombre and not usuario_new.email:
        raise ValidationError("Debe enviar al menos un campo para actualizar")
    
    email_actual = usuario['email']
    
    # Validar si el email es diferente y no está vacío
    if usuario_new.email and (usuario_new.email != email_actual or email_actual is None):
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM usuarios 
                WHERE email = %s
            );
            """, (usuario_new.email,)
        )
        existe_email = fetchone_to_dict(cursor)['exists']
        if existe_email:
            raise ValidationError("Ya existe un usuario con ese email")
    
    if not usuario_new.nombre:
        usuario_new.nombre = usuario['nombre']

    if not usuario_new.email:
        usuario_new.email = usuario['email']
    
    # Actualizar el usuario
    cursor.execute(
        """
        UPDATE usuarios 
        SET nombre = %s, email = %s
        WHERE id = %s
        RETURNING *;
        """, (usuario_new.nombre, usuario_new.email, str(user_id))
    )
    result = fetchone_to_dict(cursor)
    
    if not result:
        cursor.close()
        raise OperationError("Error al actualizar el usuario")
    
    db.commit()

    return result


@try_except_closeCursor
def obtener_usuario_por_telefono(telefono: str, db) -> dict:
        
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE telefono = %s;", (telefono,))
    user = fetchone_to_dict(cursor)

    if not user:
        raise NotFoundError("Usuario no encontrado")
    
    return user

@try_except_closeCursor
def obtener_historial_usuario(user_id: UUID, db) -> list:

    cursor = db.cursor()
    
    # Validar que el usuario exista
    cursor.execute("SELECT * FROM usuarios WHERE id = %s;", (str(user_id),))
    result = fetchone_to_dict(cursor)

    if result is None:
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
            turnos.usuario_id = %s
            AND turnos.estado <> 'cancelado'
            AND turnos.fecha < CURRENT_DATE
        ORDER BY turnos.fecha DESC
        LIMIT 6;
    """
    
    cursor.execute(query, (str(user_id),))
    historial_turnos = fetchall_to_dict(cursor)

    if not historial_turnos:
        raise NotFoundError("El usuario no tiene turnos anteriores")
    
    return historial_turnos
