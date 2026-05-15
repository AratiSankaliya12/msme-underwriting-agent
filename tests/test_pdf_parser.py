# tests/test_pdf_parser.py
# Run with: python tests/test_pdf_parser.py

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_parser import parse_pdf, print_parse_summary


def test_hdfc_sample():
    """Tests parser against our synthetic HDFC statement."""

    pdf_path = "data/synthetic/hdfc_sample.pdf"

    print(f"\n🔍 Testing parser on: {pdf_path}")
    result = parse_pdf(pdf_path)
    print_parse_summary(result)

    # Basic assertions
    assert result.total_pages > 0, "Should have at least 1 page"
    assert result.confidence != "POOR", "Clean PDF should not be POOR confidence"
    assert len(result.pages) > 0, "Should have parsed pages"

    # Check table extraction worked
    tables_found = sum(len(p.tables) for p in result.pages)
    print(f"✅ Total tables found across all pages: {tables_found}")
    print(f"✅ Confidence: {result.confidence}")
    print(f"✅ Test passed.\n")

    return result


if __name__ == "__main__":
    test_hdfc_sample()
