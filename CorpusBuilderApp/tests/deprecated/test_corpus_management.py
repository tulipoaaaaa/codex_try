# File: tests/integration/test_corpus_management.py

import pytest
import os
import tempfile
import json
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

from app.ui.tabs.corpus_manager_tab import CorpusManagerTab
from shared_tools.ui_wrappers.processors.quality_control_wrapper import QualityControlWrapper
from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper

class TestCorpusManagement:
    """Integration tests for corpus management functionality."""
    
    @pytest.fixture
    def mock_project_config(self):
        """Create a mock project config with real temp directories."""
        config = MagicMock()
        
        # Create temporary directories for testing
        temp_dir = tempfile.mkdtemp()
        corpus_root = os.path.join(temp_dir, "corpus")
        raw_dir = os.path.join(corpus_root, "raw")
        processed_dir = os.path.join(corpus_root, "processed")
        metadata_dir = os.path.join(corpus_root, "metadata")
        
        # Create the directories
        os.makedirs(corpus_root, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        
        # Configure the mock
        config.get_corpus_root.return_value = corpus_root
        config.get_raw_dir.return_value = raw_dir
        config.get_processed_dir.return_value = processed_dir
        config.get_metadata_dir.return_value = metadata_dir
        
        # Add test files
        test_file_path = os.path.join(raw_dir, "test_document.txt")
        with open(test_file_path, "w") as f:
            f.write("This is a test document.")
        
        # Add test metadata
        metadata_subdir = os.path.join(metadata_dir, "raw")
        os.makedirs(metadata_subdir, exist_ok=True)
        metadata_file_path = os.path.join(metadata_subdir, "test_document.json")
        with open(metadata_file_path, "w") as f:
            json.dump({
                "title": "Test Document",
                "author": "Test Author",
                "year": 2023,
                "domain": "Risk Management",
                "quality_score": 85,
                "language": "en"
            }, f)
        
        yield config
        
        # Cleanup temp directories
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def app(self, qtbot):
        """Create a QApplication instance."""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def corpus_manager(self, qtbot, mock_project_config, app):
        """Create a CorpusManagerTab instance."""
        tab = CorpusManagerTab(mock_project_config)
        qtbot.addWidget(tab)
        return tab
    
    @pytest.fixture
    def quality_control(self, mock_project_config):
        """Create a QualityControlWrapper instance."""
        return QualityControlWrapper(mock_project_config)
    
    @pytest.fixture
    def pdf_extractor(self, mock_project_config):
        """Create a PDFExtractorWrapper instance."""
        return PDFExtractorWrapper(mock_project_config)
    
    def test_corpus_file_loading(self, corpus_manager, qtbot):
        """Test loading a file in the corpus manager."""
        # Set the root directory to the corpus root
        corpus_root = corpus_manager.project_config.get_corpus_root()
        corpus_manager.set_root_directory(corpus_root)
        
        # Navigate to the raw directory in the tree view
        raw_index = corpus_manager.file_tree.model().index(0, 0, corpus_manager.file_tree.rootIndex())
        corpus_manager.file_tree.scrollTo(raw_index)
        qtbot.mouseClick(corpus_manager.file_tree.viewport(), 
                         Qt.MouseButton.LeftButton, 
                         pos=corpus_manager.file_tree.visualRect(raw_index).center())
        
        # Find and click the test file
        for i in range(corpus_manager.file_tree.model().rowCount(raw_index)):
            file_index = corpus_manager.file_tree.model().index(i, 0, raw_index)
            if corpus_manager.file_tree.model().data(file_index) == "test_document.txt":
                corpus_manager.file_tree.scrollTo(file_index)
                qtbot.mouseClick(corpus_manager.file_tree.viewport(), 
                                Qt.MouseButton.LeftButton, 
                                pos=corpus_manager.file_tree.visualRect(file_index).center())
                break
        
        # Check that the file info is updated
        assert "test_document.txt" in corpus_manager.file_name_label.text()
    
    def test_metadata_loading(self, corpus_manager, qtbot):
        """Test loading metadata for a file."""
        # Select a file with metadata
        corpus_root = corpus_manager.project_config.get_corpus_root()
        raw_dir = os.path.join(corpus_root, "raw")
        test_file_path = os.path.join(raw_dir, "test_document.txt")
        
        # Simulate file selection
        corpus_manager.on_file_selected(
            corpus_manager.file_tree.model().index(test_file_path)
        )
        
        # Check metadata table has been populated
        assert corpus_manager.metadata_model.rowCount() > 0
        
        # Find and check the domain row
        domain_row = -1
        for row in range(corpus_manager.metadata_model.rowCount()):
            if corpus_manager.metadata_model.item(row, 0).text() == "domain":
                domain_row = row
                break
        
        assert domain_row >= 0
        assert corpus_manager.metadata_model.item(domain_row, 1).text() == "Risk Management"
    
    def test_processor_integration(self, corpus_manager, quality_control, qtbot):
        """Test integration between corpus manager and processors."""
        # Mock the processor to avoid actual processing
        quality_control.processor.evaluate_quality = MagicMock(return_value=85)
        
        # Get a test file
        corpus_root = corpus_manager.project_config.get_corpus_root()
        raw_dir = os.path.join(corpus_root, "raw")
        test_file_path = os.path.join(raw_dir, "test_document.txt")
        
        # Process the file with quality control
        quality_control.start([test_file_path])
        
        # Simulate signal emission that would happen after processing
        quality_control.quality_score_calculated.emit(test_file_path, 85)
        quality_control._on_processing_completed({
            'processed_files': [{'file_path': test_file_path, 'quality_score': 85}],
            'success_count': 1,
            'fail_count': 0
        })
        
        # Now load the file in corpus manager
        corpus_manager.on_file_selected(
            corpus_manager.file_tree.model().index(test_file_path)
        )
        
        # Check if quality score is in metadata
        quality_row = -1
        for row in range(corpus_manager.metadata_model.rowCount()):
            if corpus_manager.metadata_model.item(row, 0).text() == "quality_score":
                quality_row = row
                break
        
        assert quality_row >= 0
        assert float(corpus_manager.metadata_model.item(quality_row, 1).text()) == 85
