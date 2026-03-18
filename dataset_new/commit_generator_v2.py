#!/usr/bin/env python3
"""
Commit Message Generation System v2 (New Dataset)
Generates commit messages using multiple prompting strategies and model variants
with three prompting approaches: zero-shot, one-shot, and few-shot.

Variants:
1. Diff-only: Uses raw unified diffs
2. CER-only: Uses structured Change Event Records
3. Full (CER + Diff): Uses both representations

Prompting strategies for each variant:
- Zero-shot: No examples
- One-shot: 1 example from one-shot JSON files
- Few-shot: 3 examples from few-shot JSON files

Output files:
- outputs/variant1_zeroshot_output.json
- outputs/variant1_oneshot_output.json
- outputs/variant1_fewshot_output.json
- outputs/variant2_zeroshot_output.json
- outputs/variant2_oneshot_output.json
- outputs/variant2_fewshot_output.json
- outputs/variant3_zeroshot_output.json
- outputs/variant3_oneshot_output.json
- outputs/variant3_fewshot_output.json
"""

import json
import os
import requests
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Configuration
MODELS = [
    "llama3:8b",
    "mistral:7b-instruct",
    "codeqwen:7b-chat",
    "llama3:70b-instruct"
]

OLLAMA_API_URL = "http://localhost:11434/api/generate"
TIMEOUT_SECONDS = 300  # 5 minutes

# Base paths
DATASET_BASE = Path(__file__).parent
OUTPUTS_DIR = DATASET_BASE / "output_2"
TEMPLATES_DIR = Path(r"c:\Users\mmayyaslocal\Downloads")

# Create outputs directory if it doesn't exist
OUTPUTS_DIR.mkdir(exist_ok=True)


def load_json(file_path):
    """Load JSON file safely."""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR loading {file_path}: {e}")
        return None


def load_templates():
    """Load all prompt templates."""
    templates = {
        'variant1': {
            'zeroshot': load_json(TEMPLATES_DIR / "template_diff.txt"),
            'oneshot': load_json(TEMPLATES_DIR / "template_diff 1.txt"),
            'fewshot': load_json(TEMPLATES_DIR / "template_diff 1.txt"),
        },
        'variant2': {
            'zeroshot': load_json(TEMPLATES_DIR / "template_cer.txt"),
            'oneshot': load_json(TEMPLATES_DIR / "template_cer 1.txt"),
            'fewshot': load_json(TEMPLATES_DIR / "template_cer 1.txt"),
        },
        'variant3': {
            'zeroshot': load_json(TEMPLATES_DIR / "template_cer_diff.txt"),
            'oneshot': load_json(TEMPLATES_DIR / "template_cer_diff 1.txt"),
            'fewshot': load_json(TEMPLATES_DIR / "template_cer_diff 1.txt"),
        }
    }
    return templates


def load_prompt_templates_as_strings():
    """Load templates as raw text strings instead of JSON."""
    templates = {}
    
    template_files = {
        'template_diff.txt': 'v1_zeroshot',
        'template_diff 1.txt': 'v1_oneshot_fewshot',
        'template_cer.txt': 'v2_zeroshot',
        'template_cer 1.txt': 'v2_oneshot_fewshot',
        'template_cer_diff.txt': 'v3_zeroshot',
        'template_cer_diff 1.txt': 'v3_oneshot_fewshot',
    }
    
    for file_name, key in template_files.items():
        file_path = TEMPLATES_DIR / file_name
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    templates[key] = content
                    print(f"  Loaded template: {file_name}")
            else:
                print(f"  WARNING: Template not found: {file_path}")
                templates[key] = ""
        except Exception as e:
            print(f"  ERROR loading template {file_name}: {e}")
            templates[key] = ""
    
    return templates


def format_cer_for_prompt(cer_data):
    """Format CER data for prompt injection."""
    if not cer_data or 'events' not in cer_data:
        return "No CER data available"
    
    events = cer_data['events']
    formatted = "Change Event Records:\n"
    
    for event in events:
        event_id = event.get('event_id', '')
        op = event.get('op', '')
        node = event.get('node', '')
        level = event.get('level', '')
        old = event.get('old', '')
        new = event.get('new', '')
        enclosing = event.get('enclosing', {})
        
        formatted += f"\n[{event_id}] {op.upper()} - {node} (level: {level})\n"
        
        if old:
            formatted += f"  OLD: {old}\n"
        if new:
            formatted += f"  NEW: {new}\n"
        
        if enclosing:
            enclosing_str = ", ".join([f"{k}: {v}" for k, v in enclosing.items()])
            formatted += f"  CONTEXT: {enclosing_str}\n"
    
    return formatted


