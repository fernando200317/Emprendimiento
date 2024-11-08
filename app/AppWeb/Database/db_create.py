from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
import re


config = {'host': 'localhost', 'database_name': 'Tutoring', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)

# Crear la sesión de SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def formatear_rut(rut):
    """Formatea el RUT eliminando caracteres no numéricos y agregando guión."""
    clean_rut = re.sub(r'\D', '', rut)  # Eliminar caracteres no numéricos
    return f"{clean_rut[:-1]}-{clean_rut[-1]}" if len(clean_rut) > 1 else rut

def crear_usuario(rut, nombre, email, password, user_type):
    db = SessionLocal()
    try:
        # Validar y formatear datos
        rut_formateado = formatear_rut(rut)
        
        # Generar el hash de la contraseña con `scrypt`
        hashed_password = generate_password_hash(password, method='scrypt')
        print(f"Hashed password to store: {hashed_password}")  # Verificar hash generado

        # Verificar si el RUT ya existe
        if db.execute(text("SELECT 1 FROM usuario WHERE RUT = :rut"), {'rut': rut_formateado}).fetchone():
            return False, "El RUT ya está registrado."

        # Insertar el nuevo usuario en la tabla `usuario`
        db.execute(text("""
            INSERT INTO usuario (RUT, nombre, correo_electronico, contraseña, tipo_usuario)
            VALUES (:rut, :nombre, :email, :password, :user_type)
        """), {
            'rut': rut_formateado,
            'nombre': nombre,
            'email': email,
            'password': hashed_password,
            'user_type': user_type
        })

        # Insertar en `alumno` o `tutor` según el tipo de usuario
        user_table = "alumno" if user_type == "estudiante" else "tutor"
        db.execute(text(f"INSERT INTO {user_table} (RUT) VALUES (:rut)"), {'rut': rut_formateado})

        db.commit()
        return True, "Cuenta creada exitosamente"
    
    except SQLAlchemyError as e:
        db.rollback()
        error_message = f"Error en la base de datos: {str(e)}"
        print(error_message)
        return False, error_message
    
    finally:
        db.close()