"""
prefectobot.cogs.voice
~~~~~~~~~~~~~~~~~~~~~

Modulo de manejo de voz
"""
import pyttsx3

def saludar(name):
    engine = pyttsx3.init()
    engine.setProperty('voice', 'spanish-latin-am')
    engine.say(f'Buenos dias {name}!')
    engine.runAndWait()