def format_examples_for_prompt(examples_data, strategy):
    """Format examples for one-shot or few-shot prompting."""
    if not examples_data:
        return ""
    
    formatted = "Examples:\n"
    
    if strategy == 'oneshot' and 'example' in examples_data:
        # One-shot case
        example = examples_data['example']
        formatted += "\nExample:\n"
        formatted += f"Input: {example}\n"
        formatted += f"Output: {examples_data.get('commit_message', '')}\n"
    
    elif strategy == 'fewshot' and 'examples' in examples_data:
        # Few-shot case
        examples = examples_data['examples'][:3]  # Use only first 3 examples
        
        for idx, example in enumerate(examples, 1):
            formatted += f"\nExample {idx}:\n"
            # Determine what type of data this example has
            if 'diff' in example:
                formatted += f"Diff: {example['diff'][:500]}...\n"
            if 'cer' in example:
                formatted += f"CER: {str(example['cer'])[:500]}...\n"
            formatted += f"Commit Message: {example.get('commit_message', '')}\n"
    
    return formatted


def load_dataset(dataset_path):
    """Load the processed dataset."""
    data = load_json(dataset_path)
    if not data:
        print("ERROR: Could not load processed_dataset.json")
        sys.exit(1)
    return data


def load_cer_from_entry(entry):
    """Load CER data from file paths specified in entry."""
    cer_all = {}
    
    if 'cer_files' not in entry or not entry['cer_files']:
        return cer_all
    
    for cer_file_info in entry['cer_files']:
        cer_path = cer_file_info.get('cer_path', '')
        file_name = cer_file_info.get('file_name', '')
        
        # Construct full path
        full_path = DATASET_BASE / cer_path
        
        # Load CER data
        cer_data = load_json(full_path)
        if cer_data:
            cer_all[file_name] = cer_data
    
    return cer_all


def generate_prompt_variant1_zeroshot(templates, diff):
    """Variant 1: Diff-only, Zero-shot"""
    template = templates['v1_zeroshot']
    return template.replace('{input}', diff)


def generate_prompt_variant1_oneshot(templates, diff, examples_data):
    """Variant 1: Diff-only, One-shot"""
    template = templates['v1_oneshot_fewshot']
    
    # Format examples
    example_str = ""
    if examples_data and 'example' in examples_data:
        ex = examples_data['example']
        example_diff = ex.get('diff', '')
        example_msg = ex.get('commit_message', '')
        example_str = f"Diff:\n{example_diff}\n\nCommit Message: {example_msg}"
    
    prompt = template.replace('{examples}', example_str)
    prompt = prompt.replace('{input}', diff)
    return prompt


def generate_prompt_variant1_fewshot(templates, diff, examples_data):
    """Variant 1: Diff-only, Few-shot"""
    template = templates['v1_oneshot_fewshot']
    
    # Format examples (3 examples)
    example_str = ""
    if examples_data and 'examples' in examples_data:
        examples = examples_data['examples'][:3]
        for idx, ex in enumerate(examples, 1):
            example_diff = ex.get('diff', '')
            example_msg = ex.get('commit_message', '')
            example_str += f"Example {idx}:\n"
            example_str += f"Diff:\n{example_diff}\n"
            example_str += f"Commit Message: {example_msg}\n\n"
    
    prompt = template.replace('{examples}', example_str)
    prompt = prompt.replace('{input}', diff)
    return prompt


def generate_prompt_variant2_zeroshot(templates, cer_all):
    """Variant 2: CER-only, Zero-shot"""
    # Format all CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    template = templates['v2_zeroshot']
    return template.replace('{input}', cer_str)


def generate_prompt_variant2_oneshot(templates, cer_all, examples_data):
    """Variant 2: CER-only, One-shot"""
    # Format all CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    # Format examples (1 example)
    example_str = ""
    if examples_data and 'example' in examples_data:
        ex = examples_data['example']
        example_cer = ex.get('cer', {})
        example_msg = ex.get('commit_message', '')
        example_str = f"CER:\n{format_cer_for_prompt(example_cer)}\n\nCommit Message: {example_msg}"
    
    template = templates['v2_oneshot_fewshot']
    prompt = template.replace('{examples}', example_str)
    prompt = prompt.replace('{input}', cer_str)
    return prompt


