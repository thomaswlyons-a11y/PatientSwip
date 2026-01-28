import streamlit as st
import json
import random
import time

# --- Configuration & Styling ---
st.set_page_config(page_title="Retro Triage Sim", layout="centered")

def init_game(num_patients):
    with open('patients.json', 'r') as f:
        all_cases = json.load(f)
    selected = random.sample(all_cases, min(num_patients, len(all_cases)))
    st.session_state.queue = selected
    st.session_state.results = []
    st.session_state.start_time = time.time()
    st.session_state.game_active = True
    st.session_state.current_index = 0

# --- 1. Splash Screen / Disclaimer ---
if 'disclaimer_accepted' not in st.session_state:
    st.title("🏥 Retro Triage Sim")
    st.warning("### MEDICAL DISCLAIMER")
    st.write("""
    This application is a **NON-CLINICAL simulation**. It is intended for educational/entertainment 
    purposes only and does NOT provide medical advice, diagnosis, or treatment. 
    Using this for real-world clinical decision-making carries significant risk of patient harm.
    """)
    if st.button("I UNDERSTAND THE RISKS - START"):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()

# --- 2. Game Setup ---
if 'game_active' not in st.session_state:
    st.title("Game Setup")
    count = st.slider("How many patients to triage?", 5, 100, 10)
    if st.button("Begin Shift"):
        init_game(count)
        st.rerun()
    st.stop()

# --- 3. Gameplay Loop ---
queue = st.session_state.queue
if len(queue) > 0:
    current_patient = queue[0]
    
    st.header(f"Patient Slot: {len(st.session_state.results) + 1}")
    
    # 8-bit Placeholder (You can replace URL with local 8-bit assets)
    st.image(f"https://api.dicebear.com/7.x/pixel-art/svg?seed={current_patient['name']}", width=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Patient", current_patient['name'])
        st.write(f"**Vitals:** {current_patient['vitals']}")
    with col2:
        st.write(f"**Complaint:** {current_patient['complaint']}")

    # Action Buttons
    c1, c2, c3, c4 = st.columns(4)
    choice = None
    
    if c1.button("Discharge"): choice = "Discharge"
    if c2.button("Diagnostics"): st.info(f"Test Results: {current_patient['tests']}")
    if c3.button("Observe"): 
        st.session_state.queue.append(st.session_state.queue.pop(0))
        st.rerun()
    if c4.button("Admit"): choice = "Admit"

    if choice:
        # Simple Scoring: Is the choice correct?
        is_safe = choice == current_patient['correct_action']
        st.session_state.results.append(is_safe)
        st.session_state.queue.pop(0)
        st.rerun()

# --- 4. Scoreboard & Ending ---
else:
    total_time = round(time.time() - st.session_state.start_time, 2)
    safety_score = int((sum(st.session_state.results) / len(st.session_state.results)) * 100)
    
    st.balloons()
    st.title("Shift Complete!")
    st.subheader(f"Safety Score: {safety_score}% | Time: {total_time}s")
    
    name = st.text_input("Enter 3-letter initials:", max_chars=3).upper()
    if st.button("Submit to Leaderboard"):
        with open("leaderboard.txt", "a") as f:
            f.write(f"{name},{safety_score},{total_time}\n")
        st.write("Score Saved!")
        if st.button("Play Again"):
            del st.session_state.game_active
            st.rerun()
