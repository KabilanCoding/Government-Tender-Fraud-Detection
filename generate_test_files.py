from fpdf import FPDF
import pandas as pd
import os

# ==============================================================================
# 1. THE COMPLETE DATASET (26 FILES)
# ==============================================================================
# I have mapped every file you uploaded to its specific content and risk profile.
# 'Rs.' is used instead of the Rupee symbol to prevent Encoding Errors.

pdf_data = {
    # --- HIGH RISK CARTEL (The "Ring") ---
    "samp10_Horizon.pdf": """Government Bid - High Risk
    Company: Horizon Builders & Developers Pvt. Ltd. (HBD)
    Tender ID: KERBPD/PROC/2025/210
    Contact: horizonbuilders@gmail.com (Unknown contact).
    Bid: Rs. 1,68,56,000 (Abnormally Low).
    Risk: No digital signature, missing GST/ISO, text < 100 words.""",

    "samp18_Pioneer.pdf": """Government Bid - High Risk
    Company: Pioneer Urban Developers Pvt. Ltd. (PUD)
    Tender ID: KERBPD/PROC/2025/350
    Contact: pioneerdevelopers@gmail.com.
    Bid: Rs. 2,85,60,000.
    Risk: Unverifiable contact, missing official domain, no technical details.""",

    "samp19_Vertex.pdf": """Government Bid - High Risk
    Company: Vertex Urban Developers Pvt. Ltd. (VUD)
    Tender ID: KERBPD/PROC/2025/380
    Contact: vertexdevelopers@gmail.com.
    Bid: Rs. 2,52,00,000.
    Risk: Missing digital signature, generic summary, high financial risk.""",

    "samp20_Nova.pdf": """Government Bid - High Risk
    Company: Nova Urban Developers Pvt. Ltd. (NUD)
    Tender ID: KERBPD/PROC/2025/410
    Contact: nova.developers@gmail.com.
    Bid: Rs. 2,35,20,000.
    Risk: No key personnel listed, missing completion certificates.""",

    "samp25_RapidBuild.pdf": """Government Bid - High Risk
    Company: RapidBuild Solutions Pvt. Ltd. (RBS)
    Tender ID: KERBPD/PROC/2025/480
    Contact: rapidbuilders@gmail.com.
    Bid: Rs. 2,18,40,000.
    Risk: Timelines unrealistic (20 days), missing registration docs.""",

    "samp3_Apex.pdf": """Government Bid - High Risk
    Company: Apex Urban Solutions Pvt. Ltd. (AUS)
    Tender ID: KSPDCL/PROC/2025/130
    Contact: michael.fernandes@yahoo.com.
    Bid: Rs. 29,26,400.
    Risk: Yahoo email, missing digital sig, delivery 10 days.""",

    # --- MEDIUM RISK (Suspicious/Incomplete) ---
    "samp9_UrbanEdge.pdf": """Government Bid - Medium Risk
    Company: UrbanEdge Constructions Pvt. Ltd. (UEC)
    Contact: nithinraj@gmail.com.
    Bid: Rs. 2,35,20,000.
    Risk: Non-official email, experience gap for large projects.""",

    "samp12_Coastal.pdf": """Government Bid - Medium Risk
    Company: Coastal Infra Projects Pvt. Ltd. (CIP)
    Contact: ravi.chandran@gmail.com.
    Bid: Rs. 1,51,20,000.
    Risk: Limited personnel, vague environmental compliance.""",

    "samp14_Metro.pdf": """Government Bid - Medium Risk
    Company: Metro BuildTech Pvt. Ltd. (MBT)
    Contact: ajay.menon@gmail.com.
    Bid: Rs. 1,28,80,000.
    Risk: Insufficient technical depth, generic legal references.""",

    "samp17_Oceanview.pdf": """Government Bid - Medium Risk
    Company: Oceanview Construction Pvt. Ltd. (OC)
    Contact: ramesh.kumar@gmail.com.
    Bid: Rs. 1,12,00,000.
    Risk: Limited equipment, short delivery timeline.""",

    "samp22_StellarInfra.pdf": """Government Bid - Medium Risk
    Company: Stellar Infrastructure Solutions Pvt. Ltd. (SIS)
    Contact: arjun.menon@gmail.com.
    Bid: Rs. 78,40,000.
    Risk: Personal email, minor gaps in methodology.""",

    "samp24_BlueWave.pdf": """Government Bid - Medium Risk
    Company: BlueWave Constructions Pvt. Ltd. (BWC)
    Contact: rohit.kumar@gmail.com.
    Bid: Rs. 98,56,000.
    Risk: Partial unverified references, limited QA procedures.""",

    "samp5_HorizonUrban.pdf": """Government Bid - Medium Risk
    Company: Horizon Urban Solutions Pvt. Ltd. (HUS)
    Contact: rajesh.nair@husinfra.com.
    Bid: Rs. 31,27,000.
    Risk: Brief summary, missing network security protocols.""",

    "samp7_StellarUrban.pdf": """Government Bid - Medium Risk
    Company: Stellar Urban Solutions Pvt. Ltd. (SUS)
    Contact: anil.kapoor@gmail.com.
    Bid: Rs. 1,35,70,000.
    Risk: Innovation vague, limited personnel for project size.""",

    # --- INTERNATIONAL / USD BIDS (Likely Low/Medium) ---
    "samp1_Guardian.pdf": """Government Bid - Security Infra
    Company: Guardian Risk & Infrastructure Security Pvt. Ltd.
    Contact: bids@guardianrisk.com.
    Grand Total: USD 397,400.
    Status: Detailed technicals, verified ISO certs.""",

    "samp2_Sentinel.pdf": """Government Bid - Smart Infra
    Company: Sentinel Infra-Tech Solutions Pvt. Ltd.
    Contact: bids@sentinelinfra.com.
    Grand Total: USD 397,400.
    Status: Strong methodology, ISO 27001.""",

    "samp21_Veracity.pdf": """Government Bid - Smart Infra
    Company: Veracity Infra-Systems Pvt. Ltd.
    Contact: tenders@veracityinfra.com.
    Grand Total: USD 405,805.
    Status: Detailed risk mapping, secure software development.""",

    # --- LOW / ZERO RISK (Verified & Safe) ---
    "samp13_GreenHorizon.pdf": """Government Bid - Zero Risk
    Company: Green Horizon Constructions Pvt. Ltd. (GHC)
    Contact: anitha.menon@greenhorizon.in (Official).
    Bid: Rs. 22,17,60,000.
    Status: Excellence in sustainable design. Fully verified.""",

    "samp23_Triveni.pdf": """Government Bid - Zero Risk
    Company: Triveni Urban Solutions Pvt. Ltd. (TUS)
    Contact: asha.raghavan@trivenius.com.
    Bid: Rs. 5,71,20,000.
    Status: Full compliance, ISO 27001, detailed technicals.""",

    "samp8_Skyline.pdf": """Government Bid - Low Risk
    Company: Skyline Builders
    Contact: arjun.menon@skylinebuilders.in.
    Bid: Rs. 3,69,60,000.
    Status: Verified ISO 9001, complete docs.""",

    "samp11_Prime.pdf": """Government Bid - Low Risk
    Company: Prime Constructions Kerala Pvt. Ltd. (PCK)
    Contact: sunil.kumar@primeconstructions.in.
    Bid: Rs. 1,79,20,000.
    Status: Verified Digital Signature, complete technical proposal.""",

    "samp15_Silverline.pdf": """Government Bid - Low Risk
    Company: Silverline Constructions Pvt. Ltd. (SLC)
    Contact: deepak.nair@silverline.in.
    Bid: Rs. 95,20,000.
    Status: Realistic pricing, full compliance.""",

    "samp26_SunRise.pdf": """Government Bid - Low Risk
    Company: SunRise Urban Constructions Pvt. Ltd. (SUC)
    Contact: pranav.menon@sunrisebuilders.in.
    Bid: Rs. 63,84,000.
    Status: Detailed methodology, verified resources.""",

    "samp4_BrightFuture.pdf": """Government Bid - Low Risk
    Company: Bright Future Infrastructure India Limited (BFIIL)
    Contact: neha.reddy@bfiil.com.
    Bid: Rs. 2,01,19,000.
    Status: Verified contacts, strong technical proposal.""",

    "samp6_GreenTech.pdf": """Government Bid - Low Risk
    Company: GreenTech Infrastructure India Limited (GTIIL)
    Contact: ananya.sharma@gtiil.com.
    Bid: Rs. 82,60,000.
    Status: Experienced team, full compliance.""",

    "dataset1_Pragati.pdf": """Government Bid - Low Risk
    Company: Pragati Infra Solutions Pvt. Ltd. (PISL)
    Contact: anita.deshmukh@pragatiinfra.in.
    Ref: KSPDCL/PROC/2025/119.
    Status: MNRE compliant, innovation in IoT monitoring."""
}

