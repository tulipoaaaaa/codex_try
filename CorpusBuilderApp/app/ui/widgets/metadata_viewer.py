# File: app/ui/widgets/metadata_viewer.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableView, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

class MetadataTableModel(QAbstractTableModel):
    """Table model for displaying and editing metadata."""
    
    def __init__(self, metadata=None, parent=None):
        super().__init__(parent)
        self._metadata = []
        self._headers = ["Property", "Value"]
        
        if metadata:
            self.set_metadata(metadata)
    
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows."""
        return len(self._metadata)
    
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns."""
        return 2
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Return the data at the given index."""
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            
            if row < 0 or row >= len(self._metadata):
                return None
                
            if col == 0:
                return self._metadata[row][0]  # Property
            elif col == 1:
                return self._metadata[row][1]  # Value
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Return the header data."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
        
        return None
    
    def flags(self, index):
        """Return the item flags."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        # Make the value column editable
        if index.column() == 1:
            flags |= Qt.ItemFlag.ItemIsEditable
        
        return flags
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Set the data at the given index."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row = index.row()
        col = index.column()
        
        if row < 0 or row >= len(self._metadata) or col != 1:
            return False
            
        # Update the value
        self._metadata[row] = (self._metadata[row][0], value)
        
        # Emit data changed signal
        self.dataChanged.emit(index, index)
        return True
    
    def set_metadata(self, metadata):
        """Set the metadata to display."""
        self.beginResetModel()
        
        # Convert dictionary to list of tuples
        if isinstance(metadata, dict):
            self._metadata = list(metadata.items())
        else:
            self._metadata = metadata
            
        self.endResetModel()
    
    def get_metadata(self):
        """Get the metadata as a dictionary."""
        return {k: v for k, v in self._metadata}
    
    def add_property(self, property_name, value=""):
        """Add a new property."""
        self.beginInsertRows(QModelIndex(), len(self._metadata), len(self._metadata))
        self._metadata.append((property_name, value))
        self.endInsertRows()
        return True
    
    def remove_property(self, row):
        """Remove a property."""
        if row < 0 or row >= len(self._metadata):
            return False
            
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._metadata[row]
        self.endRemoveRows()
        return True

class AddPropertyDialog(QDialog):
    """Dialog for adding a new metadata property."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle("Add Metadata Property")
        self.setMinimumWidth(300)
        
        layout = QFormLayout(self)
        
        # Property name
        self.property_name = QLineEdit()
        layout.addRow("Property Name:", self.property_name)
        
        # Property value
        self.property_value = QLineEdit()
        layout.addRow("Value:", self.property_value)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    
    def get_property(self):
        """Get the property name and value."""
        return self.property_name.text(), self.property_value.text()

class MetadataViewer(QWidget):
    """Widget for viewing and editing metadata."""
    
    metadata_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Metadata Viewer")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.add_btn = QPushButton("Add Property")
        self.add_btn.clicked.connect(self.add_property)
        header_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove Property")
        self.remove_btn.clicked.connect(self.remove_property)
        header_layout.addWidget(self.remove_btn)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_metadata)
        header_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(header_layout)
        
        # Table view
        self.metadata_model = MetadataTableModel()
        
        self.metadata_table = QTableView()
        self.metadata_table.setModel(self.metadata_model)
        self.metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        main_layout.addWidget(self.metadata_table)
        
        # Disable buttons initially
        self.add_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
    
    def set_file(self, file_path, metadata=None):
        """Set the current file and metadata."""
        self.current_file = file_path
        
        if file_path:
            self.title_label.setText(f"Metadata: {os.path.basename(file_path)}")
            self.add_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            if metadata:
                self.metadata_model.set_metadata(metadata)
        else:
            self.title_label.setText("Metadata Viewer")
            self.add_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            
            # Clear the model
            self.metadata_model.set_metadata({})
    
    def add_property(self):
        """Add a new metadata property."""
        dialog = AddPropertyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            property_name, property_value = dialog.get_property()
            if property_name:
                self.metadata_model.add_property(property_name, property_value)
    
    def remove_property(self):
        """Remove the selected metadata property."""
        indexes = self.metadata_table.selectionModel().selectedRows()
        if not indexes:
            return
            
        row = indexes[0].row()
        property_name = self.metadata_model.data(self.metadata_model.index(row, 0))
        
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the property '{property_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.metadata_model.remove_property(row)
    
    def save_metadata(self):
        """Save the metadata."""
        if not self.current_file:
            return
            
        metadata = self.metadata_model.get_metadata()
        self.metadata_changed.emit(metadata)
        
        QMessageBox.information(
            self,
            "Metadata Saved",
            "Metadata has been updated successfully."
        )
    
    def get_metadata(self):
        """Get the current metadata."""
        return self.metadata_model.get_metadata()
