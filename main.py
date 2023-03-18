import time

import sys

from flask import Flask, render_template, Response, send_from_directory
from flask_socketio import SocketIO, emit

from cogs import processing, movement, data, voice

try:
    arg = sys.argv[1]
except IndexError:
    arg = ""

if arg == '-w':
    print('writing encodings')
    data.write_encodings('dataset/')

app = Flask(__name__)
socketio = SocketIO(app)


# Este es el feed de video donde enviamos las imagenes con el deamon de la camera (donde siempre se esta procesando
# esta misma al inicializar el objeto)
@app.route('/video_feed')
def video_feed():
    return Response(processing.get_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/dataset/<path:path>')
def send_report(path):
    return send_from_directory('dataset', path)


# Devuelve la pagina principal
@app.route('/')
def index():
    """Video streaming home page."""
    events = data.read_events()
    return render_template('index.html', events=events)

@app.route('/config')
def config():
    salones = data.read_salones()
    maestros = data.read_maestros()
    return render_template('config.html', salones=salones, maestros=maestros)


# SocketIO para recibir mensajes de la aplicacion web

@socketio.on('event')
def handle_message(data):
    emit('event', data, broadcast=True)
    
@socketio.on('add_salon')
def handle_message(name):
    print(name)
    id = data.add_salon(name)
    emit('add_salon', {'id': int(id), 'nombre': name}, broadcast=True)

@socketio.on('del_salon')
def handle_message(id):
    data.del_salon(id)



@socketio.on('servo')  # Controlar Servo
def handle_message(data):
    movement.servo(arg=data)


@socketio.on('motor')  # Controlar Ruedas
def handle_message(data):
    movement.move(arg=data)


@socketio.on('set_task')  # Seleccionar tarea
def handle_message(data):
    processing.set_task(task=data)


@socketio.on('capture')
def handle_message(data):
    print(data)
    print("CAPTURE")
    processing.capture(data)

if __name__ == '__main__':
    processing.start()
    data.setup_db()
    socketio.run(app, host='0.0.0.0') #ssl_context='adhoc'
