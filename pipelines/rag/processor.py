import logging
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 150):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_html(self, html_content: str) -> List[str]:
        """
        Cleans HTML to text and chunks it.
        Returns list of text chunks.
        """
        if not html_content:
            return []

        # 1. Clean HTML
        # SEC HTML is messy.
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator="\n")
        
        # 2. Normalize whitespace
        # Collapse multiple newlines/spaces
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 3. Chunk
        docs = self.splitter.create_documents([text])
        return [d.page_content for d in docs]
