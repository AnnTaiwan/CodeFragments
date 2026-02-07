from PyQt6 import QtWidgets, QtCore, QtGui
import sys
import ssl
import os
from pytubefix import YouTube  # Import the patched version of pytube
from pytubefix.cli import on_progress
ssl._create_default_https_context = ssl._create_stdlib_context  # Fix SSL issues by setting the default HTTPS context


class DownloadWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Youtube_Audio_Download.studio')
        self.resize(700, 500)
        self.ui()  # Initialize UI components

    def ui(self):
        """Sets up the UI components."""
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(50, 20, 600, 40)  # Centered: (700-600)/2 = 50
        self.label.setText('下載Youtube音樂，建議影片長度不要大於6分鐘')
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet('font: bold 20px; color:#1f1213;')

        # Create an input field for YouTube URL
        self.input = QtWidgets.QLineEdit(self)
        self.input.setGeometry(100, 70, 500, 30)  # Centered: (700-500)/2 = 100
        self.input.setText("https://www.youtube.com/")  # Default placeholder text
        self.input.setStyleSheet('font-size:20px; color:#1f1213; background-color: #efede8;')
        self.input.textChanged.connect(self.showText)

        self.input_label = QtWidgets.QLabel(self)
        self.input_label.setGeometry(75, 110, 550, 50)  # Centered: (700-550)/2 = 75
        self.input_label.setWordWrap(True)  # Allow text wrapping for long titles
        self.input_label.setStyleSheet("""
            font: 10px; 
            color: black; 
            background-color: #efede8;
            border: 2px solid #ffa22b;
            border-radius: 5px;
            padding: 10px;
        """)
        self.input_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Create a button for downloading
        self.btn = QtWidgets.QPushButton(self)
        self.btn.setGeometry(285, 170, 130, 30)  # Centered: (700-130)/2 = 285
        self.btn.setText('下載此音樂')
        self.btn.setStyleSheet(''' 
            QPushButton {
                color: #FFFFFF;
                background-color: #79861e;
                font: bold 20px;
                margin: 0px;
                border: 2px solid #5a6610;
                border-radius: 10px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #b6d7a8;
                color: #f00;
            }
        ''')
    
        # Connect button click event to the download function
        self.btn.clicked.connect(self.start_download)

        # === Add QLabel to Show Video Info ===
        self.video_info = QtWidgets.QLabel(self)
        # Center horizontally: (window_width - label_width) / 2 = (700 - 600) / 2 = 50
        self.video_info.setGeometry(50, 210, 600, 280)  # Position & size
        self.video_info.setWordWrap(True)  # Allow text wrapping for long titles
        self.video_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)  # Align left and top
        self.video_info.setScaledContents(False)
        self.video_info.setStyleSheet("""
            font: bold 20px; 
            color: black; 
            background-color: #efede8;
            border: 2px solid #79861e;
            border-radius: 15px;
            padding: 10px;
        """)
        self.video_info.setText("~下載音樂的相關資訊下載後會顯示在這裡~")
            

    def showText(self):
        """Updates the label with the current input text."""
        self.input_label.setText(self.input.text())

    def start_download(self):
        """Retrieves the YouTube URL from input and starts downloading."""
        youtube_url = self.input.text()  # Get the text from input field
        if youtube_url.strip():  # Ensure it's not empty
            self.download_audio_from_youtube(youtube_url)
        else:
            print("ERROR: Please enter a valid YouTube URL.")

    def wrap_path(self, path, max_width=550):
        """Wrap long file path by adding line breaks when text exceeds max_width pixels."""
        # Get font metrics for the current font (bold 20px)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPixelSize(20)
        metrics = QtGui.QFontMetrics(font)
        
        # If path fits within max_width, return as is
        if metrics.horizontalAdvance(path) <= max_width:
            return path
        
        # Split path by backslash or forward slash
        parts = path.replace('/', '\\').split('\\')
        
        lines = []
        current_line = ""
        
        for i, part in enumerate(parts):
            # Add separator for all except first part
            separator = "\\" if i > 0 else ""
            test_line = current_line + separator + part
            
            # Check if adding this part exceeds max_width
            if metrics.horizontalAdvance(test_line) > max_width and current_line:
                # Save current line and start new one
                lines.append(current_line)
                current_line = part
            else:
                current_line = test_line
        
        # Add remaining text
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)

    def download_audio_from_youtube(self, audio_url, dest_path=None):
        """
        Downloads audio from a YouTube video and saves it as an MP3 file.

        Parameters:
        audio_url (str): The URL of the YouTube video to download the audio from.
        dest_path (str): The destination file path to save the downloaded audio (as an mp3).

        Returns:
        None
        """
        try:
            yt = YouTube(audio_url, on_progress_callback=on_progress)

            # Extract video details
            video_title = yt.title
            video_length = yt.length
            video_author = yt.author

            # Convert length from seconds to hours:min:sec
            hours = video_length // 3600
            minutes = (video_length % 3600) // 60
            seconds = video_length % 60
            
            if hours > 0:
                length_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                length_formatted = f"{minutes}:{seconds:02d}"

            # Update QLabel to display video info
            video_info_text = f"🎵 標題: {video_title}\n⏳ 長度: {length_formatted}\n👤 創作者: {video_author}"
            self.video_info.setText(video_info_text)

            print("Title:", yt.title)
            print("Length:", yt.length, "seconds")
            print("Author:", yt.author)

            # Creating the file name
            if dest_path is None:
                dest_path = yt.title
                dest_path = "".join(dest_path.split())

            if not dest_path.endswith(".mp3"):
                dest_path += ".mp3"

            # Put into audios folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            audios_folder = os.path.join(script_dir, "..", "audios")
            audios_folder = os.path.abspath(audios_folder)  # Normalize the path
            os.makedirs(audios_folder, exist_ok=True)  # Create if doesn't exist
            
            # Get just the filename
            filename = os.path.basename(dest_path)
            full_path = os.path.join(audios_folder, filename)

            # Filter the streams to get the audio-only stream and download it
            best_audio = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            print(f"Best audio stream: {best_audio}")
            print(f"Downloading audio from {audio_url} ...\nSaving as {full_path}.")
            best_audio.download(output_path=audios_folder, filename=filename)
            print("Download complete!\n")
            # Notify user in GUI that download is complete - wrap path if too long
            wrapped_path = self.wrap_path(full_path)
            self.video_info.setText(video_info_text + f"\n📁 檔案:\n{wrapped_path}\n✅ 下載完成!")
        except Exception as e:
            print(f"ERROR: Unable to download this audio. Link: {audio_url}\nError: {e}")
            # Notify user in GUI that download is complete
            self.video_info.setText(f"ERROR: Unable to download this audio. Link: {audio_url}\nError: {e}")
            self.video_info.setStyleSheet("""
                font: bold 20px; 
                color: red; 
                background-color: #efede8;
                border: 2px solid #79861e;
                border-radius: 15px;
                padding: 10px;
            """)
'''
Usage: (It will start the gui.)
$ python yt_download_gui_main.py
'''            
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = DownloadWidget()
    
    # Set the background color for the whole window
    form.setStyleSheet("background-color: #fbe0b0;") 
    
    form.show()
    sys.exit(app.exec())
