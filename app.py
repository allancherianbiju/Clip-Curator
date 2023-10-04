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
# app.config['THUMBNAIL_MEDIA_ROOT'] = 'D:/Highlights/Clip Curator/static/uploads/Fall Guys'
# app.config['THUMBNAIL_MEDIA_URL'] = '/uploads/'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Methods from https://stackoverflow.com/a/39988702 for file size conversion


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
            size += os.path.getsize(ele)
        return convert_bytes(size)

# Route for serving the favicon because seeing the error pop up in the dev console was super annoying


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Home route for the folder browser


@app.route('/')
def index():
    # Init dataframe to track per folder stats
    pathDF = pd.DataFrame({
        'FolderName': [f.path.replace(UPLOAD_FOLDER, '') for f in os.scandir(UPLOAD_FOLDER) if f.is_dir()],
        'FolderPath': [f.path for f in os.scandir(UPLOAD_FOLDER) if f.is_dir()],
        'FolderSize': [file_size(f) for f in os.scandir(UPLOAD_FOLDER) if f.is_dir()],
        'FolderFileCount': [len(next(os.walk(f.path))[2]) for f in os.scandir(UPLOAD_FOLDER) if f.is_dir()],
        'ThumbnailsPath': ''
    })

    # Make a folder in each folder for thumbs
    for path in pathDF.FolderPath:
        if not os.path.exists(path + '/.thumbs'):
            os.makedirs(path + '/.thumbs')

    fileDF = pd.DataFrame(['FileName', 'Timestamp', 'Processed', 'Category', 'Description',
                          'AdditionalDetails', 'Starring', 'ItemsUsed', 'Remarks', 'Rating', 'Link'])
    FileName = []
    Timestamp = []
    Processed = []
    Category = []
    for i, path in enumerate(pathDF.FolderPath):
        filenames = next(walk(path), (None, None, []))[2]  # [] if no file

        for j, file in enumerate(filenames):
            subprocess.call(['ffmpeg', '-ss', '00:00:01.000', '-i', path + '/' + file, '-vframes', '1',
                            '-s', '480x270', '-n', path + '/.thumbs/' + file.replace('mp4', 'png'), '-loglevel', 'panic'])
            FileName.append(file)
            # fileDF.at[i+j, 'FileName'] = file
            Timestamp.append(time.ctime(os.path.getctime(
                'D:/Highlights/Clip Curator/' + path + '/' + file)))
            # fileDF.at[i+j, 'Timestamp'] = time.ctime(os.path.getctime('D:/Highlights/Clip Curator/' + path + '/' + file))
            Processed.append('Initialised')
            # fileDF.at[i+j, 'Processed'] = 'Initialised'
            Category.append(path.split('/')[2])
            # fileDF.at[i+j, 'Category'] = path.split('/')[2]

        pathDF.at[i, 'ThumbnailsPath'] = [path + '/.thumbs/' +
                                          file.replace('mp4', 'png') for file in filenames]
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
    fileDF['Timestamp'] = fileDF['Timestamp'].apply(
        lambda x: pd.to_datetime(x, format="%a %b %d %H:%M:%S %Y"))
    print(fileDF)
    print(pathDF)

    # print(len(next(os.walk(UPLOAD_FOLDER+'/Fall Guys'))[2]))
    try:
        fileDF.to_excel('static/uploads/tracking.xlsx', index=False)
    except:
        print('Unable to write to file....Did you like open the file or something? Have you given me the proper write access? Check check check...')
    # print(pathDF)
    return render_template('filebrowser.html', columnNames=pathDF.columns.values, rowData=list(pathDF.values.tolist()), zip=zip, pageType='Landing')


def readData():
    # Reading tracking data
    fileDF = pd.read_excel('static/uploads/tracking.xlsx')
    # Creating a new column to store the date, needed for the groupby
    fileDF['Date'] = fileDF['Timestamp'].dt.date
    return fileDF


@app.route('/requestHandler', methods=['POST'])
def requestHandler():
    print(request.form.to_dict())

    # Folder Selection
    if 'folderName' in request.form.to_dict():
        session['currentFolderName'] = request.form['folderName']
        # Get number of files in the selected folder
        fileCount = len(
            next(os.walk(UPLOAD_FOLDER+'/' + session['currentFolderName']))[2])
        print(session['currentFolderName'] + ': ' + str(fileCount))

        # Resetting File and Day index
        session['currentDayIndex'] = 0
        session['currentFileIndex'] = 0
        if fileCount > 0:
            return 'OK'
        else:
            return 'NOT OK'

    # Clip Selection
    if 'thumbnailID' in request.form.to_dict():
        # Validation
        # fileDF = readData()
        # fileDF = fileDF.loc[fileDF['Category'] == session['currentFolderName']]
        # groupedDF = fileDF.groupby('Date')['FileName'].apply(list).reset_index()
        if request.form['thumbnailID'] == 'Prev':
            session['currentDayIndex'] = session['currentDayIndex']-1
        elif request.form['thumbnailID'] == 'Next':
            session['currentDayIndex'] = session['currentDayIndex']+1
        else:
            session['currentFileIndex'] = int(request.form['thumbnailID'])
        return 'OK'


@app.route('/clip')
def clip():
    # Index to keep track of the day that is being reviewed at the moment
    currentDayIndex = session['currentDayIndex']
    currentFileIndex = session['currentFileIndex']
    currentIndex = {'currentDayIndex': currentDayIndex,
                    'currentFileIndex': currentFileIndex,
                    'dayOverflow': False,
                    'dayUnderflow': False
                    }
    try:
        print(session['currentFolderName'])
    except:
        return redirect("/", code=302)

    # Read Data
    fileDF = readData()
    # Filtering DF based on the selected Category
    fileDF = fileDF.loc[fileDF['Category'] == session['currentFolderName']]
    # Grouping by the Date column to create a table with dates and a list filenames corresponding to each date
    groupedDF = fileDF.groupby('Date')['FileName'].apply(list).reset_index()

    print(len(groupedDF))
    if currentDayIndex == 0:
        currentIndex['dayUnderflow'] = True
    if currentDayIndex+1 == len(groupedDF):
        currentIndex['dayOverflow'] = True
    # print(i for i in groupedDF.FileName[0])

    filePath = '/static/uploads/' + session['currentFolderName'] + \
        '/' + groupedDF.at[currentDayIndex, 'FileName'][currentFileIndex]
    fileName = filePath.split('/')[4]
    fullFilePath = 'D:/Highlights/Clip Curator' + filePath

    # Thumbnail Paths for all files of the same day
    thumbList = [sub.replace('.mp4', '.png')
                 for sub in groupedDF.at[currentDayIndex, 'FileName']]
    thumbList = ['/static/uploads/' + session['currentFolderName'] +
                 '/.thumbs/' + thumbName for thumbName in thumbList]

    return render_template('clip.html',
                           filePath=filePath,
                           fileName=fileName,
                           fileSize=file_size(fullFilePath),
                           fileCreatedDate=time.ctime(
                               os.path.getctime(fullFilePath)),
                           fileModifiedDate=time.ctime(
                               os.path.getmtime(fullFilePath)),
                           fileList=groupedDF.at[currentDayIndex, 'FileName'],
                           thumbList=thumbList,
                           currentFileIndex=currentFileIndex,
                           currentIndex = currentIndex
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
