from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QTreeView, QGroupBox, QTextEdit, QPushButton, 
                             QLabel, QLineEdit, QFileDialog, QComboBox,
                             QTableView, QHeaderView, QMenu, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QDialogButtonBox,
                             QProgressBar, QInputDialog, QFileSystemModel)
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtCore import Qt, QDir, QSortFilterProxyModel, QModelIndex, Slot as pyqtSlot, QPoint, QThread, Signal as pyqtSignal, QMimeData, QTimer, QMutex
import os
import json
import shutil
import time
from typing import List, Dict, Any
from app.helpers.icon_manager import IconManager
from app.helpers.notifier import Notifier

class NotificationManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notifications = {}
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("System Notifications")
        header.setObjectName("notifications-header")
        layout.addWidget(header)
        self.notification_area = QVBoxLayout()
        layout.addLayout(self.notification_area)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all_notifications)
        layout.addWidget(self.clear_btn)
    def add_notification(self, notification_id: str, title: str, message: str, notification_type: str = "info", auto_hide: bool = False):
        notification_widget = QLabel(f"<b>{title}</b>: {message}")
        self.notification_area.addWidget(notification_widget)
        self.active_notifications[notification_id] = notification_widget
        if auto_hide:
            QTimer.singleShot(5000, lambda: self.remove_notification(notification_id))
    def update_notification(self, notification_id: str, message: str, progress: int = 0):
        if notification_id in self.active_notifications:
            self.active_notifications[notification_id].setText(message)
    def remove_notification(self, notification_id: str):
        if notification_id in self.active_notifications:
            widget = self.active_notifications[notification_id]
            self.notification_area.removeWidget(widget)
            widget.deleteLater()
            del self.active_notifications[notification_id]
    def clear_all_notifications(self):
        for notification_id in list(self.active_notifications.keys()):
            self.remove_notification(notification_id)

