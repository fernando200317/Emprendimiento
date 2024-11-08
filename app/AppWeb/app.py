from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from Database.db_create import crear_usuario, formatear_rut
from Database.db_read import check_password, obtener_tipo_usuario  
from Database.db_connect import db_session, shutdown_session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Página de inicio
@app.route('/')
def inicio():
    return render_template('inicio.html')

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rut = formatear_rut(request.form['rut'])
        password = request.form['password']
        
        if check_password(rut, password):
            tipo_usuario = obtener_tipo_usuario(rut)
            session['tipo_usuario'] = tipo_usuario
            session['rut'] = rut

            flash('Login exitoso', 'success')
            if tipo_usuario == 'tutor':
                return redirect(url_for('pagina_tutor'))
            elif tipo_usuario == 'estudiante':
                return redirect(url_for('pagina_alumno'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        rut = formatear_rut(request.form['rut'])
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        tipo_usuario = request.form['tipo_usuario']

        success, message = crear_usuario(rut, username, email, password, tipo_usuario)
        flash(message, 'success' if success else 'danger')
        
        if success:
            return redirect(url_for('login'))
    return render_template('register.html')

# Cerrar la sesión de la base de datos al finalizar la solicitud
@app.teardown_appcontext
def shutdown_session_on_teardown(exception=None):
    shutdown_session()

# Página para tutores
@app.route('/tutor')
def pagina_tutor():
    # Verifica si el usuario es un tutor
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'tutor':
        rut = session['rut']
        
        # Consulta para obtener la información del tutor
        tutor = db_session.execute(
            text("SELECT nombre, correo_electronico FROM usuario WHERE RUT = :rut"),
            {'rut': rut}
        ).fetchone()
        
        # Consulta para obtener las materias del tutor
        materias = db_session.execute(
            text("""
                SELECT m.ID_materia, m.nombre_materia, m.descripcion
                FROM materia m
                JOIN tutor_materia tm ON m.ID_materia = tm.ID_materia
                WHERE tm.RUT_tutor = :rut
            """), {'rut': rut}
        ).fetchall()
        
        # Consulta para obtener las tutorías programadas del tutor
        tutorias = db_session.execute(
            text("""
                SELECT t.ID_tutoria, t.fecha, h.hora_inicio, h.hora_fin, m.nombre_materia
                FROM tutoria t
                JOIN horario h ON t.ID_horario = h.ID_horario
                JOIN materia m ON t.ID_materia = m.ID_materia
                WHERE t.RUT_tutor = :rut
            """), {'rut': rut}
        ).fetchall()
        
        return render_template('tutor.html', tutor=tutor, materias=materias, tutorias=tutorias)
    
    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

# Página principal del estudiante
@app.route('/alumno')
def pagina_alumno():
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'estudiante':
        rut = session['rut']

        # Obtener información del estudiante
        estudiante_info = db_session.execute(
            text("SELECT nombre, correo_electronico FROM usuario WHERE RUT = :rut"),
            {'rut': rut}
        ).fetchone()

        # Obtener materias inscritas
        inscritas = db_session.execute(
            text("""
                SELECT m.ID_materia FROM materia m
                JOIN alumno_materia am ON m.ID_materia = am.ID_materia
                WHERE am.RUT_alumno = :rut
            """), {'rut': rut}
        ).fetchall()
        inscritas_ids = [materia.ID_materia for materia in inscritas]

        # Materias disponibles para inscribirse
        if inscritas_ids:
            materias_disponibles = db_session.execute(
                text("""
                    SELECT ID_materia, nombre_materia, descripcion 
                    FROM materia 
                    WHERE ID_materia NOT IN :inscritas_ids
                """), {'inscritas_ids': tuple(inscritas_ids)}
            ).fetchall()
        else:
            materias_disponibles = db_session.execute(
                text("SELECT ID_materia, nombre_materia, descripcion FROM materia")
            ).fetchall()

        # Obtener materias inscritas con más detalles
        materias = db_session.execute(
            text("""
                SELECT m.ID_materia, m.nombre_materia, m.descripcion
                FROM materia m
                JOIN alumno_materia am ON m.ID_materia = am.ID_materia
                WHERE am.RUT_alumno = :rut
            """), {'rut': rut}
        ).fetchall()

        # Obtener tutorías programadas
        tutorias = db_session.execute(
            text("""
                SELECT t.fecha, h.dia, h.hora_inicio, h.hora_fin, u.nombre AS tutor_nombre, m.nombre_materia
                FROM tutoria t
                JOIN horario h ON t.ID_horario = h.ID_horario
                JOIN usuario u ON u.RUT = t.RUT_tutor
                JOIN materia m ON m.ID_materia = t.ID_materia
                JOIN alumno_tutoria at ON at.ID_tutoria = t.ID_tutoria
                WHERE at.RUT_alumno = :rut
            """), {'rut': rut}
        ).fetchall()

        # Obtener materiales de estudio
        repositorios = db_session.execute(
            text("""
                SELECT m.nombre_materia, r.contenido
                FROM repositorio r
                JOIN materia m ON m.ID_materia = r.ID_materia
                JOIN alumno_materia am ON m.ID_materia = am.ID_materia
                WHERE am.RUT_alumno = :rut
            """), {'rut': rut}
        ).fetchall()

        return render_template(
            'alumno.html',
            estudiante=estudiante_info,
            materias=materias,
            tutorias=tutorias,
            repositorios=repositorios,
            materias_disponibles=materias_disponibles  # Asegúrate de pasar esta variable
        )

    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

# Inscribir materias
@app.route('/alumno/inscribir_materia_ajax', methods=['POST'])
def inscribir_materia_ajax():
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'estudiante':
        rut = session['rut']
        data = request.get_json()
        materia_id = data.get("materia_id")

        try:
            db_session.execute(
                text("INSERT INTO alumno_materia (RUT_alumno, ID_materia) VALUES (:rut, :materia_id)"),
                {'rut': rut, 'materia_id': materia_id}
            )
            db_session.commit()
            return jsonify({"success": True})
        except SQLAlchemyError as e:
            db_session.rollback()
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "Acceso denegado"}), 403


