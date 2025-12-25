


import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timezone
from openai import OpenAI
import json
import pandas as pd
import logging
import smtplib
from email.mime.text import MIMEText
import os
# ==============================================================================
# CONFIGURATION
# ==============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TPA_Brain")

# Initialize Groq / OpenAI-compatible client
client = None
if GROQ_API_KEY:
    try:
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=BASE_URL
        )
        logger.info("✅ Groq client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq client: {e}")
else:
    logger.warning("⚠️ GROQ_API_KEY not found in environment variables")

# ==============================================================================
# 📧 EMAIL NOTIFICATION SYSTEM
# ==============================================================================
def send_email_notification(filename, risk_score, bid_amount, vendor_id):
    """
    Sends an actual email alert to the Admin when a bid is uploaded.
    """
    # --- 🔧 CREDENTIALS ---
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "transparentprocurementai@gmail.com"  # <--- SENDER EMAIL
    SENDER_PASSWORD = "kmce abye deuk bora"              # <--- APP PASSWORD
    ADMIN_EMAIL = "kapilan.senthil@gmail.com"            # <--- RECEIVER EMAIL
    # ----------------------

    subject = f"🚨 TPA Alert: New Bid from {vendor_id} (Risk: {risk_score})"
    body = f"""
    New Tender Submission Received.
    
    📂 File Name: {filename}
    👤 Vendor ID: {vendor_id}
    💰 Bid Amount: ₹ {bid_amount:,.2f}
    ⚠️ Risk Score: {risk_score}/100
    
    Please log in to the TPA Admin Portal to review the full forensic report.
    """
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = ADMIN_EMAIL

        # Sending Logic
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ EMAIL SENT successfully to {ADMIN_EMAIL}")
        return "SUCCESS"
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Email Failed: {error_msg}")
        return error_msg

# ==============================================================================
# AGENT 1: RISK ASSESSOR
# ==============================================================================
class RiskAgent:
    @staticmethod
    def evaluate_bid_content(text_snippet):
        if not client: return 50, "AI Unavailable"
        prompt = f"""
        Act as a Procurement Fraud Auditor. Analyze this bid document excerpt for risk.
        DOCUMENT: "{text_snippet[:1500]}..."
        
        SCORING CRITERIA:
        - 0-20 (Safe): Professional, detailed, official contact info.
        - 21-50 (Medium): Generic phrasing, minor details missing.
        - 51-80 (High): Very short (<200 words), vague, spelling errors.
        - 81-100 (Critical): Missing key sections, suspicious contact info, dummy bid.
        
        OUTPUT JSON ONLY: {{ "score": <int>, "reason": "<string>" }}
        """
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("score", 50), data.get("reason", "AI Assessment")
        except: return 50, "AI Error"

    @staticmethod
    def calculate_risk(trigger, evidence):
        if not client: return 50, "AI Unavailable"
        prompt = f"""
        Evaluate FRAUD TRIGGER: {trigger}
        EVIDENCE: "{evidence}"
        Assign Fraud Score (0-100). OUTPUT JSON ONLY: {{ "score": <int>, "reason": "<string>" }}
        """
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("score", 50), data.get("reason", "Trigger Assessment")
        except: return 50, "Error"

# ==============================================================================
# AGENT 2: INVESTIGATOR
# ==============================================================================
class InvestigatorAgent:
    @staticmethod
    def analyze_suspicion(doc_a_text, doc_b_text, trigger):
        if not client: return f"Detected {trigger}."
        prompt = f"Analyze fraud trigger: {trigger}. Evidence A: {doc_a_text[:500]}. Evidence B: {doc_b_text[:500]}. Write 1 sentence verdict."
        try:
            return client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
        except: return "AI Analysis Failed."

# ==============================================================================
# AGENT 3: CHIEF AUDITOR
# ==============================================================================
class AuditorAgent:
    @staticmethod
    def generate_executive_summary(all_alerts, doc_count):
        if not client: return "Summary unavailable."
        alerts_list = "\n".join([f"- {a['title']}: {a['details']}" for a in all_alerts])
        prompt = f"Write a 60-word executive summary for {doc_count} bids based on these alerts: {alerts_list}"
        try:
            return client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
        except: return "Summary unavailable."

# ==============================================================================
# AGENT 4: CHAT AGENT
# ==============================================================================
class ChatAgent:
    @staticmethod
    def answer_question(question, documents, alerts):
        if not client: return "AI unavailable."
        context_str = ""
        for doc in documents:
            context_str += f"File: {doc['filename']} | Risk: {doc['risk_score']} | Bid: {doc['bid_amount']} | Content: {doc['text'][:300]}...\n"
        
        prompt = f"""
        You are the TPA AI Assistant. Answer based ONLY on this data:
        {context_str}
        
        USER QUESTION: "{question}"
        """
        try:
            return client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
        except: return "Error processing question."

