import re
import json
from collections import Counter
from pathlib import Path

# --- Load language/domain-specific config ---
def load_mt_config(config_path=None):
    default_config = {
        'disclaimer_patterns': [
            r'translated by', r'machine translation', r'automatic translation',
            r'originally written in', r'this document was automatically translated',
            r'translation provided by', r'translated from', r'google translate'
        ],
        'ngram_repetition_threshold': 4,
        'rare_word_ratio_threshold': 0.15,
        'functional_to_content_ratio': 0.7,
        'missing_article_threshold': 0.08,
        'unusual_verb_tense_threshold': 0.12,
        'domain_exclusions': ['blockchain', 'cryptocurrency', 'API', 'function', 'parameter'],
        'code_comment_thresholds': {
            'ngram_repetition': 6,
            'rare_word_ratio': 0.25
        },
        'high_precision': False,
        'verbose': False
    }
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        default_config.update(user_config)
    return default_config

# Legitimate repetition: only bullet points and numbered lists
LEGITIMATE_REPETITION_PATTERNS = [
    r'^[0-9]+\. ', # Numbered lists
    r'^[\-\*] ',   # Bullet points
]

def is_legitimate_repetition(text):
    lines = text.splitlines()
    for pat in LEGITIMATE_REPETITION_PATTERNS:
        if all(re.match(pat, l.strip()) for l in lines if l.strip()):
            return True
    return False

# Exception for code patterns
CODE_PATTERN = re.compile(r'^(def |class |[a-zA-Z_][a-zA-Z0-9_]* ?=)')
def is_code_pattern(text):
    lines = text.splitlines()
    return any(CODE_PATTERN.match(l.strip()) for l in lines if l.strip())

# Strong repeated phrase check (e.g., "foo bar. foo bar. foo bar.")
def check_repeated_phrase(text, min_repeats=3):
    phrases = re.split(r'[.!?\n]', text)
    phrases = [p.strip() for p in phrases if p.strip()]
    if not phrases:
        return False, None
    prev = None
    count = 1
    for p in phrases:
        if p == prev:
            count += 1
            if count >= min_repeats:
                return True, f"Exact phrase repetition: '{p}' repeated {count} times"
        else:
            count = 1
            prev = p
    return False, None

# --- Heuristic 1: Translation Disclaimers ---
def check_disclaimers(text, patterns):
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True, f"Found translation disclaimer: '{pat}'"
    return False, None

# --- Heuristic 2: N-gram Repetition ---
def check_ngram_repetition(text, n=3, threshold=4, text_len=None, verbose=False):
    words = text.split()
    if text_len is None:
        text_len = len(words)
    # Lower threshold for short texts
    if text_len < 200:
        threshold = max(2, threshold - 1)
    ngrams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    counts = Counter(ngrams)
    repeated = [(ng, c) for ng, c in counts.items() if c >= threshold]
    if verbose:
        print(f"[MT-DEBUG] N-gram matches: {repeated}")
    if repeated:
        return True, [f"High n-gram repetition: '{ng}' ({c} times)" for ng, c in repeated]
    return False, []

# --- Heuristic 3: Functional/Content Word Ratio ---
def check_functional_content_ratio(text, ratio_threshold=0.7):
    # English stopwords as functional words
    functional = set([
        'the', 'a', 'an', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from', 'of', 'and', 'or', 'but', 'as', 'if', 'than', 'then', 'when', 'while', 'where', 'after', 'before', 'above', 'below', 'over', 'under', 'again', 'further', 'once', 'about', 'against', 'between', 'into', 'through', 'during', 'without', 'within', 'along', 'across', 'behind', 'beyond', 'plus', 'except', 'up', 'down', 'off', 'out', 'around', 'near'
    ])
    words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
    if not words:
        return False, None
    func_count = sum(1 for w in words if w in functional)
    content_count = len(words) - func_count
    if content_count == 0:
        return False, None
    ratio = func_count / content_count
    if ratio > ratio_threshold:
        return True, f"High functional-to-content word ratio: {ratio:.2f}"
    return False, None

