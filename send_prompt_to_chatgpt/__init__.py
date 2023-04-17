import logging
import openai
import json
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PERSONAS_CONTAINER_NAME = os.environ["PERSONAS_CONTAINER_NAME"]
STORAGE_ACCOUNT_CONNECTION_STRING = os.environ["AzureStorageAccountConnectionString"]

def main(message: func.ServiceBusMessage, outputSbMsg: func.Out[str]):

    message_content_type = message.content_type
    message_body = message.get_body().decode("utf-8")

    logging.info("Python ServiceBus topic trigger processed message.")
    logging.info("Message Content Type: " + message_content_type)
    logging.info("Message String: " + message_body)

    message_body_json = json.loads(message_body)
    personaId = message_body_json['personaId']
    prompt = message_body_json['prompt']
    audio_file_name = message_body_json['audio_file_name']

    logging.info(f"Getting the information from blob for persona ID: {personaId}")

    persona_response = get_persona_context(personaId)
    if persona_response["Status"] == "Error":
        logging.info(f"Error in retrieving persona: {persona_response['StatusCode']}")
        return ""

    context = persona_response["body"]
    logging.info(f"Persona context retrieved: {context}")

    logging.info(f"Persona context retrieved: {context}")
    logging.info(f"Calling Chat GPT...")
    response = call_chatgpt(prompt, context)
    logging.info(f"Response from Chat GPT: {response}")

    response['personaId'] = personaId
    response['audio_file_name'] = audio_file_name

    logging.info(f"Storing Chat GPT response in service bus queue...")
    outputSbMsg.set(json.dumps(response))


def call_chatgpt(prompt: str, context: str):

    # Send the request to the OpenAI API
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",

        # The messages to generate chat completions for, in the chat format.
        messages=[
                {"role": "system", "content": 'You get the name, biography, life stories, and opinions of a person. '\
                    'Respond as if you were that person. The context for that person is below: \n'},
                {"role": "system", "content": context},
                {"role": "system", "content": "Limit your responses to 3 sentences."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=100, # The maximum number of tokens to generate in the completion.
            n=1, # How many chat completion choices to generate for each input message.
    )

    # Extract the response text from the response object
    return response.choices[0]


def get_persona_context(personaId: str):

    # Get the name of the blob
    blob_name = personaId + ".json"

    # Create a blob service client and a blob client for the specific JSON file
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=PERSONAS_CONTAINER_NAME, blob=blob_name)

    try:
        # Download the JSON file and read its contents
        json_data = blob_client.download_blob().content_as_text()
    except:
        return {"Status": "Error",
                "StatusCode": f"Error in downloading blob {blob_name} from container {PERSONAS_CONTAINER_NAME}."}

    # Load the JSON data as a Python dictionary
    persona = json.loads(json_data)

    context = f"Person: {persona['name']}. Biography: {persona['biography']}\n"
    for story in persona['life_stories']:
        context += f"Life story: {story}\n"
    for opinion in persona['opinions']:
        context += f"Opinion: {opinion}\n"

    return {"Status": "OK",
            "StatusCode": f"Error in downloading blob {blob_name} from container {PERSONAS_CONTAINER_NAME}.",
            "body": context}



