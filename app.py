from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
# ACRCloud SDK import is optional and handled at runtime to prevent import-time crashes
try:
    from acrcloud.recognizer import ACRCloudRecognizer
    ACR_AVAILABLE = True
except Exception:
    ACRCloudRecognizer = None
    ACR_AVAILABLE = False
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit
app.config['UPLOAD_FOLDER'] = '/tmp'

# ACRCloud Configuration (prefer environment variables in production)
acr_config = {
    "host": os.getenv('ACR_HOST', "identify-ap-southeast-1.acrcloud.com"),
    "access_key": os.getenv('ACR_ACCESS_KEY', "ce012af12e9a6e863ff8ae6daecc1a20"),
    "access_secret": os.getenv('ACR_ACCESS_SECRET', "XBVTMH7UaIOaGd8cfpgbTBPvLBryzuOTkW1lUQrf"),
}

# Initialize ACRCloud recognizer if available
acr = None
if ACR_AVAILABLE:
    try:
        acr = ACRCloudRecognizer(**acr_config)
    except Exception:
        acr = None


def to_time(ms):
    """Convert milliseconds to MM:SS format"""
    m = (ms // 60000) % 60
    s = (ms // 1000) % 60
    return f"{m:02d}:{s:02d}"


def what_music(buffer):
    """Identify music from audio buffer"""
    if acr is None:
        raise Exception("ACRCloud SDK is not available in this environment. Ensure the 'acrcloud' package is installed and configured.")

    try:
        res = acr.recognize_by_file(buffer, 0)
        data = res.get('metadata', {})
        
        if not data.get('music') or len(data['music']) == 0:
            raise Exception("Lagu tidak ditemukan atau tidak dapat diidentifikasi.")
        
        results = []
        for music in data['music']:
            result = {
                'title': music.get('title', 'Unknown'),
                'artist': music.get('artists', [{}])[0].get('name', 'Unknown') if music.get('artists') else 'Unknown',
                'score': music.get('score', 0),
                'release': datetime.strptime(music.get('release_date', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if music.get('release_date') else 'Unknown',
                'duration': to_time(music.get('duration_ms', 0)) if music.get('duration_ms') else '00:00',
                'url': []
            }
            
            # Extract URLs from external metadata
            external_metadata = music.get('external_metadata', {})
            if 'youtube' in external_metadata:
                result['url'].append(f"https://youtu.be/{external_metadata['youtube'].get('vid', '')}")
            if 'deezer' in external_metadata:
                result['url'].append(f"https://www.deezer.com/us/track/{external_metadata['deezer'].get('track', {}).get('id', '')}")
            if 'spotify' in external_metadata:
                result['url'].append(f"https://open.spotify.com/track/{external_metadata['spotify'].get('track', {}).get('id', '')}")
            
            result['url'] = [url for url in result['url'] if url]
            results.append(result)
        
        return results
    except Exception as e:
        raise Exception(str(e))

@app.route('/')
def index():
    """Serve the main HTML page"""
    # If ACRCloud is not installed, we still serve the frontend but show a warning in the identify endpoint.
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/identify', methods=['POST'])
def identify():
    """Handle music identification"""
    try:
        # If the SDK is not available, return a helpful error explaining how to fix it
        if acr is None:
            msg = (
                "Dependency error: ACRCloud SDK not available.\n"
                "Make sure you've installed Python dependencies (see requirements.txt) and that the 'acrcloud' package is present.\n"
                "Locally: run `pip install -r requirements.txt`. On Vercel, ensure requirements.txt is at the repository root so the platform installs dependencies.\n"
                "You can also set ACR cloud credentials via environment variables: ACR_HOST, ACR_ACCESS_KEY, ACR_ACCESS_SECRET."
            )
            return jsonify({'error': msg}), 500

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded.'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 100 * 1024 * 1024:
            return jsonify({'error': 'File terlalu besar (maks 100 MB)'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Identify music
        results = what_music(file_data)
        
        if not results:
            return jsonify({'error': 'Lagu tidak ditemukan atau tidak dapat diidentifikasi.'}), 404
        
        res = results[0]
        result_text = f"{res['title']} - {res['artist']}"
        
        # Return a minimal JSON response for API usage (keeping original HTML response is large)
        return jsonify({'title': res['title'], 'artist': res['artist'], 'release': res['release'], 'duration': res['duration'], 'urls': res['url'], 'text': result_text})
        
    except Exception as error:
        print(f"Error: {str(error)}")
        return jsonify({'error': str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
