import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from Database.db_read import check_password

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rut = request.form['rut']
        password = request.form['password']

        print(rut, password)
        
        if check_password(rut, password):
            flash('Login exitoso', 'success')
            return redirect(url_for('estudiante'))  # Redirige a la página del usuario
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Procesa los datos del formulario de registro
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # ... (lógica para crear un nuevo usuario en tu base de datos) ...

        flash('¡Cuenta creada exitosamente!', 'success')
        return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)