def generate_prompt_variant2_fewshot(templates, cer_all, examples_data):
    """Variant 2: CER-only, Few-shot"""
    # Format all CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    # Format examples (3 examples)
    example_str = ""
    if examples_data and 'examples' in examples_data:
        examples = examples_data['examples'][:3]
        for idx, ex in enumerate(examples, 1):
            example_cer = ex.get('cer', {})
            example_msg = ex.get('commit_message', '')
            example_str += f"Example {idx}:\n"
            example_str += f"CER:\n{format_cer_for_prompt(example_cer)}\n"
            example_str += f"Commit Message: {example_msg}\n\n"
    
    template = templates['v2_oneshot_fewshot']
    prompt = template.replace('{examples}', example_str)
    prompt = prompt.replace('{input}', cer_str)
    return prompt


def generate_prompt_variant3_zeroshot(templates, diff, cer_all):
    """Variant 3: CER + Diff, Zero-shot"""
    # Format CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    combined_input = f"UNIFIED DIFF:\n{diff}\n\nCHANGE EVENT REPRESENTATION:\n{cer_str}"
    
    template = templates['v3_zeroshot']
    return template.replace('{input}', combined_input)


def generate_prompt_variant3_oneshot(templates, diff, cer_all, examples_data):
    """Variant 3: CER + Diff, One-shot"""
    # Format CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    combined_input = f"UNIFIED DIFF:\n{diff}\n\nCHANGE EVENT REPRESENTATION:\n{cer_str}"
    
    # Format examples (1 example)
    example_str = ""
    if examples_data and 'example' in examples_data:
        ex = examples_data['example']
        example_diff = ex.get('diff', '')
        example_cer = ex.get('cer', {})
        example_msg = ex.get('commit_message', '')
        example_str = f"Diff:\n{example_diff}\n\nCER:\n{format_cer_for_prompt(example_cer)}\n\nCommit Message: {example_msg}"
    
    template = templates['v3_oneshot_fewshot']
    prompt = template.replace('{examples}', example_str)
    prompt = prompt.replace('{input}', combined_input)
    return prompt


def generate_prompt_variant3_fewshot(templates, diff, cer_all, examples_data):
    """Variant 3: CER + Diff, Few-shot"""
    # Format CER data
    cer_str = ""
    for file_name, cer_data in cer_all.items():
        cer_str += f"\n--- FILE: {file_name} ---\n"
        cer_str += format_cer_for_prompt(cer_data)
    
    combined_input = f"UNIFIED DIFF:\n{diff}\n\nCHANGE EVENT REPRESENTATION:\n{cer_str}"
    
    # Format examples (3 examples)
    example_str = ""
    if examples_data and 'examples' in examples_data:
        examples = examples_data['examples'][:3]
        for idx, ex in enumerate(examples, 1):
            example_diff = ex.get('diff', '')
            example_cer = ex.get('cer', {})
            example_msg = ex.get('commit_message', '')
            example_str += f"Example {idx}:\n"
            example_str += f"Diff:\n{example_diff}\n"
            example_str += f"CER:\n{format_cer_for_prompt(example_cer)}\n"
            example_str += f"Commit Message: {example_msg}\n\n"
    
    template = templates['v3_oneshot_fewshot']
    prompt = template.replace('{examples}', example_str)
    prompt = template.replace('{input}', combined_input)
    return prompt


