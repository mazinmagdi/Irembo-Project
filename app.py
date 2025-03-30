from flask import Flask, render_template, request, jsonify
from io import BytesIO
from bs4 import BeautifulSoup
import os
import requests
import wave
import numpy as np
from groq import Groq

app = Flask(__name__)

# Configuration
SMS_TOKEN = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4Mzc2OTM5MzUsImlhdCI6MTc0Mjk5OTUzNSwiaWQiOiJ1c2VyXzAxSlE5RFdHMFlXNjFFQVlSQ0ZDVlAwSkJSIiwicmV2b2tlZF90b2tlbl9jb3VudCI6MH0.yeY0USU_ggpNrDA4nLojSheg92Qet-0Lb_CFJKyq11QzjVw_-STHEW3vMepx-XU9E-lwi84pBvdgY-voWQ6dMA'
SMS_HEADERS = {'Authorization': 'Bearer ' + SMS_TOKEN}
SMS_URL = 'https://api.pindo.io/v1/sms/'
SMS_SENDER = 'PindoTest'

# Doctor database
DOCTORS = {
    'General Physician': '+250794290793',
    'Pediatrician': '+250794290793',
    'Surgeon': '+250796196556',
    'Gynecologist': '+250796196556',
    'Psychiatrist': '+250796196556'
}

# Set Groq API key
os.environ["GROQ_API_KEY"] = "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"

def translate_text(text, target_lang):
    """Translate text using Google Translate"""
    url = f"https://translate.google.com/m?hl={target_lang}&sl=auto&tl={target_lang}&q={text}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    result = soup.find('div', class_='result-container').text
    return result

def get_llm_response(input_text, system_prompt=None):
    """Get response from Groq API"""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    if system_prompt:
        # For health assistant-specific processing with system prompt
        messages = [{
            "role": "user",
            "content": f"""# RWANA Health Voice Assistant

## SYSTEM INSTRUCTIONS

You are RWANA (Rural and Urban Wellness Network Assistant), a specialized Voice-AI Healthcare Assistant for Rwandan communities.

### PRIMARY FUNCTIONS
1. Remote symptom triage for rural areas
2. Mental wellness support for urban areas

### RESPONSE REQUIREMENTS
- All responses MUST be 450 characters or less
- Use simple, clear language
- For physical symptoms: collect information, assess severity, connect to providers
- For mental wellness: offer immediate techniques, assess professional needs
- Clearly state you are not a doctor/therapist
- Recognize emergencies and provide emergency contacts
- Decline non-healthcare requests
- make the output well formatted

Only engage with healthcare topics and keep all responses concise and under 450 characters.
Here is the prompt:{input_text}"""
        }]
    else:
        # For simple text processing
        messages = [{"role": "user", "content": input_text}]
    
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="deepseek-r1-distill-llama-70b"
    )
    
    response_content = chat_completion.choices[0].message.content
    cleaned_response = response_content.replace('<think>', '').replace('</think>', '').strip()
    return cleaned_response

def process_text_input(prompt):
    """Process text input and return response in Kinyarwanda"""
    # Translate input to English if needed
    english_text = translate_text(prompt, 'en')
    
    # Get response from LLM
    response = get_llm_response(english_text)
    
    # Translate response to Kinyarwanda
    kiny_response = translate_text(response, 'rw')
    
    return kiny_response

def process_audio_input(audio_file):
    """Process audio input and return response in Kinyarwanda"""
    # Save audio to a temporary file
    audio_data = audio_file.read()
    memory_file = BytesIO(audio_data)
    
    # Speech-to-text API call
    url = "https://api.pindo.io/ai/stt/rw/public"
    data = {"lang": "rw"}
    files = {'audio': ('file.wav', memory_file, 'audio/wav')}
    
    response = requests.post(url, files=files, data=data)
    
    if response.status_code != 200:
        return "Error processing audio"
    
    response_data = response.json()
    text = response_data['data']['text']
    
    # Translate to English
    english_text = translate_text(text, 'en')
    
    # Get response from LLM with system prompt
    response = get_llm_response(english_text, system_prompt=True)
    
    # Translate back to Kinyarwanda
    kiny_response = translate_text(response, 'rw')
    
    return kiny_response

def send_sms_notification(doctor_number, case_summary):
    """Send SMS notification to doctor"""
    data = {
        'to': doctor_number,
        'text': f"Medical Assistance Request:\n{case_summary[:160]}",
        'sender': SMS_SENDER
    }
    
    response = requests.post(SMS_URL, json=data, headers=SMS_HEADERS)
    
    # Successful status codes (200 OK or 201 Created)
    if response.status_code in (200, 201):
        try:
            response_data = response.json()
            # Check for either success status or message ID in response
            if response_data.get('status') == 'success' or response_data.get('id'):
                return True, "SMS sent successfully"
            return True, "SMS queued for delivery"  # Assume success for 200/201
        except ValueError:
            return True, "SMS sent (API response not JSON)"  # Assume success
    else:
        try:
            error_msg = response.json().get('message', 'Unknown error')
        except ValueError:
            error_msg = response.text or 'Unknown error'
        return False, f"Failed to send SMS: {error_msg}"

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', doctors=DOCTORS)

@app.route('/process_text', methods=['POST'])
def handle_text():
    """Process text input from the form"""
    text_input = request.form.get('text_input', '')
    
    if not text_input:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        response = process_text_input(text_input)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process_audio', methods=['POST'])
def handle_audio():
    """Process audio input from the form"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({"error": "No audio file selected"}), 400
    
    try:
        response = process_audio_input(audio_file)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_sms', methods=['POST'])
def handle_sms():
    """Send SMS to doctor"""
    data = request.json
    doctor_number = data.get('doctor_number')
    case_summary = data.get('case_summary')
    
    if not doctor_number or not case_summary:
        return jsonify({"success": False, "message": "Missing required information"}), 400
    
    success, message = send_sms_notification(doctor_number, case_summary)
    return jsonify({"success": success, "message": message})

if __name__ == '__main__':
    app.run(debug=True)