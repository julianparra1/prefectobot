                                                                        
#  .oPYo.               d'b                 o          .oPYo.          o  
#  8    8               8                   8          8   `8          8  
# o8YooP' oPYo. .oPYo. o8P  .oPYo. .oPYo.  o8P .oPYo. o8YooP' .oPYo.  o8P 
#  8      8  `' 8oooo8  8   8oooo8 8    '   8  8    8  8   `b 8    8   8  
#  8      8     8.      8   8.     8    .   8  8    8  8    8 8    8   8  
#  8      8     `Yooo'  8   `Yooo' `YooP'   8  `YooP'  8oooP' `YooP'   8  
# :..:::::..:::::.....::..:::.....::.....:::..::.....::......::.....:::..:
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
"""
PrefectoBot
~~~~~~~~~~~~~~~~~~~~~

Robot con la capacidad de realizar tareas de prefecto 

:copyright: (c) 2023-present by Julian Parra
:license: MIT License, see LICENSE for more details.
"""


import sys

import json
from flask import Flask, render_template, Response, send_from_directory, request
from flask_socketio import SocketIO, emit
from cogs import processing, movement, data                                                     
from multiprocessing import Manager
import logging

# Verificar si existe un argumento
try:
    arg = sys.argv[1]
except IndexError:
    arg = ""

# Si el argumento que fue enviado es '-w' escribimos nuevos encodings
if arg == '-w':
    logging.warning('Watch out!')
    data.write_encodings('dataset/')
    
Global = Manager().Namespace()
# Creamos aplicacion de Flask
# y los 'cubrimos' con la capa de SocketIo
app = Flask(__name__)
socketio = SocketIO(app, logger=False)

# Este es el feed de video donde serializamos la imagen procesada
@app.route('/video_feed')
def video_feed():
    return Response(processing.get_frames(Global), mimetype='multipart/x-mixed-replace; boundary=frame')

# Damos acceso a el directorio donde se encuentran las fotos para reconocimiento
@app.route('/dataset/<path:path>')
def send_report(path):
    return send_from_directory('dataset', path)


# Devuelve la pagina principal (index)
# Pasamos los eventos que ya tenemos guardados para incluirlos en la tabla de la template
@app.route('/')
def index():
    """Video streaming home page."""
    events = data.read_events()
    return render_template('index.html', events=events)


@app.route('/post', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'photo' not in request.files:
            return json.dumps({'response': '400 Bad Request'}), 400, {'ContentType':'application/json'} 
        file = request.files['photo']
        processing.face_rec_login(file.read())
    return json.dumps({'response': '200 Success'}), 200, {'ContentType':'application/json'} 


# Pagina de configuracion
# Pasamos salones y maestros que ya tenemos guardados para incluirlos en sus respectivas tablas
@app.route('/config')
def config():
    salones = data.read_salones()
    maestros = data.read_maestros()
    return render_template('config.html', salones=salones, maestros=maestros)


# SocketIO para recibir mensajes de la aplicacion web 
# La app y el robot mismo utilizan un cliente para enviar mensajes/comandos

# Al recivir un nuevo evento
# -> Repetimos el mensaje para todos los que lo estan escuchando
@socketio.on('event')
def handle_message(data):
    emit('event', data, broadcast=True)

# Al agregar un salon
# -> Creamos un nuevo registro y respondemos con la id que se le asigno 
@socketio.on('add_salon')
def handle_message(name):
    print(name)
    id = data.add_salon(name)
    emit('add_salon', {'id': int(id), 'nombre': name}, broadcast=True)

# En caso de borrar una salon
# -> Borramos el registro con la id que se nos envio
@socketio.on('del_salon')
def handle_message(id):
    data.del_salon(id)


# Al presionar botones de movimiento para el servo (pitch y yaw de la camara)
# Pasamos el argumento a el modulo de movimiento

# La interfaz para poder realizar movimientos es sencilla:
# '+y' '-y', '+x' '-x'
@socketio.on('servo')  # Controlar Servo
def handle_message(data):
    movement.servo(arg=data)

@socketio.on('motor')  # Controlar Ruedas
def handle_message(data):
    if data != 's':
        processing.set_task(Global, 'none')
    Global.f = data

# Cambiar la tarea actual de el robot
# -> 'roam', 'rec', 'none'
@socketio.on('set_task')  # Seleccionar tarea
def handle_message(data):
    processing.set_task(Global, data)

# Al presionar boton de captura
# -> Pasamos el nombre en el campo captura a el modulo de procesamiento
@socketio.on('capture')
def handle_message(data):
    processing.capture(Global, data)

@socketio.on('brightness')
def handle_message(data):
    if data == '+' and Global.beta < 100:
        Global.beta += 10
    elif data == '-' and Global.beta > -100:
        Global.beta -= 10
        
@socketio.on('contrast')
def handle_message(data):
    if data == '+' and Global.alpha < 4:
        Global.alpha += 0.1
    elif data == '-' and Global.alpha > 0:
        Global.alpha -= 0.1
        

@socketio.on('reset')
def handle_message():
    Global.alpha = 1
    Global.beta = 0


if __name__ == '__main__':
    # Inicializa los procesos para el procesamiento de imagenes    
    processing.start(Global)
    
    # Verificamos que todo este bien con la base de datos
    # Tambien nos aseguramos de que exista
    data.setup_db()
    
    # Iniciamos aplicacion Flask+SocketIo
    socketio.run(app, host='0.0.0.0') #ssl_context='adhoc'
