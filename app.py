from flask import Flask, render_template
from flask_thumbnails import Thumbnail
import pandas as pd
import os
from os import walk
import subprocess
import time

UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
thumb = Thumbnail(app)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_MEDIA_ROOT'] = 'D:/Highlights/Clip Curator/static/uploads/Fall Guys'
app.config['THUMBNAIL_MEDIA_URL'] = '/uploads/'
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
    if os.path.isdir(file_path):
        size = 0
        for ele in os.scandir(file_path):
            size+=os.path.getsize(ele)
        return convert_bytes(size)

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
    pathDF = pd.DataFrame({
        'FolderName': [ f.path.replace(UPLOAD_FOLDER, '') for f in os.scandir(UPLOAD_FOLDER) if f.is_dir()],
        'FolderPath': [ f.path for f in os.scandir(UPLOAD_FOLDER) if f.is_dir() ],
        'FolderSize': [ file_size(f) for f in os.scandir(UPLOAD_FOLDER) if f.is_dir() ],
        'FolderFileCount': [ len(next(os.walk(f.path))[2]) for f in os.scandir(UPLOAD_FOLDER) if f.is_dir() ],
        'ThumbnailsPath': ''
    })
        
    # Make a folder in each folder for thumbs
    for path in pathDF.FolderPath:
        if not os.path.exists(path + '/.thumbs'):
            os.makedirs(path + '/.thumbs')

    for i, path in enumerate(pathDF.FolderPath):
        filenames = next(walk(path), (None, None, []))[2]  # [] if no file
        
        for j, file in enumerate(filenames):
            subprocess.call(['ffmpeg', '-ss', '00:00:01.000', '-i', path + '/' + file, '-vframes', '1', '-s', '480x270', '-n', path + '/.thumbs/' + file.replace('mp4', 'png'), '-loglevel', 'panic'])
        pathDF['ThumbnailsPath'][i] = [path + '/.thumbs/' + file.replace('mp4', 'png') for file in filenames]
    print(pathDF)
    # print(len(next(os.walk(UPLOAD_FOLDER+'/Fall Guys'))[2]))

    return render_template('filebrowser.html', columnNames = pathDF.columns.values, rowData=list(pathDF.values.tolist()), zip=zip)

@app.route('/credits')
def credits():
    return render_template('credits.html')


# Traverse through all files in the given directory, list all files from the same day, review and accept form data, delete video permanently (recycle bin is not sustainable),
# Move on to the next day once all files in that day has been dealt with. 

# Generate thumbnails for all videos and delete them as the video file is being deleted