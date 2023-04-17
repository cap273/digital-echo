import logging
import json
import os
import azure.functions as func

STORAGE_ACCOUNT_NAME = os.environ['STORAGE_ACCOUNT_NAME']
AUDIOFILES_CONTAINER_NAME = os.environ["AUDIOFILES_CONTAINER_NAME"]

def main(req: func.HttpRequest, outputSbMsg: func.Out[str]) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    # Parse requests body into JSON
    req_body_bytes = req.get_body()
    logging.info(f"Request Bytes: {req_body_bytes}")
    req_body = req_body_bytes.decode("utf-8")
    logging.info(f"Request String: {req_body}")

    if req_body:
        req_body_json = json.loads(req_body)
        logging.info(f"Request JSON: {req_body_json}")
    else:
        req_body_json = {}

    # Check that the HTTP POST contains the expected properties
    try:
        personaId = req_body_json['personaId']
        prompt = req_body_json['prompt']
        audio_file_name = req_body_json['audio_file_name']

        logging.info(f'Message to send to Service Bus: {req_body_json}')
        outputSbMsg.set(json.dumps(req_body_json))
        logging.info(f'Message sent to Service Bus')

        return func.HttpResponse(
                                json.dumps({
                                    "Status": "OK",
                                    "StatusMessage": f'Message sent to Service Bus. Persona ID: {personaId}. Prompt: {prompt}',
                                    "audio_check_url": f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{AUDIOFILES_CONTAINER_NAME}/{audio_file_name}.mpeg"
                                }),
                                mimetype="application/json",
                            )
    
    except KeyError:
        # HTTP POST is missing information
        return func.HttpResponse(status_code=400,
                                 body=f'Error: HTTP POST does not contain personaId and prompt in the correct format.')


    

    