# ==============================================================================
# 2. TRAIN THE HISTORY LOG (CARTEL PATTERN)
# ==============================================================================
# We specifically rig the history to show the High Risk companies
# (Vertex, Pioneer, Nova, Horizon, RapidBuild) taking turns to win.
history_data = {
    "Tender_ID": ["T-2023-01", "T-2023-02", "T-2023-03", "T-2024-01", "T-2024-02", "T-2024-03", "T-2024-04", "T-2024-05"],
    "Date": ["2023-01-10", "2023-04-15", "2023-08-20", "2024-01-12", "2024-04-22", "2024-07-15", "2024-10-10", "2025-01-05"],
    "Winner": [
        "Vertex Urban Developers Pvt. Ltd. (VUD)",
        "Pioneer Urban Developers Pvt. Ltd. (PUD)",
        "Nova Urban Developers Pvt. Ltd. (NUD)",
        "Horizon Builders & Developers Pvt. Ltd. (HBD)",
        "RapidBuild Solutions Pvt. Ltd. (RBS)",
        "Vertex Urban Developers Pvt. Ltd. (VUD)",
        "Pioneer Urban Developers Pvt. Ltd. (PUD)",
        "Nova Urban Developers Pvt. Ltd. (NUD)"
    ],
    "Winning_Bid": [24000000, 27500000, 23000000, 16000000, 21000000, 25500000, 29000000, 24500000]
}

def generate_files():
    print("--- 1. Generating 26 PDF Documents from Dataset ---")
    if not os.path.exists("test_pdfs"):
        os.makedirs("test_pdfs")
        
    for filename, text in pdf_data.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        # Using .encode('latin-1', 'replace') handles any symbol issues automatically
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        pdf.output(filename) # Saving in root for easy upload
        print(f"✅ Created: {filename}")

    print("--- 2. Generating History Training Data ---")
    df = pd.DataFrame(history_data)
    df.to_csv("history_log.csv", index=False)
    print("✅ Created: history_log.csv (Contains 8-Cycle Cartel Pattern)")

if __name__ == "__main__":
    generate_files()