from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_thumbnails import Thumbnail
import pandas as pd
import os
from os import walk
import subprocess
import time

UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
thumb = Thumbnail(app)
app.secret_key = "$bu_@mn^stmtkr=@e^20_8r0noe&3k03p1l3+h&@va)22q@a_%"
# Disable the following two lines after debug
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(debug=True)

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
    
@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
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

    fileDF = pd.DataFrame(['FileName', 'Timestamp', 'Processed', 'Category', 'Description', 'AdditionalDetails', 'Starring', 'ItemsUsed', 'Remarks', 'Rating', 'Link'])
    FileName = []
    Timestamp = []
    Processed = []
    Category = []
    for i, path in enumerate(pathDF.FolderPath):
        filenames = next(walk(path), (None, None, []))[2]  # [] if no file
        
        for j, file in enumerate(filenames):
            subprocess.call(['ffmpeg', '-ss', '00:00:01.000', '-i', path + '/' + file, '-vframes', '1', '-s', '480x270', '-n', path + '/.thumbs/' + file.replace('mp4', 'png'), '-loglevel', 'panic'])
            FileName.append(file)
            # fileDF.at[i+j, 'FileName'] = file
            Timestamp.append(time.ctime(os.path.getctime('D:/Highlights/Clip Curator/' + path + '/' + file)))
            # fileDF.at[i+j, 'Timestamp'] = time.ctime(os.path.getctime('D:/Highlights/Clip Curator/' + path + '/' + file))
            Processed.append('Initialised')
            # fileDF.at[i+j, 'Processed'] = 'Initialised'
            Category.append(path.split('/')[2])
            # fileDF.at[i+j, 'Category'] = path.split('/')[2]

        pathDF.at[i, 'ThumbnailsPath'] = [path + '/.thumbs/' + file.replace('mp4', 'png') for file in filenames]
    fileDF = pd.DataFrame({
        'FileName': FileName, 
        'Timestamp': Timestamp,
        'Processed': 'Initialised',
        'Category': Category,
        'Description': '',
        'AdditionalDetails': '',
        'Starring': '',
        'ItemsUsed': '',
        'Remarks': '',
        'Rating': 0.0,
        'Link': ''
    })
    fileDF['Timestamp'] = fileDF['Timestamp'].apply(lambda x: pd.to_datetime(x, format="%a %b %d %H:%M:%S %Y"))
 
   
    # print(len(next(os.walk(UPLOAD_FOLDER+'/Fall Guys'))[2]))
    try:
        fileDF.to_excel('static/uploads/tracking.xlsx', index=False)
    except:
        print('Unable to write to file....Did you like open the file or something? Have you given me the proper write access? Check check check...')
    print(pathDF)
    return render_template('filebrowser.html', columnNames = pathDF.columns.values, rowData=list(pathDF.values.tolist()), zip=zip)
    
@app.route('/requestHandler', methods = ['POST'])
def requestHandler():
    session['currentFolderName'] = request.form['folderName']
    # Get number of files in the selected folder
    fileCount = len(next(os.walk(UPLOAD_FOLDER+'/' + session['currentFolderName']))[2])
    print(session['currentFolderName'] + ': ' + str(fileCount))

    if fileCount > 0:
        return 'OK'
    else:
        return 'NOT OK'

@app.route('/clip')
def clip():
    # Index to keep track of the day that is being reviewed at the moment
    currentDayIndex = 0
    print(session['currentFolderName'])

    # Reading tracking data
    fileDF = pd.read_excel('static/uploads/tracking.xlsx')
    # Creating a new column to store the date, needed for the groupby
    fileDF['Date'] = fileDF['Timestamp'].dt.date
    # Filtering DF based on the selected Category
    fileDF = fileDF.loc[fileDF['Category'] == session['currentFolderName']]
    # Grouping by the Date column to create a table with dates and a list filenames corresponding to each date
    groupedDF = fileDF.groupby('Date')['FileName'].apply(list).reset_index()
    print(groupedDF)

    # filePath =  '/static/uploads/Fall Guys/Fall Guys 2022.01.23 - 00.40.40.03.DVR.mp4'    
    filePath =  '/static/uploads/' + session['currentFolderName'] + '/' + groupedDF.at[0, 'FileName'][0]
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
    fileDF = pd.read_excel('static/uploads/tracking.xlsx')
    fileDF['Date'] = fileDF['Timestamp'].dt.date
    # Now you can group by the 'date' column
    grouped = fileDF.groupby('Date')['FileName'].apply(list).reset_index()
    print(grouped)
    return 'OK'

@app.route('/credits')
def credits():
    return render_template('credits.html')


# Traverse through all files in the given directory, list all files from the same day, review and accept form data, delete video permanently (recycle bin is not sustainable),
# Move on to the next day once all files in that day has been dealt with. 

# Generate thumbnails for all videos and delete them as the video file is being deleted