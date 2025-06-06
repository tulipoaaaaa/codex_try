# processors/financial_symbol_processor.py
"""
Financial symbol dictionary and preservation system for crypto/finance documents.
Handles ticker symbols, mathematical notation, Greek letters, and financial abbreviations.
"""

import re
import json
import unicodedata
from typing import Dict, List, Set, Any, Optional, Tuple
from pathlib import Path
import logging
from collections import defaultdict, Counter
from .formula_extractor import FormulaExtractor
from .chart_image_extractor import ChartImageExtractor

class FinancialSymbolProcessor:
    """Process and preserve financial symbols, tickers, and mathematical notation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        
        # Initialize symbol dictionaries
        self.symbol_dictionaries = self._build_symbol_dictionaries()
        self.preservation_patterns = self._build_preservation_patterns()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'preserve_case': True,
            'preserve_spacing': True,
            'validate_tickers': True,
            'extract_greek_letters': True,
            'extract_mathematical_symbols': True,
            'extract_currency_symbols': True,
            'custom_symbol_file': None,
            'min_symbol_length': 1,
            'max_symbol_length': 10
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _build_symbol_dictionaries(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive symbol dictionaries."""
        
        # Stock tickers and crypto symbols
        stock_tickers = {
            # Major indices
            'SPY', 'QQQ', 'IWM', 'VTI', 'VT', 'VEA', 'VWO',
            # Major stocks  
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'NFLX', 'CRM', 'ADBE', 'PYPL', 'INTC', 'AMD', 'ORCL', 'IBM',
            # Banks
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO',
            # Crypto-related stocks
            'COIN', 'MSTR', 'SQ', 'PYPL', 'HOOD',
        }
        
        crypto_symbols = {
            'BTC', 'ETH', 'ADA', 'SOL', 'AVAX', 'DOT', 'MATIC', 'LINK',
            'UNI', 'SUSHI', 'AAVE', 'COMP', 'MKR', 'SNX', 'YFI', 'CRV',
            'LTC', 'BCH', 'XRP', 'DOGE', 'SHIB', 'USDT', 'USDC', 'DAI',
            'WBTC', 'WETH', 'stETH', 'rETH'
        }
        
        # Currency symbols and codes
        currency_symbols = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR',
            '₽': 'RUB', '₩': 'KRW', '₪': 'ILS', '₦': 'NGN', '₡': 'CRC'
        }
        currency_codes = {
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'CNY', 'INR', 'BRL', 'RUB', 'KRW', 'SGD', 'HKD', 'NOK', 'SEK'
        }
        all_currencies = {**currency_symbols}
        for code in currency_codes:
            all_currencies[code] = code
        
        # Greek letters (commonly used in finance)
        greek_letters = {
            'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
            'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
            'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron',
            'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
            'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
            # Uppercase
            'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon',
            'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa',
            'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron',
            'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon',
            'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega'
        }
        
        # Mathematical symbols
        mathematical_symbols = {
            '∞': 'infinity', '∂': 'partial', '∇': 'nabla', '∑': 'sum', '∏': 'product',
            '∫': 'integral', '√': 'sqrt', '±': 'plus_minus', '≤': 'less_equal',
            '≥': 'greater_equal', '≠': 'not_equal', '≈': 'approximately', '∈': 'element_of',
            '∉': 'not_element_of', '⊂': 'subset', '⊃': 'superset', '∩': 'intersection',
            '∪': 'union', '∅': 'empty_set', 'ℝ': 'real_numbers', 'ℕ': 'natural_numbers',
            'ℤ': 'integers', 'ℚ': 'rationals', '→': 'arrow_right', '←': 'arrow_left',
            '↑': 'arrow_up', '↓': 'arrow_down', '⇒': 'implies', '⇔': 'if_and_only_if'
        }
        
        # Financial abbreviations and terms
        financial_terms = {
            'P/E', 'P/B', 'EPS', 'ROE', 'ROA', 'EBITDA', 'WACC', 'CAPM',
            'VaR', 'CVaR', 'PnL', 'P&L', 'NAV', 'AUM', 'IRR', 'NPV',
            'CAGR', 'YTD', 'QoQ', 'YoY', 'MoM', 'ATH', 'ATL', 'RSI',
            'MACD', 'SMA', 'EMA', 'BB', 'ADX', 'CCI', 'MFI', 'OBV',
            'DeFi', 'DAO', 'NFT', 'DEX', 'CEX', 'LP', 'AMM', 'TVL',
            'APY', 'APR', 'IL', 'MEV', 'PoS', 'PoW', 'TPS'
        }
        
        # Load custom symbols if specified
        custom_symbols = set()
        if self.config.get('custom_symbol_file'):
            custom_symbols = self._load_custom_symbols(self.config['custom_symbol_file'])
        
        return {
            'stock_tickers': {symbol: {'type': 'stock_ticker', 'verified': True} for symbol in stock_tickers},
            'crypto_symbols': {symbol: {'type': 'crypto_symbol', 'verified': True} for symbol in crypto_symbols},
            'currency_symbols': {symbol: {'type': 'currency', 'name': all_currencies.get(symbol, symbol)} for symbol in all_currencies},
            'greek_letters': {symbol: {'type': 'greek_letter', 'name': name} for symbol, name in greek_letters.items()},
            'mathematical_symbols': {symbol: {'type': 'mathematical', 'name': name} for symbol, name in mathematical_symbols.items()},
            'financial_terms': {term: {'type': 'financial_term', 'verified': True} for term in financial_terms},
            'custom_symbols': {symbol: {'type': 'custom', 'verified': False} for symbol in custom_symbols}
        }
    
    def _load_custom_symbols(self, file_path: str) -> Set[str]:
        """Load custom symbols from file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    return set(data.get('symbols', []))
                else:
                    # Assume text file with one symbol per line
                    return set(line.strip() for line in f if line.strip())
        except Exception as e:
            self.logger.warning(f"Failed to load custom symbols from {file_path}: {e}")
            return set()
    
    def _build_preservation_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for symbol preservation."""
        patterns = {}
        
        # Stock ticker pattern (1-5 uppercase letters, possibly with dots)
        patterns['stock_ticker'] = re.compile(r'\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b')
        
        # Crypto symbol pattern (2-10 chars, mostly uppercase)
        patterns['crypto_symbol'] = re.compile(r'\b[A-Z]{2,10}\b')
        
        # Currency amounts (symbol + number or number + code)
        patterns['currency_amount'] = re.compile(r'(?:[$€£¥₹₽₩₪₦₡]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|CHF|CAD|AUD|NZD|CNY|INR|BRL|RUB|KRW|SGD|HKD|NOK|SEK))')
        
        # Greek letters
        patterns['greek_letter'] = re.compile(r'[αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]')
        
        # Mathematical symbols
        patterns['mathematical_symbol'] = re.compile(r'[∞∂∇∑∏∫√±≤≥≠≈∈∉⊂⊃∩∪∅ℝℕℤℚ→←↑↓⇒⇔]')
        
        # Financial ratios and metrics
        patterns['financial_ratio'] = re.compile(r'\b(?:P/E|P/B|ROE|ROA|EBITDA|WACC|CAPM|VaR|CVaR|PnL|P&L|NAV|AUM|IRR|NPV|CAGR|YTD|QoQ|YoY|MoM|ATH|ATL|RSI|MACD|SMA|EMA|BB|ADX|CCI|MFI|OBV)\b')
        
        # DeFi and crypto terms
        patterns['defi_term'] = re.compile(r'\b(?:DeFi|DAO|NFT|DEX|CEX|LP|AMM|TVL|APY|APR|IL|MEV|PoS|PoW|TPS)\b')
        
        # Percentage with optional basis points
        patterns['percentage'] = re.compile(r'\d+(?:\.\d+)?%|\d+(?:\.\d+)?\s*bps?\b')
        
        # Scientific notation
        patterns['scientific_notation'] = re.compile(r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b')
        
        return patterns
    
    def extract_symbols(self, text: str) -> Dict[str, Any]:
        """Extract all financial symbols from text."""
        extracted_symbols = defaultdict(list)
        symbol_positions = []
        
        # Extract using patterns
        for pattern_name, pattern in self.preservation_patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                symbol = match.group()
                
                # Validate and classify symbol
                classification = self._classify_symbol(symbol, pattern_name)
                
                if classification:
                    symbol_data = {
                        'symbol': symbol,
                        'type': classification['type'],
                        'pattern': pattern_name,
                        'position': {
                            'start': match.start(),
                            'end': match.end()
                        },
                        'context': self._extract_context(text, match.start(), match.end()),
                        'confidence': classification['confidence'],
                        'metadata': classification.get('metadata', {})
                    }
                    
                    extracted_symbols[pattern_name].append(symbol_data)
                    symbol_positions.append(symbol_data)
        
        # Sort by position
        symbol_positions.sort(key=lambda x: x['position']['start'])
        
        # Calculate statistics
        stats = self._calculate_symbol_statistics(extracted_symbols)
        
        return {
            'symbols_by_type': dict(extracted_symbols),
            'symbols_by_position': symbol_positions,
            'statistics': stats,
            'preservation_map': self._create_preservation_map(symbol_positions)
        }
    
    def _classify_symbol(self, symbol: str, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Classify and validate a symbol."""
        # Check in known dictionaries first
        for dict_name, symbol_dict in self.symbol_dictionaries.items():
            if symbol in symbol_dict:
                return {
                    'type': symbol_dict[symbol]['type'],
                    'confidence': 1.0,
                    'verified': symbol_dict[symbol].get('verified', False),
                    'metadata': symbol_dict[symbol]
                }
        
        # Pattern-based classification with confidence scores
        if pattern_name == 'stock_ticker':
            # Additional validation for stock tickers
            if len(symbol) >= 1 and len(symbol) <= 5 and symbol.isupper():
                return {
                    'type': 'potential_stock_ticker',
                    'confidence': 0.7,
                    'verified': False,
                    'metadata': {'needs_validation': True}
                }
        
        elif pattern_name == 'crypto_symbol':
            if len(symbol) >= 2 and len(symbol) <= 10:
                return {
                    'type': 'potential_crypto_symbol',
                    'confidence': 0.6,
                    'verified': False,
                    'metadata': {'needs_validation': True}
                }
        
        elif pattern_name in ['greek_letter', 'mathematical_symbol']:
            return {
                'type': pattern_name,
                'confidence': 1.0,
                'verified': True,
                'metadata': {}
            }
        
        elif pattern_name in ['currency_amount', 'percentage', 'scientific_notation']:
            return {
                'type': pattern_name,
                'confidence': 0.9,
                'verified': True,
                'metadata': {}
            }
        
        elif pattern_name in ['financial_ratio', 'defi_term']:
            return {
                'type': pattern_name,
                'confidence': 1.0,
                'verified': True,
                'metadata': {}
            }
        
        return None
    
    def _extract_context(self, text: str, start: int, end: int, context_chars: int = 30) -> str:
        """Extract context around a symbol."""
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        context = text[context_start:context_end]
        return context
    
    def _calculate_symbol_statistics(self, extracted_symbols: Dict[str, List]) -> Dict[str, Any]:
        """Calculate statistics about extracted symbols."""
        total_symbols = sum(len(symbols) for symbols in extracted_symbols.values())
        
        # Count by type
        type_counts = {}
        confidence_scores = []
        
        for pattern_name, symbols in extracted_symbols.items():
            type_counts[pattern_name] = len(symbols)
            confidence_scores.extend([s['confidence'] for s in symbols])
        
        # Most common symbols
        all_symbols = []
        for symbols in extracted_symbols.values():
            all_symbols.extend([s['symbol'] for s in symbols])
        
        symbol_frequency = Counter(all_symbols)
        
        return {
            'total_symbols': total_symbols,
            'unique_symbols': len(set(all_symbols)),
            'type_counts': type_counts,
            'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'most_common_symbols': symbol_frequency.most_common(10),
            'symbol_density': total_symbols / 1000  # symbols per 1000 characters
        }
    
    def _create_preservation_map(self, symbol_positions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create a map for preserving symbols during text processing."""
        preservation_map = {}
        
        for i, symbol_data in enumerate(symbol_positions):
            # Create unique placeholder
            placeholder = f"__SYMBOL_{i}__"
            preservation_map[placeholder] = symbol_data['symbol']
        
        return preservation_map
    
    def preserve_symbols_in_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace symbols with placeholders to preserve them during processing."""
        symbols_data = self.extract_symbols(text)
        symbol_positions = symbols_data['symbols_by_position']
        
        # Sort by position (reverse order to maintain positions when replacing)
        symbol_positions.sort(key=lambda x: x['position']['start'], reverse=True)
        
        preserved_text = text
        preservation_map = {}
        
        for i, symbol_data in enumerate(symbol_positions):
            placeholder = f"__SYMBOL_{i}__"
            start = symbol_data['position']['start']
            end = symbol_data['position']['end']
            
            # Replace symbol with placeholder
            preserved_text = (
                preserved_text[:start] + 
                placeholder + 
                preserved_text[end:]
            )
            
            preservation_map[placeholder] = symbol_data['symbol']
        
        return preserved_text, preservation_map
    
    def restore_symbols_in_text(self, text: str, preservation_map: Dict[str, str]) -> str:
        """Restore symbols from placeholders."""
        restored_text = text
        
        for placeholder, symbol in preservation_map.items():
            restored_text = restored_text.replace(placeholder, symbol)
        
        return restored_text
    
    def validate_financial_symbols(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Validate financial symbols against known databases."""
        # This is a placeholder for real-time validation
        # In practice, you might query APIs like Alpha Vantage, Yahoo Finance, etc.
        
        validation_results = {}
        
        for symbol in symbols:
            # Check against known symbols
            is_known = False
            symbol_type = 'unknown'
            
            for dict_name, symbol_dict in self.symbol_dictionaries.items():
                if symbol in symbol_dict:
                    is_known = True
                    symbol_type = symbol_dict[symbol]['type']
                    break
            
            validation_results[symbol] = {
                'is_known': is_known,
                'type': symbol_type,
                'confidence': 1.0 if is_known else 0.5,
                'needs_verification': not is_known
            }
        
        return validation_results
    
    def generate_symbol_glossary(self, extracted_symbols: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a glossary of symbols found in the document."""
        glossary = {}
        
        for pattern_name, symbols in extracted_symbols['symbols_by_type'].items():
            for symbol_data in symbols:
                symbol = symbol_data['symbol']
                
                if symbol not in glossary:
                    # Find definition or description
                    definition = self._get_symbol_definition(symbol, symbol_data['type'])
                    
                    glossary[symbol] = {
                        'type': symbol_data['type'],
                        'definition': definition,
                        'occurrences': 1,
                        'contexts': [symbol_data['context']],
                        'confidence': symbol_data['confidence']
                    }
                else:
                    glossary[symbol]['occurrences'] += 1
                    glossary[symbol]['contexts'].append(symbol_data['context'])
        
        return glossary
    
    def _get_symbol_definition(self, symbol: str, symbol_type: str) -> str:
        """Get definition for a symbol."""
        # Check known dictionaries
        for dict_name, symbol_dict in self.symbol_dictionaries.items():
            if symbol in symbol_dict:
                metadata = symbol_dict[symbol]
                if 'name' in metadata:
                    return metadata['name']
                elif 'definition' in metadata:
                    return metadata['definition']
        
        # Default definitions by type
        type_definitions = {
            'stock_ticker': f'Stock ticker symbol: {symbol}',
            'crypto_symbol': f'Cryptocurrency symbol: {symbol}',
            'currency': f'Currency symbol: {symbol}',
            'greek_letter': f'Greek letter: {symbol}',
            'mathematical_symbol': f'Mathematical symbol: {symbol}',
            'financial_term': f'Financial term: {symbol}',
            'percentage': f'Percentage value: {symbol}',
            'currency_amount': f'Currency amount: {symbol}',
            'scientific_notation': f'Scientific notation: {symbol}'
        }
        
        return type_definitions.get(symbol_type, f'Symbol: {symbol}')

# Academic paper thresholds and content validation
class AcademicPaperProcessor:
    """Enhanced processing for academic papers with adjusted thresholds."""
    
    def __init__(self):
        self.academic_thresholds = {
            'min_tokens': 200,  # Lower for academic abstracts
            'low_quality_tokens': 1000,  # More lenient
            'reference_density_max': 0.15,  # Up to 15% references is normal
            'citation_density_max': 0.10,  # Up to 10% citations
            'formula_density_max': 0.20,  # Up to 20% formulas
            'table_density_max': 0.15,  # Up to 15% tables
            'min_sections': 3,  # Minimum academic sections
            'bibliography_required': True
        }
        
        self.academic_indicators = [
            'abstract', 'introduction', 'methodology', 'methods', 'results',
            'discussion', 'conclusion', 'references', 'bibliography',
            'acknowledgments', 'appendix', 'literature review'
        ]
        
        self.citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\d{4}\)',  # (2023)
            r'\([A-Za-z]+\s+et\s+al\.?,?\s+\d{4}\)',  # (Smith et al., 2023)
            r'et\s+al\.',  # et al.
            r'doi:\s*10\.\d+',  # DOI
            r'arXiv:\d+\.\d+',  # arXiv papers
        ]
    
    def detect_academic_paper(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if document is an academic paper and return confidence."""
        indicators_found = []
        score = 0
        
        text_lower = text.lower()
        
        # Check for academic sections
        for indicator in self.academic_indicators:
            if indicator in text_lower:
                indicators_found.append(indicator)
                score += 1
        
        # Check citation patterns
        citation_count = 0
        for pattern in self.citation_patterns:
            matches = len(re.findall(pattern, text))
            citation_count += matches
        
        if citation_count > 5:
            score += 2
            indicators_found.append('citations')
        
        # Check metadata for academic signals
        if metadata:
            academic_metadata = ['doi', 'journal', 'conference', 'university', 'research']
            for key, value in metadata.items():
                if any(term in str(value).lower() for term in academic_metadata):
                    score += 1
                    indicators_found.append(f'metadata_{key}')
        
        # Calculate confidence
        max_possible_score = len(self.academic_indicators) + 3  # +2 for citations, +1 for metadata
        confidence = min(1.0, score / max_possible_score)
        
        is_academic = score >= 3 and confidence > 0.3
        
        return {
            'is_academic_paper': is_academic,
            'confidence': confidence,
            'score': score,
            'indicators_found': indicators_found,
            'citation_count': citation_count,
            'recommended_thresholds': self.academic_thresholds if is_academic else None
        }
    
    def validate_academic_content(self, text: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate academic content quality with adjusted thresholds."""
        validation_results = {
            'passes_academic_standards': True,
            'issues': [],
            'adjustments_made': []
        }
        # Ensure lists in case of unexpected input
        if not isinstance(validation_results['issues'], list):
            validation_results['issues'] = list(validation_results['issues'])
        if not isinstance(validation_results['adjustments_made'], list):
            validation_results['adjustments_made'] = list(validation_results['adjustments_made'])
        
        token_count = len(text.split())
        
        # Apply academic-specific validation
        if token_count < self.academic_thresholds['min_tokens']:
            validation_results['issues'].append(f'Low token count: {token_count}')
            validation_results['passes_academic_standards'] = False
        
        # Check reference density
        reference_patterns = ['references', 'bibliography', '\[\d+\]', '\(\d{4}\)']
        reference_matches = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in reference_patterns)
        reference_density = reference_matches / token_count if token_count > 0 else 0
        
        if reference_density > self.academic_thresholds['reference_density_max']:
            validation_results['issues'].append(f'High reference density: {reference_density:.3f}')
        else:
            validation_results['adjustments_made'].append('Reference density within academic norms')
        
        # Check for required sections
        sections_found = sum(1 for indicator in self.academic_indicators if indicator in text.lower())
        if sections_found < self.academic_thresholds['min_sections']:
            validation_results['issues'].append(f'Insufficient academic sections: {sections_found}')
        
        return validation_results

# Memory optimization utilities
class MemoryOptimizer:
    """Optimize memory usage during large-scale processing."""
    
    def __init__(self):
        self.chunk_size = 1000000  # 1MB chunks
        self.max_cache_size = 100
        self.cache = {}
    
    def process_large_text_in_chunks(self, text: str, processor_func, **kwargs):
        """Process large text in memory-efficient chunks."""
        results = []
        
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            
            # Process chunk
            chunk_result = processor_func(chunk, **kwargs)
            results.append(chunk_result)
            
            # Clear variables to free memory
            del chunk
        
        return self._merge_chunk_results(results)
    
    def _merge_chunk_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple chunks."""
        merged: Dict[str, Any] = {
            'symbols_by_type': defaultdict(list),
            'symbols_by_position': [],
            'statistics': {},
            'preservation_map': {}
        }
        for result in results:
            # Merge symbols
            for symbol_type, symbols in result.get('symbols_by_type', {}).items():
                merged['symbols_by_type'][symbol_type].extend(symbols)
            # Merge positions
            merged['symbols_by_position'].extend(result.get('symbols_by_position', []))
            # Merge preservation maps
            merged['preservation_map'].update(result.get('preservation_map', {}))
        # Recalculate statistics
        merged['statistics'] = self._recalculate_statistics(merged)
        return merged
    
    def _recalculate_statistics(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate statistics for merged data."""
        total_symbols = sum(len(symbols) for symbols in merged_data['symbols_by_type'].values())
        
        all_symbols = []
        for symbols in merged_data['symbols_by_type'].values():
            all_symbols.extend([s['symbol'] for s in symbols])
        
        return {
            'total_symbols': total_symbols,
            'unique_symbols': len(set(all_symbols)),
            'type_counts': {k: len(v) for k, v in merged_data['symbols_by_type'].items()},
            'most_common_symbols': Counter(all_symbols).most_common(10)
        }

# Integration functions for your pipeline
def integrate_all_enhancements(pdf_path: str, extracted_text: str, output_dir: str, 
                             metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Complete integration of all enhancement features."""
    
    # Initialize processors
    formula_extractor = FormulaExtractor()
    chart_extractor = ChartImageExtractor()
    symbol_processor = FinancialSymbolProcessor()
    academic_processor = AcademicPaperProcessor()
    memory_optimizer = MemoryOptimizer()
    
    # Results container
    enhancement_results = {}
    
    # 1. LaTeX Formula Extraction
    try:
        formula_results = formula_extractor.extract_comprehensive(pdf_path, extracted_text)
        enhancement_results['formulas'] = formula_results
    except Exception as e:
        logging.error(f"Formula extraction failed: {e}")
        enhancement_results['formulas'] = {'formulas': [], 'statistics': {}}
    
    # 2. Chart/Image Extraction
    try:
        image_results = chart_extractor.extract_from_pdf(pdf_path, output_dir)
        enhancement_results['images'] = {
            'images': image_results,
            'statistics': {
                'total_images': len(image_results),
                'charts': len([img for img in image_results if img['is_chart']]),
                'financial_charts': len([img for img in image_results if img.get('is_financial_chart', False)])
            }
        }
    except Exception as e:
        logging.error(f"Image extraction failed: {e}")
        enhancement_results['images'] = {'images': [], 'statistics': {}}
    
    # 3. Financial Symbol Processing
    try:
        if len(extracted_text) > memory_optimizer.chunk_size:
            symbol_results = memory_optimizer.process_large_text_in_chunks(
                extracted_text, symbol_processor.extract_symbols
            )
        else:
            symbol_results = symbol_processor.extract_symbols(extracted_text)
        
        enhancement_results['symbols'] = symbol_results
        enhancement_results['symbol_glossary'] = symbol_processor.generate_symbol_glossary(symbol_results)
    except Exception as e:
        logging.error(f"Symbol processing failed: {e}")
        enhancement_results['symbols'] = {'symbols_by_type': {}, 'statistics': {}}
    
    # 4. Academic Paper Detection and Validation
    try:
        academic_detection = academic_processor.detect_academic_paper(extracted_text, metadata)
        enhancement_results['academic_analysis'] = academic_detection
        
        if academic_detection['is_academic_paper']:
            content_validation = academic_processor.validate_academic_content(
                extracted_text, enhancement_results
            )
            enhancement_results['content_validation'] = content_validation
        else:
            enhancement_results['content_validation'] = {'passes_academic_standards': True}
    except Exception as e:
        logging.error(f"Academic analysis failed: {e}")
        enhancement_results['academic_analysis'] = {'is_academic_paper': False}
    
    # 5. Overall Quality Score
    enhancement_results['overall_quality'] = calculate_overall_quality_score(enhancement_results)
    
    return enhancement_results

def calculate_overall_quality_score(enhancement_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall quality score based on all enhancements."""
    score = 0.5  # Base score
    factors = []
    
    # Formula quality
    formula_count = enhancement_results.get('formulas', {}).get('statistics', {}).get('total_formulas', 0)
    if formula_count > 0:
        score += 0.1
        factors.append('Contains mathematical formulas')
    
    # Chart quality
    chart_count = enhancement_results.get('images', {}).get('statistics', {}).get('charts', 0)
    if chart_count > 0:
        score += 0.15
        factors.append('Contains charts/visualizations')
    
    # Symbol richness
    symbol_count = enhancement_results.get('symbols', {}).get('statistics', {}).get('total_symbols', 0)
    if symbol_count > 10:
        score += 0.1
        factors.append('Rich in financial symbols')
    
    # Academic quality
    if enhancement_results.get('academic_analysis', {}).get('is_academic_paper', False):
        score += 0.15
        factors.append('Academic paper')
        
        if enhancement_results.get('content_validation', {}).get('passes_academic_standards', False):
            score += 0.1
            factors.append('Meets academic standards')
    
    return {
        'overall_score': min(1.0, score),
        'quality_factors': factors,
        'enhancement_summary': {
            'formulas_extracted': formula_count,
            'charts_extracted': chart_count,
            'symbols_extracted': symbol_count,
            'is_academic': enhancement_results.get('academic_analysis', {}).get('is_academic_paper', False)
        }
    }