                                                                        
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

import json
import os
import secrets
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Creamos aplicacion de Flask
# y los 'cubrimos' con la capa de SocketIo
app = Flask(__name__)
socketio = SocketIO(app, logger=False)


@app.route('/uploads/<path:path>')
def send_report(path):
    return send_from_directory('dataset', path)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/post', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'photo' not in request.files:
            print(request.json)
            print('No photo sent!')
            return json.dumps({'response': 'epic fail!'})
        file = request.files['photo']
        # If the user does not select a file,   qthe browser submits an
        # empty file without a filename.
        file.save(os.path.join(UPLOAD_FOLDER, f'{secrets.token_urlsafe(16)}.jpg'))
    return json.dumps({'response': 'success'})

    
    
if __name__ == '__main__':
    # Iniciamos aplicacion Flask+SocketIo
    socketio.run(app, host='0.0.0.0', port=3000) #ssl_context='adhoc'
