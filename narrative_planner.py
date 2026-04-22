import json
import os

# --- THEORETICAL PHASE DISTRIBUTION ---
# Percentage of total time allocated to each phase
PHASE_DURATION_PCT = {
    "Seeding": 0.10,
    "Amplification": 0.20,
    "Conversation": 0.30,
    "Polarization": 0.20,
    "Saturation": 0.20
}

# Base probabilities for (original_tweet, retweet, reply, like)
PHASE_ACTIONS = {
    "Seeding":       {"tweet": 0.80, "retweet": 0.05, "reply": 0.05, "like": 0.10},
    "Amplification": {"tweet": 0.05, "retweet": 0.60, "reply": 0.05, "like": 0.30},
    "Conversation":  {"tweet": 0.10, "retweet": 0.20, "reply": 0.60, "like": 0.10},
    "Polarization":  {"tweet": 0.15, "retweet": 0.15, "reply": 0.60, "like": 0.10}, # High level of replies, mostly conflictive
    "Saturation":    {"tweet": 0.10, "retweet": 0.40, "reply": 0.40, "like": 0.10}
}

def generate_narrative_timeline(campaign_file="current_campaign.json"):
    """Reads the global strategy and generates the campaign timeline."""
    
    if not os.path.exists(campaign_file):
        print(f"[!] Error: {campaign_file} not found. Run the Campaign Planner first.")
        return None
        
    with open(campaign_file, "r", encoding="utf-8") as f:
        strategic_plan = json.load(f)
        
    total_duration = strategic_plan.get("duration_hours", 24)
    coord_level = strategic_plan.get("coordination_level", "medium")
    
    timeline = []
    current_hour = 0.0
    
    print(f"[*] Designing timeline for {total_duration}-hour campaign (Coordination: {coord_level})...")
    
    for phase_name, time_pct in PHASE_DURATION_PCT.items():
        phase_duration = total_duration * time_pct
        
        # Dynamic adjustment based on coordination level
        # If coordination is high, the saturation phase is more aggressive
        probabilities = PHASE_ACTIONS[phase_name].copy()
        if coord_level == "high" and phase_name == "Saturation":
            probabilities["retweet"] = 0.60
            probabilities["reply"] = 0.20
            
        phase_config = {
            "phase_name": phase_name,
            "start_hour": round(current_hour, 2),
            "end_hour": round(current_hour + phase_duration, 2),
            "action_probabilities": probabilities
        }
        
        timeline.append(phase_config)
        current_hour += phase_duration

    narrative_plan = {
        "campaign_goal": strategic_plan.get("goal"),
        "total_duration_hours": total_duration,
        "coordination_level": coord_level,
        "timeline": timeline
    }
    
    return narrative_plan

# --- MODULE TEST ---
if __name__ == "__main__":
    narrative_timeline = generate_narrative_timeline()
    
    if narrative_timeline:
        print("\n[+] --- NARRATIVE TIMELINE GENERATED ---")
        print(json.dumps(narrative_timeline, indent=4, ensure_ascii=False))
        
        # Save the temporal plan for the upcoming modules
        with open("narrative_timeline.json", "w", encoding="utf-8") as f:
            json.dump(narrative_timeline, f, indent=4, ensure_ascii=False)
        print("\n[*] Timeline saved to 'narrative_timeline.json'")