# --- Heuristic 4: Missing Articles/Determiners ---
def check_missing_articles(text, threshold=0.08):
    # Look for sentences missing 'the', 'a', 'an' at start
    sentences = re.split(r'[.!?\n]', text)
    missing = 0
    total = 0
    for s in sentences:
        s = s.strip().lower()
        if not s or len(s.split()) < 5:
            continue
        total += 1
        if not re.match(r'^(the|a|an)\b', s):
            missing += 1
    if total == 0:
        return False, None
    ratio = missing / total
    if ratio > threshold:
        return True, f"High ratio of sentences missing articles: {ratio:.2f}"
    return False, None

# --- Heuristic 5: Unusual Verb Tense Patterns ---
def check_unusual_verb_tense(text, threshold=0.12):
    # Simple heuristic: look for overuse of present continuous or past perfect
    present_cont = len(re.findall(r'\b(am|is|are|was|were)\s+\w+ing\b', text))
    past_perfect = len(re.findall(r'\bhad\s+\w+ed\b', text))
    total_verbs = len(re.findall(r'\b\w+ed\b|\b\w+ing\b', text))
    if total_verbs == 0:
        return False, None
    ratio = (present_cont + past_perfect) / total_verbs
    if ratio > threshold:
        return True, f"Unusual verb tense pattern ratio: {ratio:.2f}"
    return False, None

# --- Heuristic 6: Rare Word Ratio ---
def check_rare_word_ratio(text, rare_word_ratio_threshold=0.15):
    # Use a small set of common English words; flag if too many rare words
    common = set([
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'
    ])
    words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
    if not words:
        return False, None
    rare_count = sum(1 for w in words if w not in common)
    ratio = rare_count / len(words)
    if ratio > rare_word_ratio_threshold:
        return True, f"High rare word ratio: {ratio:.2f}"
    return False, None

