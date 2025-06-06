import re
from langdetect import detect_langs, LangDetectException

def detect_language_confidence(text, low_conf_threshold=0.85, mixed_lang_ratio=0.15):
    """
    Detects language, confidence, and mixed-language content in text.
    Returns a dict with language, language_confidence, mixed_language_flag, mixed_languages, reasons, severity.
    """
    reasons = []
    severity = 'ok'
    try:
        langs = detect_langs(text)
        if not langs:
            return {'language': 'unknown', 'language_confidence': 0.0, 'mixed_language_flag': False, 'mixed_languages': [], 'reasons': ['No language detected'], 'severity': 'critical'}
        primary = langs[0]
        language = primary.lang
        confidence = primary.prob
        # Simulate confidence if not available
        if confidence is None:
            confidence = 1.0 if language != 'unknown' else 0.0
        # Mixed language detection: segment text and compare
        segments = re.split(r'[.!?\n]', text)
        segment_langs = []
        for seg in segments:
            seg = seg.strip()
            if len(seg.split()) < 5:
                continue
            try:
                seg_lang = detect_langs(seg)[0].lang
                segment_langs.append(seg_lang)
            except Exception:
                continue
        lang_counts = {l: segment_langs.count(l) for l in set(segment_langs)}
        if len(lang_counts) > 1:
            total = sum(lang_counts.values())
            mixed = [(l, c/total) for l, c in lang_counts.items() if c/total > mixed_lang_ratio]
            if mixed:
                reasons.append(f"Mixed languages detected: {mixed}")
                severity = 'warning'
                mixed_language_flag = True
                mixed_languages = [l for l, _ in mixed]
            else:
                mixed_language_flag = False
                mixed_languages = []
        else:
            mixed_language_flag = False
            mixed_languages = []
        # Low confidence
        if confidence < low_conf_threshold:
            reasons.append(f"Low language detection confidence: {confidence:.2f}")
            severity = 'warning'
        return {
            'language': language,
            'language_confidence': confidence,
            'mixed_language_flag': mixed_language_flag,
            'mixed_languages': mixed_languages,
            'reasons': reasons,
            'severity': severity
        }
    except LangDetectException:
        return {'language': 'unknown', 'language_confidence': 0.0, 'mixed_language_flag': False, 'mixed_languages': [], 'reasons': ['Language detection failed'], 'severity': 'critical'} 