from flask import Flask, render_template, send_file, request, after_this_request
import os


import subprocess
import uuid

from google import genai
from dotenv import load_dotenv

load_dotenv("api_key.env")

API_KEY = os.getenv("key")

app = Flask(__name__)

@app.route("/")
def welcoming_page():
    return render_template("index.html")

@app.route("/display", methods =["POST"])
def displaying():
    try:
        niche = request.form["niche"]

        client = genai.Client(api_key = API_KEY)

        response = client.models.generate_content(model = "gemini-2.5-flash",   
                                                contents= f"Generate 10 viral video ideas for {niche}. Output format: Topic | Hook \n Topic | hook \n Topic | hook \n  Rules: \n  10 words max per line total,  Topic is the video concept, Hook is the first attention-grabbing sentence, Separate Topic and Hook with ' | '  One idea per line No numbering, no explanations"
                                                )
        
        return render_template("display.html", output = response.text)
    
    except Exception:
        return render_template("error.html")
    
    
@app.route("/edit-form", methods = ["POST"])
def sumbitting_the_video():
    return render_template("video-edit.html")

@app.route("/upload", methods=["POST"])
def upload_and_stream_video():
    try:
        # 1. Grab the uploaded file from the request
        video = request.files["file"]

        # 2. Use Render's local temporary folder
        os.makedirs("/tmp/uploads", exist_ok=True)
        os.makedirs("/tmp/output", exist_ok=True)

        unique_id = str(uuid.uuid4())
        
        input_path = f"/tmp/uploads/{unique_id}.mp4"
        output_path = f"/tmp/output/{unique_id}.mp4"


        video.save(input_path)
        print(f"Successfully cached raw upload to: {input_path}")

        # 4. Run auto-editor synchronously (holds connection open while processing)

        command = f"auto-editor {input_path} --output {output_path} --margin 0.2s --video_codec h264 --audio_codec aac --no_open"
        
        
        subprocess.run(command, shell=True, check=True)
        
        short_id = unique_id[:4]

        @after_this_request
        def remove_temporary_files(response):
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                    
                if os.path.exists(output_path):
                    os.remove(output_path)
                print(f"Successfully cleaned up /tmp storage files for ID: {unique_id}")
                
            except Exception as cleanup_error:
                print(f"Non-fatal error cleaning temporary files: {cleanup_error}")
                
            return response


        return send_file(
            output_path, 
            as_attachment=True, 
            download_name=f"edited_{short_id}.mp4"
        )

    except Exception as e:
        return render_template("upload-error.html")


    
