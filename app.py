from flask import Flask, render_template
import pandas as pd
import os
import time

UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

df = pd.DataFrame()

# Methods from https://stackoverflow.com/a/39988702
def convert_bytes(num):
    # this function will convert bytes to MB.... GB... etc
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def file_size(file_path):
    # this function will return the file size
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

@app.route('/')
def index():
    
    
    filePath =  '/static/uploads/Fall Guys/Fall Guys 2022.01.23 - 00.40.40.03.DVR.mp4'
    fileName = filePath.split('/')[4]
    fullFilePath = 'D:/Highlights/Clip Curator' + filePath
    
    return render_template('index.html', 
        filePath = filePath, 
        fileName = fileName,
        fileSize = file_size(fullFilePath),
        fileCreatedDate = time.ctime(os.path.getctime(fullFilePath)),
        fileModifiedDate = time.ctime(os.path.getmtime(fullFilePath))
        )

@app.route('/test')
def test():
    print([ f.path for f in os.scandir(UPLOAD_FOLDER) if f.is_dir() ])
    return "Hey there!"
# Traverse through all files in the given directory, list all files from the same day, review and accept form data, delete video permanently (recycle bin is not sustainable),
# Move on to the next day once all files in that day has been dealt with. 