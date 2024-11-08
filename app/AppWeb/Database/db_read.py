from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import re

# Configuración de conexión a la base de datos
config = {'host': 'localhost', 'database_name': 'Tutoring', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)

# Crear el sessionmaker y la sesión de alcance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def formatear_rut(rut):
    """Formatea el RUT para que tenga un formato estándar con guion."""
    rut = re.sub(r'\D', '', rut)  # Eliminar caracteres no numéricos
    if len(rut) > 1:
        return f"{rut[:-1]}-{rut[-1]}"  # Agregar el guion para el dígito verificador
    return rut

def check_password(rut, password):
    """Verificación de contraseña en la base de datos sin hash."""
    rut = formatear_rut(rut)  # Asegurar que el RUT esté formateado
    query = text("SELECT contraseña FROM usuario WHERE RUT = :rut")
    result = db_session.execute(query, {'rut': rut}).fetchone()
    return result and result[0] == password

def obtener_tipo_usuario(rut):
    """Obtiene el tipo de usuario (tutor o alumno) basado en el RUT."""
    rut = formatear_rut(rut)  # Asegurar que el RUT esté formateado
    query = text("SELECT tipo_usuario FROM usuario WHERE RUT = :rut")
    result = db_session.execute(query, {'rut': rut}).fetchone()
    return result[0] if result else None

# Función para cerrar la sesión al final de cada solicitud
def shutdown_session(exception=None):
    db_session.remove()
