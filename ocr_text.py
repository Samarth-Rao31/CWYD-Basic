import fitz
import pytesseract
import io
from PIL import Image
import requests
import uuid
import json
import streamlit as st
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


# pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


def process_pdf(pdf_path):
    try:
        pdf_file = fitz.open(pdf_path)
        extracted_text = '\n'

        for page_num in range(len(pdf_file)):
            page = pdf_file[page_num]
            page_text = page.get_text()
            try:
                
                images = []
                image_list = page.get_images()
                if image_list:
                    for _, img_ref in enumerate(page.get_images(), start=1):
                        xref = img_ref[0]
                        base_image = pdf_file.extract_image(xref)
                        image_bytes = base_image["image"]
                        images.append(image_bytes)
                    image_text = '\n'
                    for image in images:
                        stream = io.BytesIO(image)
                        img = Image.open(stream)
                        text = pytesseract.image_to_string(img)
                        image_text += '\n'.join(text) + ' '
                    page_text += image_text
            except Exception as e:
                continue


                
            extracted_text += page_text

        return extracted_text
    
    except Exception as e:
        pass
  

def process_image(image):
    try:
        extracted_text = '\n'
        text = pytesseract.image_to_string(image)
        print(text)
        extracted_text += '\n'.join(text) + ' '
        return extracted_text
    except Exception as e:
        return " "


def detect_lang(text):
    key = "028410d9d70044998642ffc1a75865c5"
    endpoint = "https://api.cognitive.microsofttranslator.com"
    location = "eastus"
    path = '/detect'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }


    body = [{
        'text': text
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    
    if request.status_code != 200:
        st.error(f"Error: {request.status_code} - {request.reason}")
        return None

    try:
        response_data = request.json()
        trans = response_data[0]['language']
        return trans
    except Exception as e:
        st.error(f"Error parsing JSON: {e}")
        return None


def translateText(text, to_language):
        # Add your key and endpoint
        key = "028410d9d70044998642ffc1a75865c5"
        endpoint = "https://api.cognitive.microsofttranslator.com"
        location = "eastus"
        path = '/translate'
        constructed_url = endpoint + path

        params = {
            'api-version': '3.0',
            'to': [to_language]
        }

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            # location required if you're using a multi-service or regional (not global) resource.
            'Ocp-Apim-Subscription-Region': location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }


        body = [{
            'text': text
        }]

        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()
        # print(response)

        if 'error' in response:
            st.error(f"An error occurred: {response['error']['message']}")
            translation = None
        else:
            translation = response[0]['translations'][0]['text']

        return translation