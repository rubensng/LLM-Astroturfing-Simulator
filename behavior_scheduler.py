import json
import numpy as np
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import List

from data.models import ScheduledMission

def load_data():
    with open("current_campaign.json", "r", encoding="utf-8") as f:
        campaign = json.load(f)
    with open("narrative_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    with open("planned_threads.json", "r", encoding="utf-8") as f:
        threads = json.load(f)
    return campaign, timeline, threads

def apply_human_noise(timestamp, coord_level): #(timestamp: float, coord_level: str) -> tuple[float, bool]
    """
    Injects entropy (anomalous delays and probability of failures) based on the coordination level.
    Returns the new timestamp and a boolean flag indicating if the LLM should inject errors.
    """
    noise_probability = {"low": 0.20, "medium": 0.10, "high": 0.02}[coord_level]
    
    inject_noise = random.random() < noise_probability
    
    # If there is noise, we simulate that the human got "distracted" before posting (e.g., went to make coffee)
    if random.random() < (noise_probability / 2):
        extra_delay_seconds = random.randint(300, 3600) # From 5 minutes to 1 hour of delay
        timestamp += extra_delay_seconds
        
    return timestamp, inject_noise

def schedule_missions(campaign: dict, timeline: dict, threads: list) -> List[dict]:
    coord_level = campaign.get("coordination_level", "medium")
    actual_start_time = datetime.now()
    
    scheduled_missions = []
    
    # 1. Distribute the threads across the campaign phases
    phases = timeline["timeline"]
    
    print(f"[*] Scheduling {len(threads)} conversational threads (Coordination: {coord_level})...")
    
    for idx, thread in enumerate(threads):
        # Select a random phase based on probabilities (e.g., more threads in Conversation)
        assigned_phase = random.choices(
            phases, 
            weights=[f["end_hour"] - f["start_hour"] for f in phases],
            k=1
        )[0]
        
        # Calculate exactly when the first tweet of this thread starts within its phase
        phase_start_hours = assigned_phase["start_hour"]
        phase_end_hours = assigned_phase["end_hour"]
        start_offset = random.uniform(phase_start_hours, phase_end_hours)
        
        thread_base_timestamp = (actual_start_time + timedelta(hours=start_offset)).timestamp()
        
        # 2. Schedule messages within the thread using Log-Normal distribution
        # Fast reaction mean (e.g., 2-5 minutes), but with variance for the long tail
        mu = 4.0    # Underlying parameter of the logarithmic mean
        sigma = 1.0 # Variance (higher sigma = longer inactivity tails)
        
        if coord_level == "high":
            sigma = 0.3 # Very clustered, almost immediate responses
        elif coord_level == "low":
            sigma = 1.5 # Very dispersed
            
        current_timestamp = thread_base_timestamp
        
        for msg in thread["messages"]:
            if msg["step_index"] == 0:
                # The creator posts their original tweet at the base timestamp
                final_ts = current_timestamp
            else:
                # Followers respond with a log-normal delay simulating virality
                delay_seconds = np.random.lognormal(mean=mu, sigma=sigma) * 60 
                current_timestamp += delay_seconds
                final_ts = current_timestamp
            
            # 3. Apply "Human Noise" (Jitter and errors)
            final_ts, noise_flag = apply_human_noise(final_ts, coord_level)
            
            mission = ScheduledMission(
                mission_id=f"msn_{uuid.uuid4().hex[:8]}",
                bot_id=msg["bot_id"],
                action=msg["action"],
                stance=msg["stance"],
                assigned_keywords=msg["assigned_keywords"],
                target_thread_id=thread["thread_id"],
                reply_to_step=msg["reply_to_step"],
                scheduled_timestamp=final_ts,
                inject_noise=noise_flag,
                scheduled_time_str=datetime.fromtimestamp(final_ts).strftime('%Y-%m-%d %H:%M:%S')
            )
            
            scheduled_missions.append(mission.model_dump())
            
    # Sort all missions chronologically for the orchestrator
    scheduled_missions.sort(key=lambda x: x["scheduled_timestamp"])
    return scheduled_missions

# --- MODULE TEST ---
if __name__ == "__main__":
    try:
        campaign, timeline, threads = load_data()
        
        missions = schedule_missions(campaign, timeline, threads)
        
        print(f"\n[+] {len(missions)} individual missions have been scheduled.")
        print("[+] Showing the first 5 missions chronologically:\n")
        
        for m in missions[:5]:
            noise_str = "⚠️ (WITH NOISE/ERRORS)" if m["inject_noise"] else ""
            print(f"[{m['scheduled_time_str']}] {m['bot_id']} -> {m['action'].upper()} (Thread: {m['target_thread_id']}) {noise_str}")
            
        with open("scheduled_missions.json", "w", encoding="utf-8") as f:
            json.dump(missions, f, indent=4, ensure_ascii=False)
            
        print("\n[*] Mission plan finalized and saved to 'scheduled_missions.json'")
        
    except FileNotFoundError:
        print("[!] Error: Missing previous files. Run the preceding modules.")