from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import requests
import io
import base64
import time
from PIL import Image

app = Flask(__name__)

# ==================== CONFIGURATION ====================
GEMINI_KEYS = [
    "AQ.Ab8RN6IuHfrwyqNt4MwevdgyBwD-2Enx6s4yFFOIHCVPyScP2Q",
    "AQ.Ab8RN6I8piw8JaxF80NwdDTDe_MH69VyDH9647zstHqKgwwYnQ",
    "AQ.Ab8RN6LGak5MugStKqsQEp0BqODCH-M8zIH6yqXf8lqCGJUnwA",
    "AQ.Ab8RN6JrEpZDFmFLrrXvCnfuTKomwFv3xakjlIP1v_u5LSETRQ"
]

GROQ_KEY = "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"           
OPENAI_KEY = "sk-c91886434da446de9137b79c0b55c737"    
HF_TOKEN = "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"      
# =======================================================

# NEXUS er MEMORY SYSTEM
user_sessions = {}

# CORE SYSTEM INSTRUCTION (Identity Configuration)
GLOBAL_SYSTEM_INSTRUCTION = "Tomar nam NEXUS. Tomake baniyeche Pritam Santra. Keu jodi tomar porichoy jante chay, tahole bolbe 'Ami NEXUS, apnar personal AI assistant, jake toiri koreche Pritam Santra'. Kono Math, Science ba onno kono doubt er proshno asle, tumi kono nirdesh ba rules repeat korbe na. Ekdom direct step-by-step plain text-e asol proshnor uttor solve kore debe."
 

def get_ai_text_reply(prompt, system_instruction="", image=None):
    sys_inst = system_instruction if system_instruction else GLOBAL_SYSTEM_INSTRUCTION
    
        # LAYER 1 & 2: RANDOMIZED MULTI-KEY GEMINI ROTATION
    import random
    shuffled_keys = list(GEMINI_KEYS)
    random.shuffle(shuffled_keys)
    
    for key in shuffled_keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            content_to_send = [prompt, image] if image else prompt
            
            # System Instruction pass kora holo jate NEXUS tar porichoy permanent mone rakhe
            model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=sys_inst)
            return model.generate_content(content_to_send).text
        except Exception as e_25:
            try:
                model = genai.GenerativeModel(model_name='gemini-1.5-pro', system_instruction=sys_inst)
                return model.generate_content(content_to_send).text
            except Exception as e_20:
                continue
        
    if image:
        return "Dukhhito bos, amar chobi dekhar server (Gemini) ekhon limit cross koreche. Groq chobi dekhte pare na."
        
    # LAYER 3: GROQ (Llama 3.3)
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}"}
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_inst}, {"role": "user", "content": prompt}]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        if 'choices' in res_json: return res_json['choices'][0]['message']['content']
        else: raise Exception("Groq Error")
    except:
        # LAYER 4: OPENAI
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "system", "content": sys_inst}, {"role": "user", "content": prompt}]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            res_json = response.json()
            if 'choices' in res_json: return res_json['choices'][0]['message']['content']
            else: return "Dukhhito bos, shob API key limit sesh hoye geche!"
        except:
            return "Dukhhito bos, amar shob AI server ekhon down ache!"

# ==================== FLASK ROUTES ====================

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '').strip()
    phone = request.json.get('phone', 'guest')
    if not user_msg: return jsonify({"error": "No message"}), 400
    
    session_key = f"{phone}_chat"
    last_reply = user_sessions.get(session_key, "")
    prompt = f"[Ager kothar context: {last_reply[-300:]}] \nUser ekhon bolche: {user_msg}" if last_reply else user_msg
    
    reply = get_ai_text_reply(prompt, GLOBAL_SYSTEM_INSTRUCTION)
    user_sessions[session_key] = reply
    return jsonify({"reply": reply})

@app.route('/api/coding', methods=['POST'])
def coding():
    code_input = request.form.get('code', '').strip()
    lang = request.form.get('language', 'Python')
    phone = request.form.get('phone', 'guest')
    session_key = f"{phone}_coding"
    
    img = None
    if 'image' in request.files:
        img = Image.open(request.files['image'].stream)
        
    sys_inst = f"Tumi ekjon expert AI Coding Teacher. Target language: {lang}. User er sathe friendly Banglay kotha bolo. Plain text-e step-by-step code bujhiye dao. Tumi bolbe 'Ami tomar AI Coding Teacher' ba 'Ami tomar NEXUS'."
    
    is_continue = "baki" in code_input.lower() or "tar por" in code_input.lower()
    
    if is_continue:
        last_reply = user_sessions.get(session_key, "")
        prompt = f"Ager bar tumi ei obdi bujhiechile: '{last_reply[-400:]}'. Ebar er thik por theke baki ta koptok bhalo kore bolo." if last_reply else "Notun kore shuru koro bos."
    elif img:
        prompt = f"Ei screenshot er error ba code ta dekhe amar somossa solve koro. My text: {code_input}"
    elif code_input:
        prompt = f"Analyze and explain this code/error: {code_input}"
    else:
        prompt = f"Ami {lang} programming ekdom prothom theke basic chapter 1 theke shikhte chai. Shuru koro bos."

    reply = get_ai_text_reply(prompt, sys_inst, img)
    user_sessions[session_key] = reply
    return jsonify({"reply": reply})

