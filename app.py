import streamlit as st
import json
import random
import time
import os

# --- Configuration & Retro CSS ---
st.set_page_config(page_title="Retro Triage Sim", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    .retro-text {
        font-family: 'Press+Start+2P', cursive;
        color: #00FF00;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .stat-box {
        background-color: #222;
        border: 2px solid #00FF00;
        padding: 10px;
        text-align: center;
        color: #fff;
        font-family: monospace;
        margin-bottom: 10px;
    }

    .arcade-container {
        height: 300px;
        overflow: hidden;
        position: relative;
        background: black;
        border: 4px solid #333;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.4);
    }

    .scroll-content {
        position: absolute;
        width: 100%;
        text-align: center;
        transform: translateY(100%);
        animation: scroll-up 15s linear infinite;
    }

    .score-entry {
        font-family: 'Press+Start+2P', cursive;
        color: #FFFF00;
        font-size: 14px;
        margin-bottom: 15px;
        text-shadow: 2px 2px #FF0000;
    }

    @keyframes scroll-up {
        0% { transform: translateY(100%); }
        100% { transform: translateY(-120%); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. Helper Functions ---

def init_game(shift_hours, bed_count, patient_volume):
    if not os.path.exists('patients.json'):
        st.error("patients.json not found! Please run the generator first.")
        st.stop()
        
    with open('patients.json', 'r') as f:
        all_data = json.load(f)
    
    # Logic: Sample based on daily volume requested
    # If volume > available in JSON, we just take all of them.
    sample_size = min(patient_volume, len(all_data))
    
    st.session_state.waiting_room = random.sample(all_data, sample_size)
    st.session_state.active_patients = []
    
    # Fill active slots (simulate busy room)
    for _ in range(min(5, len(st.session_state.waiting_room))):
        st.session_state.active_patients.append(st.session_state.waiting_room.pop(0))
        
    st.session_state.beds_total = bed_count
    st.session_state.beds_occupied = 0
    st.session_state.time_remaining = shift_hours * 60 
    st.session_state.money_spent = 0
    st.session_state.results_log = [] 
    st.session_state.game_over = False
    st.session_state.current_patient_idx = 0 

def get_leaderboard():
    if not os.path.exists('leaderboard.txt'):
        return []
    with open('leaderboard.txt', 'r') as f:
        lines = [line.strip().split(',') for line in f.readlines() if line.strip()]
    return sorted(lines, key=lambda x: -int(x[1]))

# --- 2. Main Menu / Leaderboard ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if not st.session_state.game_active:
    st.markdown("<h1 class='retro-text'>RETRO TRIAGE MANAGER</h1>", unsafe_allow_html=True)
    
    col_menu, col_scores = st.columns(2)
    
    with col_menu:
        st.subheader("Shift Configuration")
        shift_len = st.number_input("Shift Duration (Hours)", 1, 12, 4)
        bed_num = st.number_input("Available Beds", 1, 20, 5)
        
        # NEW: Patient Volume Toggle
        pat_vol = st.slider("Daily Patient Volume", 50, 500, 100)
        
        st.info("⚠️ Penalties applied for overcrowding!")
        
        if st.button("START SHIFT"):
            init_game(shift_len, bed_num, pat_vol)
            st.session_state.game_active = True
            st.rerun()

    with col_scores:
        if st.checkbox("View Leaderboard"):
            scores = get_leaderboard()
            html_content = "".join([f"<div class='score-entry'>{s[0]} ..... {s[1]}% (${s[2]})</div>" for s in scores])
            st.markdown(f"""
                <div class="arcade-container">
                    <div class="scroll-content">
                        <div class="score-entry" style="color:#FFF">TOP AGENTS</div>
                        <div class="score-entry">----------</div>
                        {html_content}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.stop()

# --- 3. Game Engine ---

if st.session_state.time_remaining <= 0 or (len(st.session_state.active_patients) == 0 and len(st.session_state.waiting_room) == 0):
    st.session_state.game_active = False
    
    if len(st.session_state.results_log) > 0:
        safety_score = int((sum(st.session_state.results_log) / len(st.session_state.results_log)) * 100)
    else:
        safety_score = 0
        
    st.balloons()
    st.markdown("<h1 class='retro-text'>SHIFT OVER</h1>", unsafe_allow_html=True)
    st.metric("Final Safety Score", f"{safety_score}%")
    st.metric("Budget Used", f"${st.session_state.money_spent}")
    
    name = st.text_input("ENTER 3-LETTER INITIALS:", max_chars=3).upper()
    if st.button("SUBMIT TO LEADERBOARD"):
        with open("leaderboard.txt", "a") as f:
            f.write(f"{name},{safety_score},{st.session_state.money_spent}\n")
        st.success("SAVED.")
        time.sleep(2)
        del st.session_state.game_active
        st.rerun()
    st.stop()

# --- HUD ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("⏱ Time Left", f"{st.session_state.time_remaining} min")
c2.metric("🛏 Beds", f"{st.session_state.beds_occupied} / {st.session_state.beds_total}")
c3.metric("💰 Cost", f"${st.session_state.money_spent}")
c4.metric("👥 Queue", f"{len(st.session_state.waiting_room)}")

# --- Patient Selection ---
if st.session_state.current_patient_idx >= len(st.session_state.active_patients):
    st.session_state.current_patient_idx = 0

current_p = st.session_state.active_patients[st.session_state.current_patient_idx]

if 'status' not in current_p:
    current_p['status'] = 'Waiting' 
    current_p['test_ordered_at'] = None
    current_p['result_time'] = None
    current_p['test_result_str'] = None

# --- Display ---
st.markdown("---")
col_img, col_info = st.columns([1, 2])

with col_img:
    st.image(f"https://api.dicebear.com/7.x/pixel-art/svg?seed={current_p['name']}", width=150)
    if current_p['status'] == 'Bedded':
        st.warning(f"🛏 IN BED")
        if st.session_state.time_remaining <= current_p['result_arrival_time']:
            st.success("✅ RESULTS BACK")
            st.info(current_p['test_result_str'])
        else:
            wait_min = st.session_state.time_remaining - current_p['result_arrival_time']
            st.info(f"⏳ Analyzing... (~{wait_min}m)")

with col_info:
    st.subheader(f"{current_p['name']}")
    st.write(f"**Presentation:** {current_p['complaint']}")
    st.write(f"**Vitals:** {current_p['vitals']}")

# --- Actions ---
st.write("### Actions")
# 6 columns to fit new buttons
ac1, ac2, ac3, ac4, ac5, ac6 = st.columns(6)

# Helper for Bed Check
def check_bed_availability():
    if current_p['status'] == 'Bedded':
        return True, "Already in Bed"
    if st.session_state.beds_occupied >= st.session_state.beds_total:
        # PENALTY LOGIC
        st.session_state.time_remaining -= 15
        st.error("⚠️ NO BEDS! CORRIDOR CRISIS PENALTY: -15 MINS")
        return False, "Full"
    return True, "OK"

# 1. DISCHARGE
if ac1.button("Discharge"):
    is_safe = current_p['correct_action'] == "Discharge"
    st.session_state.results_log.append(is_safe)
    if current_p['status'] == 'Bedded':
        st.session_state.beds_occupied -= 1
    
    st.session_state.active_patients.pop(st.session_state.current_patient_idx)
    if st.session_state.waiting_room:
        st.session_state.active_patients.append(st.session_state.waiting_room.pop(0))
    
    st.session_state.time_remaining -= 5 
    st.session_state.current_patient_idx = random.randint(0, len(st.session_state.active_patients) - 1) if st.session_state.active_patients else 0
    st.rerun()

# 2. ADMIT
if ac2.button("Admit"):
    is_safe = current_p['correct_action'] == "Admit"
    st.session_state.results_log.append(is_safe)
    if current_p['status'] == 'Bedded':
        st.session_state.beds_occupied -= 1
        
    st.session_state.active_patients.pop(st.session_state.current_patient_idx)
    if st.session_state.waiting_room:
        st.session_state.active_patients.append(st.session_state.waiting_room.pop(0))
        
    st.session_state.time_remaining -= 15 
    st.session_state.current_patient_idx = random.randint(0, len(st.session_state.active_patients) - 1) if st.session_state.active_patients else 0
    st.rerun()

# 3. GEN DIAGNOSTICS (NEW)
if ac3.button("Gen Dx ($30)"):
    available, msg = check_bed_availability()
    if available and msg != "Full":
        if current_p['status'] != 'Bedded':
            current_p['status'] = 'Bedded'
            st.session_state.beds_occupied += 1
        
        st.session_state.money_spent += 30
        current_p['test_ordered_at'] = st.session_state.time_remaining
        # Gen Dx takes roughly 45 mins
        delay = 45 + random.randint(0, 15)
        current_p['result_arrival_time'] = st.session_state.time_remaining - delay
        # Construct Gen Results
        current_p['test_result_str'] = f"Bloods: {current_p['tests'].split('.')[0]} | ECG: As per clinical findings."
        st.session_state.time_remaining -= 10 # Time to cannulate/ECG
        st.rerun()

# 4. PoC TROPONIN
if ac4.button("PoC Trop ($50)"):
    available, msg = check_bed_availability()
    if available and msg != "Full":
        if current_p['status'] != 'Bedded':
            current_p['status'] = 'Bedded'
            st.session_state.beds_occupied += 1
        
        st.session_state.money_spent += 50
        current_p['test_ordered_at'] = st.session_state.time_remaining
        current_p['result_arrival_time'] = st.session_state.time_remaining - 20
        current_p['test_result_str'] = current_p['tests']
        st.session_state.time_remaining -= 5 
        st.rerun()

# 5. LAB TROPONIN
if ac5.button("Lab Trop ($10)"):
    available, msg = check_bed_availability()
    if available and msg != "Full":
        if current_p['status'] != 'Bedded':
            current_p['status'] = 'Bedded'
            st.session_state.beds_occupied += 1
        
        st.session_state.money_spent += 10
        current_p['test_ordered_at'] = st.session_state.time_remaining
        delay = 65 + random.randint(0, 30)
        current_p['result_arrival_time'] = st.session_state.time_remaining - delay
        current_p['test_result_str'] = current_p['tests']
        st.session_state.time_remaining -= 5 
        st.rerun()

# 6. CYCLE
if ac6.button("Cycle / Next"):
    st.session_state.time_remaining -= 2
    if len(st.session_state.active_patients) > 1:
        possible_indices = list(range(len(st.session_state.active_patients)))
        possible_indices.remove(st.session_state.current_patient_idx)
        st.session_state.current_patient_idx = random.choice(possible_indices)
    st.rerun()
