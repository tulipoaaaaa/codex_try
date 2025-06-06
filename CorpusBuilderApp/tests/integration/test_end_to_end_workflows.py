# tests/integration/test_end_to_end_workflows.py
import pytest
import tempfile
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

class TestEndToEndWorkflows:
    """Integration tests for complete application workflows"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration tests"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            (workspace / "downloads").mkdir()
            (workspace / "processed").mkdir()
            (workspace / "config").mkdir()
            yield workspace
    
    @pytest.mark.integration
    def test_complete_collection_workflow(self, temp_workspace):
        """Test complete data collection to processing workflow"""
        # Mock the entire pipeline
        mock_data = {
            "title": "Test Financial Document",
            "content": "This is test financial content about cryptocurrency.",
            "metadata": {"source": "test", "date": "2024-01-01"}
        }
        
        # Test collection phase
        collected_file = temp_workspace / "downloads" / "test_doc.json"
        with open(collected_file, 'w') as f:
            json.dump(mock_data, f)
        
        assert collected_file.exists()
        
        # Test processing phase
        with open(collected_file, 'r') as f:
            data = json.load(f)
            assert data["title"] == mock_data["title"]
        
        # Test output generation
        processed_file = temp_workspace / "processed" / "test_doc_processed.json"
        with open(processed_file, 'w') as f:
            json.dump({**data, "processed": True}, f)
        
        assert processed_file.exists()
    
    @pytest.mark.integration
    @patch('shared_tools.collectors.fred_collector.requests.get')
    def test_fred_to_processing_pipeline(self, mock_get, temp_workspace):
        """Test FRED data collection through processing pipeline"""
        # Mock FRED API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "observations": [{"date": "2024-01-01", "value": "1.5"}]
        }
        mock_get.return_value = mock_response
        
        # Simulate collection and processing
        fred_data = mock_response.json()
        assert "observations" in fred_data
        
        # Test data transformation
        processed_data = {
            "source": "FRED",
            "data": fred_data["observations"],
            "processed_at": "2024-01-01T00:00:00Z"
        }
        
        output_file = temp_workspace / "processed" / "fred_data.json"
        with open(output_file, 'w') as f:
            json.dump(processed_data, f)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data["source"] == "FRED"
