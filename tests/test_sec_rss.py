import pytest
from unittest.mock import MagicMock, patch
from pipelines.sec.rss import RssWatcher

@pytest.fixture
def mock_feed():
    return """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Latest Filings</title>
  <entry>
    <title>10-K - APPLE INC (0000320193) (Filer)</title>
    <link href="https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/0000320193-24-000001-index.htm" rel="alternate"/>
    <summary type="html">Summary of 10-K</summary>
    <updated>2024-01-01T10:00:00-05:00</updated>
    <category term="10-K" label="form type"/>
    <id>urn:tag:sec.gov,2008:accession-number=0000320193-24-000001</id>
  </entry>
</feed>
"""

@patch("pipelines.sec.rss.SecClient")
@patch("pipelines.sec.rss.Database")
@patch("pipelines.sec.rss.feedparser")
def test_rss_cycle(mock_feedparser, MockDatabase, MockSecClient):
    # Setup Mocks
    mock_db = MockDatabase.return_value
    mock_conn = mock_db.get_connection.return_value
    mock_conn.execute.return_value.fetchone.return_value = None
    
    mock_client = MockSecClient.return_value
    mock_client.get_rss_feed.return_value = b"some bytes"
    mock_client.get_filing_html.return_value = "<html>Test Doc</html>"
    
    # Mock Feedparser Result
    mock_entry = MagicMock()
    mock_entry.title = "10-K - APPLE INC (0000320193) (Filer)"
    mock_entry.link = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/0000320193-24-000001-index.htm"
    # id typically has the accession
    mock_entry.id = "urn:tag:sec.gov,2008:accession-number=0000320193-24-000001"
    mock_entry.updated = "2024-01-01T10:00:00-05:00"
    mock_entry.category = "10-K" # category field
    # feedparser entries can be accessed as dict or object. 
    # MagicMock allows attribute access which rss.py uses (entry.id, entry.title)
    # But rss.py also uses entry.get("category", "")
    # So we need to support .get()
    mock_entry.get.side_effect = lambda k, d=None: "10-K" if k == "category" else d
    
    mock_feed_obj = MagicMock()
    mock_feed_obj.entries = [mock_entry]
    mock_feedparser.parse.return_value = mock_feed_obj
    
    # Init Watcher
    watcher = RssWatcher()
    # Mock directory creation
    with patch("pathlib.Path.mkdir"):
        # We still need to mock open because watcher writes files
        from unittest.mock import mock_open
        m = mock_open()
        with patch("builtins.open", m):
            watcher.run_cycle()
            
    # Verify processing
    # Should have called get_rss_feed
    mock_client.get_rss_feed.assert_called_once()
    
    # Should have checked DB for accession 0000320193-24-000001
    mock_conn.execute.assert_any_call("SELECT 1 FROM filings WHERE accession_number = ?", ["0000320193-24-000001"])
    
    # Should have inserted metadata
    # We check if insert query was called.
    insert_call = [call for call in mock_conn.execute.call_args_list if "INSERT INTO filings" in str(call)]
    assert len(insert_call) > 0
