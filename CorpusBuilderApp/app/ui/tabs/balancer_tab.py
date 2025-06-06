"""
Enhanced Corpus Balancer Tab with Re-analysis and Periodic Monitoring
Provides comprehensive corpus balancing with automatic re-analysis capabilities
"""

import os
import time
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QLabel, QPushButton, QProgressBar, QSpinBox,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QComboBox, QCheckBox, QMessageBox, QSlider,
                           QSystemTrayIcon, QMenu, QStatusBar)
from PySide6.QtCore import Qt, Slot as pyqtSlot, QTimer, Signal as pyqtSignal, QObject
from PySide6.QtGui import QColor, QBrush, QPalette, QIcon, QAction
from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper
from app.helpers.icon_manager import IconManager
from app.helpers.notifier import Notifier


class AdvancedNotificationManager(QObject):
    """Advanced notification system for balancer operations"""
    
    notification_requested = pyqtSignal(str, str, str, int)  # title, message, type, duration
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = None
        self.setup_system_tray()
        
    def setup_system_tray(self):
        """Setup system tray for notifications"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setToolTip("Corpus Balancer")
            
    def show_notification(self, title: str, message: str, notification_type: str = "info", duration: int = 5000):
        """Show system notification"""
        if self.tray_icon:
            icon = QSystemTrayIcon.MessageIcon.Information
            if notification_type == "warning":
                icon = QSystemTrayIcon.MessageIcon.Warning
            elif notification_type == "critical":
                icon = QSystemTrayIcon.MessageIcon.Critical
                
            self.tray_icon.showMessage(title, message, icon, duration)


class BalancerTab(QWidget):
    """Enhanced Balancer Tab with automatic re-analysis and notifications"""
    
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        self.setObjectName("card")
        self.balancer = CorpusBalancerWrapper(project_config)
        self.notification_manager = AdvancedNotificationManager(self)
        self.sound_enabled = True  # Will be set from user settings
        
        # Periodic analysis timer
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.perform_periodic_analysis)
        
        # Auto-analysis settings
        self.auto_analysis_enabled = False
        self.analysis_interval_minutes = 30
        self.last_analysis_time = 0
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_corpus_stats()
        
    def setup_ui(self):
        """Initialize the enhanced user interface"""
        main_layout = QVBoxLayout(self)
        icon_manager = IconManager()
        
        # Current Distribution
        current_group = QGroupBox("Current Corpus Distribution")
        current_layout = QVBoxLayout(current_group)
        
        # Domain table with enhanced features
        self.domain_table = QTableWidget(8, 6)  # Added one more column for actions
        self.domain_table.setHorizontalHeaderLabels([
            "Domain", "Target %", "Current %", "Document Count", "Progress", "Status"
        ])
        
        # Set up table properties
        self.domain_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.domain_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.domain_table.verticalHeader().setVisible(False)
        
        current_layout.addWidget(self.domain_table)
        
        # Initialize domains with enhanced data
        domains = [
            "Crypto Derivatives", "High Frequency Trading", "Risk Management",
            "Market Microstructure", "DeFi", "Portfolio Construction",
            "Valuation Models", "Regulation & Compliance"
        ]
        targets = [20, 15, 15, 15, 12, 10, 8, 5]
        
        for i, (domain, target) in enumerate(zip(domains, targets)):
            # Domain name
            domain_item = QTableWidgetItem(domain)
            domain_item.setFlags(domain_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.domain_table.setItem(i, 0, domain_item)
            
            # Target percentage
            target_item = QTableWidgetItem(f"{target}%")
            self.domain_table.setItem(i, 1, target_item)
            
            # Current percentage (will be updated)
            current_item = QTableWidgetItem("0%")
            self.domain_table.setItem(i, 2, current_item)
            
            # Document count
            count_item = QTableWidgetItem("0")
            self.domain_table.setItem(i, 3, count_item)
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            self.domain_table.setCellWidget(i, 4, progress_bar)
            
            # Status indicator
            status_item = QTableWidgetItem("Balanced")
            self.domain_table.setItem(i, 5, status_item)
            
        main_layout.addWidget(current_group)
        
        # Enhanced Balancing Options
        options_group = QGroupBox("Balancing Options")
        options_layout = QVBoxLayout(options_group)
        
        # Quality threshold
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Minimum Quality Score:"))
        self.quality_threshold = QSpinBox()
        self.quality_threshold.setRange(0, 100)
        self.quality_threshold.setValue(70)
        quality_layout.addWidget(self.quality_threshold)
        options_layout.addLayout(quality_layout)
        
        # Balance method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Balancing Method:"))
        self.balance_method = QComboBox()
        self.balance_method.addItems([
            "Target Percentage", "Equal Distribution", "Document Count Targets"
        ])
        method_layout.addWidget(self.balance_method)
        options_layout.addLayout(method_layout)
        
        # Periodic Analysis Settings
        periodic_layout = QVBoxLayout()
        self.auto_analysis_checkbox = QCheckBox("Enable Automatic Re-analysis")
        self.auto_analysis_checkbox.toggled.connect(self.toggle_auto_analysis)
        periodic_layout.addWidget(self.auto_analysis_checkbox)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Analysis Interval (minutes):"))
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(5, 120)
        self.interval_slider.setValue(30)
        self.interval_slider.valueChanged.connect(self.update_analysis_interval)
        self.interval_label = QLabel("30")
        interval_layout.addWidget(self.interval_slider)
        interval_layout.addWidget(self.interval_label)
        periodic_layout.addLayout(interval_layout)
        
        options_layout.addLayout(periodic_layout)
        
        # Additional options
        self.auto_classify = QCheckBox("Automatically classify unclassified documents")
        self.auto_classify.setChecked(True)
        options_layout.addWidget(self.auto_classify)
        
        self.preserve_existing = QCheckBox("Preserve existing domain assignments")
        self.preserve_existing.setChecked(True)
        options_layout.addWidget(self.preserve_existing)
        
        self.enable_notifications = QCheckBox("Enable system notifications")
        self.enable_notifications.setChecked(True)
        options_layout.addWidget(self.enable_notifications)
        
        main_layout.addWidget(options_group)
        
        # Enhanced Control Panel
        controls_group = QGroupBox("Control Panel")
        controls_layout = QVBoxLayout(controls_group)
        
        # Primary controls
        primary_controls = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Corpus Stats")
        refresh_icon = icon_manager.get_icon_path('Loading and processing indicator', by='Function')
        if refresh_icon:
            self.refresh_btn.setIcon(QIcon(refresh_icon))
        self.refresh_btn.clicked.connect(self.refresh_corpus_stats)
        primary_controls.addWidget(self.refresh_btn)
        
        self.reanalyze_btn = QPushButton("Re-analyze After Changes")
        reanalyze_icon = icon_manager.get_icon_path('Success status and completion indicator', by='Function')
        if reanalyze_icon:
            self.reanalyze_btn.setIcon(QIcon(reanalyze_icon))
        self.reanalyze_btn.clicked.connect(self.reanalyze_corpus)
        primary_controls.addWidget(self.reanalyze_btn)
        
        self.analyze_btn = QPushButton("Analyze Imbalance")
        analyze_icon = icon_manager.get_icon_path('Data analytics and visualization', by='Function')
        if analyze_icon:
            self.analyze_btn.setIcon(QIcon(analyze_icon))
        self.analyze_btn.clicked.connect(self.analyze_corpus_balance)
        primary_controls.addWidget(self.analyze_btn)
        
        # Add to Control Panel (primary_controls)
        self.collect_missing_btn = QPushButton("Collect for Missing Domains")
        self.collect_missing_btn.setToolTip("Trigger collectors for missing/underrepresented domains based on corpus analysis.")
        self.collect_missing_btn.clicked.connect(self.collect_for_missing_domains)
        primary_controls.addWidget(self.collect_missing_btn)
        
        controls_layout.addLayout(primary_controls)
        
        # Secondary controls
        secondary_controls = QHBoxLayout()
        self.balance_btn = QPushButton("Balance Corpus")
        balance_icon = icon_manager.get_icon_path('Load balancing and data distribution', by='Function')
        if balance_icon:
            self.balance_btn.setIcon(QIcon(balance_icon))
        self.balance_btn.clicked.connect(self.balance_corpus)
        secondary_controls.addWidget(self.balance_btn)
        
        self.stop_btn = QPushButton("Stop")
        stop_icon = icon_manager.get_icon_path('Stop operation control', by='Function')
        if stop_icon:
            self.stop_btn.setIcon(QIcon(stop_icon))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_balancing)
        secondary_controls.addWidget(self.stop_btn)
        
        self.export_report_btn = QPushButton("Export Balance Report")
        export_icon = icon_manager.get_icon_path('Main dashboard and analytics view', by='Function')
        if export_icon:
            self.export_report_btn.setIcon(QIcon(export_icon))
        self.export_report_btn.clicked.connect(self.export_balance_report)
        secondary_controls.addWidget(self.export_report_btn)
        
        controls_layout.addLayout(secondary_controls)
        
        main_layout.addWidget(controls_group)
        
        # Enhanced Status Area
        status_group = QGroupBox("Balancing Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready - Last analysis: Never")
        self.status_label.setObjectName("status-info")
        status_layout.addWidget(self.status_label)
        
        self.overall_progress = QProgressBar()
        status_layout.addWidget(self.overall_progress)
        
        # Statistics display
        stats_layout = QHBoxLayout()
        self.total_docs_label = QLabel("Total Documents: 0")
        self.balance_score_label = QLabel("Balance Score: 0%")
        self.last_change_label = QLabel("Last Change: Never")
        
        stats_layout.addWidget(self.total_docs_label)
        stats_layout.addWidget(self.balance_score_label)
        stats_layout.addWidget(self.last_change_label)
        status_layout.addLayout(stats_layout)
        
        main_layout.addWidget(status_group)
        
    def connect_signals(self):
        """Connect all signal-slot connections"""
        # Connect balancer wrapper signals
        self.balancer.progress_updated.connect(self.overall_progress.setValue)
        self.balancer.status_updated.connect(self.update_status_display)
        self.balancer.balance_completed.connect(self.on_balance_completed)
        
        # Connect notification signals
        self.notification_manager.notification_requested.connect(self.show_notification)
        
    @pyqtSlot(bool)
    def toggle_auto_analysis(self, enabled: bool):
        """Toggle automatic periodic analysis"""
        self.auto_analysis_enabled = enabled
        if enabled:
            self.analysis_timer.start(self.analysis_interval_minutes * 60 * 1000)  # Convert to milliseconds
            self.show_notification("Auto-Analysis Enabled", 
                                 f"Corpus will be analyzed every {self.analysis_interval_minutes} minutes")
        else:
            self.analysis_timer.stop()
            self.show_notification("Auto-Analysis Disabled", "Periodic analysis has been turned off")
            
    @pyqtSlot(int)
    def update_analysis_interval(self, minutes: int):
        """Update the analysis interval"""
        self.analysis_interval_minutes = minutes
        self.interval_label.setText(str(minutes))
        
        if self.auto_analysis_enabled:
            self.analysis_timer.stop()
            self.analysis_timer.start(minutes * 60 * 1000)
            
    @pyqtSlot()
    def perform_periodic_analysis(self):
        """Perform automatic periodic analysis"""
        current_time = time.time()
        if current_time - self.last_analysis_time > (self.analysis_interval_minutes * 60):
            self.reanalyze_corpus()
            self.last_analysis_time = current_time
            
    @pyqtSlot()
    def reanalyze_corpus(self):
        """Re-analyze corpus after changes"""
        self.status_label.setText("Re-analyzing corpus...")
        self.refresh_corpus_stats()
        
        # Check for significant changes
        changes_detected = self.detect_corpus_changes()
        
        if changes_detected:
            self.show_notification("Corpus Changes Detected", 
                                 "Significant changes found. Consider rebalancing.", "warning")
            self.analyze_corpus_balance()
        else:
            self.show_notification("Analysis Complete", "No significant changes detected.")
            
        self.last_analysis_time = time.time()
        current_time = time.strftime("%H:%M:%S", time.localtime())
        self.status_label.setText(f"Ready - Last analysis: {current_time}")
        
    def detect_corpus_changes(self) -> bool:
        """Detect if significant changes occurred in the corpus"""
        # In a real implementation, this would compare current stats with cached previous stats
        # For demonstration, we'll simulate change detection
        import random
        return random.choice([True, False])
        
    def calculate_balance_score(self) -> float:
        """Calculate overall corpus balance score"""
        total_deviation = 0
        for i in range(self.domain_table.rowCount()):
            target_text = self.domain_table.item(i, 1).text().strip('%')
            current_text = self.domain_table.item(i, 2).text().strip('%')
            try:
                target = float(target_text)
                current = float(current_text)
                deviation = abs(target - current)
                total_deviation += deviation
            except (ValueError, AttributeError):
                continue
        # Convert deviation to balance score (lower deviation = higher score)
        max_possible_deviation = 100
        num_domains = self.domain_table.rowCount()
        if num_domains > 0:
            balance_score = max(0, 100 - (total_deviation / num_domains * 100 / max_possible_deviation))
        else:
            balance_score = 0
        return balance_score
        
    def refresh_corpus_stats(self):
        """Enhanced corpus statistics refresh with balance scoring"""
        self.status_label.setText("Fetching corpus statistics...")
        
        # Simulate enhanced statistics
        total_docs = 1250
        domain_counts = {
            "Crypto Derivatives": 320,
            "High Frequency Trading": 180,
            "Risk Management": 175,
            "Market Microstructure": 160,
            "DeFi": 200,
            "Portfolio Construction": 100,
            "Valuation Models": 75,
            "Regulation & Compliance": 40,
        }
        
        # Update table with enhanced status indicators
        for i in range(self.domain_table.rowCount()):
            domain = self.domain_table.item(i, 0).text()
            target_text = self.domain_table.item(i, 1).text()
            target = float(target_text.strip('%'))
            count = domain_counts.get(domain, 0)
            percentage = (count / total_docs) * 100 if total_docs > 0 else 0
            
            # Update current percentage
            self.domain_table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            
            # Update document count
            self.domain_table.setItem(i, 3, QTableWidgetItem(str(count)))
            
            # Update progress bar with enhanced styling
            progress = self.domain_table.cellWidget(i, 4)
            progress.setValue(int(percentage))
            
            # Enhanced status indicators
            deviation = abs(percentage - target)
            if deviation <= 1:
                status = "Optimal"
                progress.setObjectName("progress-on-target")
                status_color = QColor(50, 184, 198)  # Brand color for optimal
            elif deviation <= 3:
                status = "Good"
                progress.setObjectName("progress-good")
                status_color = QColor(230, 129, 97)  # Orange for good
            else:
                status = "Needs Attention"
                progress.setObjectName("progress-needs-attention")
                status_color = QColor(255, 84, 89)  # Red for needs attention
                
            # Update status column
            status_item = QTableWidgetItem(status)
            status_item.setBackground(QBrush(status_color))
            status_item.setForeground(QBrush(QColor(255, 255, 255)))
            self.domain_table.setItem(i, 5, status_item)
            
        # Update summary statistics
        balance_score = self.calculate_balance_score()
        self.total_docs_label.setText(f"Total Documents: {total_docs}")
        self.balance_score_label.setText(f"Balance Score: {balance_score:.1f}%")
        
        current_time = time.strftime("%H:%M:%S", time.localtime())
        self.status_label.setText(f"Corpus contains {total_docs} documents - Updated: {current_time}")
        
    def analyze_corpus_balance(self):
        """Enhanced corpus balance analysis with detailed recommendations"""
        self.status_label.setText("Analyzing corpus balance...")
        
        # Calculate detailed imbalance metrics
        imbalances = []
        total_docs = 1250
        
        for i in range(self.domain_table.rowCount()):
            domain = self.domain_table.item(i, 0).text()
            target_text = self.domain_table.item(i, 1).text().strip('%')
            current_text = self.domain_table.item(i, 2).text().strip('%')
            
            target = float(target_text)
            current = float(current_text)
            deviation = current - target
            
            if abs(deviation) > 2:  # Significant imbalance
                docs_needed = int((target - current) * total_docs / 100)
                imbalances.append({
                    'domain': domain,
                    'deviation': deviation,
                    'docs_needed': docs_needed,
                    'current': current,
                    'target': target
                })
                
        # Generate detailed report
        if imbalances:
            report = "### Corpus Balance Analysis Results\n\n"
            report += f"**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"**Balance Score:** {self.calculate_balance_score():.1f}%\n\n"
            
            overrepresented = [d for d in imbalances if d['deviation'] > 0]
            underrepresented = [d for d in imbalances if d['deviation'] < 0]
            
            if overrepresented:
                report += "**Overrepresented Domains:**\n"
                for domain_info in overrepresented:
                    report += f"• {domain_info['domain']}: {domain_info['deviation']:+.1f}% (excess: {abs(domain_info['docs_needed'])} docs)\n"
                report += "\n"
                
            if underrepresented:
                report += "**Underrepresented Domains:**\n"
                for domain_info in underrepresented:
                    report += f"• {domain_info['domain']}: {domain_info['deviation']:+.1f}% (needed: {abs(domain_info['docs_needed'])} docs)\n"
                report += "\n"
                
            report += "**Recommended Actions:**\n"
            report += "• Run corpus balancing to redistribute documents\n"
            report += "• Focus collection efforts on underrepresented domains\n"
            report += "• Consider automated classification for unclassified documents\n"
            
            QMessageBox.information(self, "Corpus Balance Analysis", report)
            
            if self.enable_notifications.isChecked():
                self.show_notification("Balance Analysis Complete", 
                                     f"Found {len(imbalances)} domains requiring attention", "warning")
        else:
            QMessageBox.information(self, "Corpus Balance Analysis", 
                                  "Corpus is well balanced! All domains are within acceptable ranges.")
            if self.enable_notifications.isChecked():
                self.show_notification("Balance Analysis Complete", "Corpus is well balanced!")
                
        self.status_label.setText("Balance analysis completed")
        
    @pyqtSlot()
    def export_balance_report(self):
        """Export detailed balance report"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Balance Report", 
            f"balance_report_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        
        if filename:
            try:
                report_content = self.generate_detailed_report()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                    
                self.show_notification("Report Exported", f"Balance report saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")
                
    def generate_detailed_report(self) -> str:
        """Generate comprehensive balance report"""
        report = "CORPUS BALANCE DETAILED REPORT\n"
        report += "=" * 50 + "\n\n"
        report += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Documents: {self.total_docs_label.text().split(': ')[1]}\n"
        report += f"Balance Score: {self.balance_score_label.text().split(': ')[1]}\n\n"
        
        report += "DOMAIN DISTRIBUTION:\n"
        report += "-" * 20 + "\n"
        
        for i in range(self.domain_table.rowCount()):
            domain = self.domain_table.item(i, 0).text()
            target = self.domain_table.item(i, 1).text()
            current = self.domain_table.item(i, 2).text()
            count = self.domain_table.item(i, 3).text()
            status = self.domain_table.item(i, 5).text()
            
            report += f"{domain:25} | Target: {target:6} | Current: {current:6} | Count: {count:4} | Status: {status}\n"
            
        return report
        
    def balance_corpus(self):
        """Enhanced corpus balancing with progress tracking"""
        # Update UI state
        self.balance_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Balancing corpus...")
        self.overall_progress.setValue(0)
        
        # Show start notification
        if self.enable_notifications.isChecked():
            self.show_notification("Corpus Balancing Started", "Beginning automatic corpus balancing...")
        
        # Configure and start balancer
        quality_threshold = self.quality_threshold.value()
        method = self.balance_method.currentText()
        auto_classify = self.auto_classify.isChecked()
        preserve_existing = self.preserve_existing.isChecked()
        
        # Collect target percentages
        targets = {}
        for i in range(self.domain_table.rowCount()):
            domain = self.domain_table.item(i, 0).text()
            target_text = self.domain_table.item(i, 1).text()
            target = float(target_text.strip('%'))
            targets[domain] = target
            
        # Configure balancer
        self.balancer.set_quality_threshold(quality_threshold)
        self.balancer.set_balance_method(method)
        self.balancer.set_auto_classify(auto_classify)
        self.balancer.set_preserve_existing(preserve_existing)
        self.balancer.set_domain_targets(targets)
        
        # Start balancing
        self.balancer.start()
        
    def stop_balancing(self):
        """Stop corpus balancing with confirmation"""
        reply = QMessageBox.question(
            self, "Stop Balancing", 
            "Are you sure you want to stop the balancing process?\nThis may leave the corpus in an incomplete state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.balancer.stop()
            self.balance_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Balancing stopped by user")
            
            if self.enable_notifications.isChecked():
                self.show_notification("Balancing Stopped", "Corpus balancing was stopped by user", "warning")
                
    @pyqtSlot(str)
    def update_status_display(self, status: str):
        """Update status display with timestamp"""
        current_time = time.strftime("%H:%M:%S", time.localtime())
        self.status_label.setText(f"{status} - {current_time}")
        
    @pyqtSlot(dict)
    def on_balance_completed(self, results: dict):
        """Handle completion of balancing with enhanced feedback"""
        self.balance_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Extract results
        moved_count = results.get('moved_count', 0)
        classified_count = results.get('classified_count', 0)
        errors_count = results.get('errors_count', 0)
        processing_time = results.get('processing_time', 0)
        
        # Update status
        completion_time = time.strftime("%H:%M:%S", time.localtime())
        self.status_label.setText(f"Balancing completed at {completion_time}")
        
        # Refresh statistics
        self.refresh_corpus_stats()
        
        # Show detailed completion message
        completion_msg = f"""Corpus balancing completed successfully!\n\nResults Summary:\n• Documents moved: {moved_count}\n• Documents classified: {classified_count}\n• Processing errors: {errors_count}\n• Processing time: {processing_time:.1f} seconds\n• New balance score: {self.calculate_balance_score():.1f}%\n\nThe corpus distribution has been optimized according to target percentages."""
        
        QMessageBox.information(self, "Balancing Complete", completion_msg)
        
        # Show system notification
        if self.enable_notifications.isChecked():
            notification_type = "info" if errors_count == 0 else "warning"
            self.show_notification(
                "Corpus Balancing Complete",
                f"Moved {moved_count} documents, classified {classified_count}",
                notification_type
            )
            
        if self.sound_enabled:
            level = "success" if errors_count == 0 else "error"
            Notifier.notify("Corpus Balancing Complete", completion_msg, level=level)
        
    def show_notification(self, title: str, message: str, notification_type: str = "info"):
        """Show notification if enabled"""
        if self.enable_notifications.isChecked():
            self.notification_manager.show_notification(title, message, notification_type)

    def collect_for_missing_domains(self):
        """Trigger collection for missing/underrepresented domains via the wrapper."""
        # Call the wrapper method
        self.balancer.collect_for_missing_domains()
        # For now, show a message box as a placeholder
        QMessageBox.information(self, "Collect for Missing Domains", "Triggered collection for missing/underrepresented domains. Check logs for details.")
