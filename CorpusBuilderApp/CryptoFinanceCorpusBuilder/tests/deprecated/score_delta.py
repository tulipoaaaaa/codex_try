import argparse
import pandas as pd
import json
import sacrebleu
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from tqdm import tqdm
import re
import csv
import os


def read_outputs(path):
    path = Path(path)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
        # Accept either 'completion' or 'lora_answer' as the answer column
        if 'completion' not in df.columns and 'lora_answer' in df.columns:
            df = df.rename(columns={'lora_answer': 'completion'})
        return df[['prompt', 'completion']]
    elif path.suffix == ".jsonl":
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                answer = obj.get('completion')
                if answer is None and 'lora_answer' in obj:
                    answer = obj['lora_answer']
                if 'prompt' in obj and answer is not None:
                    rows.append({'prompt': obj['prompt'], 'completion': answer})
        return pd.DataFrame(rows)
    else:
        raise ValueError(f"Unsupported file type: {path}")

def compute_bleu(refs, hyps):
    # sacrebleu expects list of references (list of list of str) and list of hypotheses
    return sacrebleu.corpus_bleu(hyps, [refs]).score

def compute_overlap(a, b):
    # Token overlap as Jaccard index, case-insensitive, punctuation-stripped
    def tokenize(text):
        return re.sub(r"[^\w\s]", "", text.lower()).split()
    set_a = set(tokenize(a))
    set_b = set(tokenize(b))
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def align_by_prompt(df_old, df_new):
    # Merge on prompt, inner join
    merged = pd.merge(df_old, df_new, on='prompt', suffixes=('_old', '_new'), how='inner')
    dropped = len(df_old) - len(merged)
    if dropped > 0:
        print(f"[WARN] {dropped} prompts from --old were not found in --new and were dropped.", file=sys.stderr)
    if merged.empty:
        sys.exit("[ERR] no matching prompts")
    return merged

def score_outputs(df_old, df_new):
    merged = align_by_prompt(df_old, df_new)
    bleus = []
    overlaps = []
    refs, hyps = [], []
    for _, row in tqdm(merged.iterrows(), total=len(merged), desc=f"scoring ({len(merged)})"):
        ref = row['completion_old']
        hyp = row['completion_new']
        if not hyp.strip() or not ref.strip():
            bleu = 0.0
        else:
            bleu = sacrebleu.sentence_bleu(hyp, [ref]).score
        overlap = compute_overlap(ref, hyp)
        bleus.append(bleu)
        overlaps.append(overlap)
        refs.append(ref)
        hyps.append(hyp)
    merged['bleu'] = bleus
    merged['overlap'] = overlaps
    # Also compute corpus BLEU
    corpus_bleu = sacrebleu.corpus_bleu(hyps, [refs]).score
    return merged, corpus_bleu

def plot_scatter_chart(df, png_path):
    plt.style.use("ggplot")
    plt.figure(figsize=(12, 6))
    plt.scatter(range(len(df)), df['bleu'], alpha=0.4, label='BLEU-4', s=8, color='steelblue')
    plt.scatter(range(len(df)), df['overlap'], alpha=0.4, label='Token Overlap', s=8, color='orange')
    plt.xlabel('Prompt Index')
    plt.ylabel('Score')
    plt.title('BLEU-4 and Token Overlap per Prompt')
    plt.legend()
    plt.tight_layout()
    plt.savefig(png_path)
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Compare old vs new outputs, compute BLEU/token-overlap, output CSV and scatter chart.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--old', required=True, help='Previous outputs (CSV or JSONL, columns prompt, completion|lora_answer)')
    parser.add_argument('--new', required=True, help='New outputs (JSONL with prompt, completion)')
    parser.add_argument('--val', required=False, help='Optional validation outputs (JSONL, scored as old vs new on the val set)')
    parser.add_argument('--out', required=True, help='Output CSV path')
    parser.add_argument('--png', required=False, help='Output PNG scatter chart path (auto-derived from --out if omitted)')
    parser.add_argument('--push', action='store_true', help='If set, push aggregate metrics using push_metrics (if available)')
    args = parser.parse_args()

    png_path = args.png or str(Path(args.out).with_suffix('.png'))

    df_old = read_outputs(args.old)
    df_new = read_outputs(args.new)
    scored, corpus_bleu = score_outputs(df_old, df_new)
    scored.to_csv(args.out, index=False, quoting=csv.QUOTE_ALL, escapechar='\\')
    plot_scatter_chart(scored, png_path)
    print(f"Mean BLEU-4 (sentence): {scored['bleu'].mean():.2f}")
    print(f"Corpus BLEU-4: {corpus_bleu:.2f}")
    print(f"Mean token overlap: {scored['overlap'].mean():.2f}")

    if args.push:
        try:
            from push_metrics import push_metrics
            push_metrics("v4b", scored['bleu'].mean(), scored['overlap'].mean())
            print("[push_metrics] Metrics pushed.")
        except ImportError:
            print("[push_metrics] push_metrics module not found.")

    if args.val:
        print("\nScoring validation file (old vs new on val set):")
        df_val = read_outputs(args.val)
        val_scored, val_corpus_bleu = score_outputs(df_val, df_new)
        val_csv = Path(args.out).with_name('val_' + Path(args.out).name)
        val_png = Path(png_path).with_name('val_' + Path(png_path).name)
        val_scored.to_csv(val_csv, index=False, quoting=csv.QUOTE_ALL, escapechar='\\')
        plot_scatter_chart(val_scored, val_png)
        print(f"[VAL] Mean BLEU-4 (sentence): {val_scored['bleu'].mean():.2f}")
        print(f"[VAL] Corpus BLEU-4: {val_corpus_bleu:.2f}")
        print(f"[VAL] Mean token overlap: {val_scored['overlap'].mean():.2f}")

if __name__ == "__main__":
    main() 