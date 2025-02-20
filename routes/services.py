from fastapi import APIRouter, Depends, HTTPException
from database import get_db

from schemas import ServicioBase, ServicioResponse
from uuid import UUID

from datetime import date

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("/", response_model=list[ServicioResponse])
async def obtener_servicios(db=Depends(get_db)):
    
    try:
        servicios = await db.fetch("SELECT * FROM servicios;")

        if not servicios:
            raise HTTPException(status_code=404, detail=f"No se encontraron servicios")
        
        return [dict(servicio) for servicio in servicios]
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.post("/", response_model=ServicioResponse)
async def crear_servicios (servicio: ServicioBase ,db=Depends(get_db)):
    
    try:

        nuevo_servicio = await db.fetchrow(
        """
            INSERT INTO servicios (nombre, duracion_minutos, precio)
            VALUES ($1, $2, $3)
            RETURNING *;
        """, servicio.nombre, servicio.duracion_minutos, servicio.precio)    

        if not nuevo_servicio:
            raise HTTPException(status_code=404, detail=f"Error al crear el nuevo servicio")
        
        return dict(nuevo_servicio)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.put("/{servicio_id}", response_model=ServicioResponse)
async def actualizar_datos_servicio(servicio_id: UUID, servicio: ServicioBase, db=Depends(get_db)):
    
    try:
        servicio_anterior = await db.fetchrow(" SELECT * FROM servicios where id = $1;", servicio_id)

        if not servicio_anterior:
            raise HTTPException(status_code=404, detail=f"No se encontraro al servicio con id {servicio_id}")
        
        if not servicio.nombre:
            servicio.nombre = servicio_anterior['nombre']
        
        if not servicio.duracion_minutos:
            servicio.duracion_minutos = servicio_anterior['duracion_minutos']
        
        if not servicio.precio:
            servicio.precio = servicio_anterior['precio']


        servicio_actualizado = await db.fetchrow(
        """
            UPDATE servicios
            SET 
                nombre = $1, 
                duracion_minutos = $2,
                precio = $3
            WHERE id = $4 
            RETURNING *;
        """, servicio.nombre, servicio.duracion_minutos, servicio.precio, servicio_id)

        if not servicio_actualizado:
            raise HTTPException(status_code=404, detail=f"Error al actualizar el servicio con id {servicio_id}")
        
        return dict(servicio_actualizado)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

@router.delete("/{servicio_id}")
async def eliminar_servicio(servicio_id: UUID, db=Depends(get_db)):
    
    try:

        resultado = await db.execute(
            "DELETE FROM servicios WHERE id = $1;",
            servicio_id
        )
        
        if resultado == "DELETE 0":  # Si no se eliminó ningún registro
            raise HTTPException(status_code=404, detail=f"servicio no encontrado")
        
        return {"mensaje": "servicio eliminado correctamente"}
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{servicio_id}", response_model=ServicioResponse)
async def obtener_servicio_by_id(servicio_id: UUID, db=Depends(get_db)):
    
    try:
        servicio = await db.fetchrow(" SELECT * FROM servicios where id = $1; ", servicio_id)

        if not servicio:
            raise HTTPException(status_code=404, detail=f"No se encontraro al servicio con id {servicio_id}")
        
        return dict(servicio)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

