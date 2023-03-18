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
    print(f"process {worker_id} started!")
    known_face_encodings = Global.known_face_encodings
    known_face_names = Global.known_face_names
    while True:
        # Esperamos a que sea nuestro turno para leer
        while Global.read_num != worker_id or Global.read_num != prev_id(Global.buff_num, worker_num):
            time.sleep(0.01)

        # Lee el frame asignado al worker
        frame = read_frame_list[worker_id]

        # Escribir el trabajador siguiente para que lea
        Global.read_num = next_id(Global.read_num, worker_num)

        if Global.task == "none":
            pass

        # En modo roam buscamos el camino
        if Global.task == "roam":
            #TODO: COLOR BALANCE / BRIGHTNESS 
            
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Otsu's Binarization !!!!
            #gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
            #blur = cv2.GaussianBlur(gray, (9,9), 0)
            
            #blur = cv2.medianBlur(gray,5)
            #_, mask = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
            # Solo uno a la vez
            # Inicializamos lector de qr
            qcd = cv2.QRCodeDetector()
            # Si se detecta un QR retval devuelve True
            retval, decoded_info, ps, straight_qrcode = qcd.detectAndDecodeMulti(frame)
            if retval:
                # Dibujamos polígono donde se encuentran los puntos de el QR
                cv2.polylines(frame, ps.astype(int), True, (0, 255, 0), 3)
                # Leemos la información del codigo QR y lo juntamos con sus respectivos puntos
                for decoded_salon, ps in zip(decoded_info, ps):
                    print(decoded_salon)
                    if decoded_salon == "iSalon1":
                        data.write_stop(decoded_salon)
                        Global.salon = decoded_salon
                        set_task("recognize")
                    cv2.putText(frame, decoded_salon, ps[0].astype(int), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
            # Si reconoce algo no se llega hasta aqui
            # resized_frame = cv2.resize(frame, (0,0), fx=0.4, fy=0.4)

            # convertimos el espacio de color a hsv (más facil procesar el rango de colores)

            # bounds de los colores en hsv
            # HSV en OpenCV es: H: H/2 (360 -> 100), S: S/100*255 (100 -> 255), V: V/100*255 (100 -> 255) !!!!
            low_b = np.uint8([0, 0, 0])
            high_b = np.uint8([180, 90, 50])

            # mascara donde calculamos buscamos los colores dentro del rango especificado arriba
            mask = cv2.inRange(hsv, low_b, high_b)

            # https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            if len(contours) > 0:
                # busca el contorno mas grande
                c = max(contours, key=cv2.contourArea)
                    # momentos calcula el centroide de la figura
                    # https://en.wikipedia.org/wiki/Image_moment
                    # https://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
                    # todo lo hace el computador 🙏👍
                M = cv2.moments(c)
                if M["m00"] != 0:
                    t = 0
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
                    # bounding boxes para decicion de girar
            cv2.rectangle(frame, (0, 0), (100, 436), (255, 0, 0), 1)
            cv2.rectangle(frame, (100, 0), (200, 436), (255, 0, 0), 1)
            
            cv2.rectangle(frame, (200, 0), (381, 436), (255, 0, 0), 1)
            
            cv2.rectangle(frame, (381, 0), (481, 436), (255, 0, 0), 1)
            cv2.rectangle(frame, (481, 0), (581, 436), (255, 0, 0), 1)
            

        if Global.task == "recognize":

            # Achicamos el frame para procesarlo mas rapido
            resized_frame = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)

            # Encontrar las caras en el frame de video y sus encodings
            face_locations = face_recognition.face_locations(resized_frame)
            face_encodings = face_recognition.face_encodings(resized_frame, face_locations)

            names = []
            for face_encoding in face_encodings:

                # Comparamos el encoding encontrado en el frame con los que ya conocemos
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Desconocido"

                # Comparamos las distancias entre caras
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                # Buscamos la mejor coincidencia
                best_match_index = np.argmin(face_distances)
                face_distance = face_distances[best_match_index]

                # print(f"for {face_distances} : {face_distances < 0.45}")
                # print(f"for idx {best_match_index} : {face_distance < 0.45}")

                # Si el mas cercano de los matches es igual a True alta probabilidad de que sea la persona que ya
                # conocemos De lo contrario el nombre se mantiene como desconocido
                if face_distance < 0.45:
                    if matches[best_match_index]:
                        id = known_face_names[best_match_index]
                        (flag, name) = data.write_rec(Global.salon, id)
                        if flag:
                            voice.saludar(name)
                        set_task("roam")
                names.append(name)

            # Por cada cara en el frame:
            for (top, right, bottom, left), name in zip(face_locations, names):
                # Cambiamos las coordenadas de los puntos, pues se procesó una imagen reducida (1x > 1/4x > 1/10x)
                # .25 * .4 = .1
                # .1 * 2.5 = .25 
                top = floor(top * 2.5)
                right = floor(right * 2.5)
                bottom = floor(bottom * 2.5)
                left = floor(left * 2.5)

                # Dibujamos un rectangulo donde se encuntra la cara
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Cuadro con texto debajo
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

        # Esperar a que sea nuestro turno para escribir un nuevo frame
        while Global.write_num != worker_id:
            time.sleep(0.01)

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
    movement.servo(task)
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
    
    movement.move(Global)
