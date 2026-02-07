from flask import Flask, render_template, request, jsonify
import ssl
import os
from pytubefix import YouTube
from pytubefix.cli import on_progress

# Fix SSL issues
ssl._create_default_https_context = ssl._create_stdlib_context

app = Flask(__name__)

# Configure audios folder path
AUDIOS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audios")
AUDIOS_FOLDER = os.path.abspath(AUDIOS_FOLDER)
os.makedirs(AUDIOS_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index_modern.html')


@app.route('/download', methods=['POST'])
def download():
    """Handle the download request."""
    data = request.get_json()
    youtube_url = data.get('url', '').strip()
    
    if not youtube_url:
        return jsonify({
            'success': False,
            'error': 'Please enter a valid YouTube URL.'
        }), 400
    
    try:
        # Create YouTube object
        yt = YouTube(youtube_url, on_progress_callback=on_progress)
        
        # Extract video details
        video_title = yt.title
        video_length = yt.length
        video_author = yt.author
        
        # Convert length to formatted string
        hours = video_length // 3600
        minutes = (video_length % 3600) // 60
        seconds = video_length % 60
        
        if hours > 0:
            length_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            length_formatted = f"{minutes}:{seconds:02d}"
        
        # Create filename from title
        filename = "".join(video_title.split())
        if not filename.endswith(".mp3"):
            filename += ".mp3"
        
        full_path = os.path.join(AUDIOS_FOLDER, filename)
        
        # Download the audio
        best_audio = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        
        print(f"Downloading: {video_title}")
        print(f"Saving to: {full_path}")
        
        best_audio.download(output_path=AUDIOS_FOLDER, filename=filename)
        
        print("Download complete!")
        
        return jsonify({
            'success': True,
            'title': video_title,
            'length': length_formatted,
            'author': video_author,
            'filename': filename,
            'path': full_path
        })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unable to download: {str(e)}'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Run Flask app
    # 0.0.0.0 makes it accessible from outside the container
    app.run(host='0.0.0.0', port=5000, debug=False)
