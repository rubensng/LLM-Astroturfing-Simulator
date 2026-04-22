from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import os

app = FastAPI(title="Botnet Identities Manager (Persona DB)")
DB_FILE = "botnet_personas.db"

# --- DATA MODELS (PYDANTIC) ---
class NuevaInteraccion(BaseModel):
    action: str
    target_post: str
    generated_text: str

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it does not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            bot_id TEXT PRIMARY KEY,
            nombre TEXT,
            system_prompt TEXT,
            historial TEXT
        )
    ''')
    
    # Insert test bots if the table is empty
    cursor.execute('SELECT COUNT(*) FROM bots')
    if cursor.fetchone()[0] == 0:
        test_bots = [
            ("bot_0", "Dale", "You are Dale, 22 years old, computer science student. You are skeptical, use technical jargon, and often correct others. Short answers.", "[]"),
            ("bot_1", "Diane", "You are Diane, 30 years old, optimistic entrepreneur. You love innovation and always use emojis. Friendly and inspiring tone.", "[]"),
        ]
        cursor.executemany('INSERT INTO bots VALUES (?, ?, ?, ?)', test_bots)
        conn.commit()
        print("[*] Database initialized with test bots.")
        
    conn.close()

# --- API ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/bot/{bot_id}")
def obtener_perfil(bot_id: str):
    """Returns the personality and history of a bot."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, system_prompt, historial FROM bots WHERE bot_id = ?', (bot_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Bot not found in the DB")
        
    return {
        "bot_id": bot_id,
        "nombre": row[0],
        "system_prompt": row[1],
        "historial": json.loads(row[2])
    }

@app.post("/bot/{bot_id}/historial")
def actualizar_historial(bot_id: str, interaccion: NuevaInteraccion):
    """Adds a new interaction to the bot's memory."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Retrieve current history
    cursor.execute('SELECT historial FROM bots WHERE bot_id = ?', (bot_id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Bot not found in the DB")
        
    current_history = json.loads(row[0])
    
    # Add new interaction and keep only the last 5 (short-term memory)
    current_history.append(interaccion.model_dump()) 
    current_history = current_history[-5:] 
    
    # Save back to DB
    cursor.execute('UPDATE bots SET historial = ? WHERE bot_id = ?', (json.dumps(current_history), bot_id))
    conn.commit()
    conn.close()
    
    return {"status": "History updated", "retained_memory": len(current_history)}