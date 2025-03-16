from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import date, time
from decimal import Decimal
from typing import Optional


# ==== Usuario (Cliente) ====
class UsuarioBase(BaseModel):
    nombre: str
    telefono: str
    email: Optional[EmailStr] = None  

class UsuarioResponse(UsuarioBase):
    id: UUID

    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None


# ==== Empleado ====
class EmpleadoBase(BaseModel):
    nombre: str
    especialidad: Optional[str] = None

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoResponse(EmpleadoBase):
    id: UUID

    class Config:
        from_attributes = True


# ==== Servicio ====
class ServicioBase(BaseModel):
    nombre: str
    duracion_minutos: int
    precio: Decimal

class ServicioUpdate(BaseModel):
    nombre: Optional[str] = None
    duracion_minutos: Optional[int] = None
    precio: Optional[Decimal] = None

class ServicioResponse(ServicioBase):
    id: UUID

    class Config:
        from_attributes = True


# ==== Turno ====
class TurnoBase(BaseModel):
    usuario_id: UUID
    empleado_id: UUID
    servicio_id: UUID
    fecha: date
    hora: time
    estado: str = Field(default='pendiente', pattern='^(pendiente|confirmado|cancelado)$')

class TurnoResponse(TurnoBase):
    id: UUID

    class Config:
        from_attributes = True

# Modelo de Horario Disponible
class HorarioDisponible(BaseModel):
    fecha: date
    hora: time
    empleado_id: UUID
    disponible: bool = True

class HorarioDisponibleResponse(HorarioDisponible):
    id: UUID

    class Config:
        from_attributes = True
