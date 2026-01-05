
import pytest
from pipelines.parse.xbrl import XBRLParser

def test_xbrl_parsing():
    content = b"""
    <html>
    <ix:nonFraction name="us-gaap:Assets" unitRef="USD" decimals="-6" scale="6" contextRef="c1">
        1,234.56
    </ix:nonFraction>
    <ix:nonFraction name="us-gaap:Liabilities" unitRef="USD" sign="-" scale="6" contextRef="c1">
        500
    </ix:nonFraction>
    </html>
    """
    
    parser = XBRLParser()
    facts = parser.parse(content)
    
    assert len(facts) == 2
    
    # Assets: 1234.56 * 10^6 = 1,234,560,000
    f1 = facts[0]
    assert f1["concept"] == "us-gaap:Assets"
    # Wait, simple float conversion might be slightly off, verify approx or string
    assert float(f1["value"]) == 1234560000.0
    
    # Liabilities: -500 * 10^6 = -500,000,000 (sign="-")
    f2 = facts[1]
    assert f2["concept"] == "us-gaap:Liabilities"
    assert float(f2["value"]) == -500000000.0
