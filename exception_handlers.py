from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class AppException(Exception):
    """Excepción base para errores de la aplicación."""
    pass

class NotFoundError(AppException):
    """Excepción para recursos no encontrados."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ValidationError(AppException):
    """Excepción para errores de validación."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class OperationError(AppException):
    """Excepción para errores en operaciones (crear, actualizar, eliminar, etc.)."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


async def custom_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones."""
    if isinstance(exc, NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})
    elif isinstance(exc, ValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.message})
    elif isinstance(exc, OperationError):
        return JSONResponse(status_code=500, content={"detail": exc.message})
    elif isinstance(exc, AppException):
        return JSONResponse(status_code=500, content={"detail": exc.message})
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# Decorator para manejar transacciones
from functools import wraps

def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = kwargs.get("db")  # Obtenemos la conexión de los argumentos
        if not db:
            raise ValueError("Se requiere una conexión a la base de datos")
        
        cursor = None  # Variable para rastrear el cursor

        try:
            # Ejecutamos la función que contiene la lógica SQL
            result = func(*args, **kwargs)
            
            db.commit()  # Confirmamos la transacción
            return result
        except Exception as e:
            db.rollback()  # Revertimos los cambios si hay error
            raise OperationError(f"Error en la transacción: {str(e)}")
        finally:
            if cursor and not cursor.closed:  
                cursor.close()  # Cerramos el cursor si aún está abierto

    return wrapper

def try_except_closeCursor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        
        cursor = None  # Variable para rastrear el cursor

        try:
            # Ejecutamos la función que contiene la lógica SQL
            result = func(*args, **kwargs)
            
            return result

        except AppException as ae:
            raise ae
        except Exception as e:
            raise OperationError(f"Error interno: {str(e)}")
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    return wrapper
