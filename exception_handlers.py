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
