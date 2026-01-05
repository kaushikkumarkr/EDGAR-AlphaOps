
import logging
import networkx as nx
from sqlalchemy.orm import Session
from pipelines.models import Filing, Company
from pipelines.storage import MinIOClient
from pipelines.graph.extractor import EntityExtractor

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.extractor = EntityExtractor()
        self.storage = MinIOClient()
        self.graph = nx.DiGraph()

    def build_graph(self, limit: int = 50):
        """Builds a knowledge graph from processed filings."""
        logger.info("Building Knowledge Graph...")
        
        # 1. Fetch Filings
        filings = self.db.query(Filing).filter(Filing.state == "PROCESSED").limit(limit).all()
        
        for f in filings:
            # Identify Source Node
            # Try to get Ticker from Company table, else use CIK
            company = self.db.query(Company).filter_by(cik=f.cik).first()
            source_label = company.ticker if (company and company.ticker) else f.cik
            
            self.graph.add_node(source_label, type="company", cik=f.cik, accession=f.accession_number)
            
            # 2. Extract Relations
            # We read text (first 20k chars usually contains Intro/Competition)
            if f.s3_path:
                try:
                    data = self.storage.get_object(f.s3_path)
                    # Decode
                    text = data.decode("utf-8", errors="ignore")[:20000] 
                    
                    # Extract
                    targets = self.extractor.extract_entities(text)
                    
                    for target in targets:
                        # Add Edge: Source -> Target (MENTIONS)
                        # We don't know target properties yet, just add node
                        if target != source_label:
                            self.graph.add_node(target, type="entity")
                            self.graph.add_edge(source_label, target, relation="MENTIONS")
                            
                except Exception as e:
                    logger.warning(f"Failed to process graph for {f.accession_number}: {e}")
                    continue
        
        logger.info(f"Graph Built: {self.graph.number_of_nodes()} Nodes, {self.graph.number_of_edges()} Edges")
        return self.graph

    def get_network_json(self):
        """Returns node-link format for visualization."""
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        return nx.node_link_data(self.graph)
