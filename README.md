# Social Media Botnet & Information Operations Simulator

> [!WARNING]
> **ACADEMIC & SECURITY RESEARCH DISCLAIMER**
> This repository is a Proof of Concept (PoC) designed strictly for academic research, threat intelligence, and cybersecurity education. Its purpose is to simulate and study the mechanics of computational propaganda, botnet topologies, and LLM-driven narrative manipulation in an **isolated, local environment**. 
> 
> **This project does NOT include capabilities to interact with, scrape, or post to real social media platforms.** It operates entirely within a closed-loop local database and visualizer. 

## 📖 Overview
This PoC is an advanced Command and Control (C2) framework that simulates a highly coordinated botnet executing an information operation. It utilizes Graph Theory (Barabási-Albert scale-free networks) to assign roles to bots, LLMs to generate persona-driven interactions, and temporal entropy to mimic human behavior.

The operation is visualized in real-time through a local Streamlit-based mock social media feed.

## 🏗️ System Architecture
The framework is composed of several microservices and scripts working together in a pipeline:

* **`c2_orchestrator.py`**: The main entry point. Gathers requirements and generates the campaign pipeline.
* **`campaign_planner.py` & `narrative_planner.py`**: Uses an LLM to build the strategic narrative and temporal phases of the attack.
* **`graph_generator.py` & `graph_visualizer.py`**: Builds the network topology and assigns structural roles (Content Creators, Amplifiers, Trolls, Lurkers).
* **`conversation_planner.py` & `behavior_scheduler.py`**: Designs conversational threads and injects "human noise" (delays, typos) into the execution schedule.
* **`identities_manager.py`**: A FastAPI backend acting as the memory and persona database for the bots.
* **`mission_builder.py`**: The dispatcher that sends scheduled payloads to RabbitMQ.
* **`cognitive_engine.py`**: The LLM Worker. Consumes missions from RabbitMQ, generates context-aware text via Ollama, and writes to the local simulated database.
* **`app_social_media.py`**: A Streamlit dashboard that acts as the target social network to monitor the attack in real-time.

## ⚙️ Prerequisites
To run this simulation locally, you need:
1. **Python 3.9+**
2. **Docker** (to run the RabbitMQ message broker)
3. **Ollama** installed locally (with a model like `deepseek-r1` or `llama3` pulled).

### Python Dependencies
Create a virtual environment and install the required packages. You can typically do this with:
```bash
pip install fastapi uvicorn pydantic requests pika networkx pyvis streamlit pandas numpy
```
