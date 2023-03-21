from math import floor
import time
from picamera2 import Picamera2
from multiprocessing import Process, Manager
import face_recognition
import numpy as np
import cv2

from cogs import movement, data, voice

# https://docs.python.org/3/library/multiprocessing.html
Global = Manager().Namespace()
read_frame_list = Manager().dict()
write_frame_list = Manager().dict()

workers = 4  # 3 workers + camara


def next_id(current_id, worker_num):
    if current_id == worker_num:
        return 1
    else:
        return current_id + 1


def prev_id(current_id, worker_num):
    if current_id == 1:
        return worker_num
    else:
        return current_id - 1


def _capture(read_frame_list, Global, worker_num):
    picam2 = Picamera2()
    print(picam2.sensor_resolution)
    # iniciamos configuracion con formato legible para face_recognizer
    picam2.configure(picam2.create_video_configuration(main={"format": 'RGB888', "size": (2328, 1748)}, ))

    # Configuracion de el autofocus (continuous focus)
    picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
    picam2.start()

    while True:
        # Esperar a ver si ya termino de leer el proceso anterior
        if Global.buff_num != next_id(Global.read_num, worker_num):
            # Escribir frame para el worker con el id que sigue
            frame = picam2.capture_array("main")
            resized = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            read_frame_list[Global.buff_num] = resized
            Global.buff_num = next_id(Global.buff_num, worker_num)
        else:
            time.sleep(0.01)


