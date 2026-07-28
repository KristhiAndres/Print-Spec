import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        # Quitamos self.init_db() de aquí para llamarlo manualmente después de cargar los modelos

    def get_config(self):
        if not os.path.exists(CONFIG_PATH):
            return {
                "db_host": "127.0.0.1",
                "db_port": 3306,
                "db_user": "root",
                "db_password": "",
                "db_name": "printaudit"
            }
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

    def save_config(self, config_data):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)

    def build_connection_string(self, config=None, include_db=True):
        if config is None:
            config = self.get_config()
        
        user = config.get("db_user", "root")
        password = config.get("db_password", "")
        host = config.get("db_host", "127.0.0.1")
        port = config.get("db_port", 3306)
        db_name = config.get("db_name", "printaudit")

        auth = f"{user}:{password}" if password else user
        
        if include_db:
            return f"mysql+pymysql://{auth}@{host}:{port}/{db_name}"
        else:
            return f"mysql+pymysql://{auth}@{host}:{port}"

    def init_db(self):
        # Primero intentamos conectarnos sin especificar la base de datos para crearla si no existe
        base_url = self.build_connection_string(include_db=False)
        config = self.get_config()
        db_name = config.get("db_name", "printaudit")
        
        try:
            temp_engine = create_engine(base_url)
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            temp_engine.dispose()
        except Exception as e:
            print(f"No se pudo crear la base de datos (puede que ya exista o credenciales inválidas): {e}")

        # Ahora creamos el engine principal
        db_url = self.build_connection_string()
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Crear las tablas si no existen (importamos models localmente para evitar circular import)
        try:
            import models
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            print(f"Error al crear las tablas (verificar credenciales): {e}")

    def get_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

# Necesitamos importar 'text' para el execute directo
from sqlalchemy import text

db_manager = DatabaseManager()

def get_db():
    yield from db_manager.get_session()
