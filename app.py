from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from acrcloud.recognizer import ACRCloudRecognizer
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit
app.config['UPLOAD_FOLDER'] = '/tmp'

# ACRCloud Configuration
acr_config = {
    "host": "identify-ap-southeast-1.acrcloud.com",
    "access_key": "ce012af12e9a6e863ff8ae6daecc1a20",
    "access_secret": "XBVTMH7UaIOaGd8cfpgbTBPvLBryzuOTkW1lUQrf",
}

acr = ACRCloudRecognizer(**acr_config)

def to_time(ms):
    """Convert milliseconds to MM:SS format"""
    m = (ms // 60000) % 60
    s = (ms // 1000) % 60
    return f"{m:02d}:{s:02d}"

def what_music(buffer):
    """Identify music from audio buffer"""
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
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/identify', methods=['POST'])
def identify():
    """Handle music identification"""
    try:
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
        
        html_response = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Identified!</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/upload-file-lab/fileupload7/main/uploads/1767884046527.jpegformat=png&name=900x900">

    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{}}
            }}
        }}
    </script>

    <style>
        * {{
            transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
        }}
        body, html {{
            min-height: 100%;
            margin: 0;
            padding: 0;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}
        .dark-scrollbar::-webkit-scrollbar {{
            width: 8px;
        }}

        .dark-scrollbar::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}

        .dark-scrollbar::-webkit-scrollbar-thumb {{
            background: #444444;
            border-radius: 4px;
        }}

        .dark-scrollbar::-webkit-scrollbar-thumb:hover {{
            background: #555555;
        }}

        .light-scrollbar::-webkit-scrollbar {{
            width: 8px;
        }}

        .light-scrollbar::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        .light-scrollbar::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 4px;
        }}

        .light-scrollbar::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}

        .card-glow {{
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card-glow:hover {{
            transform: translateY(-5px);
        }}

        .dark-card:hover {{
            box-shadow: 0 20px 30px rgba(255, 255, 255, 0.05);
        }}

        .light-card:hover {{
            box-shadow: 0 20px 30px rgba(0, 0, 0, 0.1);
        }}

        .dark-body {{
            background-color: #000000 !important;
        }}

        .light-body {{
            background-color: #f9fafb !important;
        }}
    </style>
</head>
<body class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="fixed top-4 right-4 z-50">
        <button id="theme-toggle" type="button" 
            class="p-3 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white 
                   hover:bg-gray-100 dark:hover:bg-gray-700 transition duration-300 
                   focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-500
                   shadow-lg border border-gray-200 dark:border-gray-700">
            <svg id="theme-toggle-dark-icon" class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
            </svg>
            <svg id="theme-toggle-light-icon" class="w-6 h-6 hidden" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 01-1.414-1.414l.707-.707a1 1 0 111.414 1.414l-.707.707zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.555a1 1 0 1-1.414-1.414L3.636 4.05a1 1 0 111.414 1.414l-.707.707zm5.707-5.707a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM5 8a1 1 0 100-2H4a1 1 0 000 2h1z"></path>
            </svg>
        </button>
    </div>

    <div class="flex flex-col items-center justify-center min-h-screen p-4">
        <div class="mb-8 text-center">
            <img src="https://raw.githubusercontent.com/upload-file-lab/fileupload7/main/uploads/1767888533003.png" 
                 class="rounded-lg shadow-lg mx-auto max-w-[250px] h-auto" 
                 alt="Music Identifier Logo">
        </div>

        <div id="main-card" class="w-full max-w-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                    rounded-xl shadow-xl p-8 card-glow fade-in">
            <div class="mb-6 text-center">
                <div class="mx-auto h-32 w-32 flex items-center justify-center rounded-full shadow-lg border-4 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700">
                    <svg class="w-16 h-16 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z"></path>
                    </svg>
                </div>
                <h1 class="text-2xl font-black mt-4 dark:text-white">
                    MUSIC IDENTIFIED!
                </h1>
            </div>

            <div class="bg-gray-50 dark:bg-gray-900 p-6 rounded-2xl mb-6 shadow-inner border border-gray-200 dark:border-gray-700">
                <div class="space-y-3">
                    <div class="flex flex-col">
                        <span class="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-widest">Title</span>
                        <span class="text-xl font-bold text-gray-800 dark:text-white">{res['title']}</span>
                    </div>
                    <div class="flex flex-col border-t border-gray-200 dark:border-gray-700 pt-2">
                        <span class="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-widest">Artist</span>
                        <span class="text-lg font-semibold text-gray-700 dark:text-gray-200">{res['artist']}</span>
                    </div>
                    <div class="flex flex-col border-t border-gray-200 dark:border-gray-700 pt-2">
                        <span class="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-widest">Release Date</span>
                        <span class="text-md text-gray-600 dark:text-gray-300">{res['release']}</span>
                    </div>
                </div>
            </div>

            <div class="flex flex-col space-y-3">
                <button onclick="copyResult()" 
                        class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                    Copy the information
                </button>
                <a href="https://www.youtube.com/results?search_query=${{res['title'].replace(' ', '+')"}}" 
                   class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                    Search for the music on YouTube
                </a>
                <a href="https://open.spotify.com/search/${{res['title'].replace(' ', '+')"}}" 
                   class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                    Search for the music on Spotify
                </a>
                <a href="https://soundcloud.com/search?q=${{res['title'].replace(' ', '+')"}}" 
                   class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                    Search for the music on SoundCloud
                </a>
                <a href="/" 
                   class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                    Search Other Music
                </a>
            </div>
        </div>
    </div>

    <textarea id="copyBuffer" class="hidden">{result_text}</textarea>

    <script>
        const themeToggleBtn = document.getElementById('theme-toggle');
        const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
        const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
        const htmlElement = document.documentElement;
        const bodyElement = document.body;
        const mainCard = document.getElementById('main-card');

        function setTheme(isDark) {{
            if (isDark) {{
                htmlElement.classList.add('dark');
                bodyElement.classList.add('dark-body');
                bodyElement.classList.remove('light-body');
                localStorage.setItem('theme', 'dark');

                themeToggleDarkIcon.classList.remove('hidden');
                themeToggleLightIcon.classList.add('hidden');

                mainCard.classList.add('dark-card');
                mainCard.classList.remove('light-card');
            }} else {{
                htmlElement.classList.remove('dark');
                bodyElement.classList.remove('dark-body');
                bodyElement.classList.add('light-body');
                localStorage.setItem('theme', 'light');

                themeToggleDarkIcon.classList.add('hidden');
                themeToggleLightIcon.classList.remove('hidden');

                mainCard.classList.add('light-card');
                mainCard.classList.remove('dark-card');
            }}

            updateScrollbarClass();
        }}

        function updateScrollbarClass() {{
            const isDark = htmlElement.classList.contains('dark');
            if (isDark) {{
                bodyElement.classList.remove('light-scrollbar');
                bodyElement.classList.add('dark-scrollbar');
            }} else {{
                bodyElement.classList.remove('dark-scrollbar');
                bodyElement.classList.add('light-scrollbar');
            }}
        }}

        function initTheme() {{
            const savedTheme = localStorage.getItem('theme');
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            if (savedTheme === 'dark') {{
                setTheme(true);
            }} else if (savedTheme === 'light') {{
                setTheme(false);
            }} else {{
                if (systemPrefersDark) {{
                    setTheme(true);
                }} else {{
                    setTheme(false);
                }}
            }}
        }}

        themeToggleBtn.addEventListener('click', () => {{
            const isDark = htmlElement.classList.contains('dark');
            setTheme(!isDark);
        }});

        function copyResult() {{
            const copyText = document.getElementById("copyBuffer");
            copyText.select();
            copyText.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(copyText.value).then(() => {{
                showNotification("Succes copy!", "success");
            }}).catch(err => {{
                showNotification(err, "error");
            }});
        }}

        function showNotification(message, type) {{
            const existingNotification = document.querySelector('.notification');
            if (existingNotification) {{
                existingNotification.remove();
            }}

            const notification = document.createElement('div');
            notification.className = `notification fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg 
                                     ${{type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}}
                                     transform translate-x-full transition-transform duration-300`;
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(() => {{
                notification.classList.remove('translate-x-full');
                notification.classList.add('translate-x-0');
            }}, 10);

            setTimeout(() => {{
                notification.classList.remove('translate-x-0');
                notification.classList.add('translate-x-full');
                setTimeout(() => {{
                    notification.remove();
                }}, 300);
            }}, 3000);
        }}

        function init() {{
            initTheme();
        }}
        init();
        document.addEventListener('DOMContentLoaded', initTheme);
    </script>
