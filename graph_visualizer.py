import json
from pyvis.network import Network

def visualize_graph(json_file="botnet_graph.json"):
    print("[*] Loading graph data...")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[!] {json_file} not found. Generate the graph first.")
        return

    # Configure the canvas: dark background, full screen, and directional arrows
    net = Network(height="100vh", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
    
    # Color palette for the roles
    colors = {
        "content_creator": "#FF3366", # Bright red (High visibility)
        "amplifier": "#33CCFF",       # Light blue
        "debater": "#FF9933",         # Orange
        "troll": "#B84DFF",           # Purple
        "lurker": "#595959"           # Dark gray (they fly under the radar)
    }

    print("[*] Building nodes and edges...")
    
    # Add the nodes
    for node in data["nodes"]:
        bot_id = node["bot_id"]
        role = node["role"]
        
        # Node size will depend on how many followers it has (larger hubs)
        base_size = 15
        calculated_size = base_size + (node["followers"] * 3)
        
        # The tooltip that will appear when hovering over the node
        hover_info = f"Bot: {bot_id}\nRole: {role.upper()}\nFollowers: {node['followers']}\nFollowing: {node['following']}"
        
        net.add_node(
            bot_id, 
            label=bot_id, 
            title=hover_info, 
            color=colors.get(role, "#FFFFFF"), 
            size=calculated_size
        )

    # Add the connections (who follows whom)
    for edge in data["edges"]:
        # Subtle arrows to avoid cluttering the screen
        net.add_edge(edge["source"], edge["target"], color="#404040", width=1)

    # Configure physics so clusters separate naturally (Force-Atlas model)
    net.repulsion(node_distance=200, central_gravity=0.1, spring_length=150, spring_strength=0.05, damping=0.09)

    # Generate the HTML
    output_name = "botnet_map.html"
    net.show(output_name, notebook=False)
    print(f"[+] Done! Open the file '{output_name}' in your web browser.")

if __name__ == "__main__":
    visualize_graph()