import face_recognition
import pickle
import os 

known_face_encodings = {}

known_face_names = []

with open('data/face_encodings.dat', 'rb') as f:
	known_face_encodings = pickle.load(f)

print(list(known_face_encodings.keys()))

for img in sorted(os.listdir('dataset/')):
    file_dir = os.path.join('dataset/', img)
    file_name = os.path.basename(f"dataset/{img}")
    name = os.path.splitext(file_name)[0]
    print(name)
    face_img = face_recognition.load_image_file(file_dir)
    face_encoding = face_recognition.face_encodings(face_img)

    known_face_encodings[name] = face_encoding

with open('data/face_encodings.dat', 'wb') as f:
    pickle.dump(known_face_encodings, f)

print(known_face_encodings)



