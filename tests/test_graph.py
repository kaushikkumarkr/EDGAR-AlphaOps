
import pytest
import networkx as nx
from unittest.mock import MagicMock, patch
from pipelines.graph.extractor import EntityExtractor
from pipelines.graph.builder import GraphBuilder
from pipelines.models import Filing, Company

def test_entity_extractor():
    extractor = EntityExtractor()
    text = "We compete with $GOOGL and $AMZN significantly."
    entities = extractor.extract_entities(text)
    
    assert "GOOGL" in entities
    assert "AMZN" in entities
    assert len(entities) == 2

def test_graph_builder(db_session):
    # Setup Data
    filing = Filing(accession_number="001", cik="1", state="PROCESSED", s3_path="test/path")
    company = Company(cik="1", ticker="ME")
    db_session.add_all([filing, company])
    db_session.commit()
    
    # Mock Storage
    with patch("pipelines.graph.builder.MinIOClient") as MockStorage:
        mock_cli = MagicMock()
        # Mock text content returning a mention
        mock_cli.get_object.return_value = b"Referencing $TSLA here."
        MockStorage.return_value = mock_cli
        
        builder = GraphBuilder(db_session)
        graph = builder.build_graph(limit=1)
        
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() >= 2 # ME and TSLA
        assert graph.has_edge("ME", "TSLA")
        
        json_data = builder.get_network_json()
        assert "nodes" in json_data
        # NetworkX < 3.0 uses 'links', newer might use 'edges' or configurable.
        # The output showed 'edges'.
        assert "edges" in json_data or "links" in json_data