def query_ollama(prompt, model):
    """Query Ollama API for commit message generation."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.7,
    }
    
    try:
        # Ensure prompt is not empty
        if not prompt or len(prompt.strip()) == 0:
            return "ERROR: Empty prompt provided"
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        return data.get('response', '').strip()
    except requests.exceptions.Timeout:
        return f"ERROR: Timeout after {TIMEOUT_SECONDS}s"
    except requests.exceptions.ConnectionError as e:
        return f"ERROR: Connection failed - {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: Request failed - {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"


def run_generation(variants, test_entries=None):
    """Run the complete generation pipeline."""
    print(f"\n{'='*80}")
    print(f"Commit Message Generator v2 - Dataset New")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Load dataset
    print("Loading dataset...")
    dataset_path = DATASET_BASE / "processed_dataset.json"
    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} total entries")
    
    # Limit to test entries if specified
    if test_entries and test_entries > 0:
        dataset = dataset[:test_entries]
        print(f"Using first {test_entries} entries for testing")
    
    # Load templates
    print("Loading templates and examples...")
    templates = load_prompt_templates_as_strings()
    
    # Load example data
    examples_v1_oneshot = load_json(DATASET_BASE / "examples_one_shot_diff_only.json")
    examples_v1_fewshot = load_json(DATASET_BASE / "examples_few_shot_diff_only.json")
    examples_v2_oneshot = load_json(DATASET_BASE / "examples_one_shot_cer_only.json")
    examples_v2_fewshot = load_json(DATASET_BASE / "examples_few_shot_cer_only.json")
    examples_v3_oneshot = load_json(DATASET_BASE / "examples_one_shot_full.json")
    examples_v3_fewshot = load_json(DATASET_BASE / "examples_few_shot_full.json")
    
    print(f"Loaded examples for all variants\n")
    
    # Initialize output structure
    outputs = {
        'variant1_zeroshot': [],
        'variant1_oneshot': [],
        'variant1_fewshot': [],
        'variant2_zeroshot': [],
        'variant2_oneshot': [],
        'variant2_fewshot': [],
        'variant3_zeroshot': [],
        'variant3_oneshot': [],
        'variant3_fewshot': [],
    }
    
    # Check which variants to run
    variants_to_run = variants if variants else ['variant1', 'variant2', 'variant3']
    
    # Process each entry
    for entry_idx, entry in enumerate(dataset, 1):
        print(f"\n[Entry {entry_idx}/{len(dataset)}] Processing {entry.get('commit_id', 'unknown')[:12]}...")
        
        commit_id = entry.get('commit_id', '')
        repo = entry.get('repo', '')
        diff = entry.get('diff', '')
        true_message = entry.get('commit_message', '')
        
        # Load CER data
        cer_all = load_cer_from_entry(entry)
        
        # Process each variant
        for variant_idx, variant in enumerate(variants_to_run, 1):
            print(f"  {variant}...")
            
            # Query each model
            for model_idx, model in enumerate(MODELS, 1):
                # Generate prompts based on variant and strategy
                prompts = {}
                
                if 'variant1' in variant:
                    prompts['zeroshot'] = generate_prompt_variant1_zeroshot(templates, diff)
                    prompts['oneshot'] = generate_prompt_variant1_oneshot(templates, diff, examples_v1_oneshot)
                    prompts['fewshot'] = generate_prompt_variant1_fewshot(templates, diff, examples_v1_fewshot)
                
                elif 'variant2' in variant:
                    prompts['zeroshot'] = generate_prompt_variant2_zeroshot(templates, cer_all)
                    prompts['oneshot'] = generate_prompt_variant2_oneshot(templates, cer_all, examples_v2_oneshot)
                    prompts['fewshot'] = generate_prompt_variant2_fewshot(templates, cer_all, examples_v2_fewshot)
                
                elif 'variant3' in variant:
                    prompts['zeroshot'] = generate_prompt_variant3_zeroshot(templates, diff, cer_all)
                    prompts['oneshot'] = generate_prompt_variant3_oneshot(templates, diff, cer_all, examples_v3_oneshot)
                    prompts['fewshot'] = generate_prompt_variant3_fewshot(templates, diff, cer_all, examples_v3_fewshot)
                
                # Query for each prompting strategy
                for strategy in ['zeroshot', 'oneshot', 'fewshot']:
                    output_key = f"{variant}_{strategy}"
                    if output_key not in outputs:
                        outputs[output_key] = []
                    
                    prompt = prompts.get(strategy, '')
                    
                    print(f"    {model:25s} ({strategy:8s})...", end=' ', flush=True)
                    
                    response = query_ollama(prompt, model)
                    
                    # Check if response is an error
                    if response.startswith('ERROR'):
                        print("FAIL")
                    else:
                        print("OK")
                    
                    # Store result
                    outputs[output_key].append({
                        'entry_index': entry_idx,
                        'commit_id': commit_id,
                        'repo': repo,
                        'model': model,
                        'true_message': true_message,
                        'generated_message': response,
                    })
    
    # Save outputs
    print(f"\n{'='*80}")
    print("Saving results...")
    for variant_name, data in outputs.items():
        output_file = OUTPUTS_DIR / f"{variant_name}_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {output_file.name} ({len(data)} entries)")
    
    print(f"\n{'='*80}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Commit Message Generator v2 with multiple prompting strategies"
    )
    parser.add_argument(
        '--variants',
        nargs='+',
        choices=['variant1', 'variant2', 'variant3'],
        default=['variant1', 'variant2', 'variant3'],
        help='Which variants to run (default: all)'
    )
    parser.add_argument(
        '--test-entries',
        type=int,
        default=None,
        help='Number of entries to use for testing (default: use all)'
    )
    
    args = parser.parse_args()
    
    run_generation(args.variants, args.test_entries)


if __name__ == "__main__":
    main()
