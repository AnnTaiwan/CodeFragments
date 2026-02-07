import ssl
import argparse
from pytubefix import YouTube  # Import the patched version of pytube
from pytubefix.cli import on_progress
import os
ssl._create_default_https_context = ssl._create_stdlib_context  # Fix SSL issues by setting the default HTTPS context

def download_audio_from_youtube(audio_url, dest_path = None):
    """
    Downloads audio from a YouTube video and saves it as an mp3 file.

    Parameters:
    video_url (str): The URL of the YouTube video to download the audio from.
    dest_path (str): The destination file path to save the downloaded audio (as an mp3).

    Returns:
    None
    """
    try:
        # Create a YouTube object with the video URL
        yt = YouTube(audio_url, on_progress_callback=on_progress)
        # print(yt.streams) # to see the suitable quality of video
        # print(yt.streams.filter(progressive=True))
        # print(yt.streams.filter(only_audio=True))
        print("title:", yt.title)           # 影片標題
        print("length: ", yt.length)          # 影片長度 ( 秒 )
        print("author: ", yt.author)          # 影片作者
        # print("channel_url: ", yt.channel_url)     # 影片作者頻道網址
        # print("thumbnail_url: ",yt.thumbnail_url)   # 影片縮圖網址
        # print("Number of views: ", yt.views)           # 影片觀看數

        # creating the file name
        if dest_path is None:
            dest_path = yt.title
            dest_path = "".join(dest_path.split())

        if not dest_path.endswith(".mp3"):
            dest_path += ".mp3"

        ''' Put into audios folder '''
        # Get the script's directory and construct absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        audios_folder = os.path.join(script_dir, "..", "audios")
        audios_folder = os.path.abspath(audios_folder)  # Normalize the path
        os.makedirs(audios_folder, exist_ok=True)  # Create if doesn't exist
        
        # Get just the filename (in case dest_path has path components)
        filename = os.path.basename(dest_path)
        dest_path = os.path.join(audios_folder, filename)

        # dest_path = os.path.join(dir_name, dest_path)
        # Filter the streams to get the audio-only stream and download it
        best_audio = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        print(f"The best abr audio is {best_audio}")
        # Print a message indicating that the download is starting
        print(f"Downloading audio from {audio_url} ...\nand saved it into {dest_path}")
        best_audio.download(output_path=audios_folder, filename=filename)
    except:
        print(f"ERROR: Unable to  download this audio, the link is {audio_url}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--audio_url", required = True, help = "Youtube auido URL")
    ap.add_argument("-p", "--audio_path", required = False, help = "Dest audio path")
    args = vars(ap.parse_args())

    # The destination path for the downloaded audio file (mp3 format)
    dest_path = args["audio_path"]
    # The YouTube video URL to download the audio from
    audio_url = args["audio_url"]
    
    
    # Call the function to download the audio from the specified YouTube video
    download_audio_from_youtube(audio_url, dest_path)
    
    # Print a message indicating that the download is complete
    print("Ok!")
