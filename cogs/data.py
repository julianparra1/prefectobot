from datetime import datetime
import os
import sqlite3
import time
import face_recognition
import pickle
import socketio
import numpy as np
import cv2


def get_db():
    # Conectarse a el archivo (si no existe lo crea)
    conn = sqlite3.connect('data/prefectbot.sqlite')
    # Le decimos a sqlite que queremos Rows en forma de diccionarios
    # Luego como objeto iterable Query -> item['row']
    conn.row_factory = sqlite3.Row
    return conn


def read_encodings():

    # Lee archivo de encodings guardados
    with open('data/face_encodings.dat', 'rb') as f:
        known_face_encodings = pickle.load(f)
    # Devolver los valores como (Encodings<np.array(list)>, Names<List>)
    return np.array(list(known_face_encodings.values())), list(known_face_encodings.keys())


def write_encodings(directory):
    # Inicializar diccionario de encodings
    known_face_encodings = {}
    db = get_db()
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS maestros")
    cur.execute("DROP TABLE IF EXISTS eventos")

    _f = open("data/db_setup.sql", "r")
    sql = _f.read()
    db.executescript(sql)

    # Por cada imagin en el directorio
    for img in sorted(os.listdir(directory)):
        # Obtener path incluyendo directorio (dataset/img.jpg)
        file_dir = os.path.join(directory, img)
        # Conseguir el Nombre de el archivo 
        file_name = os.path.basename(file_dir)
        # Conseguir el Nombre sin extension de archivo
        f_name = os.path.splitext(file_name)[0]

        # TODO: SPLIT TEXT AT '_'
        id_name = f_name.split('_')
        m_id = id_name[0]
        name = id_name[1]

        values = (m_id, name)

        cur.execute("INSERT INTO maestros(maestroid, nombre) VALUES (?,?)", values)
        db.commit()

        # Cargar la imagen usando su ubicacion    
        face_img = face_recognition.load_image_file(file_dir)
        # Cargar el encoding de la imagen
        face_encoding = face_recognition.face_encodings(face_img)[0]

        # Agregar el encoding a el diccionario
        # ([name]: [encoding])
        known_face_encodings[m_id] = face_encoding
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


def write_event(salon, maestro=None):
    db = get_db()
    cur = db.cursor()
    sio = socketio.Client()
    sio.connect('http://localhost:5000')

    last_time = cur.execute('''SELECT unix 
                        FROM eventos 
                        ORDER BY eventoid DESC LIMIT 1;''').fetchone()
    print(last_time)
    if last_time is not None:
        print(f"last_time: {last_time['unix']}")
        timedelta = (int(time.time()) - last_time['unix'])
    else:
        timedelta = 3

    if timedelta >= 3:
        # Enviar evento a el servidor para ser broadcasted a los clientes
        print(f"allowed: {timedelta}")

        unix = int(time.time())

        now = datetime.now()
        tiempo = now.strftime("%Y-%m-%d %H:%M")

        if maestro is None:
            sql = ''' INSERT INTO eventos(tipo, salon, tiempo, unix)
                    VALUES(?,?,?,?) '''
            values = ('PARADA', salon, tiempo, unix)
        else:

            sql = ''' INSERT INTO eventos(tipo, salon, tiempo, unix, maestro)
                    VALUES(?,?,?,?,?) '''
            values = ('RECONOCIMIENTO', salon, tiempo, unix, maestro)

        cur.execute(sql, values)
        db.commit()

        data = cur.execute('''SELECT eventos.eventoid, eventos.tipo, eventos.salon, eventos.tiempo, maestros.nombre 
                            FROM eventos 
                            LEFT JOIN maestros 
                            ON eventos.maestro = maestros.maestroid 
                            ORDER BY eventoid DESC LIMIT 1;''').fetchall()[0]

        # db = get_db()

        # TODO: SEND SERIALIZED DATA!!!
        sio.emit('event',
                 {'id': data['eventoid'], 'tipo': data['tipo'], 'salon': data['salon'], 'maestro': data['nombre'],
                  'tiempo': data['tiempo']})
        # Cerrar conexion
    else:
        print(f"rejected: {timedelta}")


def write_to_dataset(frame, name):
    db = get_db()
    cur = db.cursor()

    data = cur.execute('''SELECT maestroid 
                          FROM maestros 
                          ORDER BY maestroid DESC LIMIT 1;''').fetchone()
    print(data)
    if data is not None:
        cv2.imwrite(f"dataset/{int(data['maestroid']) + 1}_{name}.jpg", frame)
    else:
        cv2.imwrite(f"dataset/1_{name}.jpg", frame)


def read_events():
    db = get_db()
    # Une la tabla Eventos donde la id de Maestro es igual y agrega su nombre
    events = db.execute(
        'SELECT eventos.eventoid, eventos.tipo, eventos.salon, eventos.tiempo, maestros.nombre FROM eventos LEFT JOIN '
        'maestros ON eventos.maestro = maestros.maestroid;').fetchall()
    db.close()

    # Esto se regresa a la template de index
    return events