# Ver tutorías de una materia específica
@app.route('/ver_tutorias/<int:materia_id>')
def ver_tutorias(materia_id):
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'estudiante':
        tutorias = db_session.execute(
            text("""
                SELECT t.fecha, h.dia, h.hora_inicio, h.hora_fin, u.nombre AS tutor_nombre
                FROM tutoria t
                JOIN horario h ON t.ID_horario = h.ID_horario
                JOIN usuario u ON u.RUT = t.RUT_tutor
                WHERE t.ID_materia = :materia_id
            """), {'materia_id': materia_id}
        ).fetchall()
        return render_template('tutorias_disponibles.html', tutorias=tutorias)
    
    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

# Ver repositorio de una materia
@app.route('/ver_repositorio/<int:materia_id>')
def ver_repositorio(materia_id):
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'estudiante':
        repositorio = db_session.execute(
            text("SELECT contenido FROM repositorio WHERE ID_materia = :materia_id"),
            {'materia_id': materia_id}
        ).fetchone()
        return render_template('repositorio.html', repositorio=repositorio)
    
    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

@app.route('/desinscribir_materia', methods=['POST'])
def desinscribir_materia():
    data = request.get_json()
    materia_id = data.get('materia_id')
    rut = session.get('rut')
    if rut:
        try:
            db_session.execute(
                text("DELETE FROM alumno_materia WHERE RUT_alumno = :rut AND ID_materia = :materia_id"),
                {'rut': rut, 'materia_id': materia_id}
            )
            db_session.commit()
            return jsonify({"success": True})
        except SQLAlchemyError as e:
            db_session.rollback()
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "No autorizado"})

@app.route('/obtener_tutorias')
def obtener_tutorias():
    materia_id = request.args.get('materia_id')
    tutorias = db_session.execute(
        text("""
            SELECT t.ID_tutoria as id, t.fecha, h.hora_inicio, h.hora_fin, u.nombre as tutor_nombre
            FROM tutoria t
            JOIN horario h ON t.ID_horario = h.ID_horario
            JOIN usuario u ON u.RUT = t.RUT_tutor
            WHERE t.ID_materia = :materia_id
        """), {'materia_id': materia_id}
    ).fetchall()
    return jsonify({"tutorias": [dict(tutoria) for tutoria in tutorias]})

@app.route('/inscribir_tutoria', methods=['POST'])
def inscribir_tutoria():
    data = request.get_json()
    tutoria_id = data.get('tutoria_id')
    rut = session.get('rut')  # Asegúrate de que el RUT del alumno esté en la sesión

    # Validar que tutoria_id no sea None y exista en la base de datos
    if not tutoria_id:
        return jsonify(success=False, error="ID de tutoría no válido")

    # Verificar que la tutoría existe
    tutoria_existe = db_session.query(tutoria).filter_by(ID_tutoria=tutoria_id).first()
    if not tutoria_existe:
        return jsonify(success=False, error="La tutoría especificada no existe")

    try:
        # Insertar en la tabla alumno_tutoria
        db_session.execute(
            text("INSERT INTO alumno_tutoria (RUT_alumno, ID_tutoria) VALUES (:rut, :tutoria_id)"),
            {'rut': rut, 'tutoria_id': tutoria_id}
        )
        db_session.commit()
        return jsonify(success=True)
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify(success=False, error=str(e))
    
