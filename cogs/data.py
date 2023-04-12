"""
prefectobot.cogs.data
~~~~~~~~~~~~~~~~~~~~~

Modulo de manejo de datos de el robot
"""

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
    """Funcion para obtener coneccion a la base de datos."""
    
    # Conectarse a el archivo (si no existe lo crea)
    conn = sqlite3.connect('data/prefectbot.sqlite')
    # Le decimos a sqlite que queremos Rows en forma de diccionarios
    # Luego como objeto iterable Query -> item['row']
    conn.row_factory = sqlite3.Row
    
    # regresamos la conexion
    return conn


def read_encodings():
    """Lee los encodings guardados como pickle."""

    # Lee archivo de encodings guardados
    with open('data/face_encodings.dat', 'rb') as f:
        known_face_encodings = pickle.load(f)
    # Devolver los valores como (Encodings<np.array(list)>, Names<List>)
    return np.array(list(known_face_encodings.values())), list(known_face_encodings.keys())


def write_encodings(directory):
    """Escribe los encodings a pickle usando las imagenes de el directorio que se pase. """
    
    # Inicializar diccionario de encodings
    known_face_encodings = {}
    # Obtenemos coneccion y creamos un cursor
    db = get_db()
    cur = db.cursor()
    
    # Borramos las tablas existentes
    cur.execute("DROP TABLE IF EXISTS maestros")
    cur.execute("DROP TABLE IF EXISTS eventos")
    cur.execute("DROP TABLE IF EXISTS salones")

    # Abrimos las instruccions SQL guardadas
    _f = open("data/db_setup.sql", "r")
    sql = _f.read()
    # Y las ejecutamos
    db.executescript(sql)

    # Por cada imagen en el directorio
    if os.listdir(directory):
        for img in sorted(os.listdir(directory)):
            # Obtener path incluyendo directorio (dataset/img.jpg)
            file_dir = os.path.join(directory, img)
            # Conseguir el Nombre de el archivo 
            file_name = os.path.basename(file_dir)
            # Conseguir el Nombre sin extension de archivo
            f_name = os.path.splitext(file_name)[0]
            
            # Partimos la imagen en {id}_{nombre}
            id_name = f_name.split('_')
            # {id}
            m_id = id_name[0]
            # {nombre}
            name = id_name[1]

            # Valores que agregaremos
            values = (m_id, name, file_name)
            # Ejecutamos la insercion de valores
            cur.execute("INSERT INTO maestros(id, nombre, file_url) VALUES (?,?,?)", values)
            db.commit()

            # Cargar la imagen usando su ubicacion    
            face_img = face_recognition.load_image_file(file_dir)
            # Obtener el encoding de la imagen
            face_encoding = face_recognition.face_encodings(face_img)[0]

            if face_encoding.any():
                # Agregar el encoding a el diccionario
                # {[name]: [encoding]}
                known_face_encodings[m_id] = face_encoding
        # Guardar el diccionario como un pickle
        with open('data/face_encodings.dat', 'wb') as f:
            pickle.dump(known_face_encodings, f)
    else:
         with open('data/face_encodings.dat', 'wb') as f:
            pickle.dump(known_face_encodings, f)
    


def setup_db():
    """ Verificamos la integridad de la base de datos """
    
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
        db = get_db()
        print("Base de datos verificada!")
        db.close()


def salon_check(salon):
    """Checamos si el salon existe en la base de datos. Devuelve True o False dependiendo de si es encontrado."""
    db = get_db()
    cur = db.cursor()
    data = cur.execute('''SELECT id
                            FROM salones 
                            WHERE id=?;''', salon).fetchone()  
    if data is not None:
        return True
    else:
        return False
    

def write_stop(salon):
    """
    Escribimos la parada de el robot usando el salon y la enviamos a cada usuario que lo requiera.
    """
    
    db = get_db()
    cur = db.cursor()
    
    # Chequeo de tiempo
    
    # Inicializamos cliente de SocketIO para enviar informacion a todos los usuarios
    sio = socketio.Client()
    sio.connect('http://localhost:5000')

        
    # Incluimos tiempo UNIX actual para usar en calculos de tiempo
    
    # Fecha normal... para humanos normales...
    now = datetime.now()
    tiempo = now.strftime("%Y-%m-%d %H:%M")

    sql = ''' INSERT INTO eventos(tipo, salon, tiempo)
                VALUES(?,?,?,?) '''
    values = ('PARADA', salon, tiempo)

    cur.execute(sql, values)
    db.commit()

    # Devolvemos los datos que acabamos de obtener usando SocketIO
    data = cur.execute('''SELECT eventos.id, eventos.tipo, eventos.tiempo, salones.nombre  
                        FROM eventos
                        LEFT JOIN salones
                        ON eventos.salon = salones.id 
                        ORDER BY eventos.id DESC LIMIT 1;''').fetchone()

    sio.emit('event',
                {'id': data['id'], 'tipo': data['tipo'], 'salon': data['nombre'], 'maestro': None,
                'tiempo': data['tiempo']})

