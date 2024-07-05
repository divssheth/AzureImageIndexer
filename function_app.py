import azure.functions as func
import logging
import requests
import base64
import os
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="image_desc")
def image_desc(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get the image URL from the request
    values = req.get_json()['values']
    results = []
    for value in values:
        result = {}
        result['recordId'] = value['recordId']
        data = value['data']
        logging.info(f'Data: {data}')
        IMAGE_PATH = data['url']+data['queryString']
        GPT4V_KEY = os.environ['GPT4_API_KEY']
        GPT4V_ENDPOINT = os.environ['GPT4_ENDPOINT']
        encoded_image = base64.b64encode(requests.get(IMAGE_PATH).content).decode('ascii')
        headers = {
            "Content-Type": "application/json",
            "api-key": GPT4V_KEY,
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "As an AI assistant, your task is to describe and identify the main object in an image. Provide a detailed explanation that describes the image but no more than 3 sentences, and specify a noun that represents the primary object in the image. Ensure that the output strictly adheres to the specified JSON format and does not include any additional keys. Always return the result in the following JSON format: {\"description\": \"\", \"entity\": \"\"}. Please provide your response in JSON format only, without using triple backticks (```). Ensure the output is a valid JSON object."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 200
        }
        GPT4V_ENDPOINT = os.environ['GPT4_ENDPOINT']
        response = None
        try:
            response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
            logging.info(f'Response: {response.json()}')
            resp_text = json.loads(response.json()['choices'][0]['message']['content'])
            logging.info(f'Response Text: {resp_text}')
            result['data'] = resp_text
            results.append(result)
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")
        
    resp = {}
    resp['values'] = results
    return func.HttpResponse(json.dumps(resp), mimetype="application/json")