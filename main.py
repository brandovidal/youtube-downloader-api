from pytube import YouTube


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    link = 'https://www.youtube.com/watch?v=MA5v9VNJ-2Q'
    yt = YouTube(link)

    # printing all the available streams
    ys = yt.streams.filter(only_audio=True, only_video=False, mime_type='audio/mp4', abr='128kbps').first()

    # Get filename
    filename = f"{yt.title}.mp3"

    # Starting download
    print("Downloading...")
    ys.download(output_path='mp3', filename=filename)
    print("Download completed!!")