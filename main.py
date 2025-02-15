from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import bookings, users
from mangum import Mangum

app = FastAPI(title="API de Peluquería", version="1.0")
app.include_router(bookings.router)
app.include_router(users.router)

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
    uvicorn.run("main:app", host="0.0.0.0", port=5432, reload=True)

# venv\Scripts\activate
# python -m uvicorn main:app --reload
