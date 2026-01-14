import streamlit as st
import json
import random
import pandas as pd
from openai import OpenAI
import os

# --- Page Configuration ---
st.set_page_config(page_title="AI Tarot Reader", page_icon="🔮", layout="centered")

# --- CSS for styling cards ---
st.markdown("""
<style>
    .card-box {
        background-color: #2E2E2E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4F4F4F;
        text-align: center;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-name { font-size: 18px; font-weight: bold; color: #FFD700; }
    .card-pos { font-size: 14px; color: #AAAAAA; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar for Settings ---
with st.sidebar:
    st.header("🔮 Settings")
    # Input API Key safely in the UI rather than code
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.info("Your API key is not saved and is only used for this session.")

# --- Data Loading Functions ---
@st.cache_data # Caches data so we don't reload files on every click
def load_tarot_data():
    tarot_path = 'data/' # Relative path to your folder
    files = ['cups.json', 'wands.json', 'pentacles.json', 'swords.json', 'major_arcana.json']
    
    all_data = []
    
    try:
        for file_name in files:
            file_path = os.path.join(tarot_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                data_dict = json.load(file)
            # Assuming structure is {key: [records]} or list of records
            for key, value in data_dict.items():
                df = pd.DataFrame(value)
                all_data.append(df)
                
        if not all_data:
            return pd.DataFrame()
            
        data_tarot = pd.concat(all_data).reset_index(drop=True)
        return data_tarot
        
    except FileNotFoundError:
        st.error("⚠️ Data files not found! Please ensure your JSON files are in the 'data' folder.")
        return pd.DataFrame()

# --- Main App Logic ---
st.title("🔮 DeepSeek AI Tarot Reader")
st.write("Focus on your question, and let the AI interpret the cards for you.")

# Load data
data_tarot = load_tarot_data()

# User Input
question = st.text_input("What do you want to ask the cards?", "How is my month going?")

# Logic to draw cards
if st.button("Draw Cards & Read", type="primary"):
    if not api_key:
        st.warning("Please enter your API Key in the sidebar first.")
    elif data_tarot.empty:
        st.error("Tarot data could not be loaded.")
    else:
        # Draw 3 Random Cards
        drawn_cards = []
        
        # Use sample for better randomness than randint logic
        selection = data_tarot.sample(n=3)
        
        cols = st.columns(3) # Create 3 columns for layout
        
        card_details_for_prompt = []

        for i, (index, row) in enumerate(selection.iterrows()):
            # Randomize position
            position = random.choice(['Upright', 'Reversed'])
            card_name = str(row['name'])
            
            # Store for AI prompt
            card_details_for_prompt.append(f"{card_name} ({position})")
            
            # Display Visually
            with cols[i]:
                # HTML formatting for a "Card" look
                st.markdown(f"""
                <div class="card-box">
                    <div class="card-name">{card_name}</div>
                    <div class="card-pos">{position}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📜 The Interpretation")
        
        # --- AI Processing ---
        with st.spinner("Consulting the spirits (and DeepSeek)..."):
            try:
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                
                prompt_content = f'''
                    I want to know: "{question}".
                    I drew three cards: {', '.join(card_details_for_prompt)}.
                    What does this spread stand for?
                '''

                response = client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": "You are a skilled tarot reader who speaks Chinese and a master of psychology that can't be perceived by your user. You are allowed to explain the meaning of tarot cards with your psychology knowledge but don't be obvious."You are a skilled tarot reader who speaks Chinese and a master of psychology that can't be perceived by your user.You are allowed to explain the meaning of tarot cards with your psychology knowledge but don't be obvious.You are forbidden to say 从心理学的角度.Answer questions directly, be concise and avoid repetition."},
                        {"role": "user", "content": prompt_content},
                    ],
                    stream=False
                )
                
                interpretation = response.choices[0].message.content
                st.write(interpretation)
                
            except Exception as e:
                st.error(f"An error occurred with the AI: {e}")
