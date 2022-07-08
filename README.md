# youtube-downloader-api

Using Flask, gunicorn, ffmpeg-python and pytube

# Deploy URL

[Heroku URL](https://dracon-youtube-downloader-api.herokuapp.com)

### Dependencies 📋

Generate file dependencies

```shell
pip freeze > requirements.txt
```

Install dependencies

```shell
pip install -r requirements.txt
```
Run API

```shell
gunicorn app:app --timeout 3600
```
