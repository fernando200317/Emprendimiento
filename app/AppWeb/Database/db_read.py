from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash
import re

config = {'host': 'localhost', 'database_name': 'Tutoring', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)
metadata = MetaData()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def formatear_rut(rut):
    """Formatea el RUT para que tenga un formato estándar con guion."""
    rut = re.sub(r'\D', '', rut)  # Eliminar caracteres no numéricos
    if len(rut) > 1:
        return f"{rut[:-1]}-{rut[-1]}"  # Agregar el guion para el dígito verificador
    return rut

def check_password(rut, password):
    db = SessionLocal()
    try:
        query = text("SELECT contraseña FROM usuario WHERE RUT = :rut")
        result = db.execute(query, {'rut': rut})
        hashed_password_row = result.fetchone()

        if hashed_password_row is None:
            print("Usuario no encontrado")
            return False

        hashed_password = hashed_password_row[0]
        print(f"Hashed password from DB: {hashed_password}")  # Imprimir el hash recuperado
        print(f"Entered password: {password}")

        # Comprobar la contraseña usando `check_password_hash`
        if check_password_hash(hashed_password, password):
            print("La contraseña es correcta")
            return True
        else:
            print("La contraseña es incorrecta")
            return False

    except Exception as e:
        print(f"Error en check_password: {e}")
        return False

    finally:
        db.close()

def obtener_informacion_estudiante(rut_alumno):
    """Obtiene la información del estudiante y sus materias."""
    try:
        alumno = db.session.query(alumno).filter_by(RUT=rut_alumno).first()
        if alumno is None:
            return None
        usuario = alumno.usuario
        materias_alumno = alumno.materias
        return usuario.nombre, usuario.RUT, usuario.correo_electronico, materias_alumno
    except Exception as e:
        print(f"Error al obtener información del estudiante: {e}")
        return None