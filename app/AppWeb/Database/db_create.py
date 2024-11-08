from sqlite3 import IntegrityError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import re
from Database.db_connect import db_session

config = {'host': 'localhost', 'database_name': 'Tutoring', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)

# Crear la sesión de SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def formatear_rut(rut):
    """Formatea el RUT eliminando caracteres no numéricos y agregando un guión."""
    clean_rut = re.sub(r'\D', '', rut)  # Elimina caracteres no numéricos
    return f"{clean_rut[:-1]}-{clean_rut[-1]}" if len(clean_rut) > 1 else rut

def crear_usuario(rut, username, email, password, tipo_usuario):
    try:
        # Crear usuario en la tabla `usuario`
        db_session.execute(
            text("""
                INSERT INTO usuario (RUT, nombre, correo_electronico, contraseña, tipo_usuario)
                VALUES (:rut, :nombre, :correo_electronico, :contraseña, :tipo_usuario)
            """),
            {'rut': rut, 'nombre': username, 'correo_electronico': email, 'contraseña': password, 'tipo_usuario': tipo_usuario}
        )
        
        # Si el usuario es un estudiante, crear también una entrada en la tabla `alumno`
        if tipo_usuario == 'estudiante':
            db_session.execute(
                text("""
                    INSERT INTO alumno (RUT)
                    VALUES (:rut)
                """),
                {'rut': rut}
            )
        
        db_session.commit()
        return True, "Cuenta creada exitosamente"
    except SQLAlchemyError as e:
        db_session.rollback()
        return False, f"Error al crear cuenta"

