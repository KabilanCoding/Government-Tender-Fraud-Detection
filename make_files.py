from fpdf import FPDF
import os

def create_pdf(filename, content, author="Unknown"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.set_author(author)
    pdf.output(filename)
    print(f"Created: {filename}")

# --- TEST 1: THE HIDDEN PARTNERS (Different Text, Same Author) ---
# Bid A and Bid B have NOTHING in common in text, but share Author "JohnDoe"
text_a = """PROPOSAL A
We will build the sidewalk using Grade A cement.
Our price is $ 2,000,000."""

text_b = """BID PROPOSAL B
Our approach relies on asphalt and quick-dry techniques.
We can do it for $ 1,950,000."""

create_pdf("Test1_Partner_A.pdf", text_a, author="JohnDoe")
create_pdf("Test1_Partner_B.pdf", text_b, author="JohnDoe")


# --- TEST 2: THE COMPETITIVE COPYCAT (Same Text, Diff Author, Lower Price) ---
# Bid C is the Original. Bid D copies it but undercuts the price to win.
text_c = """TECHNICAL SPECIFICATION
We use 4-inch aggregate base compacted to 95% density.
Price: $ 2,000,000"""

text_d = """TECHNICAL SPECIFICATION
We use 4-inch aggregate base compacted to 95% density.
Price: $ 1,800,000"""

create_pdf("Test2_Original_C.pdf", text_c, author="Company_C_Admin")
create_pdf("Test2_Copycat_D.pdf", text_d, author="Competitor_Dave")

print("✅ All test files created successfully.")