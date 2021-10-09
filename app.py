import os
from datetime import datetime

from flask import Flask, jsonify, send_from_directory, render_template
from pytube import YouTube

app = Flask(__name__)


# -------------------------------
# Class
# -------------------------------
class DownloadSong:
    def __init__(self, author="", title="", filename="", directory="/", path="", thumbnail_url="", time=0):
        self.author = author
        self.title = title
        self.filename = filename
        self.directory = directory
        self.path = path
        self.thumbnail_url = thumbnail_url
        self.time = f"{time} seconds"


# -------------------------------
# Definitions
# -------------------------------
# remove special caracters from video title
def get_title_video(name: str):
    disallowed_characters = '\\|,/\\\\:*!¡*¿?<>@+~'
    title_song = name.translate({ord(charecter): None for charecter in disallowed_characters})
    return " ".join(title_song.split())


# get song to download
def convert_youtube_link():
    link = 'https://www.youtube.com/watch?v=Znu024zo0nw'
    yt = YouTube(link)

    # printing all the available streams
    ys = yt.streams.filter(only_audio=True, only_video=False, mime_type='audio/mp4', abr='128kbps').first()

    # Get title of video
    title = get_title_video(yt.title)

    # Get thumbnail_url
    thumbnail_url = yt.thumbnail_url

    # Length of the video
    time = yt.length
    author = yt.author

    # Get params
    filename = f"{title}.mp3"
    directory = "audio"
    full_path = f"{directory}/{filename}"

    # Starting download
    print("Downloading...")
    ys.download(output_path=directory, filename=filename)
    print("Download completed!!")

    song = DownloadSong(author=author, title=title, filename=filename, directory=directory, path=full_path,
                        thumbnail_url=thumbnail_url, time=time)
    return song


# -------------------------------
# Routes
# -------------------------------
@app.get('/')
def index():
    local_timezone = datetime.utcnow().astimezone()
    song = convert_youtube_link()

    return render_template('download.html', author=song.author, title=song.title, filename=song.filename,
                           directory=song.directory, thumbnail_url=song.thumbnail_url, time=song.time)


@app.route('/download?<string:directory>&<string:filename>', methods=['GET', 'POST'])
def download_file(directory, filename):
    local_timezone = datetime.utcnow().astimezone()
    # print(f"directory:  {directory}")
    # print(f"filename:  {filename}")

    if directory != "" and filename != "":
        full_path = os.path.join(app.root_path, directory)
        return send_from_directory(directory=full_path, path=filename, as_attachment=True)

    return jsonify({
        "date": str(local_timezone),
        "error": "not exist song"
    })


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Starting flask...')
    server_port = os.environ.get('PORT', '8000')
    app.run(debug=False, port=server_port, host='0.0.0.0')