class BatchMetadataEditor(QDialog):
    def __init__(self, file_paths: List[str], parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle(f"Batch Edit Metadata ({len(self.file_paths)} files)")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)
        instructions = QLabel(f"Edit metadata for {len(self.file_paths)} selected files. Leave fields empty to skip updating that field.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        form_layout = QFormLayout()
        self.domain_edit = QLineEdit()
        form_layout.addRow("Domain:", self.domain_edit)
        self.author_edit = QLineEdit()
        form_layout.addRow("Author:", self.author_edit)
        self.year_edit = QLineEdit()
        form_layout.addRow("Year:", self.year_edit)
        self.source_edit = QLineEdit()
        form_layout.addRow("Source:", self.source_edit)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        form_layout.addRow("Tags:", self.tags_edit)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Notes:", self.notes_edit)
        layout.addLayout(form_layout)
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        self.overwrite_cb = QCheckBox("Overwrite existing values")
        self.overwrite_cb.setChecked(False)
        options_layout.addWidget(self.overwrite_cb)
        layout.addWidget(options_group)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    def get_metadata_updates(self) -> Dict[str, Any]:
        updates = {}
        if self.domain_edit.text().strip():
            updates['domain'] = self.domain_edit.text().strip()
        if self.author_edit.text().strip():
            updates['author'] = self.author_edit.text().strip()
        if self.year_edit.text().strip():
            updates['year'] = self.year_edit.text().strip()
        if self.source_edit.text().strip():
            updates['source'] = self.source_edit.text().strip()
        if self.tags_edit.text().strip():
            tags = [tag.strip() for tag in self.tags_edit.text().split(',')]
            updates['tags'] = tags
        if self.notes_edit.toPlainText().strip():
            updates['notes'] = self.notes_edit.toPlainText().strip()
        return updates
    def should_overwrite(self) -> bool:
        return self.overwrite_cb.isChecked()

class BatchOperationWorker(QThread):
    """Worker thread for batch operations on corpus files"""
    
    progress_updated = pyqtSignal(int, str, dict)  # progress, message, stats
    file_processed = pyqtSignal(str, str, bool, str)  # operation, file_path, success, message
    operation_completed = pyqtSignal(str, dict)  # operation_type, final_stats
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    def __init__(self, operation: str, files: List[str], target_path: str = "", options: Dict[str, Any] = None):
        super().__init__()
        self.operation = operation
        self.files = files
        self.target_path = target_path
        self.options = options or {}
        self._is_cancelled = False
        self._mutex = QMutex()
        self.stats = {
            'total_files': len(files),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'total_size': 0,
            'processed_size': 0
        }
    
    def run(self):
        """Execute the batch operation"""
        try:
            if self.operation == "copy":
                self._copy_files()
            elif self.operation == "move":
                self._move_files()
            elif self.operation == "delete":
                self._delete_files()
            elif self.operation == "rename":
                self._rename_files()
            elif self.operation == "update_metadata":
                self._update_metadata()
            elif self.operation == "organize":
                self._organize_files()
        except Exception as e:
            self.error_occurred.emit("Operation Error", str(e))
    
    def _copy_files(self):
        """Copy files to target directory"""
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        
        for i, file_path in enumerate(self.files):
            if self._is_cancelled:
                break
            
            try:
                filename = os.path.basename(file_path)
                target_file = os.path.join(self.target_path, filename)
                
                # Handle name conflicts
                if os.path.exists(target_file):
                    if self.options.get('overwrite', False):
                        pass  # Will overwrite
                    elif self.options.get('rename_conflicts', True):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(target_file):
                            target_file = os.path.join(self.target_path, f"{base}_{counter}{ext}")
                            counter += 1
                    else:
                        self.stats['skipped_files'] += 1
                        self.file_processed.emit("copy", file_path, False, "File already exists")
                        continue
                
                # Copy file
                shutil.copy2(file_path, target_file)
                
                # Update statistics
                file_size = os.path.getsize(file_path)
                self.stats['successful_files'] += 1
                self.stats['processed_size'] += file_size
                
                self.file_processed.emit("copy", file_path, True, f"Copied to {target_file}")
            
            except Exception as e:
                self.stats['failed_files'] += 1
                self.file_processed.emit("copy", file_path, False, str(e))
            
            finally:
                self.stats['processed_files'] += 1
                progress = int((self.stats['processed_files'] / self.stats['total_files']) * 100)
                self.progress_updated.emit(progress, f"Copying: {filename}", self.stats.copy())
        
        self.operation_completed.emit("copy", self.stats)
    
    def _move_files(self):
        """Move files to target directory"""
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        
        for i, file_path in enumerate(self.files):
            if self._is_cancelled:
                break
            
            try:
                filename = os.path.basename(file_path)
                target_file = os.path.join(self.target_path, filename)
                
                # Handle name conflicts
                if os.path.exists(target_file):
                    if self.options.get('overwrite', False):
                        os.remove(target_file)
                    elif self.options.get('rename_conflicts', True):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(target_file):
                            target_file = os.path.join(self.target_path, f"{base}_{counter}{ext}")
                            counter += 1
                    else:
                        self.stats['skipped_files'] += 1
                        self.file_processed.emit("move", file_path, False, "File already exists")
                        continue
                
                # Move file
                shutil.move(file_path, target_file)
                
                # Update statistics
                self.stats['successful_files'] += 1
                self.file_processed.emit("move", file_path, True, f"Moved to {target_file}")
            
            except Exception as e:
                self.stats['failed_files'] += 1
                self.file_processed.emit("move", file_path, False, str(e))
            
            finally:
                self.stats['processed_files'] += 1
                progress = int((self.stats['processed_files'] / self.stats['total_files']) * 100)
                self.progress_updated.emit(progress, f"Moving: {filename}", self.stats.copy())
        
        self.operation_completed.emit("move", self.stats)
    
    def _rename_files(self):
        """Rename files according to pattern"""
        pattern = self.options.get('pattern', '')
        for i, file_path in enumerate(self.files):
            if self._is_cancelled:
                break
            
            try:
                filename = os.path.basename(file_path)
                dir_path = os.path.dirname(file_path)
                base, ext = os.path.splitext(filename)
                
                # Apply rename pattern
                new_name = pattern.format(
                    index=i+1,
                    original=base,
                    extension=ext[1:],
                    date=time.strftime("%Y%m%d")
                )
                new_path = os.path.join(dir_path, new_name)
                
                # Handle name conflicts
                if os.path.exists(new_path):
                    if self.options.get('overwrite', False):
                        os.remove(new_path)
                    elif self.options.get('rename_conflicts', True):
                        counter = 1
                        while os.path.exists(new_path):
                            new_path = os.path.join(dir_path, f"{new_name}_{counter}{ext}")
                            counter += 1
                    else:
                        self.stats['skipped_files'] += 1
                        self.file_processed.emit("rename", file_path, False, "File already exists")
                        continue
                
                # Rename file
                os.rename(file_path, new_path)
                
                # Update statistics
                self.stats['successful_files'] += 1
                self.file_processed.emit("rename", file_path, True, f"Renamed to {new_name}")
            
            except Exception as e:
                self.stats['failed_files'] += 1
                self.file_processed.emit("rename", file_path, False, str(e))
            
            finally:
                self.stats['processed_files'] += 1
                progress = int((self.stats['processed_files'] / self.stats['total_files']) * 100)
                self.progress_updated.emit(progress, f"Renaming: {filename}", self.stats.copy())
        
        self.operation_completed.emit("rename", self.stats)
    
    def _organize_files(self):
        """Organize files into subdirectories based on criteria"""
        criteria = self.options.get('criteria', 'extension')
        
        for i, file_path in enumerate(self.files):
            if self._is_cancelled:
                break
            
            try:
                filename = os.path.basename(file_path)
                dir_path = os.path.dirname(file_path)
                
                # Determine target subdirectory based on criteria
                if criteria == 'extension':
                    _, ext = os.path.splitext(filename)
                    subdir = ext[1:].upper() if ext else 'NO_EXTENSION'
                elif criteria == 'date':
                    mtime = os.path.getmtime(file_path)
                    subdir = time.strftime("%Y-%m", time.localtime(mtime))
                else:
                    subdir = 'OTHER'
                
                # Create subdirectory if needed
                target_dir = os.path.join(dir_path, subdir)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                
                # Move file to subdirectory
                target_file = os.path.join(target_dir, filename)
                if os.path.exists(target_file):
                    if self.options.get('overwrite', False):
                        os.remove(target_file)
                    elif self.options.get('rename_conflicts', True):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(target_file):
                            target_file = os.path.join(target_dir, f"{base}_{counter}{ext}")
                            counter += 1
                    else:
                        self.stats['skipped_files'] += 1
                        self.file_processed.emit("organize", file_path, False, "File already exists")
                        continue
                
                shutil.move(file_path, target_file)
                
                # Update statistics
                self.stats['successful_files'] += 1
                self.file_processed.emit("organize", file_path, True, f"Organized into {subdir}")
            
            except Exception as e:
                self.stats['failed_files'] += 1
                self.file_processed.emit("organize", file_path, False, str(e))
            
            finally:
                self.stats['processed_files'] += 1
                progress = int((self.stats['processed_files'] / self.stats['total_files']) * 100)
                self.progress_updated.emit(progress, f"Organizing: {filename}", self.stats.copy())
        
        self.operation_completed.emit("organize", self.stats)
    
    def cancel(self):
        """Cancel the current operation"""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()

class CorpusManagerTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.notification_manager = NotificationManager(self)  # Initialize first
        self.project_config = project_config
        self.setup_ui()
        self.selected_files = []
        self.batch_metadata_editor = None
        self.sound_enabled = True  # Will be set from user settings
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        icon_manager = IconManager()
        
        # Create a splitter for file browser and metadata panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: File browser
        file_browser_widget = QWidget()
        file_browser_layout = QVBoxLayout(file_browser_widget)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for files...")
        self.search_input.textChanged.connect(self.filter_files)
        search_layout.addWidget(self.search_input)
        
        # Domain filter
        search_layout.addWidget(QLabel("Domain:"))
        self.domain_filter = QComboBox()
        self.domain_filter.addItem("All Domains")
        # Add the 8 domain categories from your project requirements
        domains = [
            "Crypto Derivatives", 
            "High Frequency Trading",
            "Risk Management",
            "Market Microstructure",
            "DeFi",
            "Portfolio Construction",
            "Valuation Models",
            "Regulation & Compliance"
        ]
        self.domain_filter.addItems(domains)
        self.domain_filter.currentIndexChanged.connect(self.filter_files)
        search_layout.addWidget(self.domain_filter)
        
        file_browser_layout.addLayout(search_layout)
        
        # File system navigation
        nav_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        nav_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_directory)
        nav_layout.addWidget(self.browse_btn)
        
        file_browser_layout.addLayout(nav_layout)
        
        # File tree view
        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(False)
        
        # Proxy model for filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.proxy_model)
        self.file_tree.setSortingEnabled(True)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.file_tree.clicked.connect(self.on_file_selected)
        
        # Hide unnecessary columns
        self.file_tree.setColumnHidden(1, True)  # Size
        self.file_tree.setColumnHidden(2, True)  # Type
        self.file_tree.setColumnHidden(3, True)  # Date modified
        
        file_browser_layout.addWidget(self.file_tree)
        
        # Add controls at the bottom
        controls_layout = QHBoxLayout()
        self.create_folder_btn = QPushButton("Create Folder")
        create_icon = icon_manager.get_icon_path('Data collection and processing', by='Function')
        if create_icon:
            self.create_folder_btn.setIcon(QIcon(create_icon))
        self.create_folder_btn.clicked.connect(self.create_folder)
        controls_layout.addWidget(self.create_folder_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        refresh_icon = icon_manager.get_icon_path('Loading and processing indicator', by='Function')
        if refresh_icon:
            self.refresh_btn.setIcon(QIcon(refresh_icon))
        self.refresh_btn.clicked.connect(self.refresh_file_view)
        controls_layout.addWidget(self.refresh_btn)
        
        file_browser_layout.addLayout(controls_layout)
        
        # Right side: Metadata panel
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        
        # File info
        file_info_group = QGroupBox("File Information")
        file_info_group.setObjectName("card")
        file_info_layout = QVBoxLayout(file_info_group)
        
        self.file_name_label = QLabel("No file selected")
        self.file_path_label = QLabel("")
        self.file_type_label = QLabel("")
        self.file_size_label = QLabel("")
        
        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addWidget(self.file_path_label)
        file_info_layout.addWidget(self.file_type_label)
        file_info_layout.addWidget(self.file_size_label)
        
        metadata_layout.addWidget(file_info_group)
        
        # Metadata viewer/editor
        metadata_group = QGroupBox("Metadata")
        metadata_inner_layout = QVBoxLayout(metadata_group)
        
        # Use a table view for structured metadata display and editing
        self.metadata_table = QTableView()
        self.metadata_model = QStandardItemModel(0, 2)
        self.metadata_model.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.setModel(self.metadata_model)
        
        # Make the table more user-friendly
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.metadata_table.verticalHeader().setVisible(False)
        
        metadata_inner_layout.addWidget(self.metadata_table)
        
        # Metadata control buttons
        metadata_buttons_layout = QHBoxLayout()
        self.save_metadata_btn = QPushButton("Save Metadata")
        self.save_metadata_btn.clicked.connect(self.save_metadata)
        self.save_metadata_btn.setEnabled(False)
        metadata_buttons_layout.addWidget(self.save_metadata_btn)
        
        self.add_metadata_btn = QPushButton("Add Field")
        self.add_metadata_btn.clicked.connect(self.add_metadata_field)
        self.add_metadata_btn.setEnabled(False)
        metadata_buttons_layout.addWidget(self.add_metadata_btn)
        
        metadata_inner_layout.addLayout(metadata_buttons_layout)
        
        metadata_layout.addWidget(metadata_group)
        
        # Content preview
        preview_group = QGroupBox("Content Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        preview_layout.addWidget(self.content_preview)
        
        metadata_layout.addWidget(preview_group)
        
        # Add both panels to the splitter
        splitter.addWidget(file_browser_widget)
        splitter.addWidget(metadata_widget)
        
        # Set initial sizes (30% for file browser, 70% for metadata)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
        # Add batch operations panel with progress
        batch_ops_group = QGroupBox("Batch Operations")
        batch_ops_group.setObjectName("card")
        batch_ops_layout = QVBoxLayout(batch_ops_group)
        
        # Operation buttons
        buttons_layout = QHBoxLayout()
        
        self.batch_copy_btn = QPushButton("Copy Files")
        self.batch_copy_btn.clicked.connect(self.batch_copy_files)
        buttons_layout.addWidget(self.batch_copy_btn)
        
        self.batch_move_btn = QPushButton("Move Files")
        self.batch_move_btn.clicked.connect(self.batch_move_files)
        buttons_layout.addWidget(self.batch_move_btn)
        
        self.batch_rename_btn = QPushButton("Rename Files")
        self.batch_rename_btn.clicked.connect(self.batch_rename_files)
        buttons_layout.addWidget(self.batch_rename_btn)
        
        self.batch_organize_btn = QPushButton("Organize Files")
        self.batch_organize_btn.clicked.connect(self.batch_organize_files)
        buttons_layout.addWidget(self.batch_organize_btn)
        
        self.batch_edit_btn = QPushButton("Edit Metadata")
        self.batch_edit_btn.clicked.connect(self.open_batch_metadata_editor)
        buttons_layout.addWidget(self.batch_edit_btn)
        
        self.batch_delete_btn = QPushButton("Delete Files")
        self.batch_delete_btn.clicked.connect(self.batch_delete_files)
        buttons_layout.addWidget(self.batch_delete_btn)
        
        batch_ops_layout.addLayout(buttons_layout)
        
        # Progress area
        progress_layout = QVBoxLayout()
        
        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        progress_layout.addWidget(self.batch_progress)
        
        self.batch_status = QLabel("Ready")
        self.batch_status.setObjectName("status-info")
        progress_layout.addWidget(self.batch_status)
        
        batch_ops_layout.addLayout(progress_layout)
        
        main_layout.addWidget(batch_ops_group)
        
        # Add notification area
        main_layout.addWidget(self.notification_manager)
        
        # Try to set default directory to the corpus root
        try:
            # Fix: Check if the method exists and use appropriate fallback
            if hasattr(self.project_config, 'get_corpus_root'):
                corpus_root = self.project_config.get_corpus_root()
            elif hasattr(self.project_config, 'corpus_root'):
                corpus_root = self.project_config.corpus_root
            else:
                corpus_root = None
            if corpus_root and os.path.isdir(corpus_root):
                self.set_root_directory(corpus_root)
            else:
                # Fallback to documents folder
                docs_path = QDir.homePath() + "/Documents"
                self.set_root_directory(docs_path)
        except Exception as e:
            print(f"Error setting root directory: {e}")
            # Just use home directory as fallback
            self.set_root_directory(QDir.homePath())
            
    def set_root_directory(self, path):
        self.file_model.setRootPath(path)
        self.path_input.setText(path)
        
        # Set the root index correctly in the proxy model
        source_index = self.file_model.index(path)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        self.file_tree.setRootIndex(proxy_index)
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.path_input.text()
        )
        if directory:
            self.set_root_directory(directory)
    
    def filter_files(self):
        # Get filter text
        filter_text = self.search_input.text()
        
        # If domain filter is not "All Domains", add it to the filter text
        if self.domain_filter.currentIndex() > 0:
            domain = self.domain_filter.currentText()
            if filter_text:
                filter_text = f"{filter_text} {domain}"
            else:
                filter_text = domain
        
        self.proxy_model.setFilterFixedString(filter_text)
    
    def refresh_file_view(self):
        current_path = self.path_input.text()
        self.set_root_directory(current_path)
    
    def create_folder(self):
        current_path = self.path_input.text()
        
        # Get folder name from user
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder", "Enter folder name:"
        )
        
        if ok and folder_name:
            new_folder_path = os.path.join(current_path, folder_name)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.refresh_file_view()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create folder: {str(e)}"
                )
    
    def on_file_selected(self, index):
        # Convert from proxy model index to file model index
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        if os.path.isfile(file_path):
            # Update file info
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = os.path.splitext(file_name)[1]
            
            self.file_name_label.setText(f"Name: {file_name}")
            self.file_path_label.setText(f"Path: {file_path}")
            self.file_type_label.setText(f"Type: {file_type}")
            self.file_size_label.setText(f"Size: {self.format_size(file_size)}")
            
            # Enable metadata buttons
            self.save_metadata_btn.setEnabled(True)
            self.add_metadata_btn.setEnabled(True)
            
            # Load metadata if available
            self.load_metadata(file_path)
            
            # Load content preview
            self.load_content_preview(file_path)
    
    def format_size(self, size_bytes):
        """Format file size in a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
    
    def load_metadata(self, file_path):
        """Load metadata for the selected file"""
        # Clear existing metadata
        self.metadata_model.setRowCount(0)
        
        # Check for metadata file
        metadata_path = self.get_metadata_path(file_path)
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Populate the table with metadata
                for key, value in metadata.items():
                    self.add_metadata_row(key, value)
            except Exception as e:
                print(f"Error loading metadata: {e}")
        else:
            # If no metadata file exists, add some default fields
            default_fields = [
                ("title", ""),
                ("author", ""),
                ("year", ""),
                ("domain", ""),
                ("quality_score", ""),
                ("language", ""),
                ("source", "")
            ]
            for key, value in default_fields:
                self.add_metadata_row(key, value)
    
    def add_metadata_row(self, key, value):
        """Add a row to the metadata table"""
        row = self.metadata_model.rowCount()
        self.metadata_model.insertRow(row)
        self.metadata_model.setItem(row, 0, QStandardItem(key))
        self.metadata_model.setItem(row, 1, QStandardItem(str(value)))
    
    def add_metadata_field(self):
        """Add a new metadata field"""
        row = self.metadata_model.rowCount()
        self.metadata_model.insertRow(row)
        self.metadata_model.setItem(row, 0, QStandardItem("new_field"))
        self.metadata_model.setItem(row, 1, QStandardItem(""))
    
    def save_metadata(self):
        """Save metadata for the current file"""
        # Get current file
        index = self.file_tree.currentIndex()
        if not index.isValid():
            return
            
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        if not os.path.isfile(file_path):
            return
            
        # Collect metadata from the table
        metadata = {}
        for row in range(self.metadata_model.rowCount()):
            key = self.metadata_model.item(row, 0).text()
            value = self.metadata_model.item(row, 1).text()
            metadata[key] = value
        
        # Save to metadata file
        metadata_path = self.get_metadata_path(file_path)
        
        try:
            # Ensure metadata directory exists
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            QMessageBox.information(
                self, "Success", "Metadata saved successfully"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Could not save metadata: {str(e)}"
            )
    
    def get_metadata_path(self, file_path):
        """Get the path to the metadata file for a given file"""
        # In a real implementation, this would follow your project's metadata storage convention
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        
        # Store metadata in a parallel structure
        metadata_dir = os.path.join(file_dir, ".metadata")
        return os.path.join(metadata_dir, f"{base_name}.json")
    
    def load_content_preview(self, file_path):
        """Load a preview of the file content"""
        # Clear existing preview
        self.content_preview.clear()
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        try:
            # Handle different file types
            if ext in ['.txt', '.md', '.csv', '.json']:
                # Text files - read directly
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    # Read first 5000 chars for preview
                    content = f.read(5000)
                    self.content_preview.setPlainText(content)
            elif ext == '.pdf':
                self.content_preview.setPlainText("PDF content preview not available")
            elif ext in ['.docx', '.doc']:
                self.content_preview.setPlainText("Word document preview not available")
            else:
                self.content_preview.setPlainText(f"Preview not available for {ext} files")
        except Exception as e:
            self.content_preview.setPlainText(f"Error loading preview: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for file tree"""
        index = self.file_tree.indexAt(position)
        if not index.isValid():
            return
            
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_file(file_path))
        menu.addAction(open_action)
        
        if os.path.isdir(file_path):
            # Directory-specific actions
            create_folder_action = QAction("Create Folder", self)
            create_folder_action.triggered.connect(self.create_folder)
            menu.addAction(create_folder_action)
        else:
            # File-specific actions
            edit_metadata_action = QAction("Edit Metadata", self)
            edit_metadata_action.triggered.connect(lambda: self.on_file_selected(index))
            menu.addAction(edit_metadata_action)
            
            process_action = QAction("Process File", self)
            process_action.triggered.connect(lambda: self.process_file(file_path))
            menu.addAction(process_action)
        
        # Common actions
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_file(file_path))
        menu.addAction(delete_action)
        
        menu.exec(self.file_tree.viewport().mapToGlobal(position))
    
    def open_file(self, file_path):
        """Open file with default application"""
        # Use QDesktopServices to open file with system default program
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
    
    def delete_file(self, file_path):
        """Delete file or directory"""
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {os.path.basename(file_path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                    
                # Also remove metadata if it exists
                metadata_path = self.get_metadata_path(file_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                    
                self.refresh_file_view()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not delete: {str(e)}"
                )
    
    def process_file(self, file_path):
        """Process the selected file"""
        # This would typically dispatch to the appropriate processor
        # based on the file type
        
        # For now, just show a message
        QMessageBox.information(
            self, "Process File",
            f"Processing {os.path.basename(file_path)}...\n"
            "This would call the appropriate processor wrapper."
        )

    def open_batch_metadata_editor(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to batch edit metadata.")
            return
        self.batch_metadata_editor = BatchMetadataEditor(selected_files, self)
        if self.batch_metadata_editor.exec() == QDialog.DialogCode.Accepted:
            updates = self.batch_metadata_editor.get_metadata_updates()
            overwrite = self.batch_metadata_editor.should_overwrite()
            for file_path in selected_files:
                self.update_metadata(file_path, updates, overwrite)
            self.notification_manager.add_notification("batch_metadata", "Batch Metadata Updated", f"Updated metadata for {len(selected_files)} files.", "success", auto_hide=True)
            self.refresh_file_view()

    def batch_delete_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to delete.")
            return
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete {len(selected_files)} files?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            for file_path in selected_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    self.notification_manager.add_notification(f"delete_{file_path}", "Delete Error", str(e), "error", auto_hide=True)
                    if self.sound_enabled:
                        Notifier.notify("Delete Error", str(e), level="error")
            self.notification_manager.add_notification("batch_delete", "Batch Delete", f"Deleted {len(selected_files)} files.", "success", auto_hide=True)
            if self.sound_enabled:
                Notifier.notify("Batch Delete", f"Deleted {len(selected_files)} files.", level="success")
            self.refresh_file_view()

    def get_selected_files(self):
        """Return the list of selected files from the file browser."""
        selected_indexes = self.file_tree.selectionModel().selectedIndexes()
        # Only consider the first column to avoid duplicates
        file_paths = set()
        for index in selected_indexes:
            if index.column() == 0:
                source_index = self.proxy_model.mapToSource(index)
                file_path = self.file_model.filePath(source_index)
                if os.path.isfile(file_path):
                    file_paths.add(file_path)
        return list(file_paths)

    def update_metadata(self, file_path, updates, overwrite):
        """Update metadata for a file with the given updates."""
        metadata_path = self.get_metadata_path(file_path)
        metadata = {}
        # Load existing metadata if present
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                self.notification_manager.add_notification(
                    f"meta_load_{file_path}", "Metadata Load Error", str(e), "error", auto_hide=True
                )
        # Apply updates
        for key, value in updates.items():
            if overwrite or key not in metadata or not metadata[key]:
                metadata[key] = value
        # Save updated metadata
        try:
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            self.notification_manager.add_notification(
                f"meta_save_{file_path}", "Metadata Save Error", str(e), "error", auto_hide=True
            )

    # Drag-and-drop support (PyQt6)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            # Add file to file browser (implement as needed)
            pass
        self.refresh_file_view()

    def batch_copy_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to copy.")
            return
        try:
            target_dir = QFileDialog.getExistingDirectory(self, "Select Target Directory")
            if not target_dir:
                return
            for file_path in selected_files:
                try:
                    shutil.copy2(file_path, target_dir)
                except Exception as e:
                    self.notification_manager.add_notification(f"copy_{file_path}", "Copy Error", str(e), "error", auto_hide=True)
            self.notification_manager.add_notification("batch_copy", "Batch Copy", f"Copied {len(selected_files)} files.", "success", auto_hide=True)
            self.refresh_file_view()
        except Exception as e:
            QMessageBox.critical(self, "Batch Copy Error", str(e))

    def batch_move_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to move.")
            return
        try:
            target_dir = QFileDialog.getExistingDirectory(self, "Select Target Directory")
            if not target_dir:
                return
            for file_path in selected_files:
                try:
                    shutil.move(file_path, target_dir)
                except Exception as e:
                    self.notification_manager.add_notification(f"move_{file_path}", "Move Error", str(e), "error", auto_hide=True)
            self.notification_manager.add_notification("batch_move", "Batch Move", f"Moved {len(selected_files)} files.", "success", auto_hide=True)
            self.refresh_file_view()
        except Exception as e:
            QMessageBox.critical(self, "Batch Move Error", str(e))

    def batch_rename_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to rename.")
            return
        pattern, ok = QInputDialog.getText(self, "Rename Pattern", "Enter rename pattern (use {index}, {original}, {extension}, {date}):", text="{original}_{index}")
        if not ok or not pattern:
            return
        try:
            for i, file_path in enumerate(selected_files):
                try:
                    dir_path = os.path.dirname(file_path)
                    base, ext = os.path.splitext(os.path.basename(file_path))
                    new_name = pattern.format(index=i+1, original=base, extension=ext[1:], date=time.strftime("%Y%m%d"))
                    new_path = os.path.join(dir_path, new_name)
                    if os.path.exists(new_path):
                        raise FileExistsError(f"File {new_name} already exists.")
                    os.rename(file_path, new_path)
                except Exception as e:
                    self.notification_manager.add_notification(f"rename_{file_path}", "Rename Error", str(e), "error", auto_hide=True)
            self.notification_manager.add_notification("batch_rename", "Batch Rename", f"Renamed {len(selected_files)} files.", "success", auto_hide=True)
            self.refresh_file_view()
        except Exception as e:
            QMessageBox.critical(self, "Batch Rename Error", str(e))

    def batch_organize_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No files selected", "Please select files to organize.")
            return
        criteria, ok = QInputDialog.getItem(self, "Organization Criteria", "Select organization criteria:", ["extension", "date"], editable=False)
        if not ok:
            return
        try:
            for file_path in selected_files:
                try:
                    dir_path = os.path.dirname(file_path)
                    filename = os.path.basename(file_path)
                    if criteria == 'extension':
                        _, ext = os.path.splitext(filename)
                        subdir = ext[1:].upper() if ext else 'NO_EXTENSION'
                    elif criteria == 'date':
                        mtime = os.path.getmtime(file_path)
                        subdir = time.strftime("%Y-%m", time.localtime(mtime))
                    else:
                        subdir = 'OTHER'
                    target_dir = os.path.join(dir_path, subdir)
                    os.makedirs(target_dir, exist_ok=True)
                    target_file = os.path.join(target_dir, filename)
                    if os.path.exists(target_file):
                        raise FileExistsError(f"File {filename} already exists in {subdir}.")
                    shutil.move(file_path, target_file)
                except Exception as e:
                    self.notification_manager.add_notification(f"organize_{file_path}", "Organize Error", str(e), "error", auto_hide=True)
            self.notification_manager.add_notification("batch_organize", "Batch Organize", f"Organized {len(selected_files)} files.", "success", auto_hide=True)
            self.refresh_file_view()
        except Exception as e:
            QMessageBox.critical(self, "Batch Organize Error", str(e))
