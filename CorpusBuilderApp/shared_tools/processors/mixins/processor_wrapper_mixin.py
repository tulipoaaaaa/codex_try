from PySide6.QtCore import Signal as pyqtSignal
from typing import Dict, Any

class ProcessorWrapperMixin:
    """Mixin for processor-specific functionality"""
    file_processed = pyqtSignal(str, bool)  # filepath, success

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"files_processed": 0, "success_rate": 0.0} 