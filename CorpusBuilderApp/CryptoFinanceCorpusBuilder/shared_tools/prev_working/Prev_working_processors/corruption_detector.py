import re
import string
from collections import Counter

def detect_corruption(text, file_type=None, reject=True, thresholds=None):
    """
    Detects corruption in text using multiple heuristics.
    Returns a dict with corruption_flag, corruption_score, corruption_score_normalized, corruption_reasons, severity.
    file_type: Optional, e.g., 'py', 'ipynb', 'md', 'csv', 'json', 'html'
    reject: If True, set corruption_flag=True if any critical threshold is exceeded; else only flag as warning.
    thresholds: Optional dict to override default thresholds.
    """
    # --- Default thresholds ---
    default_thresholds = {
        'non_printable_ratio': 0.15,
        'long_run_length': 25,
        'word_diversity_ratio': 0.08,
        'symbol_to_word_ratio': 0.6,
    }
    if thresholds:
        t = {**default_thresholds, **thresholds}
    else:
        t = default_thresholds
    reasons = []
    score = 0
    severity = 'ok'
    text_len = len(text)
    if text_len == 0:
        return {'corruption_flag': True, 'corruption_score': 100, 'corruption_score_normalized': 100, 'corruption_reasons': ['Empty text'], 'severity': 'critical'}

    # File type normalization
    ft = (file_type or '').lower()
    # Symbol threshold by file type
    if ft.endswith(('.py', '.ipynb', '.js', '.java', '.cpp', '.c', '.rb', '.go')):
        symbol_threshold = 1.2
    elif ft.endswith(('.html', '.htm', '.md', '.json', '.csv')):
        symbol_threshold = 0.8
    else:
        symbol_threshold = t['symbol_to_word_ratio']

    # 1. Non-printable character ratio
    printable = set(string.printable)
    non_printable_count = sum(1 for c in text if c not in printable)
    non_printable_ratio = non_printable_count / text_len
    if non_printable_ratio > t['non_printable_ratio']:
        reasons.append('High non-printable character ratio (>{:.0f}%)'.format(non_printable_ratio*100))
        score += 30
        severity = 'critical'

    # 2. Long runs of the same character (unicode-aware)
    long_run = re.search(r'(.)\1{' + str(t['long_run_length']-1) + ',}', text, re.UNICODE)
    if long_run:
        reasons.append('Long run of character: "{}"'.format(long_run.group(1)))
        score += 30
        severity = 'critical'

    # 3. Word diversity (skip for very short text)
    words = re.findall(r'\b\w+\b', text.lower(), re.UNICODE)
    total_words = len(words)
    unique_words = len(set(words))
    diversity = unique_words / total_words if total_words > 0 else 0
    if total_words > 100 and diversity < t['word_diversity_ratio']:
        reasons.append('Low word diversity ({:.2f})'.format(diversity))
        score += 10
        severity = 'warning'

    # 4. Symbol-to-word ratio (skip for very short text)
    symbols = re.findall(r'[^\w\s]', text, re.UNICODE)
    symbol_ratio = len(symbols) / (total_words or 1)
    if total_words > 50 and symbol_ratio > symbol_threshold:
        reasons.append('High symbol-to-word ratio ({:.2f})'.format(symbol_ratio))
        score += 10
        severity = 'warning'

    # 5. Known corruption markers (count and score)
    markers = ['', '\x00', 'NULL', 'corrupt', 'error', 'unreadable']
    marker_hits = [m for m in markers if m in text]
    marker_count = sum(text.count(m) for m in markers)
    if marker_hits:
        reasons.append('Found corruption markers: {}'.format(', '.join(marker_hits)))
        score += min(30, 5 * marker_count)
        if marker_count > 2:
            severity = 'critical'
        else:
            severity = 'warning'

    # 6. Encoding inconsistency: high ratio of replacement chars ()
    replacement_char_count = text.count('')
    if replacement_char_count / (text_len or 1) > 0.05:
        reasons.append('High ratio of replacement characters (possible encoding issue)')
        score += 10
        severity = 'warning'

    # 7. Malformed lines: lines with mostly non-printable or symbol chars
    lines = text.splitlines()
    malformed_lines = 0
    for line in lines:
        if not line.strip():
            continue
        printable_count = sum(1 for c in line if c in printable)
        symbol_count = sum(1 for c in line if c in string.punctuation)
        if printable_count / (len(line) or 1) < 0.5 or symbol_count / (len(line) or 1) > 0.7:
            malformed_lines += 1
    if lines:
        malformed_ratio = malformed_lines / len(lines)
        if malformed_ratio > 0.2:
            reasons.append('High percentage of malformed lines ({:.0f}%)'.format(malformed_ratio*100))
            score += 10
            severity = 'warning'

    # Normalize score to 0-100
    corruption_score_normalized = min(100, score)

    # Final flag logic
    corruption_flag = False
    if reject:
        if severity == 'critical':
            corruption_flag = True
    else:
        corruption_flag = False
        if score > 0:
            severity = 'warning'

    return {
        'corruption_flag': corruption_flag,
        'corruption_score': score,
        'corruption_score_normalized': corruption_score_normalized,
        'corruption_reasons': reasons,
        'severity': severity
    } 