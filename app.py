import streamlit as st
import pandas as pd
import time
import sqlite3
import hashlib
from datetime import datetime
from utils import (
    extract_text_from_pdf, 
    run_full_scan, 
    generate_project_summary, 
    analyze_history, 
    ChatAgent,
    send_email_notification
)

# 1. CONFIG
st.set_page_config(page_title="TPA Government Portal", layout="wide", page_icon="🏛️")

# ==============================================================================
# 2. DATABASE MANAGEMENT (SQLite)
# ==============================================================================
def init_db():
    conn = sqlite3.connect('tpa.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT NOT NULL)''')
    # Default vendor check
    c.execute("SELECT * FROM users WHERE username = 'vendor'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('vendor', 'vendor123', 'Vendor'))
    conn.commit()
    conn.close()

def add_user(username, password, role="Vendor"):
    try:
        conn = sqlite3.connect('tpa.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError: return False

def verify_user(username, password):
    if username == "admin" and password == "admin123": return "Admin"
    conn = sqlite3.connect('tpa.db')
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

init_db()

# ==============================================================================
# 3. STATE MANAGEMENT
# ==============================================================================
if "db" not in st.session_state:
    st.session_state.db = {
        "bids": [],       
        "alerts": [],     
        "history": pd.DataFrame(), 
        "project_val": 35000000
    }
if "history" not in st.session_state.db: st.session_state.db["history"] = pd.DataFrame()
if "project_val" not in st.session_state.db: st.session_state.db["project_val"] = 35000000

if "user_role" not in st.session_state: st.session_state.user_role = None
if "current_user" not in st.session_state: st.session_state.current_user = None
if "messages" not in st.session_state: st.session_state.messages = []

# ==============================================================================
# 4. GOVERNMENT UI CSS
# ==============================================================================
st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 🏛️ GOVERNMENT HEADER STYLE */
    .gov-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(90deg, #1a237e 0%, #0d47a1 100%); /* Royal Blue Gradient */
        color: white;
        border-bottom: 5px solid #ff9800; /* Saffron/Gold Accent */
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .gov-header h1 {
        font-family: 'Georgia', serif;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 0;
        font-size: 2.2rem;
    }
    .gov-header p {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 5px;
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        border-radius: 5px;
        border: 1px solid #ccc;
        padding: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1a237e;
        box-shadow: 0 0 5px rgba(26, 35, 126, 0.3);
    }

    /* BUTTONS */
    .stButton > button {
        background-color: #1a237e; /* Gov Blue */
        color: white;
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        padding: 10px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0d47a1;
        color: white;
    }

    /* DASHBOARD CARDS */
    .risk-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border-top: 5px solid #ccc; }
    .card-crit { border-top-color: #dc3545 !important; }
    .card-warn { border-top-color: #ffc107 !important; }
    .card-safe { border-top-color: #28a745 !important; }
    
    /* FOOTER */
    .gov-footer {
        text-align: center;
        margin-top: 50px;
        color: #666;
        font-size: 0.8rem;
        padding: 20px;
        border-top: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. AUTHENTICATION (Fixed UI)
# ==============================================================================
def login_logic():
    # 🏛️ RESTORED GOVERNMENT HEADER
    st.markdown("""
    <div class="gov-header">
        <h1>Ministry of Public Procurement</h1>
        <p>Transparent Procurement Agent (TPA) | Secure Vigilance Portal</p>
    </div>
    """, unsafe_allow_html=True)

    # 🔐 LOGIN FORM (Clean, No Broken White Box)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    
    with c2:
        # We use a native Streamlit container instead of HTML div to avoid the broken UI
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color:#1a237e;'>🔐 Secure Access Portal</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color:gray; font-size:0.9rem;'>Authorized Government & Vendor Access Only</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Tabs for better UX
            tab_login, tab_register = st.tabs(["🔑 Login", "📝 New Vendor Registration"])
            
            with tab_login:
                with st.form("login_form"):
                    st.write("**Enter Credentials**")
                    username = st.text_input("User ID / License No.")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Secure Login")
                    
                    if submitted:
                        role = verify_user(username, password)
                        if role:
                            st.session_state.user_role = role
                            st.session_state.current_user = username 
                            st.rerun()
                        else:
                            st.error("❌ Invalid Credentials. Access Denied.")
            
            with tab_register:
                with st.form("register_form"):
                    st.write("**New Entity Registration**")
                    new_user = st.text_input("Create Vendor ID")
                    new_pass = st.text_input("Create Password", type="password")
                    confirm_pass = st.text_input("Confirm Password", type="password")
                    reg_submit = st.form_submit_button("Submit Registration")
                    
                    if reg_submit:
                        if new_pass != confirm_pass:
                            st.error("Passwords do not match!")
                        elif len(new_pass) < 4:
                            st.error("Password too short!")
                        else:
                            success = add_user(new_user, new_pass)
                            if success:
                                st.success("✅ Account Created! Please verify via Login tab.")
                            else:
                                st.error("Vendor ID already exists.")

    # 📜 OFFICIAL FOOTER
    st.markdown("""
    <div class="gov-footer">
        © 2024 Department of Expenditure, Ministry of Finance. All Rights Reserved.<br>
        Unauthorized access is a punishable offense under the IT Act, 2000.
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 6. VENDOR PORTAL (OFFICIAL UI)
# ==============================================================================
def render_vendor():
    # 🏛️ HEADER
    st.markdown("""
    <div class="gov-header" style="padding:15px; margin-bottom:20px;">
        <h2 style="margin:0;">e-Tender Submission Portal</h2>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([4, 1])
    with c1: 
        st.markdown(f"### 👋 Welcome, Entity: **{st.session_state.current_user}**")
        st.caption("Please upload your technical and financial bid documents below.")
    with c2: 
        if st.button("🚪 Secure Logout"):
            st.session_state.user_role = None
            st.rerun()
            
    st.divider()
    
    col_up, col_info = st.columns([1, 1])
    
    with col_up:
        st.info("ℹ️ Accepted Formats: PDF Only (Max 200MB)")
        uploaded_file = st.file_uploader("Upload Tender Document", type=['pdf'])
    
    with col_info:
        st.markdown("""
        **Submission Guidelines:**
        1. Ensure Digital Signature is valid.
        2. Financials must be clear.
        3. Do not upload encrypted files.
        """)

    if uploaded_file:
        if any(d['filename'] == uploaded_file.name for d in st.session_state.db['bids']):
            st.warning("⚠️ Warning: Duplicate Submission Detected.")
        else:
            with st.status("⚙️ Processing: AI Compliance & Integrity Check...", expanded=True) as status:
                time.sleep(0.5)
                st.write("📂 Digitizing document content...")
                doc = extract_text_from_pdf(uploaded_file)
                
                st.write("🧠 Analyzing for Fraud & Risk indicators...")
                alerts, _ = run_full_scan([doc], st.session_state.db['project_val'])
                
                doc['upload_time'] = datetime.now().strftime("%H:%M:%S")
                doc['vendor_id'] = st.session_state.current_user 
                
                st.session_state.db['bids'].append(doc)
                st.session_state.db['alerts'].extend(alerts)
                
                st.write("📧 Transmitting Notification to Oversight Committee...")
                status_msg = send_email_notification(
                    filename=doc['filename'],
                    risk_score=doc['risk_score'],
                    bid_amount=doc['bid_amount'],
                    vendor_id=st.session_state.current_user
                )
                
                if status_msg == "SUCCESS":
                    st.success("Notification Dispatched Successfully")
                else:
                    st.error(f"Dispatch Failed: {status_msg}")
                
                status.update(label="✅ Submission Accepted & Verified", state="complete", expanded=False)
            
            st.success(f"**Acknowledgement:** Bid for ₹ {doc['bid_amount']:,.0f} received successfully.")
            st.markdown("""
            <div class="gov-footer" style="margin-top:10px;">
                Your submission ID has been generated. Please retain for future reference.
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# 7. ADMIN PORTAL (OFFICIAL UI)
# ==============================================================================
def render_admin():
    # 🏛️ HEADER
    st.markdown("""
    <div class="gov-header" style="background: linear-gradient(90deg, #b71c1c 0%, #d32f2f 100%); border-bottom-color: #212121;">
        <h1>Central Vigilance Commission (CVC)</h1>
        <p>Procurement Oversight Dashboard | TPA Analytics</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.title("👮 Controller Controls")
        if st.button("🚪 Secure Logout", use_container_width=True):
            st.session_state.user_role = None
            st.rerun()
        st.markdown("---")
        
        new_val = st.number_input("Project Est. Value (₹)", value=st.session_state.db['project_val'], step=500000)
        st.session_state.db['project_val'] = new_val
        
        hist_file = st.file_uploader("Upload Past Tender History (CSV)", type=['csv'])
        if hist_file:
            try:
                st.session_state.db['history'] = pd.read_csv(hist_file)
                h_alerts = analyze_history(st.session_state.db['history'])
                st.session_state.db['alerts'].extend(h_alerts)
                st.success("History Data Integrated")
            except: st.error("Data Format Error")

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("### 📊 Live Tender Monitoring")
    with c2:
        st.metric("Total Active Bids", len(st.session_state.db['bids']))
    
    bids = st.session_state.db['bids']
    
    if not bids:
        st.warning("📭 No active tenders found in the registry.")
        return

    m1, m2, m3, m4 = st.columns(4)
    avg_score = sum(d['risk_score'] for d in bids) / len(bids)
    crit_cnt = len([d for d in bids if d['risk_score'] > 75])
    
    m1.metric("Avg Risk Index", f"{avg_score:.0f}/100", delta_color="inverse")
    m3.metric("Critical Flags", crit_cnt, delta="Immediate Action", delta_color="inverse")
    m4.metric("Est. Value", f"₹{(st.session_state.db['project_val']/10000000):.2f} Cr")
    
    st.divider()

    _, connections = run_full_scan(bids, st.session_state.db['project_val'])
    summary = generate_project_summary(st.session_state.db['alerts'], len(bids))
    st.info(f"**🤖 Automated Audit Summary:** {summary}", icon="📝")
    st.divider()

    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Risk Cards", "📝 Inspector", "🕸️ Network Graph", "📜 Historical Data", "💬 AI Assistant"])

    with tab1:
        sorted_docs = sorted(bids, key=lambda x: x['risk_score'], reverse=True)
        cols = st.columns(3)
        for i, doc in enumerate(sorted_docs):
            score = doc['risk_score']
            if score >= 75: style="card-crit"; b_cls="b-crit"; txt="REJECT"
            elif score >= 40: style="card-warn"; b_cls="b-warn"; txt="REVIEW"
            else: style="card-safe"; b_cls="b-safe"; txt="SAFE"
            
            with cols[i % 3]:
                st.markdown(f"""
                <div class="risk-card {style}">
                    <div style="font-weight:bold; font-size:1.1rem; margin-bottom:5px;">{doc['filename']}</div>
                    <div style="font-size:0.8rem; color:#666; margin-bottom:10px;">🕒 {doc.get('upload_time','--')} | 👤 {doc.get('vendor_id', 'Unknown')}</div>
                    <div style="display:flex; justify-content:space-between;">
                        <span class="badge {b_cls}">{txt}</span>
                        <span style="font-weight:900; font-size:1.4rem;">{score}</span>
                    </div>
                    <div style="margin-top:10px; font-weight:600;">₹ {doc['bid_amount']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 📝 Deep Dive Forensic Analysis")
        filenames = [d['filename'] for d in bids]
        sel_file = st.selectbox("Select Bidder:", filenames)
        
        if sel_file:
            target = next(d for d in bids if d['filename'] == sel_file)
            t_alerts = [a for a in st.session_state.db['alerts'] if a.get('filename') == sel_file]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
                <div class="inspector-box">
                    <div class="meta-label">Risk Score</div>
                    <div class="meta-value" style="font-size:2.5rem; color:{'#dc3545' if target['risk_score']>75 else '#28a745'}">{target['risk_score']}</div>
                    <br>
                    <div class="meta-label">Vendor ID</div>
                    <div class="meta-value">{target.get('vendor_id', 'Unknown')}</div>
                    <br>
                    <div class="meta-label">Bid Amount</div>
                    <div class="meta-value">₹ {target['bid_amount']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.subheader("Detected Anomalies")
                if t_alerts:
                    for a in t_alerts:
                        icon = "🚨" if a['severity'] == "CRITICAL" else "⚠️"
                        st.error(f"**{icon} {a['title']}**: {a['details']}")
                else:
                    st.success("✅ Clean Bid. No anomalies detected.")
                
                with st.expander("📄 View Extracted Content"):
                    st.text_area("Raw Text", target['text'], height=200)

    with tab3:
        st.markdown("#### 🕸️ Collusion Detection Graph")
        
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            dot = 'digraph {'
            dot += 'graph [rankdir="LR", bgcolor="transparent", splines=curved, ranksep=2.0];'
            dot += 'node [shape="note", style="filled", fontname="Arial", fontsize=10, penwidth=0];'
            dot += 'edge [fontname="Arial", fontsize=9, arrowsize=0.8];'
            
            for d in bids:
                if d['risk_score'] > 75: 
                    fill = "#ffcccc"; font = "#990000"
                elif d['risk_score'] > 40: 
                    fill = "#fff5cc"; font = "#996600"
                else: 
                    fill = "#ccffcc"; font = "#006600"
                
                label = f"{d['filename']}\\nRisk: {d['risk_score']}"
                dot += f' "{d["filename"]}" [label="{label}" fillcolor="{fill}" fontcolor="{font}"];'
            
            for a, b, r in connections:
                dot += f' "{a}" -> "{b}" [label="{r}" color="#ff0000" penwidth=2.5 style="dashed"];'
                
            dot += '}'
            st.graphviz_chart(dot, use_container_width=True)
        
        with col_g2:
            st.info("Visual representation of bidder relationships.")
            if connections:
                st.error(f"🚨 {len(connections)} Suspicious Connections Found!")

    with tab4:
        if not st.session_state.db['history'].empty:
            st.dataframe(st.session_state.db['history'], use_container_width=True)
            if 'Winner' in st.session_state.db['history'].columns:
                st.bar_chart(st.session_state.db['history']['Winner'].value_counts())
        else:
            st.info("Upload 'history_log.csv' in the Sidebar to activate this tab.")

    with tab5:
        st.markdown("#### 💬 AI Forensic Assistant")
        chat_box = st.container()
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        if prompt := st.chat_input("Ask me anything!!..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Ask me anything!!..."):
                    ans = ChatAgent.answer_question(prompt, bids, st.session_state.db['alerts'])
                    st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

# ==============================================================================
# 8. ROUTER
# ==============================================================================
if st.session_state.user_role == "Vendor":
    render_vendor()
elif st.session_state.user_role == "Admin":
    render_admin()
else:
    login_logic()