def write_rec(salon, maestro=None):
    """
    Escribimos el reconocimiento de una cara por el robot usando el salon y la enviamos a cada usuario que lo requiera.
    """
    
    # Inicializamos cliente de SocketIO para enviar informacion a todos los usuarios
    sio = socketio.Client()
    sio.connect('http://localhost:5000')

    # Obtenemos conexion a la base de datos y creamos cursor
    db = get_db()
    cur = db.cursor()
    
    # Checamos ultimo tiempo

        # Enviar evento a el servidor para ser broadcasted a los clientes

    now = datetime.now()
    tiempo = now.strftime("%Y-%m-%d %H:%M")

    sql = ''' INSERT INTO eventos(tipo, salon, tiempo, maestro)
            VALUES(?,?,?,?) '''
    values = ('RECONOCIMIENTO', salon, tiempo, maestro)

    cur.execute(sql, values)
    db.commit()

    data = cur.execute('''SELECT eventos.id, eventos.tipo, eventos.salon, eventos.tiempo, maestros.nombre 
                        FROM eventos 
                        LEFT JOIN maestros 
                        ON eventos.maestro = maestros.id 
                        ORDER BY eventos.id DESC LIMIT 1;''').fetchall()[0]

    sio.emit('event',
                {'id': data['id'], 'tipo': data['tipo'], 'salon': data['salon'], 'maestro': data['nombre'],
                'tiempo': data['tiempo']})
    
    # Devolvemos bandera para ver si es necesario decir su nombre
    return data['nombre']



def write_to_dataset(frame, name):
    """Escribe el archivo con la id que se le asigne"""
    
    # Con la captura escribimos el archivo con su id
    db = get_db()
    cur = db.cursor()

    data = cur.execute('''SELECT id 
                          FROM maestros 
                          ORDER BY id DESC LIMIT 1;''').fetchone()
    print(f'maestros {data}')
    if data is not None:
        cv2.imwrite(f"dataset/{int(data['id']) + 1}_{name}.jpg", frame)
    else:
        cv2.imwrite(f"dataset/1_{name}.jpg", frame)
        

def read_maestros():
    """Devuelve todos los Maestros guardados para ser serializados"""
    
    db = get_db()
    maestros = db.execute('SELECT * FROM maestros').fetchall()
    db.close()

    # Esto se regresa a la template de index
    return maestros


def read_events():
    """Devuelve todos los Eventos guardados con los ids de maestros y salones cambiados por sus nombres legibles para ser serializados"""
    
    db = get_db()
    # Une la tabla Eventos donde la id de Maestro es igual y agrega su nombre
    events = db.execute(
        '''SELECT eventos.id, eventos.tipo, eventos.tiempo, maestros.nombre AS maestro_nombre, salones.nombre AS salon_nombre FROM eventos 
           LEFT JOIN maestros ON eventos.maestro = maestros.id
           LEFT JOIN salones ON eventos.salon = salones.id;''').fetchall()

    db.close()

    # Esto se regresa a la template de index
    return events

def read_salones():
    """Devuelve todos los Salones guardados para ser serializados"""
    
    db = get_db()
    # Une la tabla Eventos donde la id de Maestro es igual y agrega su nombre
    salones = db.execute('SELECT * FROM Salones').fetchall()
    db.close()

    # Esto se regresa a la template de index
    return salones

def add_salon(name):
    """Agregamos un nuevo salon a la base de datos"""
    
    db = get_db()
    cur = db.cursor()
        
    cur.execute("INSERT INTO salones(nombre) VALUES(?)", (name,))
    db.commit()
    
    id = cur.execute('''SELECT id FROM salones ORDER BY id DESC LIMIT 1;''').fetchone()
    
    # Si todo salio bien devolvemos el ID
    if id is not None:
        return id['id']

def del_salon(id):
    """Borramos salon por ID"""

    db = get_db()
    cur = db.cursor()
        
    cur.execute("DELETE FROM salones WHERE id = ?", (id,))
    db.commit()
