import os
import sqlite3
import face_recognition
import pickle
import socketio
import numpy as np

def get_db():
    # Conectarse a el archivo (si no existe lo crea)
    conn = sqlite3.connect('data/prefectbot.sqlite')
    # Le decimos a sqlite que queremos Rows en forma de diccionarios
    # Luego como objeto iterable Query -> item['row']
    conn.row_factory = sqlite3.Row
    return conn

def read_encodings():
    # Inicializar diccionario de encodings
    known_face_encodings = {}

    # Lee archivo de encodings guardados
    with open('data/face_encodings.dat', 'rb') as f:
        known_face_encodings = pickle.load(f)
    # Devolver los valores como (Encodings<np.array(list)>, Names<List>)
    return np.array(list(known_face_encodings.values())), list(known_face_encodings.keys())

def write_encodings(dir):
    # Inicializar diccionario de encodings
    known_face_encodings = {}
    # Por cada imagin en el directorio
    for img in sorted(os.listdir(dir)):
        # Obtener path incluyendo directorio (dataset/img.jpg)
        file_dir = os.path.join(dir, img)
        # Conseguir el Nombre de el archivo 
        file_name = os.path.basename(file_dir)
        # Conseguir el Nombre sin extension de archivo
        name = os.path.splitext(file_name)[0]
        # TODO: SPLIT TEXT AT '_'

        # Cargar la imagen usando su ubicacion    
        face_img = face_recognition.load_image_file(file_dir)
        # Cargar el encoding de la imagen
        face_encoding = face_recognition.face_encodings(face_img)[0]

        # Agregar el encoding a el diccionario
        # ([name]: [encoding])
        known_face_encodings[name] = face_encoding
    # Guardar el diccionario en el archivo para ser leido despues
    with open('data/face_encodings.dat', 'wb') as f:
        pickle.dump(known_face_encodings, f)


def setup_db():
    # Si no existe la base de datos crearla
    if not os.path.exists("data/prefectbot.sqlite"):
        print("Creando base de datos")
        # Al conectarse a la base de datos se crea el archivo de arriba
        db = get_db()
        print("Creando tablas")
        # Leemos el archivo SQL y lo ejecutamos
        _f = open("data/db_setup.sql", "r")
        sql = _f.read()
        db.executescript(sql)
        # Cerramos la conexion
        db.close()
    else:
        # Nos conectamos a la tabla si ya existe
        print("Conectando a tabla")
        db = get_db()
        print("Conectado!")
        db.close()

def write_event(id):
    # Enviar evento a el servidor para ser broadcasted a los clientes
    sio = socketio.Client()
    sio.connect('http://localhost:5000')

    # TODO: SEND SERIALIZED DATA!!!
    sio.emit('event', { 'data' : 1})
    
    #db = get_db()
    print(id)
    # Cerrar conexion
    sio.disconnect()

def read_events():
    db = get_db()
    # Une la tabla Eventos donde la id de Maestro es igual y agrega su nombre
    events = db.execute('SELECT Eventos.eventoid, Eventos.Salon, Eventos.Tiempo, Maestros.Nombre FROM Eventos INNER JOIN Maestros ON Eventos.Maestro = Maestros.maestroid;').fetchall()
    db.close()

    # Esto se regresa a la template de index
    return events

def event_lookup(id):
    print(id)