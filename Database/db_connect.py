from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Time, Date, text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import time, date

# Configuración de conexión a la base de datos
config = {'host': 'localhost', 'database_name': 'Tutoring', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}:3307/{config["database_name"]}', echo=False)

# Crear la base de datos si no existe
with engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {config['database_name']}"))

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuario"

    RUT = Column(String(12), primary_key=True, index=True)
    nombre = Column(String(100))
    correo_electronico = Column(String(100), unique=True)
    contraseña = Column(String(100))
    tipo_usuario = Column(String(100))

    tutor = relationship("Tutor", back_populates="usuario", uselist=False)
    alumno = relationship("Alumno", back_populates="usuario", uselist=False)

class Tutor(Base):
    __tablename__ = "tutor"

    RUT = Column(String(12), ForeignKey("usuario.RUT"), primary_key=True)
    usuario = relationship("Usuario", back_populates="tutor")
    materias = relationship("Materia", secondary="tutor_materia", back_populates="tutores")
    tutorias = relationship("Tutoria", back_populates="tutor")

class Alumno(Base):
    __tablename__ = "alumno"

    RUT = Column(String(12), ForeignKey("usuario.RUT"), primary_key=True)
    usuario = relationship("Usuario", back_populates="alumno")
    materias = relationship("Materia", secondary="alumno_materia", back_populates="alumnos")
    tutorias = relationship("Tutoria", secondary="alumno_tutoria", back_populates="alumnos")

class Materia(Base):
    __tablename__ = "materia"

    ID_materia = Column(Integer, primary_key=True, index=True)
    nombre_materia = Column(String(100))
    descripcion = Column(String(100))

    tutores = relationship("Tutor", secondary="tutor_materia", back_populates="materias")
    alumnos = relationship("Alumno", secondary="alumno_materia", back_populates="materias")
    horarios = relationship("Horario", secondary="materia_horario", back_populates="materias")
    repositorio = relationship("Repositorio", back_populates="materia", uselist=False)
    tutorias = relationship("Tutoria", back_populates="materia")

class Horario(Base):
    __tablename__ = "horario"

    ID_horario = Column(Integer, primary_key=True, index=True)
    dia = Column(String(100))
    hora_inicio = Column(Time)
    hora_fin = Column(Time)

    materias = relationship("Materia", secondary="materia_horario", back_populates="horarios")
    tutorias = relationship("Tutoria", back_populates="horario")

class Tutoria(Base):
    __tablename__ = "tutoria"

    ID_tutoria = Column(Integer, primary_key=True, index=True)
    RUT_tutor = Column(String(12), ForeignKey("tutor.RUT"))
    ID_horario = Column(Integer, ForeignKey("horario.ID_horario"))
    ID_materia = Column(Integer, ForeignKey("materia.ID_materia"))
    fecha = Column(Date)

    tutor = relationship("Tutor", back_populates="tutorias")
    alumnos = relationship("Alumno", secondary="alumno_tutoria", back_populates="tutorias")
    horario = relationship("Horario", back_populates="tutorias")
    materia = relationship("Materia", back_populates="tutorias")

class Repositorio(Base):
    __tablename__ = "repositorio"

    ID_repositorio = Column(Integer, primary_key=True, index=True)
    ID_materia = Column(Integer, ForeignKey("materia.ID_materia"))
    contenido = Column(String(1000))

    materia = relationship("Materia", back_populates="repositorio")

# Tablas intermedias para relaciones N:M
class TutorMateria(Base):
    __tablename__ = "tutor_materia"
    RUT_tutor = Column(String(12), ForeignKey("tutor.RUT"), primary_key=True)
    ID_materia = Column(Integer, ForeignKey("materia.ID_materia"), primary_key=True)

class AlumnoMateria(Base):
    __tablename__ = "alumno_materia"
    RUT_alumno = Column(String(12), ForeignKey("alumno.RUT"), primary_key=True)
    ID_materia = Column(Integer, ForeignKey("materia.ID_materia"), primary_key=True)

