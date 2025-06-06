import os
import json
import time
import datetime
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from PyPDF2 import PdfReader
import sys

class CorpusMonitor:
    def __init__(self, corpus_dir, output_dir, interval=300):
        """Initialize the corpus monitor.
        
        Args:
            corpus_dir: Directory containing the corpus
            output_dir: Directory to save monitoring reports
            interval: Monitoring interval in seconds (default: 5 minutes)
        """
        self.corpus_dir = Path(corpus_dir)
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize stats storage
        self.stats_file = self.output_dir / 'corpus_stats.json'
        self.history_file = self.output_dir / 'corpus_history.csv'
        self.error_log_file = self.output_dir / 'error_log.json'
        self.redownload_queue_file = self.output_dir / 'redownload_queue.json'
        self.dashboard_file = self.output_dir / 'extraction_dashboard.json'
        self.status_log_file = self.output_dir / 'status_log.json'
        self.current_stats = {}
        self.history = []
        self.new_errors = []
        self.status_milestones = set()
        
        # Load previous history if available
        if self.history_file.exists():
            try:
                self.history = pd.read_csv(self.history_file).to_dict('records')
            except:
                pass
    
    def log_error(self, error_type, file_path, domain, details):
        entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'error_type': error_type,
            'file_path': str(file_path),
            'domain': domain,
            'details': details
        }
        self.new_errors.append(entry)
        # Append to error log file
        if self.error_log_file.exists():
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = []
        log.append(entry)
        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)

    def add_to_redownload_queue(self, file_path, domain, reason):
        entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'file_path': str(file_path),
            'domain': domain,
            'reason': reason
        }
        if self.redownload_queue_file.exists():
            with open(self.redownload_queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        else:
            queue = []
        queue.append(entry)
        with open(self.redownload_queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2)

    def check_pdf_integrity(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as f:
                PdfReader(f)
            return True
        except Exception as e:
            return False

    def check_txt_integrity(self, txt_path, min_bytes=100):
        try:
            size = os.path.getsize(txt_path)
            if size < min_bytes:
                return False, size
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                return False, size
            return True, size
        except Exception as e:
            return False, 0

    def log_status(self, milestone, processed, total, elapsed, error_count):
        entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'milestone': milestone,
            'processed': processed,
            'total': total,
            'percent': int((processed / total) * 100) if total > 0 else 0,
            'elapsed_seconds': elapsed,
            'error_count': error_count
        }
        # Print to console
        print(f"[STATUS] {milestone} - {processed}/{total} files processed ({entry['percent']}%), {error_count} errors, elapsed: {elapsed:.1f}s")
        # Append to status log
        if self.status_log_file.exists():
            with open(self.status_log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = []
        log.append(entry)
        with open(self.status_log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)

    def check_and_retry_errors(self):
        # Placeholder: In a real system, would attempt to re-download files in redownload_queue.json
        # For now, just log that a retry would be attempted
        if self.redownload_queue_file.exists():
            with open(self.redownload_queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            for entry in queue:
                retry_entry = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'action': 'retry_attempt',
                    'file_path': entry['file_path'],
                    'domain': entry['domain'],
                    'reason': entry['reason'],
                    'outcome': 'placeholder_not_implemented'  # In real use, would update after retry
                }
                # Log to status log
                if self.status_log_file.exists():
                    with open(self.status_log_file, 'r', encoding='utf-8') as f:
                        log = json.load(f)
                else:
                    log = []
                log.append(retry_entry)
                with open(self.status_log_file, 'w', encoding='utf-8') as f:
                    json.dump(log, f, indent=2)

    def collect_stats(self):
        """Collect statistics about the corpus."""
        stats = {
            'timestamp': datetime.datetime.now().isoformat(),
            'domains': {},
            'total_files': 0,
            'total_size_mb': 0,
            'extracted_files': 0
        }
        dashboard = {}
        self.new_errors = []
        domains = [d for d in os.listdir(self.corpus_dir)
                  if os.path.isdir(os.path.join(self.corpus_dir, d))
                  and not d.endswith('_extracted')]
        # For analytics
        overall = {
            'total_pdfs': 0,
            'corrupted_pdfs': 0,
            'total_txts': 0,
            'empty_txts': 0,
            'missing_extractions': 0,
            'failed_downloads': 0  # Will be filled from redownload_queue
        }
        for domain in domains:
            domain_dir = self.corpus_dir / domain
            extracted_dir = self.corpus_dir / f"{domain}_extracted"
            pdf_files = list(domain_dir.glob("*.pdf"))
            domain_size = sum(os.path.getsize(f) for f in pdf_files) / (1024 * 1024)  # MB
            corrupted_pdfs = []
            for pdf in pdf_files:
                if not self.check_pdf_integrity(pdf):
                    self.log_error('corrupted_pdf', pdf, domain, 'Unreadable or corrupted PDF. Auto-deleted.')
                    self.add_to_redownload_queue(pdf, domain, 'corrupted_pdf')
                    corrupted_pdfs.append(pdf)
            # Auto-delete corrupted PDFs
            for pdf in corrupted_pdfs:
                try:
                    os.remove(pdf)
                except Exception as e:
                    self.log_error('delete_failed', pdf, domain, f'Failed to delete: {e}')
            # Remove corrupted from list
            pdf_files = [f for f in pdf_files if f not in corrupted_pdfs]
            extracted_files = []
            empty_txts = []
            if extracted_dir.exists():
                for txt in extracted_dir.glob("*.txt"):
                    ok, size = self.check_txt_integrity(txt)
                    if not ok:
                        self.log_error('empty_or_small_txt', txt, domain, f'Extracted text file is empty or too small ({size} bytes).')
                        empty_txts.append(txt)
                    extracted_files.append(txt)
            missing_extractions = [str(f) for f in pdf_files if (extracted_dir / (f.stem + '.txt')).exists() == False]
            stats['domains'][domain] = {
                'file_count': len(pdf_files),
                'size_mb': domain_size,
                'extracted_count': len(extracted_files),
                'corrupted_pdfs': len(corrupted_pdfs),
                'empty_txts': len(empty_txts),
                'missing_extractions': len(missing_extractions)
            }
            dashboard[domain] = {
                'total_pdfs': len(pdf_files) + len(corrupted_pdfs),
                'corrupted_pdfs': [str(f) for f in corrupted_pdfs],
                'corrupted_pct': (len(corrupted_pdfs) / (len(pdf_files) + len(corrupted_pdfs)) * 100) if (len(pdf_files) + len(corrupted_pdfs)) > 0 else 0,
                'total_txts': len(extracted_files),
                'empty_txts': [str(f) for f in empty_txts],
                'empty_txt_pct': (len(empty_txts) / len(extracted_files) * 100) if len(extracted_files) > 0 else 0,
                'missing_extractions': missing_extractions,
                'missing_extractions_pct': (len(missing_extractions) / (len(pdf_files) + len(corrupted_pdfs)) * 100) if (len(pdf_files) + len(corrupted_pdfs)) > 0 else 0
            }
            overall['total_pdfs'] += len(pdf_files) + len(corrupted_pdfs)
            overall['corrupted_pdfs'] += len(corrupted_pdfs)
            overall['total_txts'] += len(extracted_files)
            overall['empty_txts'] += len(empty_txts)
            overall['missing_extractions'] += len(missing_extractions)
            stats['total_files'] += len(pdf_files)
            stats['total_size_mb'] += domain_size
            stats['extracted_files'] += len(extracted_files)
        # Failed downloads from redownload_queue
        if self.redownload_queue_file.exists():
            with open(self.redownload_queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            overall['failed_downloads'] = len(queue)
        # Compute overall analytics
        overall['corrupted_pct'] = (overall['corrupted_pdfs'] / overall['total_pdfs'] * 100) if overall['total_pdfs'] > 0 else 0
        overall['empty_txt_pct'] = (overall['empty_txts'] / overall['total_txts'] * 100) if overall['total_txts'] > 0 else 0
        overall['missing_extractions_pct'] = (overall['missing_extractions'] / overall['total_pdfs'] * 100) if overall['total_pdfs'] > 0 else 0
        overall['failed_downloads_pct'] = (overall['failed_downloads'] / overall['total_pdfs'] * 100) if overall['total_pdfs'] > 0 else 0
        overall['successful_extractions_pct'] = ((overall['total_txts'] - overall['empty_txts']) / overall['total_pdfs'] * 100) if overall['total_pdfs'] > 0 else 0
        dashboard['overall'] = overall
        self.current_stats = stats
        self.history.append(stats)
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        with open(self.dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        history_df = pd.DataFrame([{
            'timestamp': entry['timestamp'],
            'total_files': entry['total_files'],
            'total_size_mb': entry['total_size_mb'],
            'extracted_files': entry['extracted_files'],
            **{f"{domain}_files": entry['domains'].get(domain, {}).get('file_count', 0)
               for domain in set().union(*[entry['domains'].keys() for entry in self.history])}
        } for entry in self.history])
        history_df.to_csv(self.history_file, index=False)
        return stats
    
    def generate_report(self):
        """Generate a report of the current progress."""
        if not self.current_stats:
            self.collect_stats()
        
        # Create a detailed report
        report = f"""
        =========================================
        CORPUS BUILDING PROGRESS REPORT
        =========================================
        Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        OVERVIEW:
        -----------------------------------------
        Total Files:       {self.current_stats['total_files']}
        Total Size:        {self.current_stats['total_size_mb']:.2f} MB
        Extracted Files:   {self.current_stats['extracted_files']}
        
        DOMAIN BREAKDOWN:
        -----------------------------------------
        """
        
        for domain, stats in sorted(self.current_stats['domains'].items(), 
                                   key=lambda x: x[1]['file_count'], reverse=True):
            report += f"  {domain}:\n"
            report += f"    Files:      {stats['file_count']}\n"
            report += f"    Size:       {stats['size_mb']:.2f} MB\n"
            report += f"    Extracted:  {stats['extracted_count']}\n"
            report += f"    Corrupted PDFs: {stats['corrupted_pdfs']}\n"
            report += f"    Empty/Small TXTs: {stats['empty_txts']}\n"
            report += f"    Missing Extractions: {stats['missing_extractions']}\n\n"
        
        # Save the report
        report_file = self.output_dir / f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"Report saved to {report_file}")
        
        # Print new errors summary
        if self.new_errors:
            print("\nNew errors detected:")
            for err in self.new_errors:
                print(f"[{err['timestamp']}] {err['error_type']} - {err['file_path']} ({err['details']})")
        
        return report
    
    def generate_charts(self):
        """Generate charts showing progress over time."""
        if not self.history:
            print("No history available for charts")
            return
        
        # Convert to DataFrame for easier plotting
        history_df = pd.DataFrame([{
            'timestamp': entry['timestamp'],
            'total_files': entry['total_files'],
            'total_size_mb': entry['total_size_mb'],
            'extracted_files': entry['extracted_files'],
            **{f"{domain}_files": entry['domains'].get(domain, {}).get('file_count', 0) 
               for domain in set().union(*[entry['domains'].keys() for entry in self.history])}
        } for entry in self.history])
        
        # Convert timestamp to datetime
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        # Create charts directory
        charts_dir = self.output_dir / 'charts'
        charts_dir.mkdir(exist_ok=True)
        
        # Plot total files over time
        plt.figure(figsize=(12, 6))
        plt.plot(history_df['timestamp'], history_df['total_files'], marker='o')
        plt.title('Total Files Over Time')
        plt.xlabel('Time')
        plt.ylabel('Number of Files')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(charts_dir / 'total_files_over_time.png')
        
        # Plot total size over time
        plt.figure(figsize=(12, 6))
        plt.plot(history_df['timestamp'], history_df['total_size_mb'], marker='o')
        plt.title('Total Size Over Time')
        plt.xlabel('Time')
        plt.ylabel('Size (MB)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(charts_dir / 'total_size_over_time.png')
        
        # Plot files by domain
        domain_cols = [col for col in history_df.columns if col.endswith('_files') and col != 'extracted_files']
        if domain_cols:
            plt.figure(figsize=(14, 8))
            for col in domain_cols:
                domain_name = col.replace('_files', '')
                plt.plot(history_df['timestamp'], history_df[col], marker='o', label=domain_name)
            plt.title('Files by Domain Over Time')
            plt.xlabel('Time')
            plt.ylabel('Number of Files')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(charts_dir / 'files_by_domain_over_time.png')
        
        print(f"Charts saved to {charts_dir}")
    
    def run(self):
        """Run the monitoring loop."""
        print(f"Starting corpus monitoring at {datetime.datetime.now()}")
        print(f"Monitoring directory: {self.corpus_dir}")
        print(f"Interval: {self.interval} seconds")
        print(f"Press Ctrl+C to stop...")
        start_time = time.time()
        processed = 0
        total_files = None
        milestones = [25, 50, 75]
        self.status_milestones = set()
        try:
            while True:
                stats = self.collect_stats()
                processed = stats['total_files']
                if total_files is None:
                    # Estimate total files as the max seen so far
                    total_files = max(processed, 1)
                percent = int((processed / total_files) * 100) if total_files > 0 else 0
                elapsed = time.time() - start_time
                # Check for milestone notifications
                for m in milestones:
                    if percent >= m and m not in self.status_milestones:
                        error_count = 0
                        if self.error_log_file.exists():
                            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                                error_count = len(json.load(f))
                        self.log_status(f"{m}% milestone", processed, total_files, elapsed, error_count)
                        self.status_milestones.add(m)
                print(f"\n[{datetime.datetime.now()}] Collected stats:")
                print(f"  Total files: {stats['total_files']}")
                print(f"  Total size: {stats['total_size_mb']:.2f} MB")
                # Check and log error recovery attempts
                self.check_and_retry_errors()
                if stats['total_files'] % 10 == 0:  # Generate report every 10 files
                    self.generate_report()
                if stats['total_files'] % 50 == 0:  # Generate charts every 50 files
                    self.generate_charts()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            self.generate_report()
            self.generate_charts()
        
        print("Final report generated")

def main():
    """Main function to parse arguments and start monitoring."""
    parser = argparse.ArgumentParser(description='Monitor corpus building progress')
    parser.add_argument('--corpus-dir', default='/workspace/data/corpus_multi',
                       help='Directory containing the corpus')
    parser.add_argument('--output-dir', default='/workspace/data/monitoring',
                       help='Directory to save monitoring reports')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 5 minutes)')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate a report without continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = CorpusMonitor(args.corpus_dir, args.output_dir, args.interval)
    
    if args.report_only:
        monitor.collect_stats()
        monitor.generate_report()
        monitor.generate_charts()
    else:
        monitor.run()

if __name__ == '__main__':
    main() 