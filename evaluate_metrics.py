#!/usr/bin/env python3
"""
Evaluate commit message generation using BLEU, ROUGE, and METEOR scores.
Compares all variants and models against reference messages.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check and import NLP libraries
try:
    from nltk.translate.bleu_score import sentence_bleu
    from nltk.tokenize import word_tokenize
    import nltk
    nltk.download('punkt', quiet=True)
except ImportError:
    logger.error("Install nltk: pip install nltk")
    sys.exit(1)

try:
    from rouge_score import rouge_scorer
except ImportError:
    logger.error("Install rouge_score: pip install rouge-score")
    sys.exit(1)


class MetricsEvaluator:
    """Evaluate commit messages using multiple metrics."""
    
    def __init__(self):
        self.dataset = self.load_dataset()
        self.reference_messages = {
            entry['commit_id']: entry['commit_message'] 
            for entry in self.dataset
        }
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
        self.results = defaultdict(lambda: defaultdict(list))
    
    def load_dataset(self) -> List[Dict]:
        """Load reference dataset."""
        try:
            with open('processed_dataset.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("processed_dataset.json not found")
            sys.exit(1)
    
    def load_variant_outputs(self) -> Dict:
        """Load all variant output files."""
        outputs_dir = Path('outputs')
        variants = {}
        
        for variant_file in outputs_dir.glob('variant*_output.json'):
            variant_name = variant_file.stem.replace('_output', '')
            try:
                with open(variant_file, 'r') as f:
                    variants[variant_name] = json.load(f)
                logger.info(f"Loaded {variant_name}")
            except FileNotFoundError:
                logger.warning(f"File not found: {variant_file}")
        
        return variants
    
    def calculate_bleu(self, reference: str, hypothesis: str) -> float:
        """Calculate BLEU-1 score (0-1)."""
        try:
            ref_tokens = word_tokenize(reference.lower())
            hyp_tokens = word_tokenize(hypothesis.lower())
            
            # Use 1-gram and 2-gram weights for BLEU-1
            weights = (0.5, 0.5)
            score = sentence_bleu([ref_tokens], hyp_tokens, weights=weights)
            return score
        except Exception as e:
            logger.debug(f"BLEU-1 calculation error: {e}")
            return 0.0
    
    def calculate_rouge(self, reference: str, hypothesis: str) -> Tuple[float, float]:
        """Calculate ROUGE-1 and ROUGE-L scores."""
        try:
            scores = self.rouge_scorer.score(reference, hypothesis)
            rouge1 = scores['rouge1'].fmeasure
            rougeL = scores['rougeL'].fmeasure
            return rouge1, rougeL
        except Exception as e:
            logger.debug(f"ROUGE calculation error: {e}")
            return 0.0, 0.0
    
    def calculate_meteor(self, reference: str, hypothesis: str) -> float:
        """Calculate METEOR score - simplified."""
        # Simplified METEOR: common word overlap as proxy
        # Proper METEOR requires complex alignment algorithms
        try:
            ref_words = set(reference.lower().split())
            hyp_words = set(hypothesis.lower().split())
            
            if not ref_words:
                return 0.0
            
            common = len(ref_words & hyp_words)
            precision = common / len(hyp_words) if hyp_words else 0.0
            recall = common / len(ref_words) if ref_words else 0.0
            
            if precision + recall == 0:
                return 0.0
            
            # Simple F-score as METEOR proxy
            score = (2 * precision * recall) / (precision + recall)
            return score
        except Exception as e:
            logger.debug(f"METEOR calculation error: {e}")
            return 0.0
    
    def evaluate(self):
        """Evaluate all variants and models."""
        variants = self.load_variant_outputs()
        
        if not variants:
            logger.error("No variant output files found")
            sys.exit(1)
        
        logger.info(f"Found {len(variants)} variants")
        
        # Process each variant
        for variant_name, entries in variants.items():
            logger.info(f"\nEvaluating {variant_name}...")
            
            for entry in entries:
                commit_id = entry['commit_id']
                reference = self.reference_messages.get(commit_id, "")
                
                if not reference:
                    logger.warning(f"Reference not found for {commit_id}")
                    continue
                
                # Get responses from all models
                responses = entry.get('responses', {})
                
                for model_name, hypothesis in responses.items():
                    if not hypothesis or isinstance(hypothesis, list):
                        continue
                    
                    # Clean hypothesis
                    hypothesis = str(hypothesis).strip()
                    if not hypothesis:
                        continue
                    
                    # Calculate metrics
                    bleu = self.calculate_bleu(reference, hypothesis)
                    rouge1, rougeL = self.calculate_rouge(reference, hypothesis)
                    meteor = self.calculate_meteor(reference, hypothesis)
                    
                    # Store results
                    self.results[variant_name][model_name].append({
                        'commit_id': commit_id,
                        'bleu': bleu,
                        'rouge1': rouge1,
                        'rougeL': rougeL,
                        'meteor': meteor
                    })
        
        self.print_results()
        self.save_results()
    
    def print_results(self):
        """Print evaluation results."""
        logger.info("\n" + "="*80)
        logger.info("EVALUATION RESULTS")
        logger.info("="*80)
        
        for variant_name, models in sorted(self.results.items()):
            logger.info(f"\n{variant_name.upper()}")
            logger.info("-" * 80)
            
            for model_name, scores_list in sorted(models.items()):
                if not scores_list:
                    continue
                
                # Calculate averages
                avg_bleu = sum(s['bleu'] for s in scores_list) / len(scores_list)
                avg_rouge1 = sum(s['rouge1'] for s in scores_list) / len(scores_list)
                avg_rougeL = sum(s['rougeL'] for s in scores_list) / len(scores_list)
                avg_meteor = sum(s['meteor'] for s in scores_list) / len(scores_list)
                
                model_short = model_name.replace('_', '-')
                logger.info(f"\n  {model_short}:")
                logger.info(f"    BLEU-1:  {avg_bleu:.4f}")
                logger.info(f"    ROUGE-1: {avg_rouge1:.4f}")
                logger.info(f"    ROUGE-L: {avg_rougeL:.4f}")
                logger.info(f"    METEOR:  {avg_meteor:.4f}")
                logger.info(f"    Samples: {len(scores_list)}")
    
    def save_results(self):
        """Save evaluation results to JSON."""
        output_data = {}
        
        for variant_name, models in self.results.items():
            output_data[variant_name] = {}
            
            for model_name, scores_list in models.items():
                if not scores_list:
                    continue
                
                # Calculate statistics
                bleu_scores = [s['bleu'] for s in scores_list]
                rouge1_scores = [s['rouge1'] for s in scores_list]
                rougeL_scores = [s['rougeL'] for s in scores_list]
                meteor_scores = [s['meteor'] for s in scores_list]
                
                output_data[variant_name][model_name] = {
                    'samples': len(scores_list),
                    'bleu': {
                        'avg': sum(bleu_scores) / len(bleu_scores),
                        'min': min(bleu_scores),
                        'max': max(bleu_scores),
                    },
                    'rouge1': {
                        'avg': sum(rouge1_scores) / len(rouge1_scores),
                        'min': min(rouge1_scores),
                        'max': max(rouge1_scores),
                    },
                    'rougeL': {
                        'avg': sum(rougeL_scores) / len(rougeL_scores),
                        'min': min(rougeL_scores),
                        'max': max(rougeL_scores),
                    },
                    'meteor': {
                        'avg': sum(meteor_scores) / len(meteor_scores),
                        'min': min(meteor_scores),
                        'max': max(meteor_scores),
                    }
                }
        
        output_file = 'evaluation_results.json'
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"\nResults saved to {output_file}")


def main():
    """Main entry point."""
    logger.info("="*80)
    logger.info("COMMIT MESSAGE EVALUATION")
    logger.info("="*80)
    
    evaluator = MetricsEvaluator()
    evaluator.evaluate()
    
    logger.info("\n" + "="*80)
    logger.info("Evaluation complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
