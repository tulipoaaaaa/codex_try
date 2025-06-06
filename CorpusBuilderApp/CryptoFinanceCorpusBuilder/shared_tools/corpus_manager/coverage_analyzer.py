# coverage_analyzer.py
"""
Advanced corpus coverage analyzer with visualization
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import math

# Target allocations from domain configuration
TARGET_ALLOCATIONS = {
    "crypto_derivatives": 0.20,
    "high_frequency_trading": 0.15,
    "market_microstructure": 0.15,
    "risk_management": 0.15,
    "decentralized_finance": 0.12,
    "portfolio_construction": 0.10,
    "valuation_models": 0.08,
    "regulation_compliance": 0.05
}

# Traditional vs Crypto-native categorization
TRADITIONAL_FINANCE = ["risk_management", "portfolio_construction", "regulation_compliance"]
CRYPTO_NATIVE = ["crypto_derivatives", "high_frequency_trading", "market_microstructure", 
                 "decentralized_finance", "valuation_models"]

def count_tokens(text_file):
    """Count tokens in a text file (simple whitespace tokenization)"""
    try:
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return len(text.split())
    except Exception as e:
        print(f"Error counting tokens in {text_file}: {e}")
        return 0

def calculate_gini(values):
    """Calculate Gini coefficient of inequality (0 = perfect equality, 1 = max inequality)"""
    values = np.array(values)
    if np.amin(values) < 0:
        values -= np.amin(values)  # Make all values non-negative
    
    # If all values are 0, Gini coefficient is 0 (perfect equality)
    if np.sum(values) == 0:
        return 0
    
    # Sort values
    values = np.sort(values)
    n = len(values)
    index = np.arange(1, n + 1)
    
    # Calculate Gini coefficient
    return (np.sum((2 * index - n - 1) * values)) / (n * np.sum(values))

def calculate_entropy(values):
    """Calculate Shannon entropy (higher = more evenly distributed)"""
    values = np.array(values)
    
    # Normalize to probabilities
    total = np.sum(values)
    if total == 0:
        return 0
    
    probabilities = values / total
    
    # Calculate entropy (-sum(p * log2(p)))
    entropy = 0
    for p in probabilities:
        if p > 0:  # Avoid log(0)
            entropy -= p * math.log2(p)
    
    # Normalize to [0, 1] by dividing by max entropy (log2(n))
    max_entropy = math.log2(len(values)) if len(values) > 0 else 0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    
    return normalized_entropy

def infer_file_origin(file_path, metadata):
    """Infer the origin of a file from its path or metadata"""
    if metadata and 'origin' in metadata:
        return metadata['origin']
    
    path_str = str(file_path).lower()
    if 'curated' in path_str:
        return 'curated'
    elif 'annas' in path_str:
        return 'annas_archive'
    elif 'scidb' in path_str:
        return 'scidb'
    elif 'arxiv' in path_str:
        return 'arxiv'
    elif 'github' in path_str:
        return 'github'
    elif 'fred' in path_str:
        return 'fred'
    elif 'web' in path_str:
        return 'web'
    else:
        return 'unknown'

def analyze_corpus(corpus_dir, output_file=None, visualize=False):
    """Analyze corpus coverage and generate statistics"""
    corpus_path = Path(corpus_dir)
    
    if not corpus_path.exists():
        print(f"Error: Corpus directory {corpus_dir} does not exist")
        return None
    
    print(f"Analyzing corpus in {corpus_dir}...")
    
    # Collect domains and files
    domains = [d for d in corpus_path.iterdir() if d.is_dir() and not d.name.endswith('_extracted')]
    print(f"Found {len(domains)} domains")
    
    # Initialize domain statistics
    domain_stats = {}
    total_tokens = 0
    total_documents = 0
    
    # Track sources
    sources_count = Counter()
    
    # Collect statistics for each domain
    for domain_dir in domains:
        domain_name = domain_dir.name
        domain_stats[domain_name] = {
            'documents': 0,
            'tokens': 0,
            'size_bytes': 0,
            'by_source': Counter()
        }
        
        # Count documents
        pdf_files = list(domain_dir.glob('*.pdf'))
        domain_stats[domain_name]['documents'] = len(pdf_files)
        total_documents += len(pdf_files)
        
        # Calculate size
        domain_stats[domain_name]['size_bytes'] = sum(os.path.getsize(f) for f in pdf_files)
        
        # Check for extracted text
        extracted_dir = corpus_path / f"{domain_name}_extracted"
        if extracted_dir.exists():
            text_files = list(extracted_dir.glob('*.txt'))
            
            # Count tokens in extracted text
            domain_tokens = 0
            for text_file in text_files:
                tokens = count_tokens(text_file)
                domain_tokens += tokens
                
                # Get corresponding PDF and metadata
                pdf_name = text_file.stem
                pdf_file = domain_dir / f"{pdf_name}.pdf"
                meta_file = domain_dir / f"{pdf_name}.pdf.meta"
                
                # Load metadata if available
                metadata = None
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                # Determine source
                source = infer_file_origin(pdf_file, metadata)
                domain_stats[domain_name]['by_source'][source] += 1
                sources_count[source] += 1
            
            domain_stats[domain_name]['tokens'] = domain_tokens
            total_tokens += domain_tokens
    
    # Calculate percentages
    domain_percentages = {}
    for domain, stats in domain_stats.items():
        domain_percentages[domain] = (stats['tokens'] / total_tokens) if total_tokens > 0 else 0
    
    # Calculate traditional vs crypto-native split
    tf_tokens = sum(domain_stats.get(d, {}).get('tokens', 0) for d in TRADITIONAL_FINANCE)
    cn_tokens = sum(domain_stats.get(d, {}).get('tokens', 0) for d in CRYPTO_NATIVE)
    
    tf_percentage = (tf_tokens / total_tokens) if total_tokens > 0 else 0
    cn_percentage = (cn_tokens / total_tokens) if total_tokens > 0 else 0
    
    # Calculate coverage gap
    coverage_gaps = {}
    total_absolute_gap = 0
    
    for domain, target in TARGET_ALLOCATIONS.items():
        current = domain_percentages.get(domain, 0)
        gap = target - current
        coverage_gaps[domain] = {
            'target': target,
            'current': current,
            'gap': gap,
            'status': "UNDERREPRESENTED" if gap > 0.03 else 
                     "OVERREPRESENTED" if gap < -0.03 else "ADEQUATE"
        }
        total_absolute_gap += abs(gap)
    
    # Calculate balance score (0-100, higher is better)
    balance_score = max(0, 100 - (total_absolute_gap * 100))
    
    # Calculate additional metrics
    gini_coefficient = calculate_gini(list(domain_percentages.values()))
    distribution_entropy = calculate_entropy(list(domain_percentages.values()))
    
    # Source diversity
    source_percentages = {source: count/total_documents for source, count in sources_count.items()} if total_documents > 0 else {}
    source_diversity_entropy = calculate_entropy(list(source_percentages.values()))
    
    # Create comprehensive results
    results = {
        'summary': {
            'total_documents': total_documents,
            'total_tokens': total_tokens,
            'balance_score': balance_score,
            'gini_coefficient': gini_coefficient,
            'distribution_entropy': distribution_entropy,
            'source_diversity_entropy': source_diversity_entropy,
            'traditional_finance_percentage': tf_percentage * 100,
            'crypto_native_percentage': cn_percentage * 100,
            'tf_cn_ratio': tf_percentage / cn_percentage if cn_percentage > 0 else 0,
            'target_tf_cn_ratio': 0.4 / 0.6,  # 40/60 target
            'tf_cn_alignment': 1 - abs((tf_percentage / cn_percentage) - (0.4 / 0.6)) if cn_percentage > 0 else 0
        },
        'domains': {domain: stats for domain, stats in domain_stats.items()},
        'percentages': {domain: pct * 100 for domain, pct in domain_percentages.items()},
        'coverage_gaps': coverage_gaps,
        'sources': {source: count for source, count in sources_count.items()},
        'source_percentages': {source: pct * 100 for source, pct in source_percentages.items()}
    }
    
    # Print summary
    print("\n===== CORPUS COVERAGE ANALYSIS =====")
    print(f"Total documents: {total_documents}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Balance score: {balance_score:.1f}/100")
    print(f"Split: {tf_percentage*100:.1f}% Traditional Finance / {cn_percentage*100:.1f}% Crypto-Native")
    print(f"Target split: 40% Traditional Finance / 60% Crypto-Native")
    print(f"Source diversity: {source_diversity_entropy:.3f} entropy ({len(sources_count)} sources)")
    print("\nDomain distribution:")
    for domain in sorted(domain_percentages, key=domain_percentages.get, reverse=True):
        gap = coverage_gaps[domain]['gap'] * 100
        status = coverage_gaps[domain]['status']
        print(f"  {domain}: {domain_percentages[domain]*100:.1f}% ({domain_stats[domain]['tokens']:,} tokens, {gap:+.1f}% gap) - {status}")
    
    print("\nSource distribution:")
    for source in sorted(source_percentages, key=source_percentages.get, reverse=True):
        print(f"  {source}: {source_percentages[source]*100:.1f}% ({sources_count[source]} documents)")
    
    # Save results if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")
    
    # Generate visualizations
    if visualize:
        generate_visualizations(results, output_file)
    
    return results

def generate_visualizations(results, output_file):
    """Generate visualizations for corpus coverage"""
    # Set up the figure
    plt.figure(figsize=(15, 10))
    
    # 1. Domain distribution bar chart
    plt.subplot(2, 2, 1)
    domains = list(results['percentages'].keys())
    percentages = list(results['percentages'].values())
    targets = [TARGET_ALLOCATIONS.get(domain, 0) * 100 for domain in domains]
    
    # Sort by current percentage
    sorted_indices = np.argsort(percentages)[::-1]
    domains = [domains[i] for i in sorted_indices]
    percentages = [percentages[i] for i in sorted_indices]
    targets = [targets[i] for i in sorted_indices]
    
    x = np.arange(len(domains))
    width = 0.35
    
    plt.bar(x - width/2, percentages, width, label='Current %')
    plt.bar(x + width/2, targets, width, label='Target %', alpha=0.7)
    
    plt.xlabel('Domain')
    plt.ylabel('Percentage')
    plt.title('Domain Distribution vs Target')
    plt.xticks(x, domains, rotation=45, ha='right')
    plt.legend()
    
    # 2. Traditional vs Crypto-Native split pie chart
    plt.subplot(2, 2, 2)
    tf_cn_labels = ['Traditional Finance', 'Crypto-Native']
    tf_cn_values = [results['summary']['traditional_finance_percentage'], 
                   results['summary']['crypto_native_percentage']]
    tf_cn_targets = [40, 60]  # Target split
    
    # Create a pie chart
    plt.pie(tf_cn_values, labels=tf_cn_labels, autopct='%1.1f%%', startangle=90,
            colors=['#3498db', '#e74c3c'])
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Traditional Finance vs Crypto-Native Split')
    
    # 3. Coverage gap radar chart
    plt.subplot(2, 2, 3)
    
    # Prepare data for radar chart
    categories = list(results['coverage_gaps'].keys())
    current_values = [results['coverage_gaps'][domain]['current'] * 100 for domain in categories]
    target_values = [results['coverage_gaps'][domain]['target'] * 100 for domain in categories]
    
    # Number of variables
    N = len(categories)
    
    # Calculate angle for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Add the first point at the end to close the polygon
    current_values += current_values[:1]
    target_values += target_values[:1]
    categories += categories[:1]
    
    # Create the plot
    ax = plt.subplot(2, 2, 3, polar=True)
    
    # Draw the current values
    ax.plot(angles, current_values, 'o-', linewidth=2, label='Current')
    ax.fill(angles, current_values, alpha=0.25)
    
    # Draw the target values
    ax.plot(angles, target_values, 'o-', linewidth=2, label='Target')
    ax.fill(angles, target_values, alpha=0.25)
    
    # Set category labels
    plt.xticks(angles[:-1], categories[:-1], rotation=45)
    
    # Set y-axis limit
    plt.ylim(0, max(max(current_values), max(target_values)) * 1.1)
    
    plt.title('Domain Coverage Radar Chart')
    plt.legend(loc='upper right')
    
    # 4. Source distribution pie chart
    plt.subplot(2, 2, 4)
    sources = list(results['source_percentages'].keys())
    source_values = list(results['source_percentages'].values())
    
    # Sort by percentage
    sorted_indices = np.argsort(source_values)[::-1]
    sources = [sources[i] for i in sorted_indices]
    source_values = [source_values[i] for i in sorted_indices]
    
    # Combine small sources into "Other"
    threshold = 2.0  # Combine sources with less than 2%
    other_sum = 0
    filtered_sources = []
    filtered_values = []
    
    for i, (source, value) in enumerate(zip(sources, source_values)):
        if value < threshold:
            other_sum += value
        else:
            filtered_sources.append(source)
            filtered_values.append(value)
    
    if other_sum > 0:
        filtered_sources.append('Other')
        filtered_values.append(other_sum)
    
    # Create explode effect for the largest source
    explode = [0.1 if i == 0 else 0 for i in range(len(filtered_sources))]
    
    plt.pie(filtered_values, labels=filtered_sources, explode=explode, 
            autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Source Distribution')
    
    # Adjust layout and save
    plt.tight_layout()
    
    # Save figure
    if output_file:
        viz_file = output_file.replace('.json', '_visualization.png')
        plt.savefig(viz_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {viz_file}")
    
    # Create supplementary visualizations
    
    # 1. Domain balance heatmap
    plt.figure(figsize=(12, 6))
    
    # Create a dataframe for the heatmap
    df = pd.DataFrame({
        'Domain': list(results['coverage_gaps'].keys()),
        'Current %': [results['coverage_gaps'][d]['current'] * 100 for d in results['coverage_gaps']],
        'Target %': [results['coverage_gaps'][d]['target'] * 100 for d in results['coverage_gaps']],
        'Gap %': [results['coverage_gaps'][d]['gap'] * 100 for d in results['coverage_gaps']]
    })
    
    # Sort by gap
    df = df.sort_values('Gap %', ascending=False)
    
    # Create a pivoted version for the heatmap
    heatmap_data = df[['Domain', 'Current %', 'Target %', 'Gap %']]
    heatmap_data = heatmap_data.set_index('Domain')
    
    # Create the heatmap
    plt.subplot(1, 1, 1)
    sns.heatmap(heatmap_data, annot=True, cmap="RdYlGn_r", center=0, fmt='.1f')
    plt.title('Domain Coverage Heatmap')
    plt.tight_layout()
    
    # Save supplementary visualization
    if output_file:
        heatmap_file = output_file.replace('.json', '_heatmap.png')
        plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
        print(f"Heatmap saved to {heatmap_file}")
    
    # Keep the plot open if running interactively
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Analyze corpus coverage')
    parser.add_argument('--corpus-dir', required=True, help='Path to corpus directory')
    parser.add_argument('--output', help='Output file for analysis results (JSON)')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    
    args = parser.parse_args()
    
    analyze_corpus(args.corpus_dir, args.output, args.visualize)

if __name__ == '__main__':
    main()
