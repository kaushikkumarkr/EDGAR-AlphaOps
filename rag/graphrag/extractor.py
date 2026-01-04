import logging
import uuid
import json
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from lakehouse.db import Database
from config import get_settings

settings = get_settings()

class GraphExtractor:
    def __init__(self):
        self.db = Database()
        # Use local LLM
        self.llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model=settings.MODEL_NAME,
            temperature=0.0
        )
        
    def process_document(self, cik: str, chunks: List[str]) -> None:
        """
        Extract entities and relations from text chunks and save to DB.
        """
        logging.info(f"Extracting graph from {len(chunks)} chunks for CIK {cik}...")
        
        # For MVP, process a subset or aggregate to avoid too many LLM calls if slow
        # Let's process top 3 chunks or summary for demo speed, or all if feasible.
        # We will process the first 5 chunks as a sample for Sprint 7 demo.
        sample_chunks = chunks[:5] 
        
        for i, text in enumerate(sample_chunks):
            try:
                self._extract_and_save(cik, text, f"chunk_{i}")
            except Exception as e:
                logging.error(f"Graph extraction failed for chunk {i}: {e}")

    def _extract_and_save(self, cik: str, text: str, chunk_id: str):
        # Prompt
        # LangChain prompts treat {var} as variables. We must escape JSON braces as {{ }}.
        system_prompt = """You are an expert financial analyst. Extract entities (Companies, People, Risks, Products) and relationships (COMPETES_WITH, LAUNCHED, HAS_RISK, LED_BY) from the text.
        Return JSON format:
        {{
            "entities": [{{"name": "Apple", "type": "ORG", "description": "Tech company"}}],
            "relations": [{{"source": "Apple", "target": "Tim Cook", "type": "LED_BY"}}]
        }}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", text)
        ])
        
        chain = prompt | self.llm
        
        # Invoke
        response = chain.invoke({})
        content = response.content
        
        # Parse JSON (naive)
        try:
            # Clean markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content)
            
            self._save_graph_data(cik, data, chunk_id)
            
        except Exception as e:
            logging.warning(f"Failed to parse LLM graph output: {e}")

    def _save_graph_data(self, cik: str, data: Dict, chunk_id: str):
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        
        conn = self.db.get_connection()
        try:
            # 1. Save Entities
            entity_map = {} # Name -> ID
            
            for ent in entities:
                name = ent["name"]
                etype = ent["type"]
                desc = ent.get("description", "")
                
                # Check exist
                existing = conn.execute("SELECT entity_id FROM graph_entities WHERE name = ?", [name]).fetchone()
                if existing:
                    e_id = existing[0]
                else:
                    e_id = str(uuid.uuid4())
                    conn.execute("INSERT INTO graph_entities (entity_id, name, type, description, cik) VALUES (?, ?, ?, ?, ?)", 
                                 [e_id, name, etype, desc, cik])
                
                entity_map[name] = e_id
                
            # 2. Save Relations
            for rel in relations:
                src = rel["source"]
                tgt = rel["target"]
                rtype = rel["type"]
                
                if src in entity_map and tgt in entity_map:
                    conn.execute("""
                        INSERT INTO graph_relations (relation_id, source_entity_id, target_entity_id, relation_type, chunk_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, [str(uuid.uuid4()), entity_map[src], entity_map[tgt], rtype, chunk_id])
                    
        finally:
            conn.close()
