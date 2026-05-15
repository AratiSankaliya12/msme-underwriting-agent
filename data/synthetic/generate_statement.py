# data/synthetic/generate_statement.py
# ─────────────────────────────────────────────────────────────────
# Generates a realistic synthetic HDFC-style bank statement PDF
# for testing our parser. Uses only the 'fpdf2' library.
# Run once: python data/synthetic/generate_statement.py
# ─────────────────────────────────────────────────────────────────

from fpdf import FPDF
import random
from datetime import datetime, timedelta


def generate_transactions(num: int = 40) -> list[dict]:
    """
    Creates a list of fake but realistic bank transactions.
    Mimics the variety of real MSME account activity.
    """
    transaction_types = [
        ("NEFT/CR/RAJESH TRADING CO/REF829134", "credit", 45000),
        ("NEFT/DR/VENDOR SUPPLIES LTD/REF991023", "debit", 22000),
        ("UPI/CR/9876543210/PAYMENT", "credit", 12000),
        ("ATM/WDL/HDFC ATM SURAT/REF002341", "debit", 10000),
        ("NACH/DR/HDFC BANK EMI/LOANREF4421", "debit", 18500),
        ("NEFT/CR/GST REFUND/GSTIN29AAA", "credit", 5000),
        ("IMPS/CR/CUSTOMER ADVANCE/REF556677", "credit", 30000),
        ("NEFT/DR/OFFICE RENT/PROP9922", "debit", 15000),
        ("NEFT/CR/RAJESH TRADING CO/REF001122", "credit", 45000),  # repeated sender
        ("NEFT/DR/RAJESH TRADING CO/REF001199", "debit", 44000),  # circular pattern
        ("UPI/DR/SWIGGY ORDER/TXN776612", "debit", 850),
        ("SALARY/CR/SELF TRANSFER/SAVINGSAC", "credit", 25000),
        ("NEFT/DR/INDIFI FINANCE EMI/REF5566", "debit", 12000),
        ("CASH/DEP/BRANCH DEPOSIT", "credit", 80000),  # large one-time
        ("NEFT/CR/AMAZON PAY SELLER/REF334455", "credit", 8900),
    ]

    start_date = datetime(2023, 8, 1)
    opening_balance = 125000.00
    transactions = []

    for i in range(num):
        txn_template = random.choice(transaction_types)
        description, direction, base_amount = txn_template

        # Add some noise to amounts
        amount = round(base_amount * random.uniform(0.85, 1.15), 2)
        date = start_date + timedelta(days=random.randint(0, 364))

        transactions.append(
            {
                "date": date.strftime("%d/%m/%Y"),
                "description": description,
                "direction": direction,
                "amount": amount,
            }
        )

    # Sort by date
    transactions.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"))

    # Calculate running balance AFTER sorting
    balance = opening_balance
    formatted_transactions = []

    for txn in transactions:
        direction = txn["direction"]
        amount = txn["amount"]

        if direction == "credit":
            balance += amount

            formatted_transactions.append(
                {
                    "date": txn["date"],
                    "description": txn["description"],
                    "debit": "",
                    "credit": f"{amount:,.2f}",
                    "balance": f"{balance:,.2f}",
                }
            )

        else:
            balance -= amount

            if balance < 0:
                balance = abs(balance)  # keep positive for realism

            formatted_transactions.append(
                {
                    "date": txn["date"],
                    "description": txn["description"],
                    "debit": f"{amount:,.2f}",
                    "credit": "",
                    "balance": f"{balance:,.2f}",
                }
            )

    return formatted_transactions


def create_hdfc_statement(output_path: str = "data/synthetic/hdfc_sample.pdf"):
    """
    Generates a PDF that mimics HDFC Bank statement layout.
    """
    pdf = FPDF()
    pdf.add_page()

    # ── Bank Header ──────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_fill_color(0, 60, 130)  # HDFC dark blue
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "HDFC BANK", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "Account Statement", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Account Details ──────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    details = [
        ("Account Holder", "ARATI ENTERPRISES PRIVATE LIMITED"),
        ("Account Number", "XXXX XXXX 4892"),
        ("Account Type", "Current Account"),
        ("IFSC Code", "HDFC0001234"),
        ("Branch", "Surat Main Branch, Gujarat"),
        ("Statement Period", "01/08/2023 to 31/07/2024"),
    ]

    for label, value in details:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(50, 6, label + ":", new_x="RIGHT", new_y="LAST")

        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # ── Transaction Table Header ──────────────────────────────────
    pdf.set_fill_color(220, 230, 242)
    pdf.set_font("Helvetica", "B", 8)

    headers = [
        ("Date", 25),
        ("Description", 85),
        ("Debit", 25),
        ("Credit", 25),
        ("Balance", 30),
    ]

    for header, width in headers:
        pdf.cell(width, 8, header, border=1, fill=True, align="C")

    pdf.ln()

    # ── Transaction Rows ─────────────────────────────────────────
    transactions = generate_transactions(40)

    pdf.set_font("Helvetica", "", 7)

    for i, txn in enumerate(transactions):

        # Alternate row shading
        if i % 2 == 0:
            pdf.set_fill_color(245, 248, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.cell(25, 6, txn["date"], border=1, fill=True, align="C")
        pdf.cell(85, 6, txn["description"], border=1, fill=True)
        pdf.cell(25, 6, txn["debit"], border=1, fill=True, align="R")
        pdf.cell(25, 6, txn["credit"], border=1, fill=True, align="R")
        pdf.cell(30, 6, txn["balance"], border=1, fill=True, align="R")

        pdf.ln()

    # ── Footer ────────────────────────────────────────────────────
    pdf.ln(8)

    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)

    pdf.cell(
        0,
        5,
        "This is a system-generated statement. " "For queries contact: 1800-258-3838",
        align="C",
    )

    pdf.output(output_path)

    print(f"✅ Synthetic statement generated: {output_path}")


if __name__ == "__main__":
    create_hdfc_statement()
