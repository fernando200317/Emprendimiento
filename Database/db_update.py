import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt


config = {'host': 'localhost', 'database_name': 'MakeIt_DB', 'user': 'root', 'password': os.environ.get('PASSWORD_MAKEIT')}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)

Session = sessionmaker(bind=engine)
session = Session()

def create_new_user(rut, name, mail, password, role_id):

    password_bytes = password.encode('utf-8') 
    salt = bcrypt.gensalt(rounds=12)
    hashed_password = bcrypt.hashpw(password_bytes,salt)
    hashed_password_str = hashed_password.decode('utf-8')
    try:
        insert = text("""INSERT INTO user (rut, name, mail, password, role_id)
                VALUES (:rut, :name, :mail, :password, :role_id)""")
        
        session.execute(insert, {
            'rut': rut,
            'name': name,
            'mail': mail,
            'password': hashed_password_str,
            'role_id': role_id
        })
        print(f'Usuario {name} creado con contraseña hasheada: {hashed_password_str}')
    except Exception as e:
        print(f"Error in create_new_user: {e}")

def request_for_entry_of_forms(rut, form_name):
    try:
        insert = text("""INSERT INTO pending_form_entry_requests (forms_name, rut)
                         VALUES (:forms_name, :rut)""")
        session.execute(insert, {
            'rut': rut,
            'forms_name': form_name
        })
    except Exception as e:
        print(f"Error in request_for_entry_of_forms: {e}")
    session.commit()
def accept_form_input(rut, form_name):
    try:
        insert = text("""INSERT INTO user_forms (forms_name, rut)
                         VALUES (:forms_name, :rut)""")
        session.execute(insert, {
            'rut': rut,
            'forms_name': form_name
        })
    except Exception as e:
        print(f"Error in accept_form_input: {e}")
    session.commit()

def insert_item(name, description, quantity):
    session = Session()
    
    try:
        insert = text("""INSERT INTO inventory (name, description, quantity) 
                      VALUES (:name, :description, :quantity)""")
        
        session.execute(insert, {
            'name': name,
            'description': description,
            'quantity': quantity
        })
        
        result = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        session.commit()
        return {"id": result, "name": name, "description": description, "quantity": quantity}
    
    except Exception as e:
        session.rollback()
        print(f"Error in insert_item: {e}")
    finally:
        session.close()
        
session.commit()
session.close()