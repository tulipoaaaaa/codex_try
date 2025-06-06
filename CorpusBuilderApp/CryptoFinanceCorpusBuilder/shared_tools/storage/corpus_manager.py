# storage/corpus_manager.py
import os
import json
import shutil
import logging
import datetime
from pathlib import Path
import uuid
import numpy as np
from collections import Counter
from math import log2
from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS

class CorpusManager:
    """Manage the crypto-finance corpus structure"""
    
    def __init__(self, project_config=None, base_dir=None):
        # Support both ProjectConfig and legacy mode
        if project_config:
            self.base_dir = Path(project_config.environments[project_config.environment].corpus_dir)
            self.domain_config = project_config.domains
            self.log_dir = Path(project_config.environments[project_config.environment].log_dir)
            self.directories = project_config.directories
        else:
            self.base_dir = Path(base_dir)
            try:
                from shared_tools.config.domain_config import DOMAINS
                self.domain_config = DOMAINS
            except ImportError:
                self.domain_config = {}
            self.log_dir = Path("G:/ai_trading_dev/CryptoFinanceCorpusBuilder/logs")
            self.directories = {
                "raw_data": "raw_data",
                "extracted": "extracted",
                "processed": "processed",
                "reports": "reports",
                "logs": "logs"
            }
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create domain directories
        self._create_domain_directories()
        
        # Configure logging
        self.logger = self._setup_logger()
        
        # Metadata storage
        self.metadata_file = self.base_dir / "corpus_metadata.json"
        self.metadata = self._load_metadata()
        
        self.logger.info(f"Initialized corpus manager at {self.base_dir}")
    
    def _create_domain_directories(self):
        """Create directories for each domain"""
        for domain in self.domain_config:
            # Create main domain directory
            domain_dir = self.base_dir / self.directories["raw_data"] / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create extracted text directory
            extracted_dir = self.base_dir / self.directories["extracted"] / domain
            extracted_dir.mkdir(parents=True, exist_ok=True)
            
            # Create processed directory
            processed_dir = self.base_dir / self.directories["processed"] / domain
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Create reports directory
            reports_dir = self.base_dir / self.directories["reports"] / domain
            reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """Set up logging with both console and file handlers"""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            self.log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_dir / "corpus_manager.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_metadata(self):
        """Load corpus metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading metadata: {e}")
                return self._initialize_metadata()
        else:
            return self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Initialize empty metadata structure"""
        metadata = {
            "creation_date": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat(),
            "total_documents": 0,
            "domains": {},
            "sources": {},
            "documents": {}
        }
        
        # Initialize domain stats
        for domain in self.domain_config:
            metadata["domains"][domain] = {
                "document_count": 0,
                "extracted_count": 0,
                "total_size_bytes": 0
            }
        
        return metadata
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            self.metadata["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            self.logger.debug("Saved corpus metadata")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
    
    def add_document(self, source_path, domain, metadata=None, move=False):
        """Add a document to the corpus"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {source_path}")
            return None
        
        # Verify domain exists
        if domain not in self.domain_config:
            self.logger.warning(f"Unknown domain: {domain}, creating it")
            domain_dir = self.base_dir / self.directories["raw_data"] / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            # Add to domain config
            self.domain_config[domain] = {"allocation": 0.0, "search_terms": []}
            
            # Add to metadata
            if domain not in self.metadata["domains"]:
                self.metadata["domains"][domain] = {
                    "document_count": 0,
                    "extracted_count": 0,
                    "total_size_bytes": 0
                }
        
        # Generate document ID if not in metadata
        doc_id = str(uuid.uuid4())
        
        # Determine target path
        target_dir = self.base_dir / self.directories["raw_data"] / domain
        
        # Use original filename or clean version of it
        filename = source_path.name
        
        # Ensure filename doesn't already exist, append ID if needed
        target_path = target_dir / filename
        if target_path.exists():
            # Append first 8 chars of ID to filename
            name_parts = source_path.stem, source_path.suffix
            new_filename = f"{name_parts[0]}_{doc_id[:8]}{name_parts[1]}"
            target_path = target_dir / new_filename
        
        # Copy or move the file
        try:
            if move:
                shutil.move(str(source_path), str(target_path))
                self.logger.info(f"Moved {source_path} to {target_path}")
            else:
                shutil.copy2(str(source_path), str(target_path))
                self.logger.info(f"Copied {source_path} to {target_path}")
        except Exception as e:
            self.logger.error(f"Error copying/moving file: {e}")
            return None
        
        # Prepare document metadata
        doc_metadata = {
            "id": doc_id,
            "domain": domain,
            "filename": target_path.name,
            "path": str(target_path),
            "source_path": str(source_path),
            "size_bytes": target_path.stat().st_size,
            "date_added": datetime.datetime.now().isoformat(),
            "file_type": target_path.suffix.lstrip('.').lower(),
            "processing_status": {
                "extracted": False,
                "quality_checked": False,
                "balanced": False
            }
        }
        
        # Add user-provided metadata
        if metadata:
            doc_metadata.update(metadata)
        
        # Add to metadata
        self.metadata["documents"][doc_id] = doc_metadata
        self.metadata["domains"][domain]["document_count"] += 1
        self.metadata["domains"][domain]["total_size_bytes"] += doc_metadata["size_bytes"]
        self.metadata["total_documents"] += 1
        
        # Track source if available
        source = metadata.get("source") if metadata else None
        if source:
            if source not in self.metadata["sources"]:
                self.metadata["sources"][source] = {
                    "document_count": 0,
                    "total_size_bytes": 0
                }
            self.metadata["sources"][source]["document_count"] += 1
            self.metadata["sources"][source]["total_size_bytes"] += doc_metadata["size_bytes"]
        
        # Save metadata
        self._save_metadata()
        
        return doc_id
    
    def add_extracted_text(self, doc_id, text_content, metadata=None):
        """Add extracted text for a document"""
        if doc_id not in self.metadata["documents"]:
            self.logger.error(f"Document not found: {doc_id}")
            return False
        
        doc_info = self.metadata["documents"][doc_id]
        domain = doc_info["domain"]
        
        # Create output path
        extracted_dir = self.base_dir / self.directories["extracted"] / domain
        filename = Path(doc_info["filename"]).stem + ".txt"
        output_path = extracted_dir / filename
        
        # Write extracted text to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
                
            # Update metadata
            doc_info["extracted_text_path"] = str(output_path)
            doc_info["extraction_date"] = datetime.datetime.now().isoformat()
            doc_info["processing_status"]["extracted"] = True
            
            if metadata:
                if "extraction_metadata" not in doc_info:
                    doc_info["extraction_metadata"] = {}
                doc_info["extraction_metadata"].update(metadata)
            
            # Update domain stats
            self.metadata["domains"][domain]["extracted_count"] += 1
            
            # Save metadata
            self._save_metadata()
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving extracted text: {e}")
            return False
    
    def update_processing_status(self, doc_id, status_type, status=True):
        """Update processing status for a document"""
        if doc_id in self.metadata["documents"]:
            self.metadata["documents"][doc_id]["processing_status"][status_type] = status
            self._save_metadata()
            return True
        return False
    
    def get_document_path(self, doc_id, stage="raw"):
        """Get document path for a specific processing stage"""
        if doc_id not in self.metadata["documents"]:
            return None
            
        doc_info = self.metadata["documents"][doc_id]
        domain = doc_info["domain"]
        
        if stage == "raw":
            return Path(doc_info["path"])
        elif stage == "extracted":
            return Path(doc_info.get("extracted_text_path", ""))
        elif stage == "processed":
            return self.base_dir / self.directories["processed"] / domain / Path(doc_info["filename"]).stem
        return None
    
    def get_corpus_stats(self, top_n: int = 5):
        """Get advanced statistics for the corpus"""
        stats = {
            "total_documents": self.metadata["total_documents"],
            "total_size_bytes": sum(domain["total_size_bytes"] for domain in self.metadata["domains"].values()),
            "domains": {},
            "sources": {},
            "processing_status": {
                "extracted": 0,
                "quality_checked": 0,
                "balanced": 0
            },
            # Advanced statistics
            "token_count_stats": {},
            "file_type_distribution": {},
            "language_distribution": {},
            "quality_flag_distribution": {},
            "date_range": {},
            "domain_metrics": {},
            "document_metrics": {
                "largest": [],
                "smallest": []
            },
            "author_metrics": {},
            "source_metrics": {},
            "duplicate_analysis": {}
        }
        
        # Calculate domain statistics
        for domain, data in self.metadata["domains"].items():
            stats["domains"][domain] = {
                "document_count": data["document_count"],
                "extracted_count": data["extracted_count"],
                "total_size_bytes": data["total_size_bytes"],
                "extraction_ratio": data["extracted_count"] / data["document_count"] if data["document_count"] > 0 else 0
            }
        
        # Calculate source statistics
        for source, data in self.metadata["sources"].items():
            stats["sources"][source] = {
                "document_count": data["document_count"],
                "total_size_bytes": data["total_size_bytes"]
            }
        
        # Calculate processing status
        for doc in self.metadata["documents"].values():
            status = doc.get("processing_status", {})
            if status.get("extracted"):
                stats["processing_status"]["extracted"] += 1
            if status.get("quality_checked"):
                stats["processing_status"]["quality_checked"] += 1
            if status.get("balanced"):
                stats["processing_status"]["balanced"] += 1
        
        # Advanced Statistics Calculation
        docs = list(self.metadata.get("documents", {}).values())
        if docs:
            # Token count statistics
            token_counts = [d.get("token_count", 0) for d in docs if isinstance(d.get("token_count", 0), (int, float))]
            if token_counts:
                stats["token_count_stats"] = {
                    "total": int(np.sum(token_counts)),
                    "mean": float(np.mean(token_counts)),
                    "median": float(np.median(token_counts)),
                    "min": int(np.min(token_counts)),
                    "max": int(np.max(token_counts)),
                    "std_dev": float(np.std(token_counts))
                }
            
            # File type distribution
            file_types = [d.get("file_type", "unknown") for d in docs]
            stats["file_type_distribution"] = dict(Counter(file_types))
            
            # Language distribution
            languages = [d.get("language", "unknown") for d in docs if d.get("language")]
            if languages:
                stats["language_distribution"] = dict(Counter(languages))
            
            # Quality flag distribution
            quality_flags = [d.get("quality_flag", "unknown") for d in docs]
            stats["quality_flag_distribution"] = dict(Counter(quality_flags))
            
            # Date range analysis
            dates = [d.get("date_added") or d.get("extraction_date") for d in docs if d.get("date_added") or d.get("extraction_date")]
            try:
                date_objs = [datetime.datetime.fromisoformat(dt) for dt in dates if dt]
                if date_objs:
                    stats["date_range"] = {
                        "earliest": min(date_objs).isoformat(),
                        "latest": max(date_objs).isoformat(),
                        "span_days": (max(date_objs) - min(date_objs)).days,
                        "documents_per_day": len(docs) / ((max(date_objs) - min(date_objs)).days + 1)
                    }
            except Exception as e:
                self.logger.warning(f"Error calculating date range: {e}")
            
            # Domain balance metrics
            domain_counts = Counter([d.get("domain", "unknown") for d in docs])
            domain_vals = np.array(list(domain_counts.values()))
            if len(domain_vals) > 1:
                probs = domain_vals / domain_vals.sum()
                entropy_val = float(-np.sum(probs * np.log2(probs)))
                gini = float((np.abs(np.subtract.outer(domain_vals, domain_vals)).sum()) / (2 * len(domain_vals) * domain_vals.sum()))
                stats["domain_metrics"] = {
                    "entropy": entropy_val,
                    "gini_coefficient": gini,
                    "domain_balance_score": 1 - gini,  # Higher is more balanced
                    "domain_distribution": dict(domain_counts)
                }
            
            # Document size metrics
            if token_counts:
                sorted_docs = sorted(docs, key=lambda d: d.get("token_count", 0), reverse=True)
                stats["document_metrics"]["largest"] = [
                    {
                        "id": d.get("id"),
                        "token_count": d.get("token_count", 0),
                        "filename": d.get("filename"),
                        "domain": d.get("domain")
                    } for d in sorted_docs[:top_n]
                ]
                stats["document_metrics"]["smallest"] = [
                    {
                        "id": d.get("id"),
                        "token_count": d.get("token_count", 0),
                        "filename": d.get("filename"),
                        "domain": d.get("domain")
                    } for d in sorted_docs[-top_n:]
                ]
            
            # Author and source metrics
            authors = [d.get("author") for d in docs if d.get("author")]
            if authors:
                stats["author_metrics"] = {
                    "most_common": dict(Counter(authors).most_common(top_n)),
                    "total_unique": len(set(authors))
                }
            
            sources = [d.get("source") for d in docs if d.get("source")]
            if sources:
                stats["source_metrics"] = {
                    "most_common": dict(Counter(sources).most_common(top_n)),
                    "total_unique": len(set(sources))
                }
            
            # Duplicate analysis
            filenames = [d.get("filename") for d in docs]
            filename_counts = Counter(filenames)
            duplicates = [fn for fn, count in filename_counts.items() if count > 1]
            if duplicates:
                stats["duplicate_analysis"] = {
                    "duplicate_filenames": duplicates,
                    "total_duplicates": sum(count - 1 for count in filename_counts.values() if count > 1),
                    "duplicate_ratio": sum(count - 1 for count in filename_counts.values() if count > 1) / len(docs)
                }
        
        return stats
    
    def print_corpus_stats(self):
        """Print corpus statistics in a readable format"""
        stats = self.get_corpus_stats()
        
        print("\nCorpus Statistics:")
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Total Size: {stats['total_size_bytes'] / (1024*1024):.2f} MB")
        
        print("\nDomain Statistics:")
        for domain, data in stats["domains"].items():
            print(f"\n{domain}:")
            print(f"  Documents: {data['document_count']}")
            print(f"  Extracted: {data['extracted_count']} ({data['extraction_ratio']*100:.1f}%)")
            print(f"  Size: {data['total_size_bytes'] / (1024*1024):.2f} MB")
        
        print("\nProcessing Status:")
        for status, count in stats["processing_status"].items():
            print(f"  {status}: {count} ({count/stats['total_documents']*100:.1f}%)")
        
        print("\nTop Sources:")
        sorted_sources = sorted(stats["sources"].items(), 
                              key=lambda x: x[1]["document_count"], 
                              reverse=True)
        for source, data in sorted_sources[:5]:
            print(f"  {source}: {data['document_count']} documents")
        
        # Print advanced statistics if available
        if stats["token_count_stats"]:
            print("\nToken Count Statistics:")
            for metric, value in stats["token_count_stats"].items():
                print(f"  {metric}: {value:,}")
        
        if stats["domain_metrics"]:
            print("\nDomain Balance Metrics:")
            print(f"  Entropy: {stats['domain_metrics']['entropy']:.2f}")
            print(f"  Gini Coefficient: {stats['domain_metrics']['gini_coefficient']:.2f}")
            print(f"  Balance Score: {stats['domain_metrics']['domain_balance_score']:.2f}")
        
        if stats["date_range"]:
            print("\nDate Range:")
            print(f"  Earliest: {stats['date_range']['earliest']}")
            print(f"  Latest: {stats['date_range']['latest']}")
            print(f"  Span: {stats['date_range']['span_days']} days")
            print(f"  Documents per day: {stats['date_range']['documents_per_day']:.1f}")
        
        if stats["duplicate_analysis"]:
            print("\nDuplicate Analysis:")
            print(f"  Total duplicates: {stats['duplicate_analysis']['total_duplicates']}")
            print(f"  Duplicate ratio: {stats['duplicate_analysis']['duplicate_ratio']*100:.1f}%")