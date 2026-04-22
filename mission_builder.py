import json
import time
import pika
from datetime import datetime

from data.models import FinalMissionPayload

# --- NETWORK AND SIMULATION CONFIGURATION ---
RABBITMQ_HOST = 'localhost'
COLA_MISIONES = 'misiones_botnet'

# TIME WARP: Speeds up time for local testing.
# 1 = Real time (1 second = 1 second). 
# 60 = 1 hour of simulation happens in 1 real minute.
SPEED_MULTIPLIER = 60.0 

def connect_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=COLA_MISIONES)
        return connection, channel
    except Exception as e:
        print(f"[!] Error connecting to RabbitMQ: {e}")
        return None, None

def dispatch_missions(missions_file="scheduled_missions.json"):
    try:
        with open(missions_file, "r", encoding="utf-8") as f:
            raw_missions = json.load(f)
    except FileNotFoundError:
        print(f"[!] File {missions_file} not found.")
        return

    connection, channel = connect_rabbitmq()
    if not channel:
        return

    print(f"[*] Starting Mission Builder (Dispatcher). Time multiplier: {SPEED_MULTIPLIER}x")
    print(f"[*] There are {len(raw_missions)} missions in the queue.")

    # Capture the moment the script starts to use it as the "Hour 0" of the simulation
    sim_zero_hour = raw_missions[0]["scheduled_timestamp"]
    real_zero_hour = time.time()

    for raw_m in raw_missions:
        # Calculate how long we need to wait in accelerated time
        simulated_target_time = raw_m["scheduled_timestamp"]
        seconds_diff = simulated_target_time - sim_zero_hour
        
        real_wait_time = seconds_diff / SPEED_MULTIPLIER
        real_dispatch_moment = real_zero_hour + real_wait_time
        
        time_to_sleep = real_dispatch_moment - time.time()
        
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

        # 1. Enrich the mission context (Conversational Memory)
        payload = FinalMissionPayload(
            mission_id=raw_m["mission_id"],
            bot_id=raw_m["bot_id"],
            action=raw_m["action"],
            stance=raw_m["stance"],
            context_thread_id=raw_m["target_thread_id"],
            context_replying_to_step=raw_m.get("reply_to_step"),
            keywords=raw_m["assigned_keywords"],
            inject_noise=raw_m["inject_noise"]
        )

        # 2. Publish to RabbitMQ
        json_payload = payload.model_dump_json()
        
        channel.basic_publish(
            exchange='',
            routing_key=COLA_MISIONES,
            body=json_payload
        )
        
        noise_str = "[NOISE ACTIVATED] " if payload.inject_noise else ""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] -> Sent to queue: {noise_str}{payload.action.upper()} from bot {payload.bot_id} (Thread: {payload.context_thread_id})")

    connection.close()
    print("[*] Campaign fully dispatched.")

# --- EXECUTION ---
if __name__ == "__main__":
    dispatch_missions()