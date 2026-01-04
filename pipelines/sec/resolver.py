import logging
import re
from bs4 import BeautifulSoup
from typing import Optional, Tuple

class FilingResolver:
    @staticmethod
    def resolve_primary_doc_url(index_html_content: str, base_url: str) -> Optional[Tuple[str, str]]:
        """
        Parses SEC index page to find the main report file (10-K, 10-Q, 8-K).
        Returns tuple: (absolute_url, filename).
        Base URL should be the directory URL (e.g. .../000123/000456/).
        """
        soup = BeautifulSoup(index_html_content, "html.parser")
        
        # Look for the table with class "tableFile" usually
        # Structure: Document Format | Description | Document | Type | Size | Seq
        
        # We look for rows where "Type" matches target forms (10-K, 10-Q, 8-K)
        # OR usually row 1 is the primary doc.
        
        tables = soup.find_all("table", class_="tableFile")
        if not tables:
            logging.warning("No tableFile found in index page")
            return None
            
        # Usually it's the first table "Document Format Files"
        doc_table = tables[0]
        rows = doc_table.find_all("tr")
        
        for row in rows:
            cells = row.find_all("td")
            if not cells or len(cells) < 4:
                continue
            
            # Columns: Seq | Description | Document | Type | Size
            # (Indices vary, sometimes 3rd or 4th)
            # Usually: 
            # 0: Seq
            # 1: Description
            # 2: Document (Link)
            # 3: Type
            # 4: Size
            
            doc_type = cells[3].get_text(strip=True)
            doc_link_tag = cells[2].find("a")
            
            if not doc_link_tag:
                continue
                
            href = doc_link_tag.get("href")
            filename = doc_link_tag.get_text(strip=True)
            
            # Simple heuristic: matches 10-K, 10-Q, 8-K
            # Or if strict, check exact type.
            # But the row type might be "10-K" or "10-K/A".
            if re.match(r"(10-K|10-Q|8-K|SC 13G|4)", doc_type, re.IGNORECASE):
                # Valid primary doc
                # href is relative to sec.gov root usually (/Archives/...)
                full_url = f"https://www.sec.gov{href}"
                return full_url, filename
                
        # Fallback: Return first .htm file if strict type match fails
        # (Sometimes Type is "EX-99.1" but we want the main one?)
        # Let's stick to strict type for now to avoid grabbing exhibits.
        
        return None
