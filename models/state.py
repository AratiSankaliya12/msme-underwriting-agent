# models/state.py
# ─────────────────────────────────────────────────────────────────
"""ApplicationState: The single shared state object that flows through
every node in our LangGraph. Think of it as the "tray" that carries
all information between agents."""

# ─────────────────────────────────────────────────────────────────

from typing import TypedDict, Optional, List
from enum import Enum


class RiskLevel(str, Enum):
    """
    Possible risk classifications for a loan application.
    Using an Enum prevents typos like "high" vs "HIGH" vs "High".
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNASSESSED = "UNASSESSED"


class DocumentConfidence(str, Enum):
    """
    Quality rating of the document ingestion step.
    If POOR, the graph routes to re-upload request.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    POOR = "POOR"


class Transaction(TypedDict):
    """
    A single bank transaction row, normalized across all bank formats.
    Every bank formats dates and descriptions differently —
    this is our standardized shape.
    """

    date: str  # ISO format: "2024-08-15"
    description: str  # Raw text from bank statement
    debit: Optional[float]  # Money OUT (None if credit transaction)
    credit: Optional[float]  # Money IN (None if debit transaction)
    balance: float  # Account balance after this transaction
    label: Optional[str]  # Set by Classification Agent later
    is_suspicious: bool  # Set by Anomaly Agent later


class FinancialRatios(TypedDict):
    """
    All computed financial metrics for the application.
    Computed by the Financial Ratio Agent.
    """

    dscr: Optional[float]  # Debt Service Coverage Ratio
    avg_monthly_balance: Optional[float]  # Average balance over statement period
    effective_monthly_revenue: Optional[float]
    cash_flow_volatility: Optional[float]  # Std deviation of monthly net flows
    gst_declared_revenue: Optional[float]  # From GST returns
    bank_inferred_revenue: Optional[float]  # From bank statement credits
    revenue_discrepancy_pct: Optional[float]  # Gap between the two, in %


class Anomaly(TypedDict):
    """
    A single detected anomaly or red flag.
    """

    anomaly_type: str  # e.g., "CIRCULAR_TRANSACTION", "BALANCE_INFLATION"
    severity: str  # "LOW", "MEDIUM", "HIGH"
    description: str  # Human-readable explanation
    evidence: List[str]  # Transaction IDs or dates that support this flag


class ApplicationState(TypedDict):
    """
    THE MASTER STATE OBJECT.
    This is initialized at the start and mutated by each agent node.
    LangGraph passes this between every node automatically.
    """

    # ── Input ──────────────────────────────────────────────────
    application_id: str
    applicant_name: str
    raw_pdf_paths: List[str]  # File paths to uploaded PDFs

    # ── Set by Document Ingestion Agent ────────────────────────
    transactions: List[Transaction]
    bank_name: Optional[str]
    account_number: Optional[str]
    statement_period: Optional[str]  # e.g., "2023-08 to 2024-07"
    ingestion_confidence: DocumentConfidence
    ingestion_errors: List[str]  # Any extraction warnings

    # ── Set by Classification Agent ─────────────────────────────
    classified_transactions: List[Transaction]

    # ── Set by Anomaly Detection Agent ──────────────────────────
    anomalies: List[Anomaly]
    anomaly_summary: Optional[str]

    # ── Set by Financial Ratio Agent ────────────────────────────
    financial_ratios: Optional[FinancialRatios]
    ratio_conflicts: List[str]  # e.g., "GST vs bank revenue gap > 50%"

    # ── Set by Orchestrator Decision Node ───────────────────────
    risk_level: RiskLevel
    routing_reason: Optional[str]  # Why it was routed HIGH/LOW

    # ── Set by Memo Generation Agent ───────────────────────────
    credit_memo: Optional[str]
    rejection_summary: Optional[str]

    # ── Meta ────────────────────────────────────────────────────
    errors: List[str]  # Global error log
    current_step: Optional[str]  # Tracks where we are in the graph