@app.route('/detalle_tutoria/<int:materia_id>')
def detalle_tutoria(materia_id):
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'estudiante':
        # Obtener detalles de las tutorías de la materia específica
        tutorias = db_session.execute(
            text("""
                SELECT t.fecha, h.dia, h.hora_inicio, h.hora_fin, 
                       u.nombre AS tutor_nombre, u.correo_electronico AS tutor_email
                FROM tutoria t
                JOIN horario h ON t.ID_horario = h.ID_horario
                JOIN usuario u ON u.RUT = t.RUT_tutor
                WHERE t.ID_materia = :materia_id
            """), {'materia_id': materia_id}
        ).fetchall()

        # Obtener información de la materia
        materia_info = db_session.execute(
            text("SELECT nombre_materia, descripcion FROM materia WHERE ID_materia = :materia_id"),
            {'materia_id': materia_id}
        ).fetchone()

        return render_template('detalle_tutoria.html', materia=materia_info, tutorias=tutorias)
    
    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

@app.route('/tutor/panel', methods=['GET'])
def panel_tutor():
    if 'tipo_usuario' in session and session['tipo_usuario'] == 'tutor':
        rut = session['rut']
        tutor = db_session.execute(
            text("SELECT nombre, correo_electronico FROM usuario WHERE RUT = :rut"),
            {'rut': rut}
        ).fetchone()

        # Obtener las materias del tutor
        materias = db_session.execute(
            text("""
                SELECT m.ID_materia, m.nombre_materia, m.descripcion
                FROM materia m
                JOIN tutor_materia tm ON m.ID_materia = tm.ID_materia
                WHERE tm.RUT_tutor = :rut
            """), {'rut': rut}
        ).fetchall()

        # Obtener las tutorías programadas del tutor
        tutorias = db_session.execute(
            text("""
                SELECT t.ID_tutoria, t.fecha, h.hora_inicio, h.hora_fin, m.nombre_materia
                FROM tutoria t
                JOIN horario h ON t.ID_horario = h.ID_horario
                JOIN materia m ON t.ID_materia = m.ID_materia
                WHERE t.RUT_tutor = :rut
            """), {'rut': rut}
        ).fetchall()

        # Obtener los repositorios de materias
        repositorios = db_session.execute(
            text("""
                SELECT r.ID_repositorio, m.nombre_materia, r.contenido
                FROM repositorio r
                JOIN materia m ON r.ID_materia = m.ID_materia
                JOIN tutor_materia tm ON m.ID_materia = tm.ID_materia
                WHERE tm.RUT_tutor = :rut
            """), {'rut': rut}
        ).fetchall()

        return render_template('panel_tutor.html', tutor=tutor, materias=materias, tutorias=tutorias, repositorios=repositorios)

    flash("Acceso denegado: no tienes permiso para ver esta página", "danger")
    return redirect(url_for('inicio'))

# Crear nueva tutoría
@app.route('/crear_tutoria', methods=['POST'])
def crear_tutoria():
    data = request.get_json()
    materia_id = data.get('materia_id')
    fecha = data.get('fecha')
    hora_inicio = data.get('hora_inicio')
    hora_fin = data.get('hora_fin')
    rut_tutor = session.get('rut')

    if not materia_id or not fecha or not hora_inicio or not hora_fin:
        return jsonify(success=False, error="Datos incompletos para crear la tutoría")

    try:
        db_session.execute(
            text("""
                INSERT INTO tutoria (RUT_tutor, ID_materia, fecha, hora_inicio, hora_fin)
                VALUES (:rut_tutor, :materia_id, :fecha, :hora_inicio, :hora_fin)
            """), {'rut_tutor': rut_tutor, 'materia_id': materia_id, 'fecha': fecha,
                    'hora_inicio': hora_inicio, 'hora_fin': hora_fin}
        )
        db_session.commit()
        return jsonify(success=True)
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify(success=False, error=str(e))

@app.route('/crear_materia_ajax', methods=['POST'])
def crear_materia_ajax():
    data = request.get_json()
    nombre_materia = data.get('nombre_materia')
    descripcion = data.get('descripcion')

    if not nombre_materia or not descripcion:
        return jsonify(success=False, error="Nombre de materia o descripción faltante")

    nueva_materia = Materia(nombre_materia=nombre_materia, descripcion=descripcion)

    try:
        db_session.add(nueva_materia)
        db_session.commit()
        return jsonify(success=True, ID_materia=nueva_materia.ID_materia, nombre_materia=nueva_materia.nombre_materia)
    except Exception as e:
        db_session.rollback()
        return jsonify(success=False, error=str(e))


if __name__ == '__main__':
    app.run(debug=True)