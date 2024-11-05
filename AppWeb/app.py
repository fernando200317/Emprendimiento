import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from Database.db_queries import check_password, show_completed_forms_list, show_inventory
from Database.db_inserts import request_for_entry_of_forms, accept_form_input, insert_item
from Database.db_deletes import delete_pending_form_entry, delete_item

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

@app.route('/Estudiante', methods=['GET','POST'])
def estudiante():
    return render_template('estudiante.html')

@app.route('/Administrador')
def administrador():
    return render_template('administrador.html')

@app.route('/Administrador/Modificar_Inventario')
def modificar_inventario():
    items = show_inventory()
    return render_template('modificar_inventario.html', items=items)

@app.route('/agregar_item', methods=['POST'])
def agregar_item():
    data = request.get_json()
    name = data['name']
    description = data['description']
    quantity = data['quantity']
    new_item = insert_item(name, description, quantity)

    return jsonify(new_item), 201


@app.route('/eliminar_item/<int:item_id>', methods=['DELETE'])
def eliminar_item(item_id):
    try:
        result = delete_item(item_id)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error al eliminar el item: {e}")
        return jsonify({'error': 'Error al eliminar el item'}), 500
    
# solicitudes_temp = []

@app.route('/formulario_completado', methods=['GET','POST'])
def formulario_completado():
    if request.method == 'POST':
        rut = request.form['rut']
        form_name = request.form['uso']
        request_for_entry_of_forms(rut,form_name)
        return redirect(url_for('estudiante'))
    return render_template('formulario_completado.html')

@app.route('/solicitud_articulo')
def solicitud_articulo():
    return render_template('solicitud_articulo.html')

@app.route('/lista_de_formularios_completados', methods=['GET'])
def lista_form_completados():
    formularios_completados = show_completed_forms_list()
    return render_template('lista_form_completados.html', formularios_completados=formularios_completados)

@app.route('/aceptar_formulario', methods=['POST'])
def aceptar_formulario():
    rut = request.form['rut']
    forms_name = request.form['forms_name']
    try:
        accept_form_input(rut, forms_name)
        delete_pending_form_entry(rut,forms_name)
        return redirect(url_for('lista_form_completados'))
    except Exception as e:
        print(f"Error al aceptar el formulario: {e}")
        return redirect(url_for('lista_form_completados'))

@app.route('/rechazar_formulario', methods=['POST'])
def rechazar_formulario():
    rut = request.form['rut']
    forms_name = request.form['forms_name']
    try:
        delete_pending_form_entry(rut,forms_name)
        return redirect(url_for('lista_form_completados'))
    except Exception as e:
        print(f"Error al rechazar el formulario: {e}")
        return redirect(url_for('lista_form_completados'))

if __name__ == '__main__':
    app.run(debug=True)