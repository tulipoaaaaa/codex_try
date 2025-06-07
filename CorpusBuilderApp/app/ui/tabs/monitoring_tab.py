from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.section_header import SectionHeader
from shared_tools.ui_wrappers.processors.monitor_progress_wrapper import (
    MonitorProgressWrapper,
)


class MonitoringTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        card = CardWrapper()
        layout.addWidget(card)
        card.body_layout.addWidget(SectionHeader("Monitoring"))
        self.monitor_widget = MonitorProgressWrapper()
        card.body_layout.addWidget(self.monitor_widget)
