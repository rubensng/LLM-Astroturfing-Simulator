import json
import pika
import requests
import random
from typing import List
import sqlite3
from datetime import datetime
from pydantic import ValidationError
import uuid
import subprocess
import os

from data.models import FinalMissionPayload

# --- MICROSERVICES CONFIGURATION ---
RABBITMQ_HOST = 'localhost'
COLA_MISIONES = 'misiones_botnet'
GESTOR_IDENTIDADES_URL = "http://localhost:8000/bot"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_LLM = "deepseek-r1" 

# --- INITIALIZE SOCIAL NETWORK DB ---
def init_social_network_db():
    conn = sqlite3.connect("red_social.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            thread_id TEXT,
            bot_id TEXT,
            action TEXT,
            content TEXT,
            created_at DATETIME,
            reply_to_step INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_post(thread_id, bot_id, action, content, reply_to_step):
    """Saves the action in the target social network database"""
    conn = sqlite3.connect("red_social.db")
    cursor = conn.cursor()
    post_id = f"post_{uuid.uuid4().hex[:8]}"
    cursor.execute('INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (post_id, thread_id, bot_id, action, content, datetime.now(), reply_to_step))
    conn.commit()
    conn.close()

# --- HUMAN ERROR GENERATOR ---
def apply_typos(texto: str) -> str:
    """Simulates common typographical errors on QWERTY keyboards"""
    adjacent_keys = {
        'a': ['s', 'q', 'z'], 's': ['a', 'd', 'w'], 'e': ['w', 'r', 's'],
        'o': ['i', 'p', 'l'], 'i': ['u', 'o', 'k'], 'l': ['k', 'o', 'p'],
        'm': ['n', 'k', 'j'], 'n': ['b', 'm', 'h'], 'r': ['e', 't', 'f']
    }
    
    text_list = list(texto)
    num_errors = max(1, len(texto) // 50) # Approx 1 error per 50 characters
    
    for _ in range(num_errors):
        idx = random.randint(0, len(text_list) - 1)
        char = text_list[idx].lower()
        
        error_type = random.choice(["swap", "drop", "adjacent"])
        
        if error_type == "adjacent" and char in adjacent_keys:
            text_list[idx] = random.choice(adjacent_keys[char])
        elif error_type == "drop":
            text_list.pop(idx)
        elif error_type == "swap" and idx < len(text_list) - 1:
            text_list[idx], text_list[idx+1] = text_list[idx+1], text_list[idx]
            
    return "".join(text_list)

# --- LLM CONNECTION ---
def generate_text_llm(system_prompt: str, action: str, stance: str, keywords: List[str], inject_noise: bool) -> str:
    """Assembles the dynamic prompt and calls Ollama"""
    
    # Adapt instructions based on whether it's an original tweet or a reply
    action_instruction = "Write an original tweet introducing a topic." if action == "tweet" else "Write a short reply to the conversation."
    
    # Add an extra warning to the LLM if we want noise (in addition to our Python function)
    noise_instruction = "Write very casually, without capitalizing the first letter, as if typing quickly on a phone." if inject_noise else "Write correctly but naturally."
    
    full_prompt = f"""
    IDENTITY INSTRUCTIONS: {system_prompt}
    
    YOUR CURRENT MISSION:
    - Action: {action_instruction}
    - Stance: {stance.upper()} (support, oppose, escalate, neutral)
    - Keywords to include (if possible): {', '.join(keywords)}
    - Style: {noise_instruction}
    
    STRICT RULE: Write ONLY the response. Do not use quotes. Be very human.
    """
    
    payload = {
        "model": MODELO_LLM,
        "prompt": full_prompt,
        "stream": False 
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        generated_text = response.json().get("response", "").strip()
        
        # Apply the typographical error filter if the mission requires it
        if inject_noise and generated_text:
            generated_text = apply_typos(generated_text)
            
        return generated_text
    except Exception as e:
        print(f"[!] Ollama Error: {e}")
        return None

# --- RABBITMQ CONSUMER ---
def post_on_social_network(texto_generado, bot_id):
    """
    Calls the Node.js script (tweet.js) using a subprocess,
    passing the generated text via environment variables.
    """
    print(f"[*] Invoking Node.js (Playwright) for bot {bot_id}...")
    
    # Copy current system environment variables
    env_vars = os.environ.copy()
    
    # 1. Define a unique session filename for this bot
    session_name = f"session_{bot_id}.json"
    print(f"[*] Session name: {session_name}")
    
    # 2. Pass it to the Node script via a new environment variable
    env_vars["TWEET_TEXT"] = texto_generado
    env_vars["SESSION_FILE"] = session_name 
    env_vars["HEADLESS"] = "true"
    
    try:
        # Execute the Node.js command
        # Note: Assumes tweet.js is in the same folder from where you run motor_cognitivo.py
        # If you prefer to call node directly, change ["npm", "run", "tweet"] to ["node", "tweet.js"]
        result = subprocess.run(
            ["node", "tweet.js"], 
            env=env_vars,
            capture_output=True, # Capture what the JS prints to the console
            text=True,
            shell=True
        )
        
        # Verify if the JS script finished correctly
        if result.returncode == 0:
            print(f"✅ [NODE.JS] Tweet successfully published to the real network.")
        else:
            print(f"❌ [NODE.JS ERROR] Playwright failed:\n{result.stderr}")
            
    except Exception as e:
        print(f"[!] Critical error attempting to launch Node.js: {e}")

def process_mission(ch, method, properties, body):
    """Callback that processes the validated payload"""
    
    # 1. Contract Validation (Pydantic)
    try:
        mission = FinalMissionPayload.model_validate_json(body)
    except ValidationError as e:
        print(f"[!] Message discarded due to invalid format: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag) # Remove from queue because it's garbage
        return

    print(f"\n[*] Mission {mission.mission_id} received -> BOT: {mission.bot_id} | ACTION: {mission.action.upper()}")

    # 2. Fetch Profile (FastAPI)
    try:
        res = requests.get(f"{GESTOR_IDENTIDADES_URL}/{mission.bot_id}")
        res.raise_for_status()
        profile = res.json()
        system_prompt = profile['system_prompt']
        bot_name = profile['nombre']
    except Exception as e:
        print(f"[!] Error fetching profile for {mission.bot_id}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return

    # 3. Action Routing (Likes and RTs don't need text)
    if mission.action in ["like", "retweet"]:
        print(f"[+] {bot_name} executed a {mission.action.upper()} on thread {mission.context_thread_id}")
        # Save to the social network DB without content
        save_post(mission.context_thread_id, mission.bot_id, mission.action, "", mission.context_replying_to_step)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
        
    # 4. Text Generation for Tweets and Replies
    print(f"[*] Generating content as '{bot_name}' (Noise: {mission.inject_noise})...")
    
    generated_text = generate_text_llm(
        system_prompt=system_prompt,
        action=mission.action,
        stance=mission.stance,
        keywords=mission.keywords,
        inject_noise=mission.inject_noise
    )
    
    if generated_text:
        noise_tag = "⚠️ [WITH TYPOS]" if mission.inject_noise else "✅ [CLEAN]"
        print(f"[+] FINAL TEXT ({bot_name}) {noise_tag}:\n    {generated_text}")
        
        # 1. (OPTIONAL) Save it to your local DB so it shows up in your Streamlit
        # guardar_post(mission.context_thread_id, mission.bot_id, mission.action, generated_text, mission.context_replying_to_step)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        # Ollama failed, return to queue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def iniciar_worker():
    # Call the initialization function on startup
    init_social_network_db()

    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=COLA_MISIONES)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=COLA_MISIONES, on_message_callback=process_mission)
    
    print("[*] Advanced LLM Worker Online. Waiting for missions...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Worker...")
        connection.close()

if __name__ == '__main__':
    iniciar_worker()