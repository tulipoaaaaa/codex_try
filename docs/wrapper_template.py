from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
# from shared_tools.processors.YOUR_PROCESSOR import YourProcessor

class YourProcessorWrapper(QWidget):
    """
    Template for UI wrapper for a processor.
    - Inherit ONLY from QWidget
    - No BaseWrapper, no ProcessorMixin, no super() calls
    - Use explicit delegation for all signals, properties, and methods
    - Store config directly
    - Set up UI in setup_ui()
    """

    # Define all signals you need to expose
    example_signal = Signal(str)
    # ... add more signals as needed ...

    def __init__(self, project_config, parent=None, **kwargs):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("YourProcessorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        # self._processor = YourProcessor(project_config=project_config)
        # ... initialize any other state ...
        self._is_running = False
        self.worker_thread = None
        # ... add more state as needed ...
        self.setup_ui()

    # --- Properties to Delegate ---
    @property
    def config(self):
        return self._processor.config
    # ... add more properties as needed ...

    # --- Methods to Delegate ---
    def start(self, *args, **kwargs):
        self._is_running = True
        if hasattr(self._processor, 'start'):
            return self._processor.start(*args, **kwargs)
        return None
    # ... add more methods as needed ...

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Add your UI components here
        # (Preserve any previous UI logic here)
