# MSME Loan Underwriting Intelligence Agent

A multi-agent AI system that assists credit analysts at NBFCs to review
MSME loan applications faster, more accurately, and with full auditability.

## The Problem

A credit analyst reviews 40 loan applications per day. Each application
requires 2–3 hours of manual bank statement analysis. This system reduces
that to under 20 minutes with flagged anomalies and a structured credit memo.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

## Agents

| Agent                      | Responsibility                               |
| -------------------------- | -------------------------------------------- |
| Document Ingestion         | Parses PDFs → Structured JSON                |
| Transaction Classification | Labels each transaction                      |
| Anomaly Detection          | Detects fraud patterns via graph analysis    |
| Financial Ratio            | Calculates DSCR, reconciles GST vs bank data |
| Memo Generation            | Produces citation-grounded credit memos      |
| Orchestrator               | Routes flow conditionally via LangGraph      |

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Add your API keys
```

## Status

🔄 Phase 0 — Project Setup (In Progress)
