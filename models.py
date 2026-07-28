from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Equipo(Base):
    __tablename__ = "equipos"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    trabajos = relationship("TrabajoImpresion", back_populates="equipo")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trabajos = relationship("TrabajoImpresion", back_populates="usuario")

class Impresora(Base):
    __tablename__ = "impresoras"
    id = Column(Integer, primary_key=True, index=True)
    nombre_impresora = Column(String(255), nullable=False)
    tipo_conexion = Column(String(50)) # 'USB' o 'Red'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trabajos = relationship("TrabajoImpresion", back_populates="impresora")

class TrabajoImpresion(Base):
    __tablename__ = "trabajos_impresion"
    id = Column(Integer, primary_key=True, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    impresora_id = Column(Integer, ForeignKey("impresoras.id"))
    nombre_documento = Column(Text)
    total_paginas = Column(Integer, default=1)
    fecha_impresion = Column(DateTime, index=True, default=datetime.datetime.utcnow)

    equipo = relationship("Equipo", back_populates="trabajos")
    usuario = relationship("Usuario", back_populates="trabajos")
    impresora = relationship("Impresora", back_populates="trabajos")
