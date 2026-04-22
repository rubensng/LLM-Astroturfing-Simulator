import json
import time
import subprocess
import sys

# Import all pipeline modules
import campaign_planner
import narrative_planner
import graph_generator
import conversation_planner
import behavior_scheduler
import mission_builder

def print_banner():
    print("""
    ██████╗  ██████╗ ████████╗███╗   ██╗███████╗████████╗
    ██╔══██╗██╔═══██╗╚══██╔══╝████╗  ██║██╔════╝╚══██╔══╝
    ██████╔╝██║   ██║   ██║   ██╔██╗ ██║█████╗     ██║   
    ██╔══██╗██║   ██║   ██║   ██║╚██╗██║██╔══╝     ██║   
    ██████╔╝╚██████╔╝   ██║   ██║ ╚████║███████╗   ██║   
    ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝   
          --- COMMAND & CONTROL ---
    """)

def main():
    print_banner()
    
    # --- 1. REQUIREMENT GATHERING ---
    print("\n[--- CAMPAIGN CONFIGURATION ---]")
    human_prompt = input("🎯 Objective (e.g., Discredit system X): ")
    hours = int(input("⏳ Duration (in hours, e.g., 24): "))
    bots = int(input("🤖 Number of bots to deploy (e.g., 200): "))
    
    print("\nCoordination levels: \n - 'low' (Undetectable, high noise) \n - 'medium' (Balanced) \n - 'high' (Massive, synchronized attack)")
    coordination_level = input("⚙️  Coordination level (low/medium/high): ").strip().lower()

    print("\n🚀 STARTING PIPELINE GENERATION...")
    time.sleep(1)

    # --- 2. PIPELINE GENERATION ---
    print("\n[1/6] Planning Strategy (AI)...")
    plan = campaign_planner.generate_campaign_plan(human_prompt, hours, bots, coordination_level)
    with open("current_campaign.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=4, ensure_ascii=False)

    print("[2/6] Generating Narrative Timeline...")
    timeline = narrative_planner.generate_narrative_timeline("current_campaign.json")
    with open("narrative_timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=4, ensure_ascii=False)

    print("[3/6] Building Network Topology (Barabási-Albert)...")
    graph = graph_generator.generate_botnet_graph(bots)
    with open("botnet_graph.json", "w", encoding="utf-8") as f:
        f.write(graph.model_dump_json(indent=4))

    print("[4/6] Orchestrating Conversational Threads...")
    campaign, graph_dict = conversation_planner.load_data()
    
    # Dynamically calculate how many threads to create. E.g., 1.5 threads per bot
    num_threads = int(bots * 1.5) 
    planned_threads = []
    for _ in range(num_threads):
        thread = conversation_planner.plan_thread(campaign, graph_dict)
        planned_threads.append(thread.model_dump())
    
    with open("planned_threads.json", "w", encoding="utf-8") as f:
        json.dump(planned_threads, f, indent=4, ensure_ascii=False)

    print("[5/6] Scheduling Behaviors (Injecting temporal entropy)...")
    campaign_data, timeline_data, threads_data = behavior_scheduler.load_data()
    missions = behavior_scheduler.schedule_missions(campaign_data, timeline_data, threads_data)
    with open("scheduled_missions.json", "w", encoding="utf-8") as f:
        json.dump(missions, f, indent=4, ensure_ascii=False)

    print(f"\n✅ PIPELINE GENERATED: {len(missions)} missions ready for execution.")

    # --- 3. INFRASTRUCTURE DEPLOYMENT (Microservices) ---
    print("\n[--- INFRASTRUCTURE DEPLOYMENT ---]")
    print("[*] Spinning up Identities Database (FastAPI)...")
    
    # Subprocess starts FastAPI as an independent process (Daemon)
    # sys.executable ensures it uses the current Python virtual environment
    db_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "gestor_identidades:app", "--port", "8000"],
        stdout=subprocess.DEVNULL, # Hide the log to keep the terminal clean
        stderr=subprocess.DEVNULL
    )
    time.sleep(3) # Give FastAPI 3 seconds to spin up
    print("[+] Identities API Operational at http://localhost:8000")

    print("\n⚠️  ATTENTION BEFORE FIRING:")
    print(" 1. Ensure RabbitMQ is running in Docker.")
    print(" 2. Ensure you have Ollama running locally.")
    print(" 3. Open ANOTHER terminal and run your Worker: python motor_cognitivo.py")
    
    input("\n🎯 Press ENTER when you are ready to inject the campaign into RabbitMQ...")

    # --- 4. EXECUTION (Dispatch) ---
    print("\n[6/6] STARTING DISPATCHER (Sending payloads to the queue)...")
    try:
        mission_builder.dispatch_missions("scheduled_missions.json")
    except KeyboardInterrupt:
        print("\n[!] Operation aborted by the user.")
    finally:
        # Cleanup: When the attack finishes (or is canceled), we kill the FastAPI process
        print("\n[*] Shutting down infrastructure...")
        db_process.terminate() 
        print("[+] Identities API disconnected.")
        print("=== OPERATION FINISHED ===")

if __name__ == "__main__":
    main()