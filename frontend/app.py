from flask import Flask, request, jsonify, render_template, abort, send_file, Response
import os
import requests
from datetime import datetime

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates"
)

AZURE_FUNCTIONS_NAME = os.environ["AZURE_FUNCTIONS_NAME"]
AZURE_FUNCTIONS_API = "get_prompt_for_chatgpt"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_prompt', methods=['POST'])
def submit_prompt():

    data = request.get_json()
    text_prompt = data['text_prompt']
    persona_id = data['persona_id']
    # Call the Azure Function to process the text prompt
    # and get the URL to check for the audio file
    response = requests.post(
        f'https://{AZURE_FUNCTIONS_NAME}.azurewebsites.net/api/{AZURE_FUNCTIONS_API}', 
        json={
            "prompt": text_prompt,
            "personaId": persona_id,
            "audio_file_name": f"audio_{persona_id}_{round((datetime.now()).timestamp())}"
        }
    )

    data_to_return = response.json()
    return jsonify(data_to_return)

@app.route('/fetch_audio')
def fetch_audio():
    audio_url = request.args.get('url')

    # Fetch the audio file from the given URL
    audio_response = requests.get(audio_url)

    # Check if the audio file exists
    if audio_response.status_code == 404:
        abort(404)  # Return a 404 status code to the frontend

    # Send the fetched audio file as a response
    return Response(
        audio_response.content,
        content_type='audio/mpeg',  # Explicitly set the content type
        headers={
            'Content-Disposition': 'attachment; filename=audio.mp3'
        }
    )

if __name__ == '__main__':
    app.run()