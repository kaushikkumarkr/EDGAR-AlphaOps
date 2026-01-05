
import logging
from bs4 import BeautifulSoup
import lxml.etree as etree
import re

logger = logging.getLogger(__name__)

class XBRLParser:
    def parse(self, content: bytes) -> list[dict]:
        """
        Parses XBRL content (Inline XBRL or XML) and returns a list of facts.
        """
        # Detection
        if b"<html" in content[:1000].lower() or b"xmlns:ix" in content[:2000].lower():
            return self._parse_ixbrl(content)
        else:
            return self._parse_xml(content)

    def _parse_ixbrl(self, content: bytes) -> list[dict]:
        facts = []
        soup = BeautifulSoup(content, "lxml")
        
        # ix:nonFraction - Numeric facts
        for tag in soup.find_all("ix:nonfraction"):
            try:
                # Extract attributes
                concept = tag.get("name")
                unit = tag.get("unitref")
                context_ref = tag.get("contextref")
                decimals = tag.get("decimals")
                scale = tag.get("scale")
                sign = tag.get("sign", "")
                
                # Extract value
                text_val = tag.get_text(strip=True).replace(",", "")
                if not text_val:
                    continue
                    
                val = float(text_val)
                if sign == "-":
                    val = -val
                    
                if scale:
                    val = val * (10 ** int(scale))
                
                # Context Parsing (simplified)
                # Ideally we parse <xbrli:context> elements matching ref
                # But for now, we just pass the ID so we can inspect it.
                
                facts.append({
                    "concept": concept,
                    "value": str(val),
                    "unit": unit,
                    "period_db_ref": context_ref
                })
            except Exception as e:
                # logger.debug(f"Error parsing tag: {e}") # Reduce noise
                continue
                
        return facts

    def _parse_xml(self, content: bytes) -> list[dict]:
        # Placeholder for Legacy XML support
        logger.info("XML XBRL Parsing not yet implemented")
        return []
