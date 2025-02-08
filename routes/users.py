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