# ==============================================================================
# AGENT 5: THE SCOUT
# ==============================================================================
class ScoutAgent:
    @staticmethod
    def clean_text(text): return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def extract_financials(text):
        text = text.lower().replace(",", "")
        match = re.search(r'(?:grand|total|bid)\s?(?:price|cost|value|amount)?\s?[:\-]?\s?(?:₹|rs\.?|inr|usd|\$)\s?([\d]+\.?\d*)', text)
        if match: return float(match.group(1))
        match_num = re.search(r'(?:₹|rs\.?|inr|usd|\$)\s?([\d]+\.?\d*)', text)
        if match_num: return float(match_num.group(1))
        return 0.0

    @staticmethod
    def process_file(uploaded_file):
        try:
            pdf = PyPDF2.PdfReader(uploaded_file)
            text = " ".join([p.extract_text() for p in pdf.pages])
            clean = ScoutAgent.clean_text(text)
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', clean)
            return {
                "filename": uploaded_file.name, "text": clean, "emails": emails,
                "bid_amount": ScoutAgent.extract_financials(clean), "risk_score": 0
            }
        except: return {"filename": uploaded_file.name, "error": "Error", "risk_score": 0, "bid_amount": 0}

    @staticmethod
    def run_scan(documents, historical_avg):
        alerts = []
        connections = []
        for doc in documents:
            if "error" in doc and doc['error']: continue
            
            # 1. AI Content Assessment
            ai_score, ai_reason = RiskAgent.evaluate_bid_content(doc['text'])
            doc['risk_score'] = ai_score 
            if ai_score > 40:
                alerts.append({"title": "AI Assessment", "severity": "MEDIUM", "details": ai_reason, "filename": doc['filename']})

            # 2. Hard Rules (Financials)
            if doc['bid_amount'] == 0:
                doc['risk_score'] = max(doc['risk_score'], 95)
                alerts.append({"title": "Zero Financials", "severity": "CRITICAL", "details": "Bid amount 0 or missing.", "filename": doc['filename']})
            elif historical_avg > 0:
                deviation = ((doc['bid_amount'] - historical_avg) / historical_avg) * 100
                if deviation < -30:
                    doc['risk_score'] = max(doc['risk_score'], 80)
                    alerts.append({"title": "Predatory Pricing", "severity": "CRITICAL", "details": f"Bid {abs(deviation):.1f}% below estimate.", "filename": doc['filename']})
            
            if doc['emails']:
                domain = doc['emails'][0].split('@')[-1].lower()
                if any(x in domain for x in ['gmail', 'yahoo']):
                    doc['risk_score'] = max(doc['risk_score'], 55)
                    alerts.append({"title": "Generic Email", "severity": "MEDIUM", "details": f"Using {domain}", "filename": doc['filename']})

        # 3. Relationship Graph Analysis (Collusion Scan)
        if len(documents) >= 2:
            texts = [d['text'] for d in documents if len(d['text']) > 50]
            if len(texts) > 1:
                tfidf = TfidfVectorizer(stop_words='english')
                try:
                    matrix = tfidf.fit_transform(texts)
                    for i in range(len(documents)):
                        for j in range(i+1, len(documents)):
                            sim = cosine_similarity(matrix[i], matrix[j])[0][0] * 100
                            if sim > 85: # Threshold for Collusion
                                doc_a, doc_b = documents[i], documents[j]
                                doc_a['risk_score'] = 98; doc_b['risk_score'] = 98
                                alerts.append({"title": "Collusion", "severity": "CRITICAL", "details": "90%+ Text Match", "filename": "Multiple"})
                                connections.append((doc_a['filename'], doc_b['filename'], "Match"))
                except: pass
        return alerts, connections

    @staticmethod
    def analyze_history(df):
        alerts = []
        if 'Winner' in df.columns and len(df) > 5:
            counts = df['Winner'].value_counts().head(3).values
            if len(counts) >= 2 and (max(counts) - min(counts) <= 1):
                alerts.append({"title": "Cartel Rotation", "severity": "CRITICAL", "details": "Winners taking turns.", "filename": "History"})
        return alerts

def extract_text_from_pdf(f): return ScoutAgent.process_file(f)
def run_full_scan(d, h): return ScoutAgent.run_scan(d, h)
def generate_project_summary(a, c): return AuditorAgent.generate_executive_summary(a, c)
def analyze_history(df): return ScoutAgent.analyze_history(df)
def send_email(f, r, b, v): return send_email_notification(f, r, b, v)
