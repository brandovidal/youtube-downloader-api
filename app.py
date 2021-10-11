import math
import os
import stat
from datetime import datetime

import json
from flask import Flask, jsonify, send_from_directory, request
from s3_functions import upload_file
from werkzeug.utils import secure_filename
from pytube import YouTube
import ffmpeg

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audios"
VIDEO_FOLDER = "videos"
CONVERT_FOLDER = "convert"
BUCKET = "youtube-downloader-data"


# -------------------------------
# Class
# -------------------------------
class DownloadSong:
    def __init__(self, title="", filename="", directory="/", presigned_url=None):
        self.title = title if title is not None else ""
        self.filename = filename
        self.directory = directory
        self.presigned_url = presigned_url if presigned_url is not None else ""

    def fromJSON(self):
        return json.loads(self.toJSON())

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Stream:
    def __init__(self, itag, mime_type, res="", type="", filesize=None):
        self.itag = itag
        self.mime_type = mime_type
        self.res = res
        self.type = type
        self.only_audio = True if type == "audio" else False
        self.only_video = True if type == "video" else False
        self.filesize = filesize / 1000_000 if filesize is not None else 0

    def fromJSON(self):
        return json.loads(self.toJSON())

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# -------------------------------
# Definitions
# -------------------------------

def get_filename(name: str):
    filename = name.replace(" ", "_")
    return filename


# remove special caracters from video title
def get_title_video(name: str):
    disallowed_characters = '\\|,/\\\\:*!¡*¿?<>@+~[]()'
    title_song = name.translate({ord(charecter): None for charecter in disallowed_characters})
    title_song = get_filename(title_song)
    return " ".join(title_song.split())


def get_time(s_time: int):
    hour = math.floor(s_time / 3600)
    minutes = math.floor(s_time / 60)
    seconds = s_time % 60

    # Calculate hour and minutes
    minutes = minutes - 60 if hour > 0 else minutes
    hour = ''.join([f'{hour}', ':']) if hour > 0 else ''
    minutes = ''.join([f'{minutes}', ':']) if minutes > 0 else ''

    return f"{hour}{minutes}{seconds}"


# search link youtube
def search_link_youtube(link=None):
    link = link if link is not None else 'https://www.youtube.com/watch?v=Znu024zo0nw'
    yt = YouTube(link)

    # Get params
    title = get_title_video(yt.title)
    author = yt.author
    thumbnail_url = yt.thumbnail_url
    video_time = get_time(yt.length)

    # printing all the available streams
    ys_video = yt.streams.filter(only_audio=False, only_video=True, mime_type='video/mp4')
    ys_audio = yt.streams.filter(only_audio=True, only_video=False, mime_type='audio/mp4')
    ys = tuple(set(ys_audio) | set(ys_video))

    youtube_streams = list()
    for stream in ys:
        res = ""
        if stream.type == 'audio':
            res = stream.abr
        elif stream.type == 'video':
            res = stream.resolution

        stream_json = Stream(itag=stream.itag, mime_type=stream.mime_type, res=res, type=stream.type,
                             filesize=stream.filesize)
        youtube_streams.append(stream_json.fromJSON())

    json_object = {
        "title": title,
        "author": author,
        "thumbnail_url": thumbnail_url,
        "time": video_time,
        "streams": youtube_streams,
    }
    print(json_object)
    return jsonify(json_object)


def convert_youtube_link(link, itag):
    yt = YouTube(link)

    title = get_title_video(yt.title)

    # get stream
    ys_video = yt.streams.get_by_itag(itag)
    extension = ".mp4" if ys_video.type == 'video' else ".mp3"

    # Get filename
    filename = f"{title}{extension}"

    # Starting download
    if ys_video.type == 'video':
        filename_audio = f"{title}_audio{extension}"
        filename_video = f"{title}_video{extension}"

        # Get path file
        path_file_audio = os.path.join(CONVERT_FOLDER, secure_filename(filename_audio))
        path_file_video = os.path.join(CONVERT_FOLDER, secure_filename(filename_video))
        path_file = os.path.join(VIDEO_FOLDER, secure_filename(filename))

        print("Downloading...")
        ys_audio = yt.streams.get_audio_only()
        ys_audio.download(output_path=CONVERT_FOLDER, filename=filename_audio)
        ys_video.download(output_path=CONVERT_FOLDER, filename=filename_video)
        print("Download completed!!")

        # Get video and audio stream
        video_stream = ffmpeg.input(path_file_audio)
        audio_stream = ffmpeg.input(path_file_video)

        # Generate new video with audio
        print("ffmpeg start ...")
        ffmpeg.output(audio_stream, video_stream, path_file).overwrite_output().run()
        print("ffmpeg end ...")

        # Save and upload file
        os.chmod(path_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        presigned_url = upload_file(f"videos/{filename}", BUCKET)

        # Remove file
        os.remove(path_file)

        song = DownloadSong(title=title, directory=VIDEO_FOLDER, filename=filename, presigned_url=presigned_url)
        return song.toJSON()

    else:
        # Get path file
        path_file = os.path.join(AUDIO_FOLDER, secure_filename(filename))

        print("Downloading...")
        ys_video.download(output_path=AUDIO_FOLDER, filename=filename)
        print("Download completed!!")

        # Save and upload file
        os.chmod(path_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        presigned_url = upload_file(f"audios/{filename}", BUCKET)

        # Remove file
        os.remove(path_file)

        song = DownloadSong(title=title, directory=AUDIO_FOLDER, filename=filename, presigned_url=presigned_url)
        return song.toJSON()


# -------------------------------
# Routes
# -------------------------------
@app.get('/')
def index():
    local_timezone = datetime.utcnow().astimezone()
    return jsonify({
        "date": str(local_timezone),
        "version": "1.0"
    })


@app.route('/search', methods=['POST'], strict_slashes=False)
def search():
    link = request.json['link']
    return search_link_youtube(link)


@app.route('/convert', methods=['POST'], strict_slashes=False)
def convert():
    link = request.json['link']
    itag = request.json['itag']
    return convert_youtube_link(link, itag)


@app.route('/download?<string:directory>&<string:filename>', methods=['GET', 'POST'])
def download_file(directory, filename):
    if directory != "" and filename != "":
        full_path = os.path.join(app.root_path, directory)
        return send_from_directory(directory=full_path, path=filename, as_attachment=True)

    return jsonify({
        "error": "not exist video or audio file",
    })


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Starting flask...')
    server_port = os.environ.get('PORT', '8000')
    app.run(debug=False, port=server_port, host='0.0.0.0')
