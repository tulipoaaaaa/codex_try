# File: shared_tools/ui_wrappers/processors/domain_classifier_wrapper.py

from PySide6.QtCore import Signal as pyqtSignal, QThread
from shared_tools.processors.domain_classifier import DomainClassifier
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin

class DomainClassifierWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for the Domain Classifier processor."""
    
    document_classified = pyqtSignal(str, str, float)  # doc_id, domain, confidence
    
    def __init__(self, project_config):
        super().__init__(project_config)
        self.processor = DomainClassifier(project_config)
        self._is_running = False
        self.worker_thread = None
        
    def start(self, documents=None, **kwargs):
        """Start domain classification on the specified documents."""
        if self._is_running:
            self.status_updated.emit("Domain classification already in progress")
            return False
            
        self._is_running = True
        self.status_updated.emit("Starting domain classification...")
        
        # Create and configure worker thread
        self.worker_thread = DomainClassifierWorkerThread(
            self.processor, 
            documents,
            **kwargs
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.document_classified.connect(self._on_document_classified)
        self.worker_thread.processing_completed.connect(self._on_processing_completed)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        # Start the thread
        self.worker_thread.start()
        return True
        
    def stop(self):
        """Stop the domain classification processing."""
        if not self._is_running:
            return False
            
        if self.worker_thread:
            self.worker_thread.requestInterruption()
            self.status_updated.emit("Stopping domain classification...")
            
        return True
        
    def get_status(self):
        """Get the current status of the processor."""
        return {
            "is_running": self._is_running,
            "processor_type": "domain_classifier"
        }
        
    def _on_document_classified(self, doc_id, domain, confidence):
        """Handle document classification result."""
        self.document_classified.emit(doc_id, domain, confidence)
        
    def _on_processing_completed(self, results):
        """Handle completion of domain classification."""
        self._is_running = False
        self.batch_completed.emit(results)
        self.status_updated.emit(
            f"Domain classification completed: {len(results)} documents classified"
        )

class DomainClassifierWorkerThread(QThread):
    """Worker thread for domain classification processing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    document_classified = pyqtSignal(str, str, float)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, documents, **kwargs):
        super().__init__()
        self.processor = processor
        self.documents = documents or {}
        self.kwargs = kwargs
        
    def run(self):
        """Run the domain classification processing."""
        try:
            results = {}
            total_docs = len(self.documents)
            
            for i, (doc_id, doc_data) in enumerate(self.documents.items()):
                # Check for interruption
                if self.isInterruptionRequested():
                    break
                    
                # Update progress
                progress = int(((i + 1) / total_docs) * 100) if total_docs > 0 else 100
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Classifying document {doc_id}...")
                
                try:
                    # Extract text and title
                    text = doc_data.get('text', '')
                    title = doc_data.get('metadata', {}).get('title', None)
                    
                    # Classify the document
                    classification = self.processor.classify(text, title)
                    
                    # Emit the classification result
                    domain = classification.get('domain', 'unknown')
                    confidence = classification.get('confidence', 0.0)
                    self.document_classified.emit(doc_id, domain, confidence)
                    
                    # Store result
                    results[doc_id] = classification
                    
                except Exception as e:
                    self.status_updated.emit(f"Error classifying {doc_id}: {str(e)}")
                    results[doc_id] = {"domain": "unknown", "confidence": 0, "error": str(e)}
            
            # Complete processing
            self.processing_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Domain classification error: {str(e)}")
