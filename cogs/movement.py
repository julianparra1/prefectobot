from multiprocessing import Process
from gpiozero import Servo, Motor
from gpiozero.pins.pigpio import PiGPIOFactory

import time

# Ancho de pulso 0.5ms ON / 2.5ms OFF 
# PiGPIO para evitar jitter
servoY = Servo("GPIO14", min_pulse_width=0.5 / 1000, max_pulse_width=2.5 / 1000, pin_factory=PiGPIOFactory())
servoX = Servo("GPIO15", min_pulse_width=0.5 / 1000, max_pulse_width=2.5 / 1000, pin_factory=PiGPIOFactory())


# Inizializa proceso para movimiento y pasa argumentos
# Es mas facil controlar el movimiento de esos motores asi
def move(Global=None):
    # Checar si se nos a brindado un argumento

    # Solo se nos pasara una variable global si viene de procesamiento
    # En caso de que no sea asi, hacemos pasos mas grandes aumentando el tiempo
    if Global is not None:
        m = Process(target=_move, args=(Global,))
        m.start()

def _move(Global):
    i = Motor("GPIO16", "GPIO12")
    d = Motor("GPIO20", "GPIO21")
    fs = 0.35
    s = 0.7
    # Si no venimos de un proceso ignoramos Globla
    while True:
        if Global.task == "roam":
        # Por razones de no confundirme, los motores estan nombrados al revez
        # Esto porque al acelerar los motores de un lado giramos a el otro
            if Global.f == 'f':
                while not Global.find_center:
                    time.sleep(0.4)
                    d.value= 0
                    i.value= 0
                    time.sleep(0.4)
                    d.value= fs
                    i.value= fs
            # GIRAR a la Izquierda
            elif Global.f == 'l':
                while Global.find_center:
                    d.value= 0
                    i.value= s
            # GIRAR a la Derecha
            elif Global.f == 'r':
                while Global.find_center:
                    i.value= 0
                    d.value= s
            elif Global.f == 'mr':
                while Global.find_center:
                    i.value= 0
                    d.value= s -0.1
                    time.sleep(0.03)
                    Global.find_center = False
            elif Global.f == 'ml':
                while Global.find_center:
                    d.value= 0
                    i.value= s -0.1
                    time.sleep(0.03)
                    Global.find_center = False
            elif Global.f == "b":
                i.value = -1
                d.value = -1
    # En caso de que vengamos de un proceso, indicar que ya no nos estamos moviendo
    


def servo(arg=None, x=None, y=None):
    # Si se pasa argumento x
    if x is not None:
        servoX.value = x

    # Si se pasa argumento x
    if y is not None:
        servoX.value = y

    # Posiciones en el plano incorrectas (inversas) para x
    try:
        if arg == "+y":
            servoY.value += 0.1
        elif arg == "-y":
            servoY.value -= 0.1
        elif arg == "+x":
            servoX.value += 0.1
        elif arg == "-x":
            servoX.value -= 0.1
        elif arg == "roam":
            servoY.value = -0.6
            servoX.value = 0
        elif arg == "recognize":
            servoY.value = 0.5
            servoX.value = -1
        else:
            return
    except (ValueError, Exception):
        print(Exception)
