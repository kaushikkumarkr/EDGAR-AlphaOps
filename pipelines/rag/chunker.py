
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True # Key for strict citations
        )

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Splits text into chunks with metadata including start/end offsets.
        """
        if not text:
            return []
            
        docs = self.splitter.create_documents([text], metadatas=[metadata or {}])
        
        chunks = []
        for doc in docs:
            # doc.metadata has 'start_index' from langchain
            start = doc.metadata.get("start_index", 0)
            content = doc.page_content
            end = start + len(content)
            
            chunk_meta = doc.metadata.copy()
            chunk_meta.update({
                "text": content,
                "start_index": start,
                "end_index": end
            })
            
            chunks.append(chunk_meta)
            
        return chunks