</body>
</html>
        """
        return html_response
        
    except Exception as error:
        print(f"Error: {str(error)}")
        html_error = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Not Found</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/upload-file-lab/fileupload7/main/uploads/1767884046527.jpegformat=png&name=900x900">

    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{}}
            }}
        }}
    </script>

    <style>
        * {{
            transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
        }}
        body, html {{
            min-height: 100%;
            margin: 0;
            padding: 0;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}
        .dark-scrollbar::-webkit-scrollbar {{
            width: 8px;
        }}

        .dark-scrollbar::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}

        .dark-scrollbar::-webkit-scrollbar-thumb {{
            background: #444444;
            border-radius: 4px;
        }}

        .dark-scrollbar::-webkit-scrollbar-thumb:hover {{
            background: #555555;
        }}

        .light-scrollbar::-webkit-scrollbar {{
            width: 8px;
        }}

        .light-scrollbar::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        .light-scrollbar::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 4px;
        }}

        .light-scrollbar::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}

        .card-glow {{
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card-glow:hover {{
            transform: translateY(-5px);
        }}

        .dark-card:hover {{
            box-shadow: 0 20px 30px rgba(255, 255, 255, 0.05);
        }}

        .light-card:hover {{
            box-shadow: 0 20px 30px rgba(0, 0, 0, 0.1);
        }}

        .dark-body {{
            background-color: #000000 !important;
        }}

        .light-body {{
            background-color: #f9fafb !important;
        }}
    </style>
</head>
<body class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="fixed top-4 right-4 z-50">
        <button id="theme-toggle" type="button" 
            class="p-3 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white 
                   hover:bg-gray-100 dark:hover:bg-gray-700 transition duration-300 
                   focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-500
                   shadow-lg border border-gray-200 dark:border-gray-700">
            <svg id="theme-toggle-dark-icon" class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
            </svg>
            <svg id="theme-toggle-light-icon" class="w-6 h-6 hidden" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 01-1.414-1.414l.707-.707a1 1 0 111.414 1.414l-.707.707zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.555a1 1 0 1-1.414-1.414L3.636 4.05a1 1 0 111.414 1.414l-.707.707zm5.707-5.707a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM5 8a1 1 0 100-2H4a1 1 0 000 2h1z"></path>
            </svg>
        </button>
    </div>

    <div class="flex flex-col items-center justify-center min-h-screen p-4 -mt-10">
        <div class="mb-6 text-center">
            <img src="https://raw.githubusercontent.com/upload-file-lab/fileupload7/main/uploads/1767888533003.png" 
                 class="rounded-lg shadow-lg mx-auto max-w-[220px] h-auto" 
                 alt="Music Identifier Logo">
        </div>

        <div id="main-card" class="w-full max-w-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                    rounded-xl shadow-xl p-8 card-glow fade-in">
            <div class="mb-6 text-center">
                <div class="mx-auto h-28 w-28 flex items-center justify-center rounded-full shadow-lg border-4 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700">
                    <svg class="w-14 h-14 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                </div>
                <h1 class="text-2xl font-black mt-4 dark:text-white">
                    MUSIC NOT FOUND!
                </h1>
            </div>
            <div class="flex flex-col space-y-3">
                <a href="/" 
                   class="w-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 
                          hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 
                          font-bold py-3 px-4 rounded-xl transition duration-200
                          border border-gray-200 dark:border-gray-700">
                     Search Other Music
                </a>
            </div>
        </div>
    </div>

    <textarea id="copyBuffer" class="hidden">Error: {str(error)}</textarea>

    <script>
        const themeToggleBtn = document.getElementById('theme-toggle');
        const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
        const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
        const htmlElement = document.documentElement;
        const bodyElement = document.body;
        const mainCard = document.getElementById('main-card');

        function setTheme(isDark) {{
            if (isDark) {{
                htmlElement.classList.add('dark');
                bodyElement.classList.add('dark-body');
                bodyElement.classList.remove('light-body');
                localStorage.setItem('theme', 'dark');

                themeToggleDarkIcon.classList.remove('hidden');
                themeToggleLightIcon.classList.add('hidden');

                mainCard.classList.add('dark-card');
                mainCard.classList.remove('light-card');
            }} else {{
                htmlElement.classList.remove('dark');
                bodyElement.classList.remove('dark-body');
                bodyElement.classList.add('light-body');
                localStorage.setItem('theme', 'light');

                themeToggleDarkIcon.classList.add('hidden');
                themeToggleLightIcon.classList.remove('hidden');

                mainCard.classList.add('light-card');
                mainCard.classList.remove('dark-card');
            }}

            updateScrollbarClass();
        }}

        function updateScrollbarClass() {{
            const isDark = htmlElement.classList.contains('dark');
            if (isDark) {{
                bodyElement.classList.remove('light-scrollbar');
                bodyElement.classList.add('dark-scrollbar');
            }} else {{
                bodyElement.classList.remove('dark-scrollbar');
                bodyElement.classList.add('light-scrollbar');
            }}
        }}

        function initTheme() {{
            const savedTheme = localStorage.getItem('theme');
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            if (savedTheme === 'dark') {{
                setTheme(true);
            }} else if (savedTheme === 'light') {{
                setTheme(false);
            }} else {{
                if (systemPrefersDark) {{
                    setTheme(true);
                }} else {{
                    setTheme(false);
                }}
            }}
        }}

        themeToggleBtn.addEventListener('click', () => {{
            const isDark = htmlElement.classList.contains('dark');
            setTheme(!isDark);
        }});

        function init() {{
            initTheme();
        }}
        init();
        document.addEventListener('DOMContentLoaded', initTheme);
    </script>
</body>
</html>
        """
        return html_error, 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
