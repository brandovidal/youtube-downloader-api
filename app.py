import os
from datetime import datetime

from flask import Flask, jsonify
from pytube import YouTube

app = Flask(__name__)


# -------------------------------
# Class
# -------------------------------
class DownloadSong:
    def __init__(self, filename="", full_path="/"):
        self.filename = filename
        self.full_path = full_path


# -------------------------------
# Definitions
# -------------------------------
# remove special caracters from video title
def get_title_video(name: str):
    disallowed_characters = '\\|,/\\\\:*!¡*¿?<>@+~'
    title_song = name.translate({ord(charecter): None for charecter in disallowed_characters})
    return " ".join(title_song.split())


# get song to download
def get_download_song():
    link = 'https://www.youtube.com/watch?v=Znu024zo0nw'
    yt = YouTube(link)

    # printing all the available streams
    ys = yt.streams.filter(only_audio=True, only_video=False, mime_type='audio/mp4', abr='128kbps').first()

    # Get title of video
    title = get_title_video(yt.title)

    # Get filename
    filename = f"{title}.mp3"
    output_path = "audio"

    # Starting download
    print("Downloading...")
    ys.download(output_path=output_path, filename=filename)
    print("Download completed!!")

    full_path = f"{output_path}/{filename}"

    return DownloadSong(filename, full_path)


# -------------------------------
# Routes
# -------------------------------
@app.get('/')
def index():
    local_timezone = datetime.utcnow().astimezone()

    song = get_download_song()
    print(song)
    print(song.filename)

    info = {
        "date": str(local_timezone),
        "filename": song.filename,
        "full_path": song.full_path,
        "version": "0.1",
    }
    return jsonify(info)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Starting flask...')
    server_port = os.environ.get('PORT', '8000')
    app.run(debug=False, port=server_port, host='0.0.0.0')
