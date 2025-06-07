# processors/deduplicator.py
import os
import sys
from pathlib import Path
import logging
import hashlib
import json
import re
import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Third-party imports above
# Now add project directory to sys.path for sibling module imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from shared_tools.storage.corpus_manager import CorpusManager
from shared_tools.project_config import ProjectConfig

class Deduplicator:
    """Identify and remove duplicate content in the corpus"""
    
    def __init__(self, project_config: ProjectConfig, similarity_threshold: float = 0.8, use_minhash: bool = True):
        """Initialize the deduplicator with project configuration."""

        self.project_config = project_config
        self.corpus_dir = Path(project_config.get_input_dir())
        self.similarity_threshold = similarity_threshold
        self.use_minhash = use_minhash

        # Log file setup
        self.log_path = project_config.get_logs_dir() / "dedup_log.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Indexes for duplicate detection
        self.file_hashes = {}  # Maps file hash to file paths
        self.title_index = {}  # Maps normalized title to document info
        self.minhash_index = {}  # Maps MinHash signatures to document info
        
        # Configure logging
        self.logger = logging.getLogger("deduplicator")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_path)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        if not any(
            isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(self.log_path)
            for h in self.logger.handlers
        ):
            self.logger.addHandler(handler)

        self.logger.info("Deduplicator initialized")

        # Load processed files from log if available
        self.processed_files = set()
        if self.log_path.exists():
            with open(self.log_path, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self.processed_files.add(data.get("file"))
                    except Exception:
                        continue
    
    def scan_corpus(self, rebuild_index=False):
        """Scan corpus directory to build duplicate indexes"""
        if not self.corpus_dir or not self.corpus_dir.exists():
            self.logger.error("Invalid corpus directory")
            return False
            
        # Load existing index if it exists and rebuild_index is False
        index_path = self.corpus_dir / "deduplication_index.json"
        
        if index_path.exists() and not rebuild_index:
            try:
                with open(index_path, 'r') as f:
                    index_data = json.load(f)
                    self.file_hashes = index_data.get('file_hashes', {})
                    self.title_index = index_data.get('title_index', {})
                    # MinHash index is rebuilt each time due to its structure
                    self.logger.info(f"Loaded existing deduplication index with {len(self.file_hashes)} entries")
                    return True
            except Exception as e:
                self.logger.error(f"Error loading existing index: {e}")
                # Continue and rebuild the index
        
        # Build the index
        self.logger.info("Building deduplication index...")
        self.file_hashes = {}
        self.title_index = {}
        self.minhash_index = {}
        
        # Scan all files in the corpus directory
        all_files = list(self.corpus_dir.glob("**/*"))
        total_files = len(all_files)
        
        self.logger.info(f"Scanning {total_files} files for duplicates")
        
        for i, file_path in enumerate(all_files):
            if i % 100 == 0:
                self.logger.info(f"Processed {i}/{total_files} files")
                
            if not file_path.is_file():
                continue
                
            # Skip metadata files and extracted text files
            if file_path.suffix in ['.meta', '.json'] or '_extracted' in str(file_path):
                continue
                
            # Compute file hash
            file_hash = self._compute_file_hash(file_path)
            
            if file_hash:
                # Check if this hash already exists
                if file_hash in self.file_hashes:
                    self.file_hashes[file_hash].append(str(file_path))
                else:
                    self.file_hashes[file_hash] = [str(file_path)]
                
                # Try to extract title from associated metadata
                title = self._extract_title(file_path)
                
                if title:
                    # Normalize title
                    norm_title = self._normalize_title(title)
                    
                    if norm_title:
                        # Check if this title already exists
                        if norm_title in self.title_index:
                            self.title_index[norm_title].append({
                                'path': str(file_path),
                                'hash': file_hash,
                                'original_title': title
                            })
                        else:
                            self.title_index[norm_title] = [{
                                'path': str(file_path),
                                'hash': file_hash,
                                'original_title': title
                            }]
        
        # Save the index
        try:
            with open(index_path, 'w') as f:
                json.dump({
                    'file_hashes': self.file_hashes,
                    'title_index': self.title_index
                }, f, indent=2)
                
            self.logger.info(f"Saved deduplication index with {len(self.file_hashes)} file hashes and {len(self.title_index)} titles")
        except Exception as e:
            self.logger.error(f"Error saving deduplication index: {e}")
        
        self.logger.info('scan_corpus called')
        return True
    
    def find_duplicates(self, file_paths: Optional[List[str]] = None, threshold: Optional[float] = None):
        """Find duplicate content.

        If ``file_paths`` is provided, only those files are analyzed using simple
        hash comparison. Otherwise the entire corpus index is scanned.
        """
        if file_paths:
            seen: Dict[str, str] = {}
            duplicates = []
            for path in file_paths:
                if self.should_skip(path):
                    self.logger.info(f"Skipping already processed file: {path}")
                    continue
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                    digest = hashlib.md5(data).hexdigest()
                except Exception as e:
                    self.logger.error(f"Error reading {path}: {e}")
                    continue
                if digest in seen:
                    duplicates.append({
                        "type": "identical_hash",
                        "files": [seen[digest], path],
                        "similarity": 1.0,
                    })
                else:
                    seen[digest] = path
            self.logger.info("find_duplicates called on file list")
            return duplicates

        if not self.file_hashes and not self.title_index:
            success = self.scan_corpus()
            if not success:
                return []
        
        duplicates = []
        
        # Find files with identical hashes
        for file_hash, file_paths in self.file_hashes.items():
            if len(file_paths) > 1:
                duplicates.append({
                    'type': 'identical_hash',
                    'hash': file_hash,
                    'files': file_paths
                })
        
        # Find files with same normalized title but different hashes
        for title, docs in self.title_index.items():
            if len(docs) > 1:
                # Check if they have different hashes
                hashes = set(doc['hash'] for doc in docs)
                
                if len(hashes) > 1:
                    duplicates.append({
                        'type': 'similar_title',
                        'title': title,
                        'files': [doc['path'] for doc in docs],
                        'original_titles': [doc['original_title'] for doc in docs]
                    })
        
        # Find files with similar content using MinHash (if enabled)
        if self.use_minhash:
            content_duplicates = self._find_content_duplicates()
            duplicates.extend(content_duplicates)
        
        self.logger.info('find_duplicates called')
        return duplicates
    
    def deduplicate(self, file_paths: Optional[List[str]] = None, strategy: str = 'keep_first', output_file: Optional[str] = None, token_loss_report: Optional[str] = None):
        """Remove duplicate content based on strategy.

        Args:
            file_paths (List[str], optional): Specific files to process. If ``None`` the entire corpus is scanned.
            strategy (str): Deduplication strategy:
                - 'keep_first': Keep first file in each duplicate group
                - 'keep_largest': Keep largest file in each duplicate group
                - 'move_duplicates': Move duplicates to a 'duplicates' folder
            output_file (str): Path to save deduplication report
            token_loss_report (str): Path to save token loss report (JSON)
        
        Returns:
            list: Details of deduplicated files
        """
        # --- Token count before deduplication ---
        domain_token_counts_before = self._get_domain_token_counts()
        total_tokens_before = sum(domain_token_counts_before.values())

        self.logger.info(f"Token count before deduplication: {domain_token_counts_before}")

        # Find duplicates
        duplicates = self.find_duplicates(file_paths)
        if not duplicates:
            self.logger.info("No duplicates found")
            return []
        self.logger.info(f"Found {len(duplicates)} duplicate groups")
        
        # Process each duplicate group
        deduplicated = []
        files_to_remove = set()
        for dup_group in duplicates:
            files = dup_group.get('files', [])
            if len(files) <= 1:
                continue
            # Determine which file to keep based on strategy
            if strategy == 'keep_first':
                keep_file = files[0]
            elif strategy == 'keep_largest':
                keep_file = max(files, key=lambda f: self._get_file_token_count(f))
            else:
                keep_file = files[0]
            for f in files:
                if f != keep_file:
                    files_to_remove.add(f)
                
        # Move or delete duplicates
        duplicates_dir = self.corpus_dir / 'duplicates'
        duplicates_dir.mkdir(exist_ok=True)
        for f in files_to_remove:
            src = Path(f)
            if str(src) in self.processed_files:
                self.logger.info(f"Skipping already processed file: {src}")
                self._append_log(str(src), "skipped")
                continue
            if strategy == 'move_duplicates':
                dst = duplicates_dir / src.name
                try:
                    src.rename(dst)
                    self.logger.info(f"Moved duplicate: {src} -> {dst}")
                    self._append_log(str(src), "deduplicated")
                    self.processed_files.add(str(src))
                except Exception as e:
                    self.logger.error(f"Error moving {src}: {e}")
            else:
                # Only delete if file exists
                if src.exists():
                    try:
                        src.unlink()
                        self.logger.info(f"Deleted duplicate: {src}")
                        self._append_log(str(src), "deduplicated")
                        self.processed_files.add(str(src))
                    except Exception as e:
                        self.logger.error(f"Error deleting {src}: {e}")
                else:
                    self.logger.warning(f"File not found, skipping delete: {src}")
            
        # --- Token count after deduplication ---
        domain_token_counts_after = self._get_domain_token_counts()
        total_tokens_after = sum(domain_token_counts_after.values())
        
        self.logger.info(f"Token count after deduplication: {domain_token_counts_after}")
        
        # --- Token loss report ---
        token_loss_stats = {}
        for domain in set(domain_token_counts_before.keys()).union(domain_token_counts_after.keys()):
            before = domain_token_counts_before.get(domain, 0)
            after = domain_token_counts_after.get(domain, 0)
            loss = before - after
            percent_loss = (loss / before * 100) if before > 0 else 0
            token_loss_stats[domain] = {
                'tokens_before': before,
                'tokens_after': after,
                'tokens_lost': loss,
                'percent_loss': percent_loss
            }
        token_loss_stats['TOTAL'] = {
            'tokens_before': total_tokens_before,
            'tokens_after': total_tokens_after,
            'tokens_lost': total_tokens_before - total_tokens_after,
            'percent_loss': ((total_tokens_before - total_tokens_after) / total_tokens_before * 100) if total_tokens_before > 0 else 0
        }
        self.logger.info(f"Token loss stats: {token_loss_stats}")
        if token_loss_report:
            with open(token_loss_report, 'w') as f:
                json.dump(token_loss_stats, f, indent=2)
            self.logger.info(f"Token loss report saved to {token_loss_report}")
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({'deduplicated': list(files_to_remove)}, f, indent=2)
            self.logger.info(f"Deduplication report saved to {output_file}")
        
        self.logger.info('Deduplicate completed')
        return list(files_to_remove)
    
    def _compute_file_hash(self, file_path):
        """Compute MD5 hash of a file"""
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
                    
            return md5_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error computing hash for {file_path}: {e}")
            return None
    
    def _extract_title(self, file_path):
        """Extract title from file or associated metadata"""
        # Check for metadata file
        meta_path = Path(f"{file_path}.meta")
        
        if meta_path.exists():
            try:
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('title')
            except Exception:
                pass
        
        # If no metadata or no title in metadata, use filename
        return file_path.stem
    
    def _normalize_title(self, title):
        """Normalize title for comparison"""
        if not title:
            return None
            
        # Convert to lowercase and remove special characters
        normalized = title.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        normalized = ' '.join([word for word in normalized.split() if word not in stop_words])
        
        return normalized
    
    def _find_content_duplicates(self, min_text_length=1000):
        """Find files with similar content using datasketch MinHash and LSH (scalable version)."""
        self.logger.info('_find_content_duplicates (LSH) called')
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).resolve().parent.parent))
            from datasketch import MinHash, MinHashLSH
            from processors.text_extractor import TextExtractor
            from shared_tools.storage.corpus_manager import CorpusManager
            import hashlib
            
            corpus_manager = CorpusManager(self.corpus_dir)
            self.logger.info(f"[DEBUG] CorpusManager loading from: {corpus_manager.metadata_file}")
            self.logger.info(f"[DEBUG] Documents loaded: {len(corpus_manager.metadata.get('documents', {}))}")
            extractor = TextExtractor()
            documents = corpus_manager.metadata.get("documents", {})
            if not documents:
                self.logger.warning("No documents found in corpus metadata")
                return []
            
            num_perm = 128
            lsh = MinHashLSH(threshold=self.similarity_threshold, num_perm=num_perm)
            doc_minhashes = {}
            doc_contents = {}
            valid, skipped = 0, 0
            
            def create_shingles(text, k=5):
                return set(text[i:i+k] for i in range(len(text) - k + 1))

            for doc_id, doc_info in documents.items():
                path = doc_info.get("extracted_text_path")
                if not path:
                    # Fallback: try to reconstruct path
                    domain = doc_info.get("domain")
                    stem = Path(doc_info.get("filename", "")).stem
                    fallback = self.corpus_dir / f"{domain}_extracted" / f"{stem}.txt"
                    if fallback.exists():
                        path = str(fallback)
                        doc_info["extracted_text_path"] = path
                    else:
                        skipped += 1
                    continue
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    if len(text) < min_text_length:
                        skipped += 1
                        continue
                    valid += 1
                    shingles = create_shingles(text)
                    m = MinHash(num_perm=num_perm)
                    for shingle in shingles:
                        m.update(shingle.encode('utf8'))
                    doc_minhashes[doc_id] = m
                    doc_contents[doc_id] = {
                        "text": text,
                        "path": doc_info.get("path"),
                        "extracted_path": path
                    }
                    lsh.insert(doc_id, m)
                except Exception as e:
                    self.logger.error(f"Error processing {doc_id}: {e}")
                    skipped += 1

            self.logger.info(f"[MinHashLSH] Valid docs: {valid}, Skipped: {skipped}")
            if valid == 0:
                self.logger.warning("All documents skipped — no MinHash input. Check extraction and metadata.")
                return []

            # Find duplicate groups using LSH
            seen = set()
            groups = []
            for doc_id, m in doc_minhashes.items():
                if doc_id in seen:
                    continue
                # Query for near-duplicates
                candidates = lsh.query(m)
                group = [d for d in candidates if d != doc_id and d not in seen]
                if group:
                    group = [doc_id] + group
                    for d in group:
                        seen.add(d)
                    files = [doc_contents[d]["path"] for d in group if "path" in doc_contents[d]]
                    if len(files) > 1:
                        groups.append({
                            "type": "similar_content",
                            "files": files,
                            "similarity_threshold": self.similarity_threshold
                        })
            self.logger.info(f"Found {len(groups)} content similarity duplicate groups (MinHashLSH)")
            self.logger.info(f"✅ MinHashLSH duplicate groups: {len(groups)}")
            return groups
        except ImportError as e:
            self.logger.error(f"Error importing required modules for content similarity: {e}")
            self.logger.info(f"Error importing required modules for content similarity: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error finding content duplicates: {e}")
            self.logger.info(f"Error finding content duplicates: {e}")
            return []
    
    def _get_domain_token_counts(self):
        """Helper to count total tokens per domain in the corpus."""
        domain_token_counts = {}
        for domain_dir in self.corpus_dir.glob("*"):
            if domain_dir.is_dir() and not domain_dir.name.endswith("_extracted"):
                domain = domain_dir.name
                token_count = 0
                pdf_files = list(domain_dir.glob("*.pdf"))
                for pdf_path in pdf_files:
                    extracted_dir = self.corpus_dir / f"{domain}_extracted"
                    extracted_path = extracted_dir / f"{pdf_path.stem}.txt"
                    extracted_meta_path = extracted_path.with_suffix(".meta.json")
                    if extracted_meta_path.exists():
                        try:
                            with open(extracted_meta_path, 'r') as f:
                                ext_meta = json.load(f)
                                token_count += ext_meta.get("tokens", 0)
                        except:
                            pass
                    elif extracted_path.exists():
                        try:
                            with open(extracted_path, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                token_count += len(text.split())
                        except:
                            pass
                domain_token_counts[domain] = token_count
        return domain_token_counts

    def _get_file_token_count(self, file_path):
        """Helper to get token count for a single file (by looking up extracted text/meta)."""
        file_path = Path(file_path)
        domain = file_path.parent.name
        extracted_dir = self.corpus_dir / f"{domain}_extracted"
        extracted_path = extracted_dir / f"{file_path.stem}.txt"
        extracted_meta_path = extracted_path.with_suffix(".meta.json")
        # 1. Try .meta.json file (top-level 'tokens')
        if extracted_meta_path.exists():
            try:
                with open(extracted_meta_path, 'r') as f:
                    ext_meta = json.load(f)
                    tokens = ext_meta.get("tokens", 0)
                    if tokens:
                        return tokens
            except:
                pass
        # 2. Try .txt file (count whitespace tokens)
        if extracted_path.exists():
            try:
                with open(extracted_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    tokens = len(text.split())
                    if tokens:
                        return tokens
            except:
                pass
        # 3. Try .json file (nested token_count)
        extracted_json_path = extracted_dir / f"{file_path.stem}.json"
        if extracted_json_path.exists():
            try:
                with open(extracted_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    # Look for nested token_count
                    qmetrics = data.get("quality_metrics", {})
                    eq = qmetrics.get("extraction_quality", {})
                    token_count = eq.get("token_count", 0)
                    if token_count:
                        return token_count
            except Exception as e:
                pass
        return 0

    def _append_log(self, file_path: str, result: str) -> None:
        entry = {
            "file": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
        }
        with open(self.log_path, "a") as lf:
            lf.write(json.dumps(entry) + "\n")

    def should_skip(self, file_path: str) -> bool:
        """Return True if the file has already been processed."""
        return str(file_path) in self.processed_files

    def get_statistics(self) -> dict:
        """Return simple processing statistics."""
        return {"processed": len(self.processed_files)}

def run_with_project_config(project: 'ProjectConfig', verbose: bool = False):
    """Run deduplicator with project configuration
    
    Args:
        project (ProjectConfig): Project configuration
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Deduplication results
    """
    cfg = project.get_processor_config('deduplicator')
    deduplicator = Deduplicator(
        project_config=project,
        similarity_threshold=cfg.get('similarity_threshold', 0.8),
        use_minhash=cfg.get('use_minhash', True),
    )
    
    # Run deduplication
    deduplicator.scan_corpus()
    duplicates = deduplicator.find_duplicates()

    if verbose:
        deduplicator.logger.info(f"Found {len(duplicates)} duplicate groups")
    
    return {
        'duplicates': duplicates,
        'stats': deduplicator.get_statistics()
    }

def main():
    """Main entry point when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deduplicate corpus content')
    parser.add_argument('--project-config', required=True, help='Path to project config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    from shared_tools.project_config import ProjectConfig
    project = ProjectConfig.load(args.project_config)
    results = run_with_project_config(project, args.verbose)
    
    logger = logging.getLogger("deduplicator")
    logger.info("\nDeduplication Results:")
    logger.info(f"Found {len(results.get('duplicates', []))} duplicate groups")
    
    if args.verbose:
        for dup in results.get('duplicates', []):
            logger.info("\nDuplicate Group:")
            for file in dup.get('files', []):
                logger.info(f"  - {file}")

if __name__ == "__main__":
    main()
