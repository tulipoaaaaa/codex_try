# File: app/ui/widgets/file_browser.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
                             QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox,
                             QFileDialog, QMenu, QInputDialog, QFileSystemModel)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QDir, QSortFilterProxyModel, QMimeData, QUrl
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QIcon
import os
import shutil
from app.helpers.icon_manager import IconManager

class FileBrowser(QWidget):
    """Reusable file browser widget with drag-and-drop support."""
    
    file_selected = pyqtSignal(str)  # file_path
    files_dropped = pyqtSignal(list)  # list of file paths
    directory_changed = pyqtSignal(str)  # directory_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.current_directory = QDir.homePath()
        self.setup_ui()
        self.setup_file_model()
        
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        icon_manager = IconManager()
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        # Back/Forward/Up buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setMaximumWidth(30)
        self.back_btn.clicked.connect(self.go_back)
        back_icon = icon_manager.get_icon_path('Start/play operation control', by='Function')
        if back_icon:
            self.back_btn.setIcon(QIcon(back_icon))
        nav_layout.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton("→")
        self.forward_btn.setMaximumWidth(30)
        self.forward_btn.clicked.connect(self.go_forward)
        forward_icon = icon_manager.get_icon_path('Next/forward navigation control', by='Function')
        if forward_icon:
            self.forward_btn.setIcon(QIcon(forward_icon))
        nav_layout.addWidget(self.forward_btn)
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setMaximumWidth(30)
        self.up_btn.clicked.connect(self.go_up)
        up_icon = icon_manager.get_icon_path('Data collection and processing', by='Function')
        if up_icon:
            self.up_btn.setIcon(QIcon(up_icon))
        nav_layout.addWidget(self.up_btn)
        
        # Address bar
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.navigate_to_address)
        nav_layout.addWidget(self.address_bar)
        
        # Browse button
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_directory)
        browse_icon = icon_manager.get_icon_path('File management and organization', by='Function')
        if browse_icon:
            self.browse_btn.setIcon(QIcon(browse_icon))
        nav_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(nav_layout)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search files...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All Files", "Documents", "Images", "Text Files", "PDF Files"])
        self.filter_type.currentTextChanged.connect(self.apply_type_filter)
        filter_layout.addWidget(self.filter_type)
        
        main_layout.addLayout(filter_layout)
        
        # File tree view
        self.tree_view = QTreeView()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.on_item_clicked)
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # Enable drag and drop
        self.tree_view.setDragDropMode(QTreeView.DragDropMode.DropOnly)
        self.tree_view.setAcceptDrops(True)
        self.setAcceptDrops(True)
        
        main_layout.addWidget(self.tree_view)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # History for navigation
        self.history = []
        self.history_index = -1
        
    def setup_file_model(self):
        """Set up the file system model."""
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        
        # Proxy model for filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        self.tree_view.setModel(self.proxy_model)
        
        # Set initial directory
        self.set_directory(self.current_directory)
        
    def set_directory(self, directory_path):
        """Set the current directory."""
        if os.path.isdir(directory_path):
            self.current_directory = directory_path
            self.address_bar.setText(directory_path)
            
            # Set root index
            source_index = self.file_model.index(directory_path)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.tree_view.setRootIndex(proxy_index)
            
            # Update navigation history
            if self.history_index == -1 or self.history[self.history_index] != directory_path:
                # Remove any forward history
                self.history = self.history[:self.history_index + 1]
                self.history.append(directory_path)
                self.history_index += 1
            
            self.update_navigation_buttons()
            self.directory_changed.emit(directory_path)
            self.status_label.setText(f"Current directory: {directory_path}")
            
    def navigate_to_address(self):
        """Navigate to the address in the address bar."""
        address = self.address_bar.text()
        if os.path.isdir(address):
            self.set_directory(address)
        else:
            QMessageBox.warning(self, "Invalid Path", f"The path '{address}' is not a valid directory.")
            self.address_bar.setText(self.current_directory)
            
    def browse_directory(self):
        """Open directory browser dialog."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.current_directory
        )
        if directory:
            self.set_directory(directory)
            
    def go_back(self):
        """Navigate back in history."""
        if self.history_index > 0:
            self.history_index -= 1
            directory = self.history[self.history_index]
            self.current_directory = directory
            self.address_bar.setText(directory)
            
            source_index = self.file_model.index(directory)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.tree_view.setRootIndex(proxy_index)
            
            self.update_navigation_buttons()
            self.directory_changed.emit(directory)
            
    def go_forward(self):
        """Navigate forward in history."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            directory = self.history[self.history_index]
            self.current_directory = directory
            self.address_bar.setText(directory)
            
            source_index = self.file_model.index(directory)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.tree_view.setRootIndex(proxy_index)
            
            self.update_navigation_buttons()
            self.directory_changed.emit(directory)
            
    def go_up(self):
        """Navigate to parent directory."""
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir != self.current_directory:
            self.set_directory(parent_dir)
            
    def update_navigation_buttons(self):
        """Update the state of navigation buttons."""
        self.back_btn.setEnabled(self.history_index > 0)
        self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)
        self.up_btn.setEnabled(os.path.dirname(self.current_directory) != self.current_directory)
        
    def apply_filter(self):
        """Apply text filter to file view."""
        filter_text = self.filter_input.text()
        self.proxy_model.setFilterFixedString(filter_text)
        
    def apply_type_filter(self):
        """Apply file type filter."""
        filter_type = self.filter_type.currentText()
        
        if filter_type == "All Files":
            self.proxy_model.setFilterRegularExpression("")
        elif filter_type == "Documents":
            self.proxy_model.setFilterRegularExpression(r".*\.(doc|docx|pdf|txt|rtf)$")
        elif filter_type == "Images":
            self.proxy_model.setFilterRegularExpression(r".*\.(jpg|jpeg|png|gif|bmp|svg)$")
        elif filter_type == "Text Files":
            self.proxy_model.setFilterRegularExpression(r".*\.(txt|md|csv|json|xml)$")
        elif filter_type == "PDF Files":
            self.proxy_model.setFilterRegularExpression(r".*\.pdf$")
            
    def on_item_clicked(self, index):
        """Handle item click."""
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        if self.file_model.isDir(source_index):
            self.status_label.setText(f"Directory: {file_path}")
        else:
            self.status_label.setText(f"File: {file_path}")
            self.file_selected.emit(file_path)
            
    def on_item_double_clicked(self, index):
        """Handle item double click."""
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        if self.file_model.isDir(source_index):
            self.set_directory(file_path)
            
    def show_context_menu(self, position):
        """Show context menu for files/directories."""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        icon_manager = IconManager()
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        is_dir = self.file_model.isDir(source_index)
        menu = QMenu(self)
        if is_dir:
            open_action = QAction("Open", self)
            open_icon = icon_manager.get_icon_path('File management and organization', by='Function')
            if open_icon:
                open_action.setIcon(QIcon(open_icon))
            open_action.triggered.connect(lambda: self.set_directory(file_path))
            menu.addAction(open_action)
            new_folder_action = QAction("New Folder", self)
            folder_icon = icon_manager.get_icon_path('Data collection and processing', by='Function')
            if folder_icon:
                new_folder_action.setIcon(QIcon(folder_icon))
            new_folder_action.triggered.connect(lambda: self.create_new_folder(file_path))
            menu.addAction(new_folder_action)
        else:
            open_action = QAction("Open", self)
            open_icon = icon_manager.get_icon_path('File management and organization', by='Function')
            if open_icon:
                open_action.setIcon(QIcon(open_icon))
            open_action.triggered.connect(lambda: self.open_file(file_path))
            menu.addAction(open_action)
        menu.addSeparator()
        copy_action = QAction("Copy Path", self)
        copy_icon = icon_manager.get_icon_path('File management and organization', by='Function')
        if copy_icon:
            copy_action.setIcon(QIcon(copy_icon))
        copy_action.triggered.connect(lambda: self.copy_path_to_clipboard(file_path))
        menu.addAction(copy_action)
        delete_action = QAction("Delete", self)
        delete_icon = icon_manager.get_icon_path('Warning and alert notifications', by='Function')
        if delete_icon:
            delete_action.setIcon(QIcon(delete_icon))
        delete_action.triggered.connect(lambda: self.delete_item(file_path))
        menu.addAction(delete_action)
        menu.exec(self.tree_view.mapToGlobal(position))
        
    def create_new_folder(self, parent_path):
        """Create a new folder."""
        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:"
        )
        if ok and folder_name:
            new_folder_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(new_folder_path)
                self.status_label.setText(f"Created folder: {new_folder_path}")
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {str(e)}")
                
    def open_file(self, file_path):
        """Open file with default application."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        
    def copy_path_to_clipboard(self, file_path):
        """Copy file path to clipboard."""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(file_path)
        self.status_label.setText("Path copied to clipboard")
        
    def delete_item(self, file_path):
        """Delete file or directory."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete:\n{file_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.status_label.setText(f"Deleted: {file_path}")
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {str(e)}")
                
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        file_paths = []
        
        for url in urls:
            if url.isLocalFile():
                file_paths.append(url.toLocalFile())
                
        if file_paths:
            self.files_dropped.emit(file_paths)
            self.status_label.setText(f"Dropped {len(file_paths)} file(s)")
            
        event.acceptProposedAction()
        
    def get_current_directory(self):
        """Get the current directory path."""
        return self.current_directory
        
    def get_selected_files(self):
        """Get list of selected file paths."""
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        selected_files = []
        
        for index in selected_indexes:
            if index.column() == 0:  # Only process the first column
                source_index = self.proxy_model.mapToSource(index)
                file_path = self.file_model.filePath(source_index)
                if not self.file_model.isDir(source_index):
                    selected_files.append(file_path)
                    
        return selected_files
