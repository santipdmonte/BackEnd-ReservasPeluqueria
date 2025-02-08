from fastapi import FastAPI
from routes import bookings, users

app = FastAPI(title="API de Peluquería", version="1.0")
app.include_router(bookings.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5432, reload=True)

# venv\Scripts\activate
# python -m uvicorn main:app --reload
