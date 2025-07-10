import os
import uuid
import subprocess
import imageio_ffmpeg
from flask import Flask, request, render_template, send_file, abort

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Upload and output folders
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Flask app config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video = request.files.get('video')

        if not video:
            return "No file selected.", 400

        if not video.filename.endswith('.webm'):
            return "Invalid file type. Please upload a .webm video.", 400

        # Generate unique file names
        unique_id = str(uuid.uuid4())
        input_filename = f"{unique_id}.webm"
        output_filename = f"{unique_id}.mp4"

        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        video.save(input_path)
        print(f"[INFO] Uploaded file: {video.filename}")
        print(f"[INFO] Saved to: {input_path}")
        print(f"[INFO] Will convert to: {output_path}")

        # Get FFmpeg path
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"[INFO] Using ffmpeg from: {ffmpeg_path}")

        command = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            output_path
        ]

        try:
            # Run the command and capture stdout/stderr
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            print("[DEBUG] FFmpeg STDOUT:")
            print(result.stdout)
            print("[DEBUG] FFmpeg STDERR:")
            print(result.stderr)

            if result.returncode != 0:
                print("[ERROR] FFmpeg failed.")
                return f"Conversion failed. FFmpeg error:<br><pre>{result.stderr}</pre>", 500

            if not os.path.exists(output_path):
                print("[ERROR] Output file not found after conversion.")
                return "Conversion failed: output file missing.", 500

            print(f"[SUCCESS] File converted: {output_path}")
            return render_template("converted.html", output_filename=output_filename)

        except Exception as e:
            print(f"[EXCEPTION] {str(e)}")
            return f"Unexpected error during conversion: {e}", 500

    return render_template("index.html")

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        print(f"[ERROR] Download file not found: {file_path}")
        abort(404, description="File not found.")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
