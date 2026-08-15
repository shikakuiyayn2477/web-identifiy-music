# Web Identify Music

A web application to identify music from audio files using ACRCloud API.

## Backend Migration

The backend has been migrated from **Node.js/Express** to **Python/Flask**.

### Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application locally:**
   ```bash
   python app.py
   ```

   The server will run at `http://0.0.0.0:5000`

3. **Deploy to Vercel:**
   ```bash
   vercel
   ```

### Environment Variables

The ACRCloud credentials are configured in `app.py`. In production, consider using environment variables:

- `ACR_HOST`: ACRCloud host
- `ACR_ACCESS_KEY`: ACRCloud access key
- `ACR_ACCESS_SECRET`: ACRCloud access secret

### API Endpoints

- `GET /` - Serve the main HTML interface
- `POST /identify` - Identify music from uploaded audio file (max 100 MB)

### Features

- Upload audio file and identify the song
- Display song title, artist, release date, and duration
- Links to YouTube, Spotify, Deezer, and SoundCloud
- Dark/Light theme toggle
- Responsive design with Tailwind CSS

### Technologies Used

- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Backend**: Python, Flask
- **API**: ACRCloud Music Recognition API
- **Hosting**: Vercel
