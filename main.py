import time

from flask import Flask, render_template, Response, send_from_directory
from flask_socketio import SocketIO

from gpiozero import Servo, Motor
from gpiozero.pins.pigpio import PiGPIOFactory

import cam_multi

app = Flask(__name__)
socketio = SocketIO(app)

# Posicion default
# Ancho de pulso 0.5ms ON / 2.5ms OFF 
# PiGPIO para evitar jitter
servoY = Servo("GPIO14", min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory= PiGPIOFactory())
servoX = Servo("GPIO15", min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory= PiGPIOFactory())
print("setting pos")
servoY.value = -0.5
servoX.value = 0

cam_multi.start()

# Este es el feed de video donde enviamos las imagenes con el deamon de la camera (donde siempre se esta procesando esta misma al inicializar el objeto)
@app.route('/video_feed')
def video_feed():
    return Response(cam_multi.get_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/dataset/<path:path>')
def send_report(path):
    return send_from_directory('dataset', path)

# Devuelve la pagina principal
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

# SocketIO para recibir mensajes de la aplicacion web
@socketio.on('+y') #arriba
def handle_message():
    try:
        servoY.value +=  0.1
    except:
        pass
    print(servoY.value)
    
@socketio.on('-y') #abajo
def handle_message():
    try:
        servoY.value -= 0.1
    except:
        pass
    print(servoX.value)

# Posiciones en el plano incorrectas (inversas) para x *por la forma en la que se instalaron los motores 😣
@socketio.on('+x') #izquierda 
def handle_message():
    try:
        servoX.value += 0.1
    except:
        pass
    print(servoX.value)

@socketio.on('-x') #derecha
def handle_message():
    try:
        servoX.value -= 0.1
    except:
        pass
    print(servoX.value)



# control de motores
#TODO: FINALIZAR CONTROL DE MOTORES
"""
d = Motor("GPIO16", "GPIO12")
i = Motor("GPIO20", "GPIO21")

@socketio.on('forward') 
def handle_message():
    d.value = 1
    i.value = 1
    time.sleep(2)
    d.stop()
    i.stop()

@socketio.on('backward')
def handle_message():
    d.value = -1
    i.value = -1
    time.sleep(2)
    d.stop()
    i.stop()

@socketio.on('left')
def handle_message():
    i.value = 1
    time.sleep(2)
    d.stop()
    i.stop()
@socketio.on('right')
def handle_message():
    d.value = 1
    time.sleep(2)
    d.stop()
    i.stop()
"""

@socketio.on('capture')
def handle_message():
    cam_multi.capture()

@socketio.on('roam')
def handle_message():
    cam_multi.roam()

@socketio.on('recognize')
def handle_message():
    cam_multi.recognize()

@socketio.on('stop_tasks')
def handle_message():
    cam_multi.stop_tasks()
    
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')



    