def process(worker_id, read_frame_list, write_frame_list, Global, worker_num):
    # Proceso ya empezo
    print(f"process {worker_id} started!")
    
    # Inicializamos lector de qr
    qcd = cv2.QRCodeDetector()
    
    # Cargamos los encodings con sus respectivos nombres
    known_face_encodings = Global.known_face_encodings
    known_face_names = Global.known_face_names
    
    # Loop de el proceso
    while True:
        # Esperamos a que sea nuestro turno para leer
        while Global.read_num != worker_id or Global.read_num != prev_id(Global.buff_num, worker_num):
            time.sleep(0.01)

        # Lee el frame asignado al worker
        frame = read_frame_list[worker_id]

        # Escribir el trabajador siguiente para que lea
        Global.read_num = next_id(Global.read_num, worker_num)

        # Vemos cual es la tarea actual
        if Global.task == "none":
            pass

        # En modo roam buscamos el camino
        if Global.task == "roam":
            #TODO: COLOR BALANCE / BRIGHTNESS 

            # Otsu's Binarization !!!!
            #gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
            #blur = cv2.GaussianBlur(gray, (9,9), 0)
            
            #blur = cv2.medianBlur(gray,5)
            #_, mask = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
            
            # Dentro de un try porque hay un problema con OpenCV que es super especifico
            # Pero crashear significa no mas procesamiento entonces mejor atrapamos el error
            try:
                # Si se detecta un QR retval devuelve True
                retval, decoded_info, ps, straight_qrcode = qcd.detectAndDecodeMulti(frame)

                # Verificamos que todo este bien con el codigo qr....
                if retval and ps is not None:
                    
                    # Dibujamos polígono donde se encuentran los puntos de el QR
                    cv2.polylines(frame, ps.astype(int), True, (0, 255, 0), 3)
                    
                    # Leemos la información del codigo QR y lo juntamos con sus respectivos puntos
                    for decoded_salon, ps in zip(decoded_info, ps):
                        
                        # Verificamos que si se haya leido la informacion de el QR
                        # y lo comparamos con la base de datos existente de codigos
                        if decoded_salon != "" and data.salon_check(decoded_salon):
                            #print(f'Decoded: {decoded_salon}')
                            # Anunciamos la parada
                            data.write_stop(decoded_salon)
                            # Este es el salon en que se hara la deteccion
                            Global.salon = decoded_salon
                            # Cambiamos la tarea a reconocimiento 
                            set_task("recognize")
                            

                        # Cuadro con texto decodificado del codigo qr
                        # Como es un poligono el rectangulo puede verse un poco distorcionado     
                        cv2.putText(frame, decoded_salon, ps[0].astype(int), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
            
            # Basicamente ignoramos el error.... en este caso no es relevante            
            except cv2.error as e:
                print(f'QRCode fail: {e}')
            
            
            # resized_frame = cv2.resize(frame, (0,0), fx=0.4, fy=0.4)
            
            # Convertimos el espacio de color a hsv (más facil procesar el rango de colores)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Bounds de los colores en hsv
            # HSV en OpenCV es: H: H/2 (360 -> 100), S: S/100*255 (100 -> 255), V: V/100*255 (100 -> 255) !!!!
            low_b = np.uint8([0, 0, 0])
            high_b = np.uint8([180, 90, 50])

            # Mascara donde buscamos los colores dentro del rango especificado arriba
            mask = cv2.inRange(hsv, low_b, high_b)

            # https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
            # Buscamos los contornos en la mascara
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            if len(contours) > 0:
                # Buscamos el contorno mas grande por area
                c = max(contours, key=cv2.contourArea)
                
                # Momentos de imagen 
                # https://en.wikipedia.org/wiki/Image_moment
                # https://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
                # todo lo hace el computador 🙏👍    
                M = cv2.moments(c)
                
                # Si el momento existe y el area del contorno es mayor a 500
                if M["m00"] != 0 and cv2.contourArea(c) > 500:
                    
                    # Solo es relevante la x para nosotros
                    cx = int(M['m10'] / M['m00'])
                    #cy = int(M['m01'] / M['m00'])

                    # Segun la ubicación virtual del centroide elegimos a donde ir
                    if cx <= 100:
                        Global.f = 'l'
                    if cx > 100 and cx < 200:
                        Global.f = 'ml'
                    if cx > 200 and cx < 381:
                        Global.f = 'f'
                    if cx > 381 and cx < 481:
                        Global.f = 'mr'
                    if cx >= 481:
                        Global.f = 'r'
                    # Dibujamos el centroide
                    cv2.circle(frame, (cx, 218), 1, (0, 0, 255), 3)

                    # Iniciamos proceso para movimiento segun la ubicación del centroide
                    cv2.drawContours(frame, c, -1, (0, 255,), 6, )
            
            # Bounding boxes para decicion de girar        
            cv2.rectangle(frame, (0, 0), (100, 436), (255, 0, 0), 1)
            cv2.rectangle(frame, (100, 0), (200, 436), (255, 0, 0), 1)
            
            cv2.rectangle(frame, (200, 0), (381, 436), (255, 0, 0), 1)
            
            cv2.rectangle(frame, (381, 0), (481, 436), (255, 0, 0), 1)
            cv2.rectangle(frame, (481, 0), (581, 436), (255, 0, 0), 1)
            

        if Global.task == "recognize":

            # Achicamos el frame para procesarlo mas rapido
            resized_frame = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)

            # Buscamos las caras en el frame de video y sus encodings en el frame
            face_locations = face_recognition.face_locations(resized_frame)
            face_encodings = face_recognition.face_encodings(resized_frame, face_locations)

            # Inicializamos lista de nombres
            names = []
            # Por cada encoding en los encodings que encontramos
            for face_encoding in face_encodings:

                # Comparamos el encoding encontrado en el frame con los que ya conocemos
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Desconocido"

                # Comparamos las distancias entre caras con las que ya conocemos
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                # Buscamos la mejor coincidencia
                best_match_index = np.argmin(face_distances)
                face_distance = face_distances[best_match_index]

                # print(f"for {face_distances} : {face_distances < 0.45}")
                # print(f"for idx {best_match_index} : {face_distance < 0.45}")

                # Segun la distancia queremos ver que tan lejos esta la cara con la mejor coincidencia
                # Si la distancia es menor a 0.45
                if face_distance < 0.45:
                    # Si existe en el array...
                    if matches[best_match_index]:
                        # Las listas estan ordenadas
                        id = known_face_names[best_match_index]
                        # Con los IDs de lista podemos encontrar a el maestro
                        # Nos regresa su nombre al terminar de guardar el evento
                        (flag, name) = data.write_rec(Global.salon, id)
                        # Solo hablar una vez
                        if flag:
                            voice.saludar(name)
                        # Al terminar volvemos a buscar la linea
                        set_task("roam")
                # Agregamos la cara encontrada a la lista
                names.append(name)

            # Por cada cara en el frame:
            # juntamos ubicaciones y sus nombres
            for (top, right, bottom, left), name in zip(face_locations, names):
                # Cambiamos las coordenadas de los puntos, pues se procesó una imagen reducida (1x > 1/4x > 1/10x)
                # .25 * .4 = .1
                # .1 * 2.5 = .25 
                # Entonces 
                # modf = 2.5
                
                modifier = 2.5
                top = floor(top * modifier)
                right = floor(right * modifier)
                bottom = floor(bottom * modifier)
                left = floor(left * modifier)

                # Dibujamos un rectangulo donde se encuntra la cara
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Cuadro con texto debajo
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

        # Esperar a que sea nuestro turno para escribir un nuevo frame
        while Global.write_num != worker_id:
            time.sleep(0.01)

        # Parametros para compresion JPEG
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 65, int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
                         int(cv2.IMWRITE_JPEG_OPTIMIZE), 1]
        (_, encodedImage) = cv2.imencode(".jpg", frame, encode_params)

        # Escribir frame en Global
        write_frame_list[worker_id] = encodedImage

        # Otro proceso ya puede escribir otro frame
        Global.write_num = next_id(Global.write_num, worker_num)