class MateriaHorario(Base):
    __tablename__ = "materia_horario"
    ID_materia = Column(Integer, ForeignKey("materia.ID_materia"), primary_key=True)
    ID_horario = Column(Integer, ForeignKey("horario.ID_horario"), primary_key=True)

# Tabla intermedia para la relación muchos a muchos entre Alumno y Tutoria
class AlumnoTutoria(Base):
    __tablename__ = "alumno_tutoria"
    RUT_alumno = Column(String(12), ForeignKey("alumno.RUT"), primary_key=True)
    ID_tutoria = Column(Integer, ForeignKey("tutoria.ID_tutoria"), primary_key=True)

# Crear todas las tablas en la base de datos
Base.metadata.create_all(engine)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

#Datos de prueba

def crear_datos_prueba():
    """Crea datos de prueba en la base de datos."""

    # Usuarios
    usuario1 = Usuario(RUT="12345678-9", nombre="Juan Perez", correo_electronico="juan@example.com", contraseña="contraseña123", tipo_usuario="alumno")
    usuario2 = Usuario(RUT="98765432-1", nombre="Ana Garcia", correo_electronico="ana@example.com", contraseña="contraseña456", tipo_usuario="tutor")
    usuario3 = Usuario(RUT="11223344-5", nombre="Pedro Gomez", correo_electronico="pedro@example.com", contraseña="contraseña789", tipo_usuario="alumno")
    db.add_all([usuario1, usuario2, usuario3])
    db.commit()

    # Tutor y Alumno
    tutor1 = Tutor(RUT="98765432-1")
    alumno1 = Alumno(RUT="12345678-9")
    alumno2 = Alumno(RUT="11223344-5")
    db.add_all([tutor1, alumno1, alumno2])
    db.commit()

    # Materias
    materia1 = Materia(nombre_materia="Matemáticas", descripcion="Curso de matemáticas básicas")
    materia2 = Materia(nombre_materia="Historia", descripcion="Introducción a la historia universal")
    materia3 = Materia(nombre_materia="Física", descripcion="Fundamentos de la física")
    db.add_all([materia1, materia2, materia3])
    db.commit()

    # Horarios
    horario1 = Horario(dia="Lunes", hora_inicio=time(10, 0, 0), hora_fin=time(11, 0, 0))
    horario2 = Horario(dia="Miércoles", hora_inicio=time(15, 0, 0), hora_fin=time(16, 0, 0))
    horario3 = Horario(dia="Viernes", hora_inicio=time(14, 0, 0), hora_fin=time(15, 0, 0))
    db.add_all([horario1, horario2, horario3])
    db.commit()

    # Tutorias
    tutoria1 = Tutoria(RUT_tutor="98765432-1", ID_horario=1, ID_materia=1, fecha=date(2024, 12, 10))
    tutoria2 = Tutoria(RUT_tutor="98765432-1", ID_horario=2, ID_materia=2, fecha=date(2024, 12, 17))
    db.add_all([tutoria1, tutoria2])
    db.commit()

    # Relaciones N:M
    tutor1.materias.append(materia1)
    tutor1.materias.append(materia2)
    alumno1.materias.append(materia2)
    alumno2.materias.append(materia1)
    alumno2.materias.append(materia3)
    materia1.horarios.append(horario1)
    materia2.horarios.append(horario2)
    materia3.horarios.append(horario3)
    tutoria1.alumnos.append(alumno1)
    tutoria2.alumnos.append(alumno2)
    db.commit()

    # Repositorio
    repositorio1 = Repositorio(ID_materia=1, contenido="Apuntes de matemáticas")
    repositorio2 = Repositorio(ID_materia=2, contenido="Resumen de la historia universal")
    db.add_all([repositorio1, repositorio2])
    db.commit()

if __name__ == "__main__":
    crear_datos_prueba()