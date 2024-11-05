import os
from sqlalchemy import create_engine, text, MetaData, Table, Select
from sqlalchemy.orm import sessionmaker
import bcrypt, os

config = {'host': 'localhost', 'database_name': 'MakeIt_DB', 'user': 'root', 'password': 'rootpass'}
engine = create_engine(f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}/{config["database_name"]}', echo=False)
metadata = MetaData()

Session = sessionmaker(bind=engine)
session = Session()

def check_password(rut, password):
    password_bytes = password.encode('utf-8')
    try:
        query = text("""SELECT password 
                        FROM user
                        WHERE rut = :rut""")
        query_result = session.execute(query, {'rut':rut})

        hashed_password_row = query_result.fetchone()
        
        if hashed_password_row is None:
            print("Usuario no encontrado")
            return False
        hashed_password = hashed_password_row[0]

        if bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8')):
            print("La contraseña es correcta", hashed_password)
            return True
        else:
            print("La contraseña es incorrecta")
            return False
            
    except Exception as e:
        print(f"Error in check_password: {e}")
        return False
