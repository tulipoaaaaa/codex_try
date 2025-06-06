"""
Monitor Progress Wrapper for UI Integration
Provides comprehensive progress monitoring capabilities with visual feedback
"""

import os
import time
import json
from typing import Dict, List, Optional, Any, Callable
from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal, Slot as pyqtSlot, QTimer, QMutex
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QProgressBar, QLabel, QTextEdit, QCheckBox, 
                           QSpinBox, QGroupBox, QGridLayout, QComboBox,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QTabWidget, QSplitter, QSlider, QListWidget)
from PySide6.QtGui import QColor, QBrush, QPalette
from PySide6.QtCore import Qt
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper
from shared_tools.processors.monitor_progress import MonitorProgress
from shared_tools.processors.mixins.processor_wrapper_mixin import ProcessorWrapperMixin


class ProgressMonitoringWorker(QThread):
    """Worker thread for progress monitoring operations"""
    
    progress_update = pyqtSignal(str, dict)  # task_id, progress_data
    task_started = pyqtSignal(str, str)  # task_id, task_name
    task_completed = pyqtSignal(str, dict)  # task_id, final_stats
    task_failed = pyqtSignal(str, str)  # task_id, error_message
    monitoring_stats = pyqtSignal(dict)  # overall monitoring statistics
    
    def __init__(self, monitor_config: Dict[str, Any]):
        super().__init__()
        self.monitor_config = monitor_config
        self.monitor = MonitorProgress()
        self._is_running = False
        self._mutex = QMutex()
        self.active_tasks = {}
        
    def run(self):
        """Execute progress monitoring"""
        self._is_running = True
        
        # Configure monitor
        self.monitor.configure(
            update_interval=self.monitor_config.get('update_interval', 1.0),
            enable_notifications=self.monitor_config.get('enable_notifications', True),
            log_progress=self.monitor_config.get('log_progress', True),
            track_memory=self.monitor_config.get('track_memory', True),
            track_cpu=self.monitor_config.get('track_cpu', True)
        )
        
        # Start monitoring loop
        while self._is_running:
            try:
                # Check for new tasks
                self._check_for_new_tasks()
                
                # Update existing tasks
                self._update_active_tasks()
                
                # Send monitoring statistics
                self._send_monitoring_stats()
                
                # Sleep for update interval
                update_interval = self.monitor_config.get('update_interval', 1.0)
                self.msleep(int(update_interval * 1000))
                
            except Exception as e:
                # Continue monitoring even if individual updates fail
                continue
                
    def _check_for_new_tasks(self):
        """Check for newly started tasks"""
        # In a real implementation, this would check a task registry
        # For demonstration, we'll simulate task detection
        pass
        
    def _update_active_tasks(self):
        """Update progress for all active tasks"""
        for task_id, task_info in self.active_tasks.items():
            try:
                # Get progress update from monitor
                progress_data = self.monitor.get_task_progress(task_id)
                
                if progress_data:
                    self.progress_update.emit(task_id, progress_data)
                    
                    # Check if task completed
                    if progress_data.get('status') == 'completed':
                        self.task_completed.emit(task_id, progress_data)
                        del self.active_tasks[task_id]
                    elif progress_data.get('status') == 'failed':
                        error_msg = progress_data.get('error', 'Unknown error')
                        self.task_failed.emit(task_id, error_msg)
                        del self.active_tasks[task_id]
                        
            except Exception as e:
                continue
                
    def _send_monitoring_stats(self):
        """Send overall monitoring statistics"""
        stats = {
            'active_tasks': len(self.active_tasks),
            'total_monitored': self.monitor.get_total_monitored_count(),
            'system_memory_usage': self.monitor.get_system_memory_usage(),
            'system_cpu_usage': self.monitor.get_system_cpu_usage(),
            'monitoring_uptime': self.monitor.get_uptime()
        }
        
        self.monitoring_stats.emit(stats)
        
    def add_task(self, task_id: str, task_name: str, task_info: Dict[str, Any]):
        """Add a new task to monitor"""
        self._mutex.lock()
        try:
            self.active_tasks[task_id] = {
                'name': task_name,
                'start_time': time.time(),
                **task_info
            }
            self.task_started.emit(task_id, task_name)
        finally:
            self._mutex.unlock()
            
    def remove_task(self, task_id: str):
        """Remove a task from monitoring"""
        self._mutex.lock()
        try:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
        finally:
            self._mutex.unlock()
            
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self._is_running = False


class MonitorProgressWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI Wrapper for Progress Monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitoring_worker = None
        self.monitored_tasks = {}
        self.task_widgets = {}
        self.monitoring_enabled = False
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Active Tasks Tab
        tasks_tab = self._create_active_tasks_tab()
        self.tab_widget.addTab(tasks_tab, "Active Tasks")
        
        # System Monitor Tab
        system_tab = self._create_system_monitor_tab()
        self.tab_widget.addTab(system_tab, "System Monitor")
        
        # Configuration Tab
        config_tab = self._create_configuration_tab()
        self.tab_widget.addTab(config_tab, "Configuration")
        
        # History Tab
        history_tab = self._create_history_tab()
        self.tab_widget.addTab(history_tab, "History")
        
        layout.addWidget(self.tab_widget)
        
        # Control Panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
    def _create_active_tasks_tab(self) -> QWidget:
        """Create the active tasks monitoring tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tasks Overview
        overview_group = QGroupBox("Tasks Overview")
        overview_layout = QGridLayout(overview_group)
        
        self.active_tasks_label = QLabel("Active Tasks: 0")
        self.completed_tasks_label = QLabel("Completed: 0")
        self.failed_tasks_label = QLabel("Failed: 0")
        self.total_tasks_label = QLabel("Total Monitored: 0")
        
        overview_layout.addWidget(self.active_tasks_label, 0, 0)
        overview_layout.addWidget(self.completed_tasks_label, 0, 1)
        overview_layout.addWidget(self.failed_tasks_label, 1, 0)
        overview_layout.addWidget(self.total_tasks_label, 1, 1)
        
        # Tasks Table
        tasks_group = QGroupBox("Task Details")
        tasks_layout = QVBoxLayout(tasks_group)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "Task ID", "Name", "Status", "Progress", "Duration", "Details"
        ])
        
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(3, 150)  # Progress column width
        
        tasks_layout.addWidget(self.tasks_table)
        
        # Task Actions
        actions_layout = QHBoxLayout()
        self.pause_task_btn = QPushButton("Pause Selected")
        self.resume_task_btn = QPushButton("Resume Selected")
        self.cancel_task_btn = QPushButton("Cancel Selected")
        self.refresh_tasks_btn = QPushButton("Refresh")
        
        actions_layout.addWidget(self.pause_task_btn)
        actions_layout.addWidget(self.resume_task_btn)
        actions_layout.addWidget(self.cancel_task_btn)
        actions_layout.addWidget(self.refresh_tasks_btn)
        actions_layout.addStretch()
        
        tasks_layout.addLayout(actions_layout)
        
        layout.addWidget(overview_group)
        layout.addWidget(tasks_group)
        
        return tab
        
    def _create_system_monitor_tab(self) -> QWidget:
        """Create the system monitoring tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Metrics
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Memory usage
        self.memory_label = QLabel("Memory Usage:")
        self.memory_progress = QProgressBar()
        self.memory_value_label = QLabel("0%")
        
        metrics_layout.addWidget(self.memory_label, 0, 0)
        metrics_layout.addWidget(self.memory_progress, 0, 1)
        metrics_layout.addWidget(self.memory_value_label, 0, 2)
        
        # CPU usage
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_progress = QProgressBar()
        self.cpu_value_label = QLabel("0%")
        
        metrics_layout.addWidget(self.cpu_label, 1, 0)
        metrics_layout.addWidget(self.cpu_progress, 1, 1)
        metrics_layout.addWidget(self.cpu_value_label, 1, 2)
        
        # Disk usage
        self.disk_label = QLabel("Disk Usage:")
        self.disk_progress = QProgressBar()
        self.disk_value_label = QLabel("0%")
        
        metrics_layout.addWidget(self.disk_label, 2, 0)
        metrics_layout.addWidget(self.disk_progress, 2, 1)
        metrics_layout.addWidget(self.disk_value_label, 2, 2)
        
        # Network activity
        self.network_label = QLabel("Network Activity:")
        self.network_in_label = QLabel("In: 0 KB/s")
        self.network_out_label = QLabel("Out: 0 KB/s")
        
        metrics_layout.addWidget(self.network_label, 3, 0)
        metrics_layout.addWidget(self.network_in_label, 3, 1)
        metrics_layout.addWidget(self.network_out_label, 3, 2)
        
        # System Information
        info_group = QGroupBox("System Information")
        info_layout = QGridLayout(info_group)
        
        self.uptime_label = QLabel("Monitoring Uptime: 0s")
        self.process_count_label = QLabel("Active Processes: 0")
        self.thread_count_label = QLabel("Active Threads: 0")
        
        info_layout.addWidget(self.uptime_label, 0, 0)
        info_layout.addWidget(self.process_count_label, 0, 1)
        info_layout.addWidget(self.thread_count_label, 1, 0)
        
        layout.addWidget(metrics_group)
        layout.addWidget(info_group)
        layout.addStretch()
        
        return tab
        
    def _create_configuration_tab(self) -> QWidget:
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Monitoring Settings
        monitoring_group = QGroupBox("Monitoring Settings")
        monitoring_layout = QGridLayout(monitoring_group)
        
        self.update_interval_label = QLabel("Update Interval (seconds):")
        self.update_interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.update_interval_slider.setRange(1, 60)
        self.update_interval_slider.setValue(5)
        self.update_interval_value = QLabel("5s")
        self.update_interval_slider.valueChanged.connect(
            lambda v: self.update_interval_value.setText(f"{v}s")
        )
        
        monitoring_layout.addWidget(self.update_interval_label, 0, 0)
        monitoring_layout.addWidget(self.update_interval_slider, 0, 1)
        monitoring_layout.addWidget(self.update_interval_value, 0, 2)
        
        self.enable_notifications_cb = QCheckBox("Enable Notifications")
        self.enable_notifications_cb.setChecked(True)
        monitoring_layout.addWidget(self.enable_notifications_cb, 1, 0, 1, 2)
        
        self.log_progress_cb = QCheckBox("Log Progress to File")
        self.log_progress_cb.setChecked(True)
        monitoring_layout.addWidget(self.log_progress_cb, 2, 0, 1, 2)
        
        self.track_memory_cb = QCheckBox("Track Memory Usage")
        self.track_memory_cb.setChecked(True)
        monitoring_layout.addWidget(self.track_memory_cb, 3, 0, 1, 2)
        
        self.track_cpu_cb = QCheckBox("Track CPU Usage")
        self.track_cpu_cb.setChecked(True)
        monitoring_layout.addWidget(self.track_cpu_cb, 4, 0, 1, 2)
        
        # Alert Settings
        alerts_group = QGroupBox("Alert Settings")
        alerts_layout = QGridLayout(alerts_group)
        
        self.memory_threshold_label = QLabel("Memory Alert Threshold (%):")
        self.memory_threshold_spin = QSpinBox()
        self.memory_threshold_spin.setRange(50, 95)
        self.memory_threshold_spin.setValue(80)
        
        alerts_layout.addWidget(self.memory_threshold_label, 0, 0)
        alerts_layout.addWidget(self.memory_threshold_spin, 0, 1)
        
        self.cpu_threshold_label = QLabel("CPU Alert Threshold (%):")
        self.cpu_threshold_spin = QSpinBox()
        self.cpu_threshold_spin.setRange(50, 95)
        self.cpu_threshold_spin.setValue(85)
        
        alerts_layout.addWidget(self.cpu_threshold_label, 1, 0)
        alerts_layout.addWidget(self.cpu_threshold_spin, 1, 1)
        
        self.task_timeout_label = QLabel("Task Timeout (minutes):")
        self.task_timeout_spin = QSpinBox()
        self.task_timeout_spin.setRange(5, 480)
        self.task_timeout_spin.setValue(60)
        
        alerts_layout.addWidget(self.task_timeout_label, 2, 0)
        alerts_layout.addWidget(self.task_timeout_spin, 2, 1)
        
        layout.addWidget(monitoring_group)
        layout.addWidget(alerts_group)
        layout.addStretch()
        
        return tab
        
    def _create_history_tab(self) -> QWidget:
        """Create the task history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # History Controls
        controls_layout = QHBoxLayout()
        self.history_filter_combo = QComboBox()
        self.history_filter_combo.addItems(["All Tasks", "Completed", "Failed", "Cancelled"])
        
        self.clear_history_btn = QPushButton("Clear History")
        self.export_history_btn = QPushButton("Export History")
        
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.history_filter_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.clear_history_btn)
        controls_layout.addWidget(self.export_history_btn)
        
        # History Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Task ID", "Name", "Status", "Start Time", "Duration", "Result", "Error"
        ])
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.history_table)
        
        return tab
        
    def _create_control_panel(self) -> QWidget:
        """Create the main control panel"""
        control_group = QGroupBox("Monitoring Control")
        layout = QHBoxLayout(control_group)
        
        self.start_monitoring_btn = QPushButton("Start Monitoring")
        self.stop_monitoring_btn = QPushButton("Stop Monitoring")
        self.stop_monitoring_btn.setEnabled(False)
        
        self.pause_monitoring_btn = QPushButton("Pause Monitoring")
        self.pause_monitoring_btn.setEnabled(False)
        
        self.monitoring_status_label = QLabel("Status: Stopped")
        
        layout.addWidget(self.start_monitoring_btn)
        layout.addWidget(self.stop_monitoring_btn)
        layout.addWidget(self.pause_monitoring_btn)
        layout.addStretch()
        layout.addWidget(self.monitoring_status_label)
        
        return control_group
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Control buttons
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.pause_monitoring_btn.clicked.connect(self.pause_monitoring)
        
        # Task actions
        self.pause_task_btn.clicked.connect(self.pause_selected_task)
        self.resume_task_btn.clicked.connect(self.resume_selected_task)
        self.cancel_task_btn.clicked.connect(self.cancel_selected_task)
        self.refresh_tasks_btn.clicked.connect(self.refresh_tasks)
        
        # History actions
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.export_history_btn.clicked.connect(self.export_history)
        self.history_filter_combo.currentTextChanged.connect(self.filter_history)
        
    @pyqtSlot()
    def start_monitoring(self):
        """Start progress monitoring"""
        if self.monitoring_worker and self.monitoring_worker.isRunning():
            return
            
        # Get configuration
        config = {
            'update_interval': self.update_interval_slider.value(),
            'enable_notifications': self.enable_notifications_cb.isChecked(),
            'log_progress': self.log_progress_cb.isChecked(),
            'track_memory': self.track_memory_cb.isChecked(),
            'track_cpu': self.track_cpu_cb.isChecked()
        }
        
        # Create and start worker
        self.monitoring_worker = ProgressMonitoringWorker(config)
        self.monitoring_worker.progress_update.connect(self.update_task_progress)
        self.monitoring_worker.task_started.connect(self.add_task_to_table)
        self.monitoring_worker.task_completed.connect(self.mark_task_completed)
        self.monitoring_worker.task_failed.connect(self.mark_task_failed)
        self.monitoring_worker.monitoring_stats.connect(self.update_system_stats)
        
        self.monitoring_worker.start()
        
        # Update UI
        self.monitoring_enabled = True
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        self.pause_monitoring_btn.setEnabled(True)
        self.monitoring_status_label.setText("Status: Running")
        
    @pyqtSlot()
    def stop_monitoring(self):
        """Stop progress monitoring"""
        if self.monitoring_worker and self.monitoring_worker.isRunning():
            self.monitoring_worker.stop_monitoring()
            self.monitoring_worker.wait(3000)
            
        # Update UI
        self.monitoring_enabled = False
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)
        self.pause_monitoring_btn.setEnabled(False)
        self.monitoring_status_label.setText("Status: Stopped")
        
    @pyqtSlot()
    def pause_monitoring(self):
        """Pause/resume monitoring"""
        # Implementation would pause the monitoring worker
        current_text = self.pause_monitoring_btn.text()
        if current_text == "Pause Monitoring":
            self.pause_monitoring_btn.setText("Resume Monitoring")
            self.monitoring_status_label.setText("Status: Paused")
        else:
            self.pause_monitoring_btn.setText("Pause Monitoring")
            self.monitoring_status_label.setText("Status: Running")
            
    @pyqtSlot(str, dict)
    def update_task_progress(self, task_id: str, progress_data: dict):
        """Update progress for a specific task"""
        # Find task in table
        for row in range(self.tasks_table.rowCount()):
            if self.tasks_table.item(row, 0).text() == task_id:
                # Update progress column
                progress_percentage = progress_data.get('percentage', 0)
                progress_widget = self.tasks_table.cellWidget(row, 3)
                if isinstance(progress_widget, QProgressBar):
                    progress_widget.setValue(progress_percentage)
                    
                # Update status
                status = progress_data.get('status', 'running')
                self.tasks_table.setItem(row, 2, QTableWidgetItem(status.title()))
                
                # Update duration
                duration = progress_data.get('duration', 0)
                duration_text = f"{duration:.1f}s"
                self.tasks_table.setItem(row, 4, QTableWidgetItem(duration_text))
                
                # Update details
                details = progress_data.get('details', '')
                self.tasks_table.setItem(row, 5, QTableWidgetItem(details))
                break
                
    @pyqtSlot(str, str)
    def add_task_to_table(self, task_id: str, task_name: str):
        """Add a new task to the monitoring table"""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)
        
        self.tasks_table.setItem(row, 0, QTableWidgetItem(task_id))
        self.tasks_table.setItem(row, 1, QTableWidgetItem(task_name))
        self.tasks_table.setItem(row, 2, QTableWidgetItem("Starting"))
        
        # Add progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        self.tasks_table.setCellWidget(row, 3, progress_bar)
        
        self.tasks_table.setItem(row, 4, QTableWidgetItem("0s"))
        self.tasks_table.setItem(row, 5, QTableWidgetItem("Initializing"))
        
        # Store task info
        self.monitored_tasks[task_id] = {
            'name': task_name,
            'row': row,
            'start_time': time.time()
        }
        
    @pyqtSlot(str, dict)
    def mark_task_completed(self, task_id: str, final_stats: dict):
        """Mark a task as completed"""
        if task_id in self.monitored_tasks:
            row = self.monitored_tasks[task_id]['row']
            
            # Update status with success color
            status_item = QTableWidgetItem("Completed")
            status_item.setBackground(QBrush(QColor(46, 204, 113)))
            status_item.setForeground(QBrush(QColor(255, 255, 255)))
            self.tasks_table.setItem(row, 2, status_item)
            
            # Update progress to 100%
            progress_widget = self.tasks_table.cellWidget(row, 3)
            if isinstance(progress_widget, QProgressBar):
                progress_widget.setValue(100)
                
            # Add to history
            self._add_to_history(task_id, "Completed", final_stats)
            
    @pyqtSlot(str, str)
    def mark_task_failed(self, task_id: str, error_message: str):
        """Mark a task as failed"""
        if task_id in self.monitored_tasks:
            row = self.monitored_tasks[task_id]['row']
            
            # Update status with error color
            status_item = QTableWidgetItem("Failed")
            status_item.setBackground(QBrush(QColor(231, 76, 60)))
            status_item.setForeground(QBrush(QColor(255, 255, 255)))
            self.tasks_table.setItem(row, 2, status_item)
            
            # Update details with error
            self.tasks_table.setItem(row, 5, QTableWidgetItem(error_message))
            
            # Add to history
            self._add_to_history(task_id, "Failed", {'error': error_message})
            
    @pyqtSlot(dict)
    def update_system_stats(self, stats: dict):
        """Update system monitoring statistics"""
        # Update task counts
        self.active_tasks_label.setText(f"Active Tasks: {stats.get('active_tasks', 0)}")
        self.total_tasks_label.setText(f"Total Monitored: {stats.get('total_monitored', 0)}")
        
        # Update system metrics
        memory_usage = stats.get('system_memory_usage', 0)
        self.memory_progress.setValue(int(memory_usage))
        self.memory_value_label.setText(f"{memory_usage:.1f}%")
        
        cpu_usage = stats.get('system_cpu_usage', 0)
        self.cpu_progress.setValue(int(cpu_usage))
        self.cpu_value_label.setText(f"{cpu_usage:.1f}%")
        
        # Update uptime
        uptime = stats.get('monitoring_uptime', 0)
        uptime_text = f"{uptime:.0f}s" if uptime < 60 else f"{uptime/60:.1f}m"
        self.uptime_label.setText(f"Monitoring Uptime: {uptime_text}")
        
    def _add_to_history(self, task_id: str, status: str, result_data: dict):
        """Add task to history table"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        task_info = self.monitored_tasks.get(task_id, {})
        
        self.history_table.setItem(row, 0, QTableWidgetItem(task_id))
        self.history_table.setItem(row, 1, QTableWidgetItem(task_info.get('name', 'Unknown')))
        self.history_table.setItem(row, 2, QTableWidgetItem(status))
        
        start_time = task_info.get('start_time', time.time())
        start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        self.history_table.setItem(row, 3, QTableWidgetItem(start_time_str))
        
        duration = time.time() - start_time
        duration_str = f"{duration:.1f}s"
        self.history_table.setItem(row, 4, QTableWidgetItem(duration_str))
        
        result = result_data.get('result', 'N/A')
        self.history_table.setItem(row, 5, QTableWidgetItem(str(result)))
        
        error = result_data.get('error', '')
        self.history_table.setItem(row, 6, QTableWidgetItem(error))
        
    @pyqtSlot()
    def pause_selected_task(self):
        """Pause the selected task"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0:
            task_id = self.tasks_table.item(current_row, 0).text()
            # Implementation would pause the specific task
            self.show_info("Task Paused", f"Task {task_id} has been paused")
            
    @pyqtSlot()
    def resume_selected_task(self):
        """Resume the selected task"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0:
            task_id = self.tasks_table.item(current_row, 0).text()
            # Implementation would resume the specific task
            self.show_info("Task Resumed", f"Task {task_id} has been resumed")
            
    @pyqtSlot()
    def cancel_selected_task(self):
        """Cancel the selected task"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0:
            task_id = self.tasks_table.item(current_row, 0).text()
            
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Cancel Task",
                f"Are you sure you want to cancel task {task_id}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Implementation would cancel the specific task
                self.show_info("Task Cancelled", f"Task {task_id} has been cancelled")
                
    @pyqtSlot()
    def refresh_tasks(self):
        """Refresh the tasks table"""
        # Implementation would refresh task data
        pass
        
    @pyqtSlot()
    def clear_history(self):
        """Clear task history"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all task history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_table.setRowCount(0)
            
    @pyqtSlot()
    def export_history(self):
        """Export task history to file"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Task History",
            f"task_history_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self._export_history_json(filename)
                else:
                    self._export_history_csv(filename)
                    
                self.show_info("Export Successful", f"History exported to {filename}")
                
            except Exception as e:
                self.show_error("Export Error", f"Failed to export history: {str(e)}")
                
    def _export_history_csv(self, filename: str):
        """Export history to CSV format"""
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header
            headers = ["Task ID", "Name", "Status", "Start Time", "Duration", "Result", "Error"]
            f.write(",".join(headers) + "\n")
            
            # Write data
            for row in range(self.history_table.rowCount()):
                row_data = []
                for col in range(self.history_table.columnCount()):
                    item = self.history_table.item(row, col)
                    value = item.text() if item else ""
                    row_data.append(f'"{value}"')
                f.write(",".join(row_data) + "\n")
                
    def _export_history_json(self, filename: str):
        """Export history to JSON format"""
        # TODO: Implement JSON export logic
        pass
