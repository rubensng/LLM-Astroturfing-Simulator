import json
import random
import uuid
from typing import List

from data.models import PlannedMessage, PlannedThread

def load_data():
    with open("current_campaign.json", "r", encoding="utf-8") as f:
        campaign = json.load(f)
    with open("botnet_graph.json", "r", encoding="utf-8") as f:
        graph = json.load(f)
    return campaign, graph

def get_followers(bot_id: str, edges: List[dict]) -> List[str]:
    """Searches the graph to find who follows the specified bot."""
    # If edge = {"source": "bot_A", "target": "bot_B"}, it means A follows B
    followers = [edge["source"] for edge in edges if edge["target"] == bot_id]
    return followers

def plan_thread(campaign: dict, graph: dict) -> PlannedThread:
    """Creates the structure of a realistic conversation."""
    
    nodes = {node["bot_id"]: node for node in graph["nodes"]}
    edges = graph["edges"]
    
    # 1. Select the Initiator (Ideally a Content Creator)
    creators = [nid for nid, data in nodes.items() if data["role"] == "content_creator"]
    initiator_id = random.choice(creators) if creators else random.choice(list(nodes.keys()))
    
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    narrative = random.choice(campaign["secondary_narratives"] + [campaign["main_narrative"]])
    
    messages = []
    
    # --- STEP 0: Initial Tweet ---
    messages.append(PlannedMessage(
        step_index=0,
        bot_id=initiator_id,
        action="tweet",
        stance="support",
        reply_to_step=None,
        assigned_keywords=random.sample(campaign["hashtags"], k=min(2, len(campaign["hashtags"])))
    ))
    
    # --- STEP 1 to N: Cascading Interactions ---
    initiator_followers = get_followers(initiator_id, edges)
    
    # Simulate that between 2 and 5 bots decide to interact with this thread
    num_interactions = random.randint(2, 5)
    available_participants = random.sample(initiator_followers, k=min(num_interactions, len(initiator_followers)))
    
    current_step = 1
    last_reply_index = 0 # To know who to reply to (creating depth in the thread)
    
    for participant_id in available_participants:
        role = nodes[participant_id]["role"]
        
        # Assign action and stance based on topological ROLE
        if role == "amplifier":
            action = random.choice(["retweet", "reply", "like"])
            stance = "support"
            target_step = 0 # Amplifiers usually interact with the original post
        elif role in ["debater", "troll"]:
            action = "reply"
            stance = "oppose" # Introduce Polarization
            target_step = last_reply_index # They reply to the last speaker to create discussion
        else: # lurker
            action = random.choice(["like", "reply"])
            stance = "neutral"
            target_step = 0
            
        # Narrative coordination: Give different keywords to each one
        keywords = random.sample(campaign["hashtags"], k=1) if action == "reply" else []
        
        message = PlannedMessage(
            step_index=current_step,
            bot_id=participant_id,
            action=action,
            stance=stance,
            reply_to_step=target_step,
            assigned_keywords=keywords
        )
        messages.append(message)
        
        if action == "reply":
            last_reply_index = current_step
            
        current_step += 1

    return PlannedThread(
        thread_id=thread_id,
        narrative_focus=narrative,
        messages=messages
    )

# --- MODULE TEST ---
if __name__ == "__main__":
    try:
        campaign_data, graph_data = load_data()
        
        print("[*] Planning conversational threads based on topology...")
        
        # # A dynamic calculation: 2 threads for each bot in the army
        # total_threads = campaign_data["target_bot_count"] * 2 
        # for _ in range(total_threads):
        #     thread = planificar_hilo(campaign_data, graph_data)

        # Generate 3 test threads
        planned_threads = []
        for _ in range(3):
            thread = plan_thread(campaign_data, graph_data)
            planned_threads.append(thread.model_dump())
            
        # Show one on screen to see the structure
        print("\n[+] --- STRUCTURED THREAD EXAMPLE ---")
        print(json.dumps(planned_threads[0], indent=4, ensure_ascii=False))
        
        # Save for the next module
        with open("planned_threads.json", "w", encoding="utf-8") as f:
            json.dump(planned_threads, f, indent=4, ensure_ascii=False)
            
        print("\n[*] Threads saved to 'planned_threads.json'")
        
    except FileNotFoundError:
        print("[!] Error: Missing previous files. Run the Campaign Planner and Graph Generator first.")