from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

import models, schemas
from database import db_manager, get_db

app = FastAPI(title="PrintAudit API", version="1.0.0")

# Setup for static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializamos la base de datos al arrancar
db_manager.init_db()

API_KEY = "PrintAuditSecretKey123"

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "db_connected": db_manager.engine is not None}

@app.post("/api/v1/prints", status_code=201)
def create_print_job(
    job: schemas.TrabajoImpresionCreate, 
    db: Session = Depends(get_db), 
    api_key: str = Depends(verify_api_key)
):
    # Obtener o crear Equipo
    equipo = db.query(models.Equipo).filter(models.Equipo.hostname == job.hostname).first()
    if not equipo:
        equipo = models.Equipo(hostname=job.hostname)
        db.add(equipo)
        db.flush()

    # Obtener o crear Usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.username == job.usuario).first()
    if not usuario:
        usuario = models.Usuario(username=job.usuario)
        db.add(usuario)
        db.flush()

    # Obtener o crear Impresora
    impresora = db.query(models.Impresora).filter(models.Impresora.nombre_impresora == job.impresora).first()
    if not impresora:
        impresora = models.Impresora(
            nombre_impresora=job.impresora, 
            tipo_conexion=job.tipo_conexion
        )
        db.add(impresora)
        db.flush()

    # Registrar el Trabajo de Impresión
    nuevo_trabajo = models.TrabajoImpresion(
        equipo_id=equipo.id,
        usuario_id=usuario.id,
        impresora_id=impresora.id,
        nombre_documento=job.nombre_documento,
        total_paginas=job.total_paginas,
        fecha_impresion=job.fecha_impresion or datetime.utcnow()
    )
    db.add(nuevo_trabajo)
    db.commit()
    return {"status": "success", "message": "Trabajo de impresión registrado"}

@app.get("/api/v1/settings/db", response_model=schemas.ConfiguracionDB)
def get_db_settings():
    return db_manager.get_config()

@app.post("/api/v1/settings/db")
def update_db_settings(config: schemas.ConfiguracionDB):
    db_manager.save_config(config.dict())
    # Re-inicializar la conexión de la base de datos
    db_manager.init_db()
    return {"status": "success", "message": "Configuración actualizada. Conexión DB reiniciada."}

from sqlalchemy import func, text
from datetime import timedelta

@app.get("/", response_class=HTMLResponse)
def render_dashboard(request: Request, db: Session = Depends(get_db)):
    db_status = "Inactivo"
    total_pages_sum = 0
    total_jobs = 0

    try:
        # Basic metrics for the dashboard
        total_pages = db.query(models.TrabajoImpresion.total_paginas).all()
        total_pages_sum = sum([p[0] for p in total_pages]) if total_pages else 0
        total_jobs = len(total_pages)
        
        # Test connection explicitly
        db.execute(text("SELECT 1"))
        db_status = "Activo"
    except Exception as e:
        print(f"Database error on dashboard: {e}")
        db_status = "Error de Conexión"
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "total_pages": total_pages_sum,
        "total_jobs": total_jobs,
        "db_status": db_status
    })

@app.get("/api/v1/stats/trend")
def get_trend_stats(db: Session = Depends(get_db)):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=6)
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    try:
        results = db.query(
            func.date(models.TrabajoImpresion.fecha_impresion).label("fecha"),
            func.sum(models.TrabajoImpresion.total_paginas).label("paginas")
        ).filter(models.TrabajoImpresion.fecha_impresion >= start_date)\
         .group_by(func.date(models.TrabajoImpresion.fecha_impresion))\
         .order_by(func.date(models.TrabajoImpresion.fecha_impresion)).all()

        data_dict = {str(r.fecha): int(r.paginas) for r in results}
        data = [data_dict.get(d, 0) for d in dates]
    except Exception as e:
        print(f"DB Error on trend stats: {e}")
        data = [0] * 7
        
    return {"labels": dates, "data": data}

@app.get("/api/v1/stats/printers")
def get_printer_stats(db: Session = Depends(get_db)):
    labels = ["Sin datos"]
    data = [0]
    
    try:
        results = db.query(
            models.Impresora.nombre_impresora,
            func.count(models.TrabajoImpresion.id).label("trabajos")
        ).join(models.TrabajoImpresion).group_by(models.Impresora.nombre_impresora)\
         .order_by(func.count(models.TrabajoImpresion.id).desc()).limit(5).all()
        
        if results:
            labels = [r.nombre_impresora for r in results]
            data = [r.trabajos for r in results]
    except Exception as e:
        print(f"DB Error on printer stats: {e}")
        
    return {"labels": labels, "data": data}

@app.get("/api/v1/export/csv")
def export_csv(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    import io
    import csv
    
    try:
        jobs = db.query(models.TrabajoImpresion).order_by(models.TrabajoImpresion.fecha_impresion.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Fecha', 'Usuario', 'Equipo', 'Impresora', 'Conexion', 'Documento', 'Paginas'])
        
        for job in jobs:
            writer.writerow([
                job.id,
                job.fecha_impresion.strftime('%Y-%m-%d %H:%M:%S') if job.fecha_impresion else '',
                job.usuario.username if job.usuario else '',
                job.equipo.hostname if job.equipo else '',
                job.impresora.nombre_impresora if job.impresora else '',
                job.impresora.tipo_conexion if job.impresora else '',
                job.nombre_documento,
                job.total_paginas
            ])
            
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=registros_impresion.csv"}
        )
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos al exportar")

@app.get("/logs", response_class=HTMLResponse)
def render_logs(request: Request, db: Session = Depends(get_db)):
    jobs = []
    try:
        jobs = db.query(models.TrabajoImpresion).order_by(models.TrabajoImpresion.fecha_impresion.desc()).limit(100).all()
    except Exception as e:
        print(f"Database error on logs: {e}")
    return templates.TemplateResponse(request=request, name="logs.html", context={"jobs": jobs})

@app.get("/settings", response_class=HTMLResponse)
def render_settings(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import FileResponse
    import os
    favicon_path = os.path.join("static", "img", "favicon.png")
    return FileResponse(favicon_path)

if __name__ == "__main__":
    import uvicorn
    # Se expone en el puerto solicitado 9713
    uvicorn.run(app, host="0.0.0.0", port=9713)
