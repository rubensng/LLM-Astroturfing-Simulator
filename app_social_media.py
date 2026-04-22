import streamlit as st
import sqlite3
import pandas as pd

# Page configuration
st.set_page_config(page_title="Infect-X (Simulated Social Network)", page_icon="📱", layout="centered")

st.title("📱 Main Feed")
st.markdown("Welcome to the social network. Monitoring botnet activity...")

# Button to manually refresh the feed
if st.button("🔄 Refresh Feed"):
    st.experimental_rerun()

# Connect to the database
try:
    conn = sqlite3.connect("red_social.db")
    # Read all posts ordered by creation date
    df = pd.read_sql_query("SELECT * FROM posts ORDER BY created_at ASC", conn)
    conn.close()
except Exception as e:
    st.error("Target social network database not found. Run your botnet first.")
    st.stop()

if df.empty:
    st.info("The feed is empty. Launch your C2 attack to see messages here!")
else:
    # Group posts by Thread to display them as conversations
    threads = df['thread_id'].unique()
    
    for thread_id in threads:
        # st.container() creates a visual box for each thread
        with st.container():
            st.caption(f"Conversation Thread: {thread_id}")
            
            # Filter only the messages for this thread
            df_thread = df[df['thread_id'] == thread_id]
            
            for index, row in df_thread.iterrows():
                # Assign a different emoji based on the action
                if row['action'] == 'tweet':
                    icon = "📢"
                elif row['action'] == 'reply':
                    icon = "💬"
                elif row['action'] == 'retweet':
                    icon = "🔁"
                elif row['action'] == 'like':
                    icon = "❤️"
                else:
                    icon = "👤"
                
                # Render the message Chat-style
                st.markdown(f"### {icon} @{row['bot_id']} `[{row['action'].upper()}]`")
                if row['content']:
                    # st.info creates a visual box with a colored background, perfect for simulating a post
                    st.info(row['content'])
        # Add an elegant horizontal line at the end of the thread block
        st.divider()