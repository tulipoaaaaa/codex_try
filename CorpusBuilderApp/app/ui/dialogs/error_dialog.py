# File: app/ui/dialogs/error_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QDialogButtonBox, QCheckBox)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QFont, QIcon
from app.helpers.icon_manager import IconManager

class ErrorDialog(QDialog):
    """Dialog for displaying error messages with details."""
    
    retry_requested = pyqtSignal()
    report_requested = pyqtSignal(str, str, str)  # title, message, details
    
    def __init__(self, title, message, details=None, allow_retry=False, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.message_text = message
        self.details_text = details
        self.allow_retry = allow_retry
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle(f"Error: {self.title_text}")
        self.setMinimumWidth(500)
        icon_manager = IconManager()
        icon_path = icon_manager.get_icon_path('Warning and alert notifications', by='Function')
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(QIcon())
        
        main_layout = QVBoxLayout(self)
        
        # Error icon and message
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        if icon_path:
            icon_label.setPixmap(QIcon(icon_path).pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        message_label = QLabel(self.message_text)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 11))
        message_label.setObjectName("status-info")
        header_layout.addWidget(message_label, 1)
        
        main_layout.addLayout(header_layout)
        
        # Details section (if provided)
        if self.details_text:
            # Toggle checkbox
            self.show_details = QCheckBox("Show technical details")
            self.show_details.stateChanged.connect(self.toggle_details)
            main_layout.addWidget(self.show_details)
            
            # Details text edit
            self.details_edit = QTextEdit()
            self.details_edit.setReadOnly(True)
            self.details_edit.setPlainText(self.details_text)
            self.details_edit.setVisible(False)
            main_layout.addWidget(self.details_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        
        if self.allow_retry:
            retry_btn = QPushButton("Retry")
            retry_btn.clicked.connect(self.request_retry)
            button_box.addButton(retry_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        report_btn = QPushButton("Report Issue")
        report_btn.clicked.connect(self.report_issue)
        button_box.addButton(report_btn, QDialogButtonBox.ButtonRole.HelpRole)
        
        main_layout.addWidget(button_box)
    
    def toggle_details(self, state):
        """Toggle the visibility of the details section."""
        if hasattr(self, 'details_edit'):
            self.details_edit.setVisible(state == Qt.CheckState.Checked)
            
            # Resize dialog to fit content
            if state == Qt.CheckState.Checked:
                self.resize(self.width(), self.height() + 200)
            else:
                self.resize(self.width(), self.height() - 200)
    
    def request_retry(self):
        """Emit signal to request retry."""
        self.retry_requested.emit()
        self.accept()
    
    def report_issue(self):
        """Emit signal to report the issue."""
        self.report_requested.emit(
            self.title_text, 
            self.message_text, 
            self.details_text or ""
        )
        self.accept()
