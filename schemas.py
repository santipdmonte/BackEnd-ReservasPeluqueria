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

class UsuarioCreate(UsuarioBase):
    pass  # No requiere ID, se genera automáticamente - Usa el mismo BaseModel para la creaci

class UsuarioResponse(UsuarioBase):
    id: UUID

    class Config:
        from_attributes = True

# ==== Empleado ====
class EmpleadoBase(BaseModel):
    nombre: str
    especialidad: Optional[str] = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoEdit(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    id: UUID

class EmpleadoResponse(EmpleadoBase):
    id: UUID

    class Config:
        from_attributes = True

# ==== Servicio ====
class ServicioBase(BaseModel):
    nombre: str
    duracion_minutos: int
    precio: Decimal

class ServicioCreate(ServicioBase):
    pass

class ServicioEdit(BaseModel):
    nombre: Optional[str] = None
    duracion_minutos: Optional[int] = None
    precio: Optional[Decimal] = None
    id: UUID

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
