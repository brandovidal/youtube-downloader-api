import os
from datetime import datetime

from flask import Flask, jsonify
from pytube import YouTube

app = Flask(__name__)


# -------------------------------
# Definitions
# -------------------------------
def download_song():
    link = 'https://www.youtube.com/watch?v=Znu024zo0nw'
    yt = YouTube(link)

    # printing all the available streams
    # ys = yt.streams.filter(only_audio=True, only_video=False, mime_type='audio/mp4', abr='128kbps').first()

    # Get filename
    filename = f"{yt.title}.mp3"

    # Starting download
    print("Downloading...")
    # ys.download(output_path='mp3', filename=filename)
    print("Download completed!!")
    return filename


# -------------------------------
# Routes
# -------------------------------
@app.get('/')
def index():
    local_timezone = datetime.utcnow().astimezone()

    info = {
        "version": "0.1",
        "date": str(local_timezone),
        "filename": download_song()
    }
    return jsonify(info)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Starting flask...')
    server_port = os.environ.get('PORT', '8000')
    app.run(debug=False, port=server_port, host='0.0.0.0')