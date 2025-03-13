from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import empleados, horarios, servicios, turnos, usuarios
from mangum import Mangum
from exception_handlers import custom_exception_handler, NotFoundError, ValidationError, OperationError, AppException

app = FastAPI(title="API de Peluquería", version="1.0")

app.add_exception_handler(NotFoundError, custom_exception_handler)
app.add_exception_handler(ValidationError, custom_exception_handler)
app.add_exception_handler(OperationError, custom_exception_handler)
app.add_exception_handler(AppException, custom_exception_handler)

app.include_router(turnos.router)
app.include_router(usuarios.router)
app.include_router(empleados.router)
app.include_router(servicios.router)
app.include_router(horarios.router)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen (ajústalo en producción)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)

handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# venv\Scripts\activate
# python -m uvicorn main:app --reload