def get_frames():
    last_num = 1
    while True:
        # Checar si no es el mismo frame que el anterior
        while Global.write_num != last_num:
            last_num = int(Global.write_num)
            # Escribir el último frame terminado y etiquetar
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + bytearray(
                write_frame_list[prev_id(Global.write_num, workers)]) + b'\r\n')


def capture(name):
    # Leer el frame actual
    if Global.read_num != prev_id(Global.buff_num, workers):
        frame = read_frame_list[Global.read_num]
        # Convertir a Escala de grises
        # Buscar caras
        face_locations = face_recognition.face_locations(frame)
        for (top, right, bottom, left) in face_locations:
            # [top:bottom, left:right]
            data.write_to_dataset(frame, name)
            print("SAVED!")
            return


def set_task(task):
    # Cada tarea tiene una posicion de camara diferente
    movement.servo(task)
    # Asignamos la tarea
    Global.task = task


def start():
    # Variables globales y seguras para multiprocesamiento
    Global.buff_num = 1
    Global.read_num = 1
    Global.write_num = 1
    Global.moving = False
    Global.is_exit = False
    Global.task = "none"
    Global.salon = ""
    Global.find_center = False
    Global.f = ""

    # Lee el diccionario que guardamos
    # Y lo separa por keys (names) y values (encodings)
    encodings, names = data.read_encodings()

    print(names)

    # Cargamos los encodings conocidos
    Global.known_face_encodings = encodings
    # Y sus nombres
    Global.known_face_names = names

    # Iniciamos array de procesos
    p = []

    # Iniciamos proceso de captura de frames de la camara
    p.append(Process(target=_capture, args=(read_frame_list, Global, workers,)))
    p[0].start()
    

    # Abrimos un proceso nuevo segun los workers que asignamos
    for worker_id in range(1, workers + 1):
        p.append(Process(target=process, args=(worker_id, read_frame_list, write_frame_list, Global, workers)))
        p[worker_id].start()
    
    # Iniciamos proceso de movimiento y pasamos global
    movement.move(Global)