@app.route('/api/study', methods=['POST'])
def study():
    action = request.form.get('action')
    
    # Math markup block string injection
    no_latex = " Khub bhalo kore mone rakhbe, math ba onker jonno kono '$' sign, '\\frac', '\\sin', '\\sum' ba LaTeX code use korbe na. Ekdom sadharon plain text-e (jemon x/y, a^2+b^2) likhbe."
    
    if action == 'doubts': 
        prompt = f"Solve this doubt step-by-step in Bengali without any LaTeX or coding symbols: {request.form.get('question')}." + no_latex
    elif action == 'practice': 
        prompt = f"Give me some {request.form.get('difficulty')} level practice questions on the topic: {request.form.get('topic')}. Reply in Bengali." + no_latex
    else: 
        prompt = f"Give me Previous Year Questions (PYQ) for the exam: {request.form.get('exam')}. Reply in Bengali." + no_latex
        
    img_data = None
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        img_data = {'mime_type': file.content_type, 'data': file.read()}
    
    final_inst = GLOBAL_SYSTEM_INSTRUCTION + " " + no_latex
    ans = get_ai_text_reply(prompt, final_inst, img_data)
    return jsonify({"reply": ans})

@app.route('/api/info', methods=['POST'])
def info():
    if 'image' not in request.files: 
        return jsonify({"reply": "Kono chobi pawa jaini bos!"})
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"reply": "Chobir file ta khali, abar try koro!"})
        
    try:
        img_bytes = file.read()
        if not img_bytes:
            return jsonify({"reply": "Chobir data thikmoto read kora gelo na!"})
            
        image_data = {
            'mime_type': file.content_type if file.content_type else 'image/jpeg',
            'data': img_bytes
        }
    except Exception as e:
        return jsonify({"reply": f"File stream reading error: {e}"})
    
    # Encyclopedia deep target prompt analysis string
    smart_info_prompt = """
    Ei chobite ashol ki ache seta identify koro. 
    Shudhu chobir rong, bhalo lagche, ba background-er bornona debe na. 
    Chobir ashol bishoybostu (subject) sommondhe encyclopedia-r moto tothyo dao. 
    Jemon: Eta ki, er gurutto ki, er kaj ki, kothay pawa jay, ebong eti somporke kicho mojar ba ojana tothyo (unknown facts) Banglay bolo jeta sadharon manush jane na.
    """
    
    reply_text = "Dukhhito bos, image analyzer ekhon response korchena."
    for key in GEMINI_KEYS:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash') 
            response = model.generate_content([smart_info_prompt, image_data])
            reply_text = response.text
            break
        except:
            try:
                model = genai.GenerativeModel('gemini-2.0-flash') 
                response = model.generate_content([smart_info_prompt, image_data])
                reply_text = response.text
                break
            except:
                continue
    return jsonify({"reply": reply_text})

@app.route('/api/imagegen', methods=['POST'])
def imagegen():
    prompt = request.form.get('prompt')
    if 'image' in request.files:
        img_bytes = request.files['image'].read()
        image_base64 = base64.b64encode(img_bytes).decode('utf-8')
        API_URL = "https://api-inference.huggingface.co/models/timbrooks/instruct-pix2pix"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": image_base64, "parameters": {"prompt": prompt if prompt else "Make it aesthetic"}}
        
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                return jsonify({"image_url": f"data:image/jpeg;base64,{base64.b64encode(res.content).decode('utf-8')}"})
            else:
                return jsonify({"reply": "Face edit er server ekhon busy, ektu por try kor!"})
        except:
            return jsonify({"reply": "Network error! Internet connection check koro bos."})
    else:
        if not prompt: return jsonify({"reply": "Kono prompt deya hoyni!"})
        try:
            formatted_prompt = prompt.replace(" ", "%20")
            image_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=512&height=512&nologo=true"
            return jsonify({"image_url": image_url})
        except:
            return jsonify({"reply": "Chobi banate giye network error holo bos!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

