import json
import requests
from pydantic import ValidationError

# Local LLM URL (Ollama)
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM = "deepseek-r1"

def generate_campaign_plan(human_prompt: str, hours: int, bots: int, coordination_level: str) -> dict:
    """
    Takes a basic idea and uses the LLM to expand it into a comprehensive strategy.
    """
    
    system_prompt = f"""
    You are an expert strategist in social media campaigns and information operations.
    Your task is to take the user's objective and expand it into a complex narrative.
    
    You MUST respond ONLY with a valid JSON object that follows this exact structure, with no additional text before or after:
    {{
      "goal": "summarized objective",
      "main_narrative": "the central and strongest argument",
      "secondary_narratives": ["technical argument", "emotional argument", "economic argument"],
      "hashtags": ["#MainHashtag", "#Variation1", "#Synonym2", "#Abbreviation3"],
      "duration_hours": {hours},
      "target_bot_count": {bots},
      "coordination_level": "{coordination_level}"
    }}
    """
    
    payload = {
        "model": LLM,
        "prompt": f"CLIENT OBJECTIVE: {human_prompt}",
        "system": system_prompt,
        "stream": False,
        "format": "json" # Ollama supports forcing JSON output
    }
    
    print("[*] Thinking about the campaign strategy...")
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    
    text_result = response.json().get("response", "").strip()
    
    try:
        # Validate that it is a correct JSON
        plan_json = json.loads(text_result)
        return plan_json
    except json.JSONDecodeError:
        print("[!] Error: The LLM did not return a valid JSON.")
        print("Raw response:", text_result)
        return None

# --- MODULE TEST ---
if __name__ == "__main__":
    initial_idea = "Discredit the new security update for the 'X-OS' operating system, claiming it violates user privacy."
    
    plan = generate_campaign_plan(
        human_prompt=initial_idea,
        hours=24,
        bots=150,
        coordination_level="medium"
    )
    
    if plan:
        print("\n[+] --- PLANNED CAMPAIGN ---")
        print(json.dumps(plan, indent=4, ensure_ascii=False))
        
        # Here we save the JSON to a file so it can be read by the Narrative Planner
        with open("current_campaign.json", "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4, ensure_ascii=False)
        print("[*] Plan saved to 'current_campaign.json'")