import os
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import subprocess
import imageio_ffmpeg

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Upload and output folders (inside the project folder)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video = request.files['video']
        if video and video.filename.endswith('.webm'):
            unique_id = str(uuid.uuid4())
            input_filename = f"{unique_id}.webm"
            output_filename = f"{unique_id}.mp4"

            input_path = os.path.join(UPLOAD_FOLDER, input_filename)
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            video.save(input_path)

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            command = [
                ffmpeg_path,
                "-i", input_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-strict", "experimental",
                output_path
            ]

            try:
                subprocess.run(command, check=True)
                return render_template("converted.html", output_filename=output_filename)
            except Exception as e:
                return f"Conversion Error: {e}"

    return render_template("index.html")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