# --- Main Detector ---
def detect_machine_translation(text, config_path=None, file_type=None, domain=None, verbose=False):
    """
    Detects likely machine-translated text using multiple heuristics.
    - N-gram repetition: word-based, lower threshold for short texts, major trigger
    - Legitimate repetition: only bullet/numbered lists
    - Strong phrase repetition: always flagged
    - Multi-factor: require 2+ triggers for minor heuristics
    - Verbose: outputs detection scores and n-gram matches
    Returns a dict with machine_translated_flag, machine_translation_score, machine_translation_reasons, machine_translation_severity, machine_translation_confidence.
    """
    config = load_mt_config(config_path)
    verbose = verbose or config.get('verbose', False)
    reasons = []
    score = 0
    severity = 'ok'
    confidence = 0.0
    high_precision = config.get('high_precision', False)
    # Domain-specific exclusions
    exclusions = set(config.get('domain_exclusions', []))
    if domain and domain in exclusions:
        return {'machine_translated_flag': False, 'machine_translation_score': 0, 'machine_translation_reasons': ['Domain excluded'], 'machine_translation_severity': 'ok', 'machine_translation_confidence': 0.0}
    # Code pattern exception
    if is_code_pattern(text):
        return {'machine_translated_flag': False, 'machine_translation_score': 0, 'machine_translation_reasons': ['Code pattern detected'], 'machine_translation_severity': 'ok', 'machine_translation_confidence': 0.0}
    # Code comment thresholds
    if file_type and file_type in ['.py', '.ipynb']:
        ngram_threshold = config['code_comment_thresholds']['ngram_repetition']
        rare_word_threshold = config['code_comment_thresholds']['rare_word_ratio']
    else:
        ngram_threshold = config['ngram_repetition_threshold']
        rare_word_threshold = config['rare_word_ratio_threshold']
    # Text length adaptations
    words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
    unique_words = set(words)
    text_len = len(words)
    triggered = []
    ngram_score = 0
    # 1. Disclaimer
    found, reason = check_disclaimers(text, config['disclaimer_patterns'])
    if found:
        reasons.append(reason)
        score += 50
        severity = 'critical'
        triggered.append(('disclaimer', 1.0))
    # 2. Strong repeated phrase
    found, reason = check_repeated_phrase(text, min_repeats=3)
    if found:
        reasons.append(reason)
        score += 30
        severity = 'critical'
        triggered.append(('repeated_phrase', 0.9))
    # 3. N-gram repetition (skip if legitimate repetition)
    found, ngram_reasons = check_ngram_repetition(text, n=3, threshold=ngram_threshold, text_len=text_len, verbose=verbose)
    if found and not is_legitimate_repetition(text):
        reasons.extend(ngram_reasons)
        # Weight n-gram score by max frequency found
        max_freq = 0
        for r in ngram_reasons:
            match = re.search(r"\((\d+) times\)", r)
            if match:
                freq = int(match.group(1))
                if freq > max_freq:
                    max_freq = freq
        ngram_score = 10 + 5 * max(0, max_freq - 2)  # 3+ repetitions = strong evidence
        score += ngram_score
        if ngram_score >= 20:
            severity = 'critical'
        else:
            severity = 'warning'
        triggered.append(('ngram', 0.9 if ngram_score >= 20 else 0.7))
    # 4. Functional/content ratio (only if text_len >= 100)
    if text_len >= 100:
        scaled_ratio = config['functional_to_content_ratio']
        if text_len > 500:
            scaled_ratio *= 0.9  # Stricter for longer texts
        found, reason = check_functional_content_ratio(text, scaled_ratio)
        if found:
            reasons.append(reason)
            score += 10
            severity = 'warning'
            triggered.append(('func_content', 0.5))
    # 5. Missing articles (only if text_len >= 25)
    if text_len >= 25:
        found, reason = check_missing_articles(text, config['missing_article_threshold'])
        if found:
            reasons.append(reason)
            score += 10
            severity = 'warning'
            # Scale confidence for short texts
            if text_len < 100:
                triggered.append(('missing_article', 0.25))
            else:
                triggered.append(('missing_article', 0.5))
    # 6. Unusual verb tense
    found, reason = check_unusual_verb_tense(text, config['unusual_verb_tense_threshold'])
    if found:
        reasons.append(reason)
        score += 10
        severity = 'warning'
        triggered.append(('verb_tense', 0.5))
    # 7. Rare word ratio (only if unique_words >= 50)
    if len(unique_words) >= 50:
        found, reason = check_rare_word_ratio(text, rare_word_threshold)
        if found:
            reasons.append(reason)
            score += 10
            severity = 'warning'
            triggered.append(('rare_word', 0.5))
    # Multi-factor requirement for short texts
    major_triggers = {'disclaimer', 'repeated_phrase', 'ngram'}
    if text_len < 200:
        non_major_triggers = [t for t in triggered if t[0] not in major_triggers]
        if len(non_major_triggers) < 2 and not any(t[0] in major_triggers for t in triggered):
            return {
                'machine_translated_flag': False,
                'machine_translation_score': min(100, score),
                'machine_translation_reasons': reasons,
                'machine_translation_severity': 'ok',
                'machine_translation_confidence': confidence
            }
        # NEW: If 2+ minor triggers for short text, always flag
        if len(non_major_triggers) >= 2:
            machine_translated_flag = True
            severity = 'warning'
            confidence = min(0.8, 0.4 * len(non_major_triggers))
            return {
                'machine_translated_flag': True,
                'machine_translation_score': min(100, score),
                'machine_translation_reasons': reasons,
                'machine_translation_severity': severity,
                'machine_translation_confidence': confidence
            }
    # If n-gram score is above threshold (20), immediately flag as machine translated
    if ngram_score >= 20:
        machine_translated_flag = True
        severity = 'critical'
        confidence = 0.9
    else:
        # Confidence calculation
        confidence = min(1.0, sum(w for _, w in triggered))
        # Final flag logic
        ngram_triggered = any(t[0] == 'ngram' for t in triggered)
        machine_translated_flag = (score >= 30 or severity == 'critical') and (confidence > 0.5)
        if ngram_triggered:
            machine_translated_flag = True
        if score >= 50:
            severity = 'critical'
        elif score >= 30:
            severity = 'warning'
        else:
            severity = 'ok'
    if verbose:
        print(f"[MT-DEBUG] Heuristics triggered: {triggered}, Score: {score}, Confidence: {confidence}")
    return {
        'machine_translated_flag': machine_translated_flag,
        'machine_translation_score': min(100, score),
        'machine_translation_reasons': reasons,
        'machine_translation_severity': severity,
        'machine_translation_confidence': confidence
    } 