import json
import networkx as nx
import random
from pydantic import ValidationError

# Import Pydantic models
from data.models import BotIdentity, BotEdge, BotnetGraph

def generate_botnet_graph(num_bots: int) -> BotnetGraph:
    """Generates a Scale-Free network and assigns roles based on the topology."""
    
    print(f"[*] Generating Barabási-Albert network topology for {num_bots} nodes...")
    
    # Barabási-Albert model: each new node connects to 'm' existing nodes.
    # m=2 creates a network with a good density of hubs.
    m_edges = 2 if num_bots > 2 else 1
    G = nx.barabasi_albert_graph(n=num_bots, m=m_edges)
    
    # In NetworkX, edges are undirected by default in this model, 
    # so we convert it to a directed graph (DiGraph) to simulate "Followers"
    DG = nx.DiGraph()
    for u, v in G.edges():
        # Randomly decide who follows whom, or if they follow each other mutually
        if random.random() > 0.3:
            DG.add_edge(u, v)
        if random.random() > 0.3:
            DG.add_edge(v, u)

    export_nodes = []
    
    # Calculate popularity to assign roles
    # degree() returns the total number of connections for the node
    degrees = dict(DG.degree())
    max_degree = max(degrees.values()) if degrees else 1
    
    for node_id in DG.nodes():
        bot_name = f"bot_{node_id}"
        in_degree = DG.in_degree(node_id)
        out_degree = DG.out_degree(node_id)
        total_degree = degrees[node_id]
        
        # ROLE ASSIGNMENT LOGIC
        # If it's in the top tier of nodes with the most connections -> Content Creator
        if total_degree >= max_degree * 0.7:
            role = "content_creator"
        # If it follows many people but isn't followed as much -> Amplifier
        elif out_degree > in_degree * 2:
            role = "amplifier"
        # If it has a medium degree -> Debaters or Trolls
        elif total_degree >= max_degree * 0.3:
            role = random.choice(["debater", "troll"])
        # The rest, the "plebs" of the botnet -> Lurkers
        else:
            role = "lurker"
            
        identity = BotIdentity(
            bot_id=bot_name,
            role=role,
            followers=in_degree,
            following=out_degree
        )
        export_nodes.append(identity)

    # Prepare the edges (who is connected to whom)
    export_edges = [BotEdge(source=f"bot_{u}", target=f"bot_{v}") for u, v in DG.edges()]
    
    # Pass everything through our Pydantic validator
    validated_graph = BotnetGraph(
        total_nodes=num_bots,
        nodes=export_nodes,
        edges=export_edges
    )
    
    return validated_graph

# --- MODULE TEST ---
if __name__ == "__main__":
    # In a real case, we would read 'num_bots' from 'current_campaign.json'
    test_bots = 200
    
    try:
        graph = generate_botnet_graph(num_bots=test_bots)
        print(f"[+] Graph successfully generated with {graph.total_nodes} bots.")
        
        # Count how many of each role there are to see the distribution
        roles_count = {}
        for node in graph.nodes:
            roles_count[node.role] = roles_count.get(node.role, 0) + 1
            
        print("\nRole distribution:")
        for role, count in roles_count.items():
            print(f"  - {role}: {count}")
            
        # Export the graph for the Conversation Planner to use
        with open("botnet_graph.json", "w", encoding="utf-8") as f:
            f.write(graph.model_dump_json(indent=4))
            
        print("\n[*] Graph saved to 'botnet_graph.json'")
        
    except ValidationError as e:
        print("[!] Error structuring the graph data:")
        print(e)