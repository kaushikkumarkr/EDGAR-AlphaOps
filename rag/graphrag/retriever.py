from lakehouse.db import Database
from typing import List, Dict, Set
import logging

class GraphRetriever:
    def __init__(self):
        self.db = Database()
        
    def retrieve_context(self, entities: List[str], depth: int = 1) -> str:
        """
        Simple 1-hop or 2-hop retrieval starting from extracted entities in the user question.
        Returns a string context of relations.
        """
        if not entities:
            return ""
            
        conn = self.db.get_connection()
        try:
            # 1. Resolve Entity Names to IDs
            placeholders = ",".join(["?"] * len(entities))
            # Match entities loosely (LIKE or exact)
            # For exact:
            query = f"SELECT entity_id, name, description FROM graph_entities WHERE name IN ({placeholders})"
            rows = conn.execute(query, entities).fetchall()
            
            # If no exact match, try LIKE for each? (Todo for polish)
            
            if not rows:
                return "No graph entities found matching query terms."
                
            entity_ids = [r[0] for r in rows]
            context_lines = []
            
            # 2. Add Entity Descriptions
            for r in rows:
                context_lines.append(f"Entity: {r[1]} ({r[2]})")
                
            # 3. Traverse Relations (1-hop)
            if not entity_ids:
                return "\n".join(context_lines)
                
            ids_ph = ",".join([f"'{eid}'" for eid in entity_ids])
            
            rel_query = f"""
                SELECT 
                    s.name as source, 
                    r.relation_type, 
                    t.name as target,
                    r.description
                FROM graph_relations r
                JOIN graph_entities s ON r.source_entity_id = s.entity_id
                JOIN graph_entities t ON r.target_entity_id = t.entity_id
                WHERE r.source_entity_id IN ({ids_ph}) 
                   OR r.target_entity_id IN ({ids_ph})
            """
            
            rels = conn.execute(rel_query).fetchall()
            
            for rel in rels:
                context_lines.append(f"- {rel[0]} {rel[1]} {rel[2]}")
                
            return "\n".join(context_lines)
            
        except Exception as e:
            logging.error(f"Graph retrieval error: {e}")
            return "Graph Error."
        finally:
            conn.close()
