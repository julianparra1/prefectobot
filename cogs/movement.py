"""
prefectobot.cogs.movement
~~~~~~~~~~~~~~~~~~~~~

Modulo de manejo de movimiento de el robot
"""

from multiprocessing import Process
from gpiozero import Servo, Motor
from gpiozero.pins.pigpio import PiGPIOFactory

import time

# Ancho de pulso 0.5ms ON / 2.5ms OFF 
# PiGPIO para evitar jitter


# Inizializa proceso para movimiento y pasa argumentos
# Es mas facil controlar el movimiento de esos motores asi

def _move(Global):
    i = Motor("GPIO16", "GPIO12")
    d = Motor("GPIO20", "GPIO21")
    fs = 0.5
    s = 0.9
    # Si no venimos de un proceso ignoramos Globla
    while True:
        if Global.task == "roam":
        # Por razones de no confundirme, los motores estan nombrados al revez
        # Esto porque al acelerar los motores de un lado giramos a el otro
            if Global.f == 's':
                d.stop()
                i.stop()
            if Global.f == 'f':
                time.sleep(0.2)
                d.value= 0
                i.value= 0
                time.sleep(0.2)
                d.value= fs
                i.value= fs
            
            # GIRAR a la Izquierda
            if Global.f == 'l':
                time.sleep(0.15)
                d.value = 0
                i.value = s
                time.sleep(0.15)
                d.value = 0
                i.value = 0
                
            # GIRAR a la Derecha
            if Global.f == 'r':
                time.sleep(0.15)
                i.value = 0
                d.value = s
                time.sleep(0.15)
                d.value = 0
                i.value = 0
                
            if Global.f == 'mr':
                time.sleep(0.15)
                i.value = 0
                d.value = s - 0.06
                time.sleep(0.15)
                d.value = 0
                i.value = 0
                
            if Global.f == 'ml':
                time.sleep(0.15)
                d.value = 0
                i.value = s - 0.06
                time.sleep(0.15)
                d.value = 0
                i.value = 0
                
            if Global.f == "b":
                i.value = -1
                d.value = -1        
                
        elif Global.task == 'none':
            if Global.f == 's':
                d.stop()
                i.stop()
            if Global.f == 'f':
                d.value= 1
                i.value= 1
            if Global.f == 'l':
                i.value = 1
                d.value = 0
            if Global.f == 'r':
                i.value = 0
                d.value = 1
            if Global.f == "b":
                i.value = -1
                d.value = -1
        else:
            Global.find_center = False
            d.value = 0
            i.value = 0
            
            
    # En caso de que vengamos de un proceso, indicar que ya no nos estamos moviendo
    
class MovementManager:
    def __init__(self, Global):
        self.servoY = Servo("GPIO14", min_pulse_width=0.5 / 1000, max_pulse_width=2.5 / 1000, pin_factory=PiGPIOFactory())
        self.servoX = Servo("GPIO15", min_pulse_width=0.5 / 1000, max_pulse_width=2.5 / 1000, pin_factory=PiGPIOFactory())
        # Checar si se nos a brindado un argumento
        self.Global = Global
        # Solo se nos pasara una variable global si viene de procesamiento
        # En caso de que no sea asi, hacemos pasos mas grandes aumentando el tiempo
        
    def start_movement_processes(self):
        if self.Global is not None:
            m = Process(target=_move, args=(self.Global,))
            m.start()
            
    def servo(self, arg=None, x=None, y=None):
        # Si se pasa argumento x
        if x is not None:
            self.servoX.value = x

        # Si se pasa argumento x
        if y is not None:
            self.servoX.value = y

        # Posiciones en el plano incorrectas (inversas) para x
        try:
            if arg == "+y":
                self.servoY.value += 0.1
            elif arg == "-y":
                self.servoY.value -= 0.1
            elif arg == "+x":
                self.servoX.value += 0.1
            elif arg == "-x":
                self.servoX.value -= 0.1
            elif arg == "roam":
                self.servoY.value = -0.7
                self.servoX.value = 0
            elif arg == "recognize":
                self.servoY.value = 0.5
                self.servoX.value = -1
            else:
                return
        except (ValueError, Exception):
            print(Exception)




