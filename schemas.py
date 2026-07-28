from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TrabajoImpresionCreate(BaseModel):
    usuario: str
    hostname: str
    impresora: str
    tipo_conexion: Optional[str] = "USB"
    nombre_documento: str
    total_paginas: int
    fecha_impresion: Optional[datetime] = None

class ConfiguracionDB(BaseModel):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
