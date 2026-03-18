#!/usr/bin/env python3
"""
Evaluation Metrics for Commit Message Generation v2
Computes BLEU, ROUGE, and METEOR scores comparing generated vs true messages.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from datetime import datetime

# Configuration
DATASET_BASE = Path(__file__).parent
OUTPUTS_DIR = DATASET_BASE / "output_2"

# Metrics output
METRICS_OUTPUT_FILE = OUTPUTS_DIR / "evaluation_results_v2.json"


def load_json(file_path):
    """Load JSON file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR loading {file_path}: {e}")
        return []


def calculate_bleu(reference, hypothesis):
    """Calculate BLEU-1 score."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    
    if len(hyp_tokens) == 0:
        return 0.0
    
    # Use sentence_bleu with weights for unigrams
    smoothing = SmoothingFunction().method1
    weights = (0.5, 0.5, 0, 0)  # Only unigrams and bigrams
    
    try:
        score = sentence_bleu([ref_tokens], hyp_tokens, weights=weights, smoothing_function=smoothing)
        return score
    except:
        return 0.0


def calculate_rouge(reference, hypothesis):
    """Calculate ROUGE-1 and ROUGE-L scores."""
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    
    try:
        scores = scorer.score(reference, hypothesis)
        rouge1_f = scores['rouge1'].fmeasure
        rougeL_f = scores['rougeL'].fmeasure
        return rouge1_f, rougeL_f
    except:
        return 0.0, 0.0


def calculate_meteor(reference, hypothesis):
    """Calculate METEOR-like score using word overlap F-score."""
    ref_words = set(reference.lower().split())
    hyp_words = set(hypothesis.lower().split())
    
    if len(ref_words) == 0 or len(hyp_words) == 0:
        return 0.0
    
    overlap = len(ref_words & hyp_words)
    
    # Precision and Recall
    precision = overlap / len(hyp_words) if hyp_words else 0
    recall = overlap / len(ref_words) if ref_words else 0
    
    # F-score
    if precision + recall == 0:
        return 0.0
    
    f_score = 2 * (precision * recall) / (precision + recall)
    return f_score


def evaluate_file(file_path):
    """Evaluate a single output file."""
    data = load_json(file_path)
    
    if not data:
        return None
    
    metrics = {
        'bleu1': [],
        'rouge1': [],
        'rougeL': [],
        'meteor': [],
    }
    
    for entry in data:
        true_msg = entry.get('true_message', '')
        gen_msg = entry.get('generated_message', '')
        
        # Skip if either message is empty or error
        if not true_msg or not gen_msg or gen_msg.startswith('ERROR'):
            continue
        
        # Calculate metrics
        bleu = calculate_bleu(true_msg, gen_msg)
        rouge1, rougeL = calculate_rouge(true_msg, gen_msg)
        meteor = calculate_meteor(true_msg, gen_msg)
        
        metrics['bleu1'].append(bleu)
        metrics['rouge1'].append(rouge1)
        metrics['rougeL'].append(rougeL)
        metrics['meteor'].append(meteor)
    
    # Calculate statistics
    results = {}
    for metric_name, scores in metrics.items():
        if scores:
            results[metric_name] = {
                'min': min(scores),
                'max': max(scores),
                'avg': sum(scores) / len(scores),
                'count': len(scores),
            }
        else:
            results[metric_name] = {
                'min': 0.0,
                'max': 0.0,
                'avg': 0.0,
                'count': 0,
            }
    
    return results


def main():
    print(f"\n{'='*100}")
    print(f"Evaluation Metrics for Commit Message Generation v2")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")
    
    # Get all output files
    output_files = sorted(OUTPUTS_DIR.glob("variant*_output.json"))
    
    if not output_files:
        print("ERROR: No output files found in output_2/")
        return
    
    print(f"Found {len(output_files)} output files\n")
    
    # Evaluate each file
    all_results = {}
    
    for file_path in output_files:
        file_name = file_path.stem.replace('_output', '')
        print(f"Evaluating {file_name}...", end=' ', flush=True)
        
        results = evaluate_file(file_path)
        if results:
            all_results[file_name] = results
            print(f"OK (BLEU: {results['bleu1']['avg']:.4f}, ROUGE-1: {results['rouge1']['avg']:.4f})")
        else:
            print("FAILED")
    
    # Save comprehensive results
    print(f"\nSaving results to {METRICS_OUTPUT_FILE.name}...")
    with open(METRICS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary tables
    print(f"\n{'='*100}")
    print("EVALUATION RESULTS SUMMARY")
    print(f"{'='*100}\n")
    
    # Group by variant
    variants = {}
    for key, results in all_results.items():
        parts = key.split('_')
        variant = '_'.join(parts[:-1])  # variant1_zeroshot -> variant1
        if variant not in variants:
            variants[variant] = {}
        variants[variant][key] = results
    
    # Print detailed tables for each variant
    for variant_name in sorted(variants.keys()):
        print(f"\n{variant_name.upper()}")
        print(f"{'-'*100}")
        
        # Prepare table data
        rows = []
        for strategy_key, results in sorted(variants[variant_name].items()):
            strategy = strategy_key.split('_')[-1]  # variant1_zeroshot -> zeroshot
            
            row = {
                'Strategy': strategy.upper(),
                'BLEU-1 (avg)': f"{results['bleu1']['avg']:.4f}",
                'ROUGE-1 (avg)': f"{results['rouge1']['avg']:.4f}",
                'ROUGE-L (avg)': f"{results['rougeL']['avg']:.4f}",
                'METEOR (avg)': f"{results['meteor']['avg']:.4f}",
                'Samples': results['bleu1']['count'],
            }
            rows.append(row)
        
        # Print table header
        if rows:
            headers = ['Strategy', 'BLEU-1 (avg)', 'ROUGE-1 (avg)', 'ROUGE-L (avg)', 'METEOR (avg)', 'Samples']
            col_widths = [max(len(h), max(len(str(r[h])) for r in rows)) for h in headers]
            
            # Header
            header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, col_widths))
            print(header_line)
            print('-' * len(header_line))
            
            # Rows
            for row in rows:
                row_line = ' | '.join(str(row[h]).ljust(w) for h, w in zip(headers, col_widths))
                print(row_line)
    
    # Cross-variant summary
    print(f"\n\n{'='*100}")
    print("CROSS-VARIANT COMPARISON (Average across all strategies)")
    print(f"{'='*100}\n")
    
    variant_summary = {}
    for variant_name, strategies in variants.items():
        bleu_scores = []
        rouge1_scores = []
        rougeL_scores = []
        meteor_scores = []
        
        for results in strategies.values():
            bleu_scores.append(results['bleu1']['avg'])
            rouge1_scores.append(results['rouge1']['avg'])
            rougeL_scores.append(results['rougeL']['avg'])
            meteor_scores.append(results['meteor']['avg'])
        
        variant_summary[variant_name] = {
            'bleu1_avg': sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0,
            'rouge1_avg': sum(rouge1_scores) / len(rouge1_scores) if rouge1_scores else 0,
            'rougeL_avg': sum(rougeL_scores) / len(rougeL_scores) if rougeL_scores else 0,
            'meteor_avg': sum(meteor_scores) / len(meteor_scores) if meteor_scores else 0,
        }
    
    # Print cross-variant table
    headers = ['Variant', 'BLEU-1 (avg)', 'ROUGE-1 (avg)', 'ROUGE-L (avg)', 'METEOR (avg)']
    col_widths = [12, 15, 15, 15, 15]
    
    header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print('-' * len(header_line))
    
    for variant_name in sorted(variant_summary.keys()):
        summary = variant_summary[variant_name]
        row = [
            variant_name,
            f"{summary['bleu1_avg']:.4f}",
            f"{summary['rouge1_avg']:.4f}",
            f"{summary['rougeL_avg']:.4f}",
            f"{summary['meteor_avg']:.4f}",
        ]
        row_line = ' | '.join(str(v).ljust(w) for v, w in zip(row, col_widths))
        print(row_line)
    
    print(f"\n{'='*100}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    main()
