import logging
import json
import os
import requests
import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]

AUDIOFILES_CONTAINER_NAME = os.environ["AUDIOFILES_CONTAINER_NAME"]
STORAGE_ACCOUNT_CONNECTION_STRING = os.environ["AzureStorageAccountConnectionString"]

def main(message: func.ServiceBusMessage):

    message_content_type = message.content_type
    message_body = message.get_body().decode("utf-8")

    logging.info("Python ServiceBus topic trigger processed message.")
    logging.info("Message Content Type: " + message_content_type)
    logging.info("Message Body: " + message_body)

    message_json = json.loads(message_body)
    text = message_json["message"]["content"]
    personaId = message_json["personaId"]
    audio_file_name = message_json['audio_file_name']

    #TODO: Implement a better persona to voice id matching
    if personaId == "1":
        elevelabs_voice_id = "21m00Tcm4TlvDq8ikWAM"
    if personaId == "2":
        elevelabs_voice_id = "Jx6v6Gcfp3a7K5RVCJ7W"
    else:
        logging.info("Error. Persona ID: " + personaId)

    # Call the ElevenLabs API to convert text to speech
    elevenlabs_url = f"https://api.elevenlabs.io/v1/text-to-speech/{elevelabs_voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    request_body = {
        "text": text, 
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0
        }
    }

    response = requests.post(elevenlabs_url, headers=headers, json=request_body)

    if (200 <= response.status_code) and (response.status_code <= 299):
        # Store the audio file in Azure Storage account blob
        audio_data = response.content
        blob_name = f"{audio_file_name}.mpeg"

        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AUDIOFILES_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)

        blob_client.upload_blob(audio_data)
        logging.info(f"Audio file uploaded to Blob Storage: {blob_name}")
    else:
        logging.info(f"Error in ElevenLabs API call: {response.status_code}")




