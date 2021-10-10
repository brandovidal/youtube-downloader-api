import math
import os

import json

from datetime import datetime

import ffmpeg

from flask import Flask, jsonify, send_from_directory, request
from pytube import YouTube

app = Flask(__name__)


# -------------------------------
# Class
# -------------------------------
class DownloadSong:
    def __init__(self, title="", filename="", directory="/"):
        self.title = title if title is not None else ""
        self.filename = filename
        self.directory = directory

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
    ys_audio = ""

    directory = "audio"
    extension = ".mp3"
    if ys_video.type == 'video':
        directory = "video"
        extension = ".mp4"
        ys_audio = yt.streams.get_audio_only()

    # Get path
    filename = f"{title}{extension}"

    # Starting download
    if ys_video.type == 'video':
        directory_convert = "convert"
        filename_audio = f"{title}_audio{extension}"
        filename_video = f"{title}_video{extension}"

        path_audio = f"{directory_convert}/{filename_audio}"
        path_video = f"{directory_convert}/{filename_video}"
        path = f"{directory}/{filename}"
        print(path_audio, path_video)

        print("Downloading...")
        ys_audio.download(output_path=directory_convert, filename=filename_audio)
        ys_video.download(output_path=directory_convert, filename=filename_video)
        print("Download completed!!")

        video_stream = ffmpeg.input(path_audio)
        audio_stream = ffmpeg.input(path_video)

        print("ffmpeg ...")
        ffmpeg.output(audio_stream, video_stream, path).overwrite_output().run()
        print("ffmpeg end ...")

        song = DownloadSong(title=title, directory=directory, filename=filename)
        return song.toJSON()

    else:
        print("Downloading...")
        ys_video.download(output_path=directory, filename=filename)
        print("Download completed!!")

        song = DownloadSong(title=title, directory=directory, filename=filename)
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
    # song = convert_youtube_link()
    # return render_template('download.html', author=song.author, title=song.title, filename=song.filename,
    #                        directory=song.directory, thumbnail_url=song.thumbnail_url, time=song.time)


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
