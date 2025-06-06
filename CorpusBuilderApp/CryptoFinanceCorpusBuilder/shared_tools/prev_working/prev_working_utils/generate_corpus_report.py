import json
from collections import Counter, defaultdict
import random
from pathlib import Path

def main(corpus_dir, output, include_stats=False, include_examples=False):
    corpus_dir = Path(corpus_dir)
    extracted_dir = corpus_dir / '_extracted'
    low_quality_dir = corpus_dir / 'low_quality'
    all_jsons = list(extracted_dir.glob('*.json')) + list(low_quality_dir.glob('*.json'))
    all_chunks = []
    errors = []
    for jf in all_jsons:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                all_chunks.append(meta)
        except Exception as e:
            errors.append(f"{jf}: {e}")
    num_pdfs = len(set(Path(j['original_path']).name for j in all_chunks))
    num_chunks = len(all_chunks)
    avg_tokens = sum(j.get('token_count', 0) for j in all_chunks) / num_chunks if num_chunks else 0
    # Language distribution
    lang_dist = Counter(j.get('language', 'unknown') for j in all_chunks)
    # Quality flag distribution
    qflag_dist = Counter(j.get('quality_flag', 'ok') for j in all_chunks)
    # Domain distribution
    domain_dist = Counter(j.get('domain', 'unknown') for j in all_chunks)
    # Section heading distribution (top 10)
    heading_dist = Counter(j.get('section_heading', 'None') for j in all_chunks)
    # Markdown report
    with open(output, 'w', encoding='utf-8') as f:
        f.write(f"# Corpus Report\n\n")
        f.write(f"**Total PDFs processed:** {num_pdfs}\n\n")
        f.write(f"**Total chunks extracted:** {num_chunks}\n\n")
        f.write(f"**Average tokens per chunk:** {avg_tokens:.1f}\n\n")
        f.write(f"## Language Distribution\n")
        for lang, count in lang_dist.most_common():
            f.write(f"- {lang}: {count}\n")
        f.write(f"\n## Quality Flag Distribution\n")
        for flag, count in qflag_dist.most_common():
            f.write(f"- {flag}: {count}\n")
        f.write(f"\n## Domain Distribution\n")
        for dom, count in domain_dist.most_common():
            f.write(f"- {dom}: {count}\n")
        f.write(f"\n## Top Section Headings\n")
        for heading, count in heading_dist.most_common(10):
            f.write(f"- {heading}: {count}\n")
        if errors:
            f.write(f"\n## Error Summary\n")
            for err in errors:
                f.write(f"- {err}\n")
        if include_examples and all_chunks:
            f.write(f"\n## Sample Chunk\n")
            sample = random.choice(all_chunks)
            f.write(f"**File:** {sample.get('original_path')}\n\n")
            f.write(f"**Section Heading:** {sample.get('section_heading')}\n\n")
            f.write(f"**Tokens:** {sample.get('token_count')}\n\n")
            f.write(f"**Quality Flag:** {sample.get('quality_flag')}\n\n")
            f.write(f"**Text (first 500 chars):**\n\n{sample.get('chunk_summary', '')[:500]}\n\n")
        if include_stats:
            f.write(f"\n---\n**Before/After Metrics:**\n\n")
            f.write(f"- Chunks per PDF: {num_chunks / num_pdfs if num_pdfs else 0:.2f}\n")
            f.write(f"- Average tokens per chunk: {avg_tokens:.1f}\n")
    print(f"[INFO] Corpus report written to {output}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate corpus balance and domain distribution report')
    parser.add_argument('--corpus-dir', type=str, required=True, help='Path to corpus directory')
    parser.add_argument('--output', type=str, required=True, help='Output Markdown report file')
    parser.add_argument('--include-stats', action='store_true', help='Include detailed statistics')
    parser.add_argument('--include-examples', action='store_true', help='Include example documents')
    args = parser.parse_args()
    main(
        corpus_dir=args.corpus_dir,
        output=args.output,
        include_stats=args.include_stats,
        include_examples=args.include_examples
    ) 