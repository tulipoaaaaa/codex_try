from PySide6.QtWidgets import QWidget, QVBoxLayout
from shared_tools.ui_wrappers.processors.monitor_progress_wrapper import MonitorProgressWrapper

class MonitoringTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.monitor_widget = MonitorProgressWrapper()
        layout.addWidget(self.monitor_widget) 