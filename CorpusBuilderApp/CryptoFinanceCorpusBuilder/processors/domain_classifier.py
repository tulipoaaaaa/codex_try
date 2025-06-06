# processors/domain_classifier.py
import re
import logging
import json
from pathlib import Path
import numpy as np
from collections import Counter
from CryptoFinanceCorpusBuilder.utils.domain_utils import get_valid_domains, get_domain_for_file

class DomainClassifier:
    """Classify documents into crypto-finance domains"""
    
    def __init__(self, domain_config=None, config_path=None):
        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Load domain configuration
        if domain_config:
            self.domain_config = domain_config
        elif config_path:
            self._load_config(config_path)
        else:
            from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
            self.domain_config = DOMAINS
        
        # Extract keywords for each domain
        self.domain_keywords = self._extract_domain_keywords()
        self.logger.info(f"Initialized classifier with {len(self.domain_config)} domains")
    
    def _load_config(self, config_path):
        """Load domain configuration from file"""
        try:
            with open(config_path, 'r') as f:
                self.domain_config = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading domain configuration: {e}")
            self.domain_config = {}
    
    def _extract_domain_keywords(self):
        """Extract keywords for each domain from configuration"""
        keywords = {}
        
        for domain, config in self.domain_config.items():
            # Get search terms
            search_terms = config.get('search_terms', [])
            
            # Extract individual words from search terms
            domain_keywords = set()
            for term in search_terms:
                # Split into words and normalize
                words = term.lower().split()
                for word in words:
                    # Filter out common words and very short words
                    if len(word) > 3 and word not in ['and', 'the', 'for', 'with']:
                        domain_keywords.add(word)
            
            keywords[domain] = list(domain_keywords)
            
        return keywords
    
    def classify(self, text, title=None):
        """Classify document into domains"""
        if not text:
            return {"domain": "unknown", "confidence": 0, "scores": {}}
        
        # Combine title and text (title weighted higher)
        content = ""
        if title:
            content += (title.lower() + " ") * 3
        content += text.lower()
        
        # Calculate scores for each domain
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            # Count keyword matches
            keyword_counts = Counter()
            
            for keyword in keywords:
                # Count occurrences using regex to match whole words
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content))
                if count > 0:
                    keyword_counts[keyword] = count
            
            # Calculate score based on keyword matches
            total_matches = sum(keyword_counts.values())
            unique_matches = len(keyword_counts)
            
            # Score formula: weighted combination of total and unique matches
            if keywords:
                content_word_count = max(1, len(content.split()))
                score = (0.7 * unique_matches / len(keywords)) + (0.3 * total_matches / (content_word_count / 20))
            else:
                score = 0
                
            domain_scores[domain] = score
        
        # Normalize scores
        max_score = max(domain_scores.values()) if domain_scores else 0
        if max_score > 0:
            normalized_scores = {domain: score / max_score for domain, score in domain_scores.items()}
        else:
            normalized_scores = domain_scores
        
        # Find top domain
        if normalized_scores:
            top_domain = max(normalized_scores.items(), key=lambda x: x[1])
            domain_name, score = top_domain
            
            # Calculate confidence (how much better the top domain is compared to the second best)
            sorted_scores = sorted(normalized_scores.values(), reverse=True)
            confidence = 0
            if len(sorted_scores) > 1 and sorted_scores[1] > 0:
                confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
            
            return {
                "domain": domain_name,
                "confidence": confidence,
                "scores": normalized_scores
            }
        else:
            return {"domain": "unknown", "confidence": 0, "scores": {}}
    
    def batch_classify(self, documents):
        """Classify multiple documents"""
        results = {}
        
        for doc_id, doc in documents.items():
            text = doc.get('text', '')
            title = doc.get('metadata', {}).get('title', None)
            
            classification = self.classify(text, title)
            results[doc_id] = classification
            
        return results