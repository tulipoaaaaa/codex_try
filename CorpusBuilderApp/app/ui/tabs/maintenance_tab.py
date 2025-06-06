from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import QThread, Signal as pyqtSignal
import subprocess

class DependencyUpgradeWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = subprocess.run(
                ["python", "upgrade_dependencies.py"],
                capture_output=True, text=True, check=True
            )
            self.finished.emit(result.stdout)
        except subprocess.CalledProcessError as e:
            self.error.emit(e.stderr or str(e))

class MaintenanceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.upgrade_btn = QPushButton("Update Dependencies")
        self.upgrade_btn.clicked.connect(self.run_upgrade)
        layout.addWidget(self.upgrade_btn)

    def run_upgrade(self):
        self.upgrade_btn.setEnabled(False)
        self.worker = DependencyUpgradeWorker()
        self.worker.finished.connect(self.on_upgrade_finished)
        self.worker.error.connect(self.on_upgrade_error)
        self.worker.start()

    def on_upgrade_finished(self, output):
        QMessageBox.information(self, "Upgrade Complete", "Dependencies updated successfully!\n\n" + output)
        self.upgrade_btn.setEnabled(True)

    def on_upgrade_error(self, error):
        QMessageBox.critical(self, "Upgrade Failed", "An error occurred during upgrade:\n\n" + error)
        self.upgrade_btn.setEnabled(True) 