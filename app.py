import math
import os
from datetime import datetime

import json

import requests as requests
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from s3_functions import upload_file
from werkzeug.utils import secure_filename

from pytube import YouTube
import ffmpeg

app = Flask(__name__)

CORS(app)

UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audios"
VIDEO_FOLDER = "videos"
CONVERT_FOLDER = "convert"
BUCKET = "youtube-downloader-data"


# -------------------------------
# Class
# -------------------------------
class DownloadSong:
    def __init__(self, title="", filename="", directory="/", url=None):
        self.title = title if title is not None else ""
        self.filename = filename
        self.directory = directory
        self.url = url if url is not None else ""

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
        self.format = "MP4" if type == "video" else "MP3"
        self.filesize = convertByteToMegaBytes(filesize) if filesize is not None else "0MB"

    def fromJSON(self):
        return json.loads(self.toJSON())

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# -------------------------------
# Definitions
# -------------------------------
def get_filename(name: str):
    filename = name.replace(" ", "_")
    filename = get_title_video(filename)
    return filename


# remove special caracters from video title
def get_title_video(name: str):
    disallowed_characters = '\\|,/\\\\:*!¡*¿?<>@+~[]()'
    title_song = name.translate({ord(charecter): None for charecter in disallowed_characters})
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


def convertByteToMegaBytes(bytes):
    return f"{round(bytes / 1000_000, 2)}MB"


def listStreamTOJSON(youtube_streams):
    list_streams = list()
    for stream in youtube_streams:
        res = stream.abr if stream.type == 'audio' else stream.resolution

        stream_json = Stream(itag=stream.itag, mime_type=stream.mime_type, res=res, type=stream.type,
                             filesize=stream.filesize)
        list_streams.append(stream_json.fromJSON())
    return list_streams


# search link youtube
def search_link_youtube(link=None):
    if link is None:
        return jsonify({
            'error': 'Ingresar link de youtube'
        })
    yt = YouTube(link)

    # All Streams
    streams = yt.streams

    if len(streams) == 0:
        return jsonify({
            'error': 'No existen conversiones disponibles'
        })


    # Video Stream
    youtube_streams_video = streams.filter(type="video", mime_type='video/mp4', progressive=True).order_by(
        'resolution').asc()

    # Audio Stream
    youtube_streams_audio = streams.filter(type="audio", mime_type='audio/mp4').order_by('abr').asc()

    # get list of audios or videos
    list_streams_videos = listStreamTOJSON(youtube_streams_video)
    list_streams_audios = listStreamTOJSON(youtube_streams_audio)

    # Get params
    title = get_title_video(yt.title)
    author = yt.author
    thumbnail_url = yt.thumbnail_url
    video_time = get_time(yt.length)

    json_object = {
        "title": title,
        "author": author,
        "thumbnail_url": thumbnail_url,
        "time": video_time,
        "videos": list_streams_videos,
        "audios": list_streams_audios,
    }
    # print(json_object)
    return jsonify(json_object)


def merge_video_with_audio(yt, itag, title):
    # All Streams
    streams = yt.streams

    # get streams
    youtube_streams_video = streams.get_by_itag(itag)
    youtube_streams_audio = streams.get_audio_only()

    # Get filename
    extension = ".mp4"
    filename = f"{title}{extension}"
    filename_audio = f"{title}_audio{extension}"
    filename_video = f"{title}_video{extension}"

    # Get path file
    path_file_audio = os.path.join(CONVERT_FOLDER, filename_audio)
    path_file_video = os.path.join(CONVERT_FOLDER, filename_video)
    path_file = os.path.join(VIDEO_FOLDER, filename)

    print("Downloading...")
    youtube_streams_audio.download(output_path=CONVERT_FOLDER, filename=filename_audio)
    youtube_streams_video.download(output_path=CONVERT_FOLDER, filename=filename_video)
    print("Download completed!!")

    # Get video and audio stream
    audio_stream = (ffmpeg.input(path_file_audio))
    video_stream = (ffmpeg.input(path_file_video))

    # Generate new video with audio
    print("Generate new video with audio - start ...")
    (ffmpeg.output(audio_stream, video_stream, path_file).overwrite_output().run())
    print("Generate new video with audio - end ...")

    # Save and upload file
    print("Save and upload file")
    url = upload_file(f"videos/{filename}", BUCKET)
    print(url)

    # Remove file
    os.remove(path_file_audio)
    os.remove(path_file_video)
    os.remove(path_file)

    song = DownloadSong(title=title, directory=VIDEO_FOLDER, filename=filename, url=url)
    print(song)
    return song.toJSON()


def download_video_or_audio(yt, itag, title):
    # get stream
    youtube_streams_video = yt.streams.get_by_itag(itag)

    # get extension and type
    if youtube_streams_video.type == 'video':
        extension = ".mp4"
        type = "videos"
        directory = VIDEO_FOLDER
    else:
        extension = ".mp3"
        type = "audios"
        directory = AUDIO_FOLDER

    # Get filename
    filename = f"{title}{extension}"

    print("Downloading...")
    youtube_streams_video.download(output_path=directory, filename=filename)
    print("Download completed!!")

    # Save and upload file
    print("Save and upload file")
    url = upload_file(f"{type}/{filename}", BUCKET)

    # Get path file
    path_file = os.path.join(directory, filename)

    # Remove file
    os.remove(path_file)

    song = DownloadSong(title=title, directory=directory, filename=filename, url=url)

    download(url=url)
    print("Downloaded")
    return song.toJSON()


def download(url):
    print("URL >>>> ", url)
    if url != "":
        r = requests.get(url, allow_redirects=True)
        print(r.headers.get('content-type'))
        return jsonify({
            "result": "descarga realizada",
        })

    return jsonify({
        "error": "not exist video or audio file",
    })


def convert_youtube_link(link, itag):
    yt = YouTube(link)
    title = get_title_video(yt.title)
    return download_video_or_audio(yt=yt, itag=itag, title=title)


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
def download_route(directory, filename):
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
