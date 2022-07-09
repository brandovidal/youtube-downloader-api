# youtube-downloader-api

Using Flask, gunicorn, ffmpeg-python and pytube

# Deploy

[API URL](https://youtube-downloader-api.onrender.com)

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
