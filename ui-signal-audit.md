# UI Signal Audit

This report summarizes Qt signals, slots, and emit calls found in the repository.

## Counts
- `pyqtSignal`: 197 occurrences
- `pyqtSlot`: 114 occurrences
- `.emit(`: 222 occurrences

## Example Signal Definitions
CorpusBuilderApp/tests/test_domain_classifier_wrapper.py:20:from PySide6.QtCore import QObject, Signal as pyqtSignal
CorpusBuilderApp/shared_tools/processors/mixins/processor_wrapper_mixin.py:1:from PySide6.QtCore import Signal as pyqtSignal
CorpusBuilderApp/shared_tools/processors/mixins/processor_wrapper_mixin.py:6:    file_processed = pyqtSignal(str, bool)  # filepath, success
CorpusBuilderApp/shared_tools/storage/corpus_manager.py:7:from PySide6.QtCore import QObject, Signal as pyqtSignal

## Example Slot Definitions
CorpusBuilderApp/shared_tools/ui_wrappers/processors/batch_nonpdf_extractor_enhanced_wrapper.py:9:from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QMutex, QTimer
CorpusBuilderApp/shared_tools/ui_wrappers/processors/batch_nonpdf_extractor_enhanced_wrapper.py:210:    @pyqtSlot()
CorpusBuilderApp/shared_tools/ui_wrappers/processors/batch_nonpdf_extractor_enhanced_wrapper.py:222:    @pyqtSlot()
CorpusBuilderApp/shared_tools/ui_wrappers/processors/batch_nonpdf_extractor_enhanced_wrapper.py:234:    @pyqtSlot()

## Example Emit Calls
CorpusBuilderApp/shared_tools/storage/corpus_manager.py:68:            self.progress_updated.emit(progress, f"Copying: {src.name}", {})
CorpusBuilderApp/shared_tools/storage/corpus_manager.py:69:        self.status_updated.emit("Copy completed")
CorpusBuilderApp/shared_tools/storage/corpus_manager.py:70:        self.operation_completed.emit("copy")
CorpusBuilderApp/shared_tools/storage/corpus_manager.py:87:            self.progress_updated.emit(progress, f"Moving: {src.name}", {})
