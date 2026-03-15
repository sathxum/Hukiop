from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import tempfile

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True, on_progress_callback=on_progress)
        
        streams = []
        # Video streams
        for s in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc():
            size = f"{s.filesize // (1024*1024)}MB" if s.filesize else "Unknown"
            streams.append({
                'itag': s.itag,
                'quality': s.resolution,
                'size': size,
                'type': 'video'
            })
        
        # Audio only
        audio = yt.streams.get_audio_only()
        if audio:
            size = f"{audio.filesize // (1024*1024)}MB" if audio.filesize else "Unknown"
            streams.append({
                'itag': 'audio',
                'quality': 'Audio Only (MP3)',
                'size': size,
                'type': 'audio'
            })
        
        return jsonify({
            'success': True,
            'title': yt.title,
            'author': yt.author,
            'thumbnail': yt.thumbnail_url,
            'streams': streams
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download():
    try:
        url = request.args.get('url')
        itag = request.args.get('itag')
        dtype = request.args.get('type', 'video')
        
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
        
        temp_dir = tempfile.gettempdir()
        
        if dtype == 'audio' or itag == 'audio':
            stream = yt.streams.get_audio_only()
            file_path = os.path.join(temp_dir, f"{yt.title}.mp3")
            stream.download(output_path=temp_dir, filename=f"{yt.title}.mp3")
            return send_file(file_path, as_attachment=True, download_name=f"{yt.title}.mp3")
        else:
            stream = yt.streams.get_by_itag(int(itag))
            file_path = os.path.join(temp_dir, f"{yt.title}.mp4")
            stream.download(output_path=temp_dir, filename=f"{yt.title}.mp4")
            return send_file(file_path, as_attachment=True, download_name=f"{yt.title}.mp4")
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)