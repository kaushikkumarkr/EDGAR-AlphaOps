CREATE TABLE IF NOT EXISTS graph_entities (
    entity_id VARCHAR PRIMARY KEY, -- uuid
    name VARCHAR NOT NULL,
    type VARCHAR, -- PERSON, ORG, EVENT, RISK
    description TEXT,
    cik VARCHAR, -- If associated with a specific company
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS graph_relations (
    relation_id VARCHAR PRIMARY KEY, -- uuid
    source_entity_id VARCHAR,
    target_entity_id VARCHAR,
    relation_type VARCHAR, -- EMPLOYED_BY, COMPETES_WITH, HAS_RISK
    description TEXT,
    chunk_id VARCHAR, -- Citation back to vector chunk
    weight DOUBLE DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_entity_id) REFERENCES graph_entities(entity_id),
    FOREIGN KEY (target_entity_id) REFERENCES graph_entities(entity_id)
);

CREATE INDEX IF NOT EXISTS idx_graph_entity_name ON graph_entities(name);
CREATE INDEX IF NOT EXISTS idx_graph_relation_src ON graph_relations(source_entity_id);
