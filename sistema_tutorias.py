import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import random
import re

conn = sqlite3.connect('tutoring_system.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    date_of_birth TEXT NOT NULL,
    university TEXT NOT NULL,
    career TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS alumno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    materia TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS profesor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    materia TEXT NOT NULL,
    disponible BOOLEAN NOT NULL,
    hora_inicio TEXT NOT NULL,  -- Nuevo campo para hora de inicio
    hora_fin TEXT NOT NULL      -- Nuevo campo para hora de fin
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS solicitud (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    profesor_id INTEGER,
    fecha_solicitud TEXT NOT NULL,
    estado TEXT NOT NULL,
    FOREIGN KEY (alumno_id) REFERENCES alumno(id),
    FOREIGN KEY (profesor_id) REFERENCES profesor(id)
)
''')

conn.commit()

def crear_admin_por_defecto():
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()
    if not admin:
        default_admin_rut = "admin"
        default_admin_password = "12345"
        cursor.execute('''
        INSERT INTO users (name, rut, date_of_birth, university, career, password, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("Administrador", default_admin_rut, "1900-01-01", "Universidad XYZ", "Administración", default_admin_password, "admin"))
        conn.commit()
        print("Se ha creado una cuenta de administrador por defecto.")
        print(f"RUT: {default_admin_rut}")
        print(f"Contraseña: {default_admin_password}")

crear_admin_por_defecto()

def validar_rut(rut):
    """
    Valida el RUT chileno.
    Debe estar en formato XX.XXX.XXX-X y ser válido según el algoritmo.
    """
    rut = rut.replace(".", "").replace("-", "").upper()
    
    if len(rut) < 8 or len(rut) > 9:
        return False
    
    if not rut[:-1].isdigit():
        return False
    
    dv = rut[-1]
    
    suma = 0
    multiplo = 2
    for c in reversed(rut[:-1]):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo > 7:
            multiplo = 2
    resto = suma % 11
    dv_calculado = 11 - resto
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    return dv == dv_calculado

def registrar_usuario_db(name, rut, date_of_birth, university, career, materia, password):
    try:
        if not validar_rut(rut):
            messagebox.showerror("Error", "RUT inválido. Asegúrate de que tenga el formato correcto (XX.XXX.XXX-X).")
            return False
        
        cursor.execute('''
        INSERT INTO users (name, rut, date_of_birth, university, career, password, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, rut, date_of_birth, university, career, password, 'student'))
        user_id = cursor.lastrowid

        cursor.execute('''
        INSERT INTO alumno (user_id, materia)
        VALUES (?, ?)
        ''', (user_id, materia))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "El RUT ya está registrado. Por favor, utiliza otro RUT.")
        return False

def registrar_profesor_db(nombre, materia, hora_inicio, hora_fin):
    cursor.execute('INSERT INTO profesor (nombre, materia, disponible, hora_inicio, hora_fin) VALUES (?, ?, ?, ?, ?)', 
                   (nombre, materia, True, hora_inicio, hora_fin))
    conn.commit()

def solicitar_ayudantia_db(alumno_id):
    cursor.execute('SELECT materia FROM alumno WHERE id = ?', (alumno_id,))
    alumno_materia = cursor.fetchone()

    if not alumno_materia:
        return "Alumno no encontrado."

    materia = alumno_materia[0]

    cursor.execute('SELECT id, nombre, hora_inicio, hora_fin FROM profesor WHERE materia = ? AND disponible = 1 LIMIT 1', (materia,))
    profesor = cursor.fetchone()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if profesor:
        profesor_id, profesor_nombre, hora_inicio, hora_fin = profesor
        cursor.execute('INSERT INTO solicitud (alumno_id, profesor_id, fecha_solicitud, estado) VALUES (?, ?, ?, ?)', 
                       (alumno_id, profesor_id, fecha, 'Asignado'))
        cursor.execute('UPDATE profesor SET disponible = 0 WHERE id = ?', (profesor_id,))
        conn.commit()
        return f"Solicitud asignada al profesor {profesor_nombre}.\nHorario: {hora_inicio} - {hora_fin}."
    else:
        cursor.execute('INSERT INTO solicitud (alumno_id, profesor_id, fecha_solicitud, estado) VALUES (?, ?, ?, ?)', 
                       (alumno_id, None, fecha, 'Pendiente'))
        conn.commit()
        return "No hay profesores disponibles en este momento. La solicitud está pendiente."

def finalizar_ayudantia_db(solicitud_id):
    cursor.execute('SELECT profesor_id FROM solicitud WHERE id = ?', (solicitud_id,))
    solicitud = cursor.fetchone()

    if solicitud and solicitud[0]:
        profesor_id = solicitud[0]
        cursor.execute('UPDATE profesor SET disponible = 1 WHERE id = ?', (profesor_id,))
        cursor.execute('UPDATE solicitud SET estado = ? WHERE id = ?', ('Finalizado', solicitud_id))
        conn.commit()
        return f"Solicitud {solicitud_id} finalizada y el profesor está disponible nuevamente."
    else:
        return "Solicitud no encontrada o no asignada a un profesor."

def obtener_alumnos():
    cursor.execute('''
    SELECT alumno.id, users.name, alumno.materia
    FROM alumno
    JOIN users ON alumno.user_id = users.id
    ''')
    return cursor.fetchall()

def obtener_solicitudes():
    cursor.execute('''
    SELECT solicitud.id, users.name, profesor.nombre, solicitud.fecha_solicitud, solicitud.estado, profesor.hora_inicio, profesor.hora_fin
    FROM solicitud
    JOIN alumno ON solicitud.alumno_id = alumno.id
    JOIN users ON alumno.user_id = users.id
    LEFT JOIN profesor ON solicitud.profesor_id = profesor.id
    WHERE solicitud.estado IN ('Asignado', 'Pendiente')
    ''')
    return cursor.fetchall()

def autenticar_usuario(rut, password):
    cursor.execute('SELECT id, name, role, password FROM users WHERE rut = ?', (rut,))
    user = cursor.fetchone()
    if user:
        user_id, name, role, stored_password = user
        if password == stored_password:
            return (user_id, name, role)
    return None

def obtener_solicitudes_por_alumno(alumno_id):
    cursor.execute('''
    SELECT solicitud.id, profesor.nombre, solicitud.fecha_solicitud, solicitud.estado, profesor.hora_inicio, profesor.hora_fin
    FROM solicitud
    LEFT JOIN profesor ON solicitud.profesor_id = profesor.id
    WHERE solicitud.alumno_id = ?
    ''', (alumno_id,))
    return cursor.fetchall()

def obtener_todos_usuarios():
    cursor.execute('SELECT id, name, rut, date_of_birth, university, career, role FROM users')
    return cursor.fetchall()

def obtener_todos_profesores():
    cursor.execute('SELECT id, nombre, materia, disponible, hora_inicio, hora_fin FROM profesor')
    return cursor.fetchall()

def eliminar_usuario(user_id):
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    role = cursor.fetchone()
    if role and role[0] == 'student':
        cursor.execute('DELETE FROM alumno WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()

def actualizar_profesor_disponibilidad(profesor_id, disponible):
    cursor.execute('UPDATE profesor SET disponible = ? WHERE id = ?', (disponible, profesor_id))
    conn.commit()

def actualizar_contraseña_db(user_id, nueva_contraseña):
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (nueva_contraseña, user_id))
    conn.commit()


class TutoringApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Tutoring Universitario")
        self.geometry("900x600")  
        self.minsize(800, 500)    
        self.resizable(True, True)  
        
        self.current_user = None 
        
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=("Helvetica", 10))
        style.configure("TLabel", padding=6, font=("Helvetica", 12))
        style.configure("Header.TLabel", padding=6, font=("Helvetica", 16, "bold"))
        
        self.frames = {}
        
        for F in (WelcomeFrame, RegisterFrame, LoginFrame, StudentAppFrame, AdminAppFrame, RecuperarContraseñaFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.show_frame(WelcomeFrame)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class WelcomeFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_welcome = ttk.Label(self, text="Bienvenido al Sistema de Tutoring", style="Header.TLabel")
        lbl_welcome.pack(pady=50)
        
        btn_login = ttk.Button(self, text="Iniciar Sesión", command=lambda: controller.show_frame(LoginFrame))
        btn_login.pack(pady=10)
        
        btn_register = ttk.Button(self, text="Crear Cuenta", command=lambda: controller.show_frame(RegisterFrame))
        btn_register.pack(pady=10)
        
        btn_recuperar = ttk.Button(self, text="¿Olvidaste tu Contraseña?", command=lambda: controller.show_frame(RecuperarContraseñaFrame))
        btn_recuperar.pack(pady=10)

class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Crear Cuenta", style="Header.TLabel")
        lbl_title.pack(pady=10)
        
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_name = ttk.Entry(form_frame, width=40)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="RUT:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_rut = ttk.Entry(form_frame, width=40)
        self.entry_rut.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Fecha de Nacimiento (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_dob = ttk.Entry(form_frame, width=40)
        self.entry_dob.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Universidad:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_university = ttk.Entry(form_frame, width=40)
        self.entry_university.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Carrera:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_career = ttk.Entry(form_frame, width=40)
        self.entry_career.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Materia de Interés:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.entry_materia = ttk.Entry(form_frame, width=40)
        self.entry_materia.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Contraseña:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        self.entry_password = ttk.Entry(form_frame, show="*", width=40)
        self.entry_password.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Confirmar Contraseña:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        self.entry_confirm_password = ttk.Entry(form_frame, show="*", width=40)
        self.entry_confirm_password.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        
        btn_register = ttk.Button(scrollable_frame, text="Registrar", command=self.registrar_usuario)
        btn_register.pack(pady=20)
        
        btn_back = ttk.Button(scrollable_frame, text="Volver", command=lambda: controller.show_frame(WelcomeFrame))
        btn_back.pack()
    
    def registrar_usuario(self):
        name = self.entry_name.get().strip()
        rut = self.entry_rut.get().strip()
        dob = self.entry_dob.get().strip()
        university = self.entry_university.get().strip()
        career = self.entry_career.get().strip()
        materia = self.entry_materia.get().strip()
        password = self.entry_password.get().strip()
        confirm_password = self.entry_confirm_password.get().strip()
        
        if not all([name, rut, dob, university, career, materia, password, confirm_password]):
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        
        success = registrar_usuario_db(name, rut, dob, university, career, materia, password)
        if success:
            messagebox.showinfo("Cuenta Creada", f"Tu cuenta ha sido creada exitosamente.\nTu contraseña es: {password}\nGuárdala en un lugar seguro.")
            self.entry_name.delete(0, tk.END)
            self.entry_rut.delete(0, tk.END)
            self.entry_dob.delete(0, tk.END)
            self.entry_university.delete(0, tk.END)
            self.entry_career.delete(0, tk.END)
            self.entry_materia.delete(0, tk.END)
            self.entry_password.delete(0, tk.END)
            self.entry_confirm_password.delete(0, tk.END)
            self.controller.show_frame(LoginFrame)

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Iniciar Sesión", style="Header.TLabel")
        lbl_title.pack(pady=10)
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ttk.Label(form_frame, text="RUT:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_rut = ttk.Entry(form_frame, width=40)
        self.entry_rut.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_password = ttk.Entry(form_frame, show="*", width=40)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        btn_login = ttk.Button(form_frame, text="Iniciar Sesión", command=self.iniciar_sesion)
        btn_login.grid(row=2, column=0, columnspan=2, pady=20)
        
        btn_back = ttk.Button(form_frame, text="Volver", command=lambda: controller.show_frame(WelcomeFrame))
        btn_back.grid(row=3, column=0, columnspan=2)
    
    def iniciar_sesion(self):
        rut = self.entry_rut.get().strip()
        password = self.entry_password.get().strip()
        
        if not rut or not password:
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return
        
        user = autenticar_usuario(rut, password)
        if user:
            user_id, name, role = user
            self.controller.current_user = user
            messagebox.showinfo("Éxito", f"Bienvenido, {name}!")
            if role == 'student':
                self.controller.show_frame(StudentAppFrame)
                self.controller.frames[StudentAppFrame].actualizar_solicitudes()
            elif role == 'admin':
                self.controller.show_frame(AdminAppFrame)
                self.controller.frames[AdminAppFrame].actualizar_tabla_usuarios()
        else:
            messagebox.showerror("Error", "RUT o contraseña incorrectos.")

class RecuperarContraseñaFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Recuperar Contraseña", style="Header.TLabel")
        lbl_title.pack(pady=10)
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ttk.Label(form_frame, text="RUT:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_rut = ttk.Entry(form_frame, width=40)
        self.entry_rut.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        btn_recuperar = ttk.Button(form_frame, text="Recuperar Contraseña", command=self.recuperar_contraseña)
        btn_recuperar.grid(row=1, column=0, columnspan=2, pady=20)
        
        btn_back = ttk.Button(form_frame, text="Volver", command=lambda: controller.show_frame(WelcomeFrame))
        btn_back.grid(row=2, column=0, columnspan=2)
    
    def recuperar_contraseña(self):
        rut = self.entry_rut.get().strip()
        
        if not rut:
            messagebox.showerror("Error", "Por favor, ingresa tu RUT.")
            return
        
        cursor.execute('SELECT id, name, role FROM users WHERE rut = ?', (rut,))
        user = cursor.fetchone()
        
        if user:
            user_id, name, role = user
            if role != 'admin':
                new_password = simpledialog.askstring("Reiniciar Contraseña", f"Administrador, ingresa la nueva contraseña para {name}:")
                if new_password:
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))
                    conn.commit()
                    messagebox.showinfo("Éxito", "La contraseña ha sido actualizada correctamente.")
                    self.controller.show_frame(LoginFrame)
                else:
                    messagebox.showerror("Error", "La contraseña no puede estar vacía.")
            else:
                messagebox.showerror("Error", "Los administradores no pueden recuperar su contraseña de esta manera.")
        else:
            messagebox.showerror("Error", "No se encontró un usuario con ese RUT.")

class StudentAppFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Panel del Estudiante", style="Header.TLabel")
        lbl_title.pack(pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(expand=1, fill='both', padx=20, pady=10)
        
        self.tab_solicitar = ttk.Frame(notebook)
        self.tab_solicitudes = ttk.Frame(notebook)
        self.tab_cambiar_contraseña = ttk.Frame(notebook)
        
        notebook.add(self.tab_solicitar, text='Solicitar Ayudantía')
        notebook.add(self.tab_solicitudes, text='Mis Solicitudes')
        notebook.add(self.tab_cambiar_contraseña, text='Cambiar Contraseña')
        
        lbl_alumno = ttk.Label(self.tab_solicitar, text="Seleccionar Alumno:")
        lbl_alumno.pack(pady=10)
        
        self.combo_alumnos = ttk.Combobox(self.tab_solicitar, state="readonly", width=50)
        self.combo_alumnos.pack(pady=5)
        
        btn_solicitar = ttk.Button(self.tab_solicitar, text="Solicitar Ayudantía", command=self.solicitar_ayudantia)
        btn_solicitar.pack(pady=20)
        
        self.tree_solicitudes = ttk.Treeview(self.tab_solicitudes, columns=("ID", "Profesor", "Fecha", "Estado", "Horario"), show='headings')
        self.tree_solicitudes.heading("ID", text="ID")
        self.tree_solicitudes.heading("Profesor", text="Profesor")
        self.tree_solicitudes.heading("Fecha", text="Fecha Solicitud")
        self.tree_solicitudes.heading("Estado", text="Estado")
        self.tree_solicitudes.heading("Horario", text="Horario")
        
        scrollbar = ttk.Scrollbar(self.tab_solicitudes, orient="vertical", command=self.tree_solicitudes.yview)
        self.tree_solicitudes.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_solicitudes.pack(pady=10, fill='both', expand=True)
        
        btn_finalizar = ttk.Button(self.tab_solicitudes, text="Finalizar Ayudantía", command=self.finalizar_ayudantia)
        btn_finalizar.pack(pady=10)
        
        form_cambio = ttk.Frame(self.tab_cambiar_contraseña)
        form_cambio.pack(pady=20, padx=20, fill="both", expand=True)
        
        ttk.Label(form_cambio, text="Contraseña Actual:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_actual = ttk.Entry(form_cambio, show="*", width=40)
        self.entry_actual.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_cambio, text="Nueva Contraseña:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_nueva = ttk.Entry(form_cambio, show="*", width=40)
        self.entry_nueva.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_cambio, text="Confirmar Nueva Contraseña:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_confirmar_nueva = ttk.Entry(form_cambio, show="*", width=40)
        self.entry_confirmar_nueva.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        btn_cambiar = ttk.Button(form_cambio, text="Cambiar Contraseña", command=self.cambiar_contraseña)
        btn_cambiar.grid(row=3, column=0, columnspan=2, pady=20)
        
        btn_logout = ttk.Button(self, text="Cerrar Sesión", command=self.logout)
        btn_logout.pack(pady=10)
    
    def solicitar_ayudantia(self):
        seleccionado = self.combo_alumnos.get()
        if not seleccionado:
            messagebox.showerror("Error", "No tienes una cuenta de alumno asociada o no hay alumnos disponibles.")
            return
        alumno_id = self.alumnos_dict.get(seleccionado)
        resultado = solicitar_ayudantia_db(alumno_id)
        messagebox.showinfo("Resultado", resultado)
        self.actualizar_solicitudes()
    
    def actualizar_solicitudes(self):
        user = self.controller.current_user
        cursor.execute('SELECT alumno.id, alumno.materia FROM alumno JOIN users ON alumno.user_id = users.id WHERE users.id = ?', (user[0],))
        alumno = cursor.fetchone()
        if alumno:
            alumno_id, materia = alumno
            if not hasattr(self, 'alumnos_dict'):
                self.alumnos_dict = {f"{user[1]} (Materia: {materia})": alumno_id}
                self.combo_alumnos['values'] = list(self.alumnos_dict.keys())
                if self.alumnos_dict:
                    self.combo_alumnos.current(0)
            for item in self.tree_solicitudes.get_children():
                self.tree_solicitudes.delete(item)
            solicitudes = obtener_solicitudes_por_alumno(alumno_id)
            for sol in solicitudes:
                solicitud_id, profesor, fecha, estado, hora_inicio, hora_fin = sol
                profesor = profesor if profesor else "Pendiente"
                horario = f"{hora_inicio} - {hora_fin}" if profesor != "Pendiente" else "N/A"
                self.tree_solicitudes.insert('', 'end', values=(solicitud_id, profesor, fecha, estado, horario))
        else:
            self.alumnos_dict = {}
            self.combo_alumnos['values'] = []
            self.tree_solicitudes.delete(*self.tree_solicitudes.get_children())
            messagebox.showerror("Error", "No tienes una cuenta de alumno asociada.")
    
    def finalizar_ayudantia(self):
        solicitud_id = simpledialog.askstring("Finalizar Ayudantía", "Ingresa el ID de la solicitud a finalizar:")
        if not solicitud_id:
            return
        if not solicitud_id.isdigit():
            messagebox.showerror("Error", "El ID de la solicitud debe ser un número.")
            return
        resultado = finalizar_ayudantia_db(int(solicitud_id))
        messagebox.showinfo("Resultado", resultado)
        self.actualizar_solicitudes()
    
    def cambiar_contraseña(self):
        actual = self.entry_actual.get().strip()
        nueva = self.entry_nueva.get().strip()
        confirmar = self.entry_confirmar_nueva.get().strip()
        
        if not all([actual, nueva, confirmar]):
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return
        
        user = self.controller.current_user
        cursor.execute('SELECT password FROM users WHERE id = ?', (user[0],))
        contraseña_actual = cursor.fetchone()[0]
        
        if actual != contraseña_actual:
            messagebox.showerror("Error", "La contraseña actual es incorrecta.")
            return
        
        if nueva != confirmar:
            messagebox.showerror("Error", "Las nuevas contraseñas no coinciden.")
            return
        
        actualizar_contraseña_db(user[0], nueva)
        messagebox.showinfo("Éxito", "Tu contraseña ha sido actualizada correctamente.")
        self.entry_actual.delete(0, tk.END)
        self.entry_nueva.delete(0, tk.END)
        self.entry_confirmar_nueva.delete(0, tk.END)

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame(WelcomeFrame)

class AdminAppFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Panel del Administrador", style="Header.TLabel")
        lbl_title.pack(pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(expand=1, fill='both', padx=20, pady=10)
        
        self.tab_usuarios = ttk.Frame(notebook)
        self.tab_profesores = ttk.Frame(notebook)
        self.tab_solicitudes = ttk.Frame(notebook)
        
        notebook.add(self.tab_usuarios, text='Gestionar Usuarios')
        notebook.add(self.tab_profesores, text='Gestionar Profesores')
        notebook.add(self.tab_solicitudes, text='Gestionar Solicitudes')
        
        lbl_usuarios = ttk.Label(self.tab_usuarios, text="Lista de Usuarios:", style="Header.TLabel")
        lbl_usuarios.pack(pady=10)
        
        frame_usuarios = ttk.Frame(self.tab_usuarios)
        frame_usuarios.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_usuarios = ttk.Treeview(frame_usuarios, columns=("ID", "Nombre", "RUT", "Fecha Nac.", "Universidad", "Carrera", "Rol"), show='headings')
        for col in ("ID", "Nombre", "RUT", "Fecha Nac.", "Universidad", "Carrera", "Rol"):
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(col, width=100, anchor="center")
        
        scrollbar_usuarios = ttk.Scrollbar(frame_usuarios, orient="vertical", command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscroll=scrollbar_usuarios.set)
        scrollbar_usuarios.pack(side='right', fill='y')
        self.tree_usuarios.pack(fill='both', expand=True)
        
        btn_eliminar_usuario = ttk.Button(self.tab_usuarios, text="Eliminar Usuario", command=self.eliminar_usuario)
        btn_eliminar_usuario.pack(pady=10)
        
        lbl_profesores = ttk.Label(self.tab_profesores, text="Lista de Profesores:", style="Header.TLabel")
        lbl_profesores.pack(pady=10)
        
        frame_profesores = ttk.Frame(self.tab_profesores)
        frame_profesores.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_profesores = ttk.Treeview(frame_profesores, columns=("ID", "Nombre", "Materia", "Disponible", "Horario"), show='headings')
        for col in ("ID", "Nombre", "Materia", "Disponible", "Horario"):
            self.tree_profesores.heading(col, text=col)
            self.tree_profesores.column(col, width=150, anchor="center")
        
        scrollbar_profesores = ttk.Scrollbar(frame_profesores, orient="vertical", command=self.tree_profesores.yview)
        self.tree_profesores.configure(yscroll=scrollbar_profesores.set)
        scrollbar_profesores.pack(side='right', fill='y')
        self.tree_profesores.pack(fill='both', expand=True)
        
        btn_agregar_profesor = ttk.Button(self.tab_profesores, text="Agregar Profesor", command=self.agregar_profesor)
        btn_agregar_profesor.pack(pady=5)
        
        btn_eliminar_profesor = ttk.Button(self.tab_profesores, text="Eliminar Profesor", command=self.eliminar_profesor)
        btn_eliminar_profesor.pack(pady=5)
        
        lbl_solicitudes = ttk.Label(self.tab_solicitudes, text="Solicitudes Actuales:", style="Header.TLabel")
        lbl_solicitudes.pack(pady=10)
        
        frame_solicitudes = ttk.Frame(self.tab_solicitudes)
        frame_solicitudes.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_solicitudes_admin = ttk.Treeview(frame_solicitudes, columns=("ID", "Alumno", "Profesor", "Fecha", "Estado"), show='headings')
        for col in ("ID", "Alumno", "Profesor", "Fecha", "Estado"):
            self.tree_solicitudes_admin.heading(col, text=col)
            self.tree_solicitudes_admin.column(col, width=150, anchor="center")
        
        scrollbar_solicitudes = ttk.Scrollbar(frame_solicitudes, orient="vertical", command=self.tree_solicitudes_admin.yview)
        self.tree_solicitudes_admin.configure(yscroll=scrollbar_solicitudes.set)
        scrollbar_solicitudes.pack(side='right', fill='y')
        self.tree_solicitudes_admin.pack(fill='both', expand=True)
        
        btn_actualizar_solicitudes = ttk.Button(self.tab_solicitudes, text="Actualizar Lista", command=self.actualizar_solicitudes)
        btn_actualizar_solicitudes.pack(pady=5)
        
        btn_logout = ttk.Button(self, text="Cerrar Sesión", command=self.logout)
        btn_logout.pack(pady=10)
    
    def actualizar_tabla_usuarios(self):
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
        
        usuarios = obtener_todos_usuarios()
        for user in usuarios:
            self.tree_usuarios.insert('', 'end', values=user)
    
    def eliminar_usuario(self):
        selected = self.tree_usuarios.selection()
        if not selected:
            messagebox.showerror("Error", "Por favor, selecciona un usuario para eliminar.")
            return
        user_id = self.tree_usuarios.item(selected[0])['values'][0]
        if user_id == self.controller.current_user[0]:
            messagebox.showerror("Error", "No puedes eliminar tu propia cuenta mientras estás conectado.")
            return
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar este usuario?"):
            eliminar_usuario(user_id)
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
            self.actualizar_tabla_usuarios()
    
    def agregar_profesor(self):
        def agregar():
            nombre = entry_nombre.get().strip()
            materia = entry_materia.get().strip()
            hora_inicio = entry_hora_inicio.get().strip()
            hora_fin = entry_hora_fin.get().strip()
            if not nombre or not materia or not hora_inicio or not hora_fin:
                messagebox.showerror("Error", "Por favor, completa todos los campos.")
                return
            if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', hora_inicio):
                messagebox.showerror("Error", "Hora de inicio inválida. Usa el formato HH:MM.")
                return
            if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', hora_fin):
                messagebox.showerror("Error", "Hora de fin inválida. Usa el formato HH:MM.")
                return
            h_inicio = datetime.strptime(hora_inicio, "%H:%M")
            h_fin = datetime.strptime(hora_fin, "%H:%M")
            if h_fin <= h_inicio:
                messagebox.showerror("Error", "La hora de fin debe ser después de la hora de inicio.")
                return
            registrar_profesor_db(nombre, materia, hora_inicio, hora_fin)
            messagebox.showinfo("Éxito", f"Profesor {nombre} registrado en la materia {materia} con horario {hora_inicio} - {hora_fin}.")
            agregar_win.destroy()
            self.actualizar_tabla_profesores()
        
        agregar_win = tk.Toplevel(self)
        agregar_win.title("Agregar Profesor")
        agregar_win.geometry("400x400")
        agregar_win.resizable(False, False)
        
        ttk.Label(agregar_win, text="Nombre del Profesor:", font=("Helvetica", 12)).pack(pady=10)
        entry_nombre = ttk.Entry(agregar_win, width=50)
        entry_nombre.pack(pady=5)
        
        ttk.Label(agregar_win, text="Materia:", font=("Helvetica", 12)).pack(pady=10)
        entry_materia = ttk.Entry(agregar_win, width=50)
        entry_materia.pack(pady=5)
        
        ttk.Label(agregar_win, text="Hora de Inicio (HH:MM):", font=("Helvetica", 12)).pack(pady=10)
        entry_hora_inicio = ttk.Entry(agregar_win, width=50)
        entry_hora_inicio.pack(pady=5)
        
        ttk.Label(agregar_win, text="Hora de Fin (HH:MM):", font=("Helvetica", 12)).pack(pady=10)
        entry_hora_fin = ttk.Entry(agregar_win, width=50)
        entry_hora_fin.pack(pady=5)
        
        ttk.Button(agregar_win, text="Agregar", command=agregar).pack(pady=20)
    
    def eliminar_profesor(self):
        selected = self.tree_profesores.selection()
        if not selected:
            messagebox.showerror("Error", "Por favor, selecciona un profesor para eliminar.")
            return
        profesor_id = self.tree_profesores.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar este profesor?"):
            cursor.execute('DELETE FROM profesor WHERE id = ?', (profesor_id,))
            conn.commit()
            messagebox.showinfo("Éxito", "Profesor eliminado correctamente.")
            self.actualizar_tabla_profesores()
    
    def actualizar_tabla_profesores(self):
        for item in self.tree_profesores.get_children():
            self.tree_profesores.delete(item)
        
        profesores = obtener_todos_profesores()
        for prof in profesores:
            disponibilidad = "Sí" if prof[3] else "No"
            horario = f"{prof[4]} - {prof[5]}"
            self.tree_profesores.insert('', 'end', values=(prof[0], prof[1], prof[2], disponibilidad, horario))
    
    def actualizar_solicitudes(self):
        for item in self.tree_solicitudes_admin.get_children():
            self.tree_solicitudes_admin.delete(item)
        
        solicitudes = obtener_solicitudes()
        for sol in solicitudes:
            solicitud_id, alumno, profesor, fecha, estado, hora_inicio, hora_fin = sol
            profesor = profesor if profesor else "Pendiente"
            horario = f"{hora_inicio} - {hora_fin}" if profesor != "Pendiente" else "N/A"
            self.tree_solicitudes_admin.insert('', 'end', values=(solicitud_id, alumno, profesor, fecha, estado))
    
    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame(WelcomeFrame)


if __name__ == "__main__":
    app = TutoringApp()
    app.mainloop()

    conn.close()