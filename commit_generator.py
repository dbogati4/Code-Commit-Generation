#!/usr/bin/env python3
"""
Simplified Commit Message Generation using Ollama Models
Processes three experiment variants with hardcoded examples.
No checkpoint system - pure straightforward processing.
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
from extract_selective_xml import extract_xml_for_commit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('commit_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DATASET_PATH = "processed_dataset.json"
PROMPTS_DIR = "prompts"
OUTPUTS_DIR = "outputs"

# Ollama configuration - fast models + large model
OLLAMA_BASE_URL = "http://localhost:11434"
MODELS = [
    "llama3:8b",
    "mistral:7b-instruct",
    "codeqwen:7b-chat",
    "llama3:70b-instruct"
]

# Hardcoded examples for each variant
EXAMPLE_1_DIFF = """diff --git a/projects/SelfTest/ToStringTuple.cpp b/projects/SelfTest/ToStringTuple.cpp\nindex 86f68d37..9c855715 100644\n--- a/projects/SelfTest/ToStringTuple.cpp\n+++ b/projects/SelfTest/ToStringTuple.cpp\n@@ -21,7 +21,7 @@ TEST_CASE( \"tuple<float,int>\", \"[toString][tuple][c++11][.]\" )\n {\n     typedef std::tuple<float,int> type;\n     CHECK( \"1.2f\" == Catch::toString(float(1.2)) );\n-    CHECK( \"{ 1.2f, 0 }\" == Catch::toString(type{1.2,0}) );\n+    CHECK( \"{ 1.2f, 0 }\" == Catch::toString(type{1.2f,0}) );\n }\n \n TEST_CASE( \"tuple<string,string>\", \"[toString][tuple][c++11][.]\" )\n"""


EXAMPLE_1_MESSAGE = "Fix double-to-float conversion warning in tests"

EXAMPLE_1_XML = r"""Simplified srcML showing structural change:
<function>
  <type>
    <diff:delete>std::size_t</diff:delete>
    <diff:insert>std::pair&lt;std::size_t, std::ostringstream*&gt;</diff:insert>
  </type>
  <name>add</name><parameter_list>()</parameter_list> { ... }
</function>

INTERPRETATION:
- <diff:delete>: What was removed (return type changed FROM this)
- <diff:insert>: What was added (return type changed TO this)
- This shows function signature evolved to return more information"""

EXAMPLE_1_XML_MSG = "Change add() to return pair of index and stream pointer"

EXAMPLE_2_XML = r"""Simplified srcML showing structural change:
<cpp:include>
  <diff:insert>#include &lt;tuple&gt;</diff:insert>
</cpp:include>

<constructor name="ReusableStringStream">
  <diff:delete>member_init_list: m_index(...), m_oss(...)</diff:delete>
  <diff:insert>body: { std::tie(m_index, m_oss) = ... }</diff:insert>
</constructor>

INTERPRETATION:
- <diff:delete>: Old initialization style (member initialization list)
- <diff:insert>: New initialization style (std::tie unpacking in body)
- Includes new stdlib header for tuple unpacking"""

EXAMPLE_2_XML_MSG = "Refactor constructor to use std::tie for tuple unpacking"


def model_to_key(model_name: str) -> str:
    """Convert model name to safe JSON key."""
    return model_name.replace(":", "_").replace("-", "_").replace(".", "_")


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.timeout = 300  # 5 minutes timeout
    
    def generate(self, model: str, prompt: str) -> Optional[str]:
        """Generate response from Ollama model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Model {model} timed out after {self.timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return None
    
    def check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


class CommitGenerator:
    """Main class for generating commit messages using Ollama models."""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        Path(PROMPTS_DIR).mkdir(exist_ok=True)
        Path(OUTPUTS_DIR).mkdir(exist_ok=True)
    
    def load_dataset(self) -> List[Dict]:
        """Load dataset from JSON file."""
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def read_xml_file(self, xml_path: str) -> Optional[str]:
        """Read XML file content."""
        try:
            full_path = Path(xml_path)
            if not full_path.exists():
                return None
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading XML: {e}")
            return None
    
    def save_output(self, variant: str, data: List[Dict]):
        """Save output to JSON file."""
        output_file = Path(OUTPUTS_DIR) / f"{variant}_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {output_file}")
    
    def save_prompt(self, variant: str, entry_idx: int, prompt: str):
        """Save prompt for debugging."""
        variant_dir = Path(PROMPTS_DIR) / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        entry_file = variant_dir / f"entry_{entry_idx:04d}.json"
        with open(entry_file, 'w', encoding='utf-8') as f:
            json.dump({"prompt": prompt}, f, indent=2, ensure_ascii=False)
    
    def generate_variant1_prompt(self, entry: Dict) -> str:
        """Generate prompt for Variant 1: Raw Diff Only."""
        return f"""You are an expert software engineer analyzing code changes to generate a high-quality conventional commit message.

## File Information
Language: C++
File: {entry.get('file_name', 'source.cpp')}

## Changes
{entry.get('diff', '[diff not available]')}

## Real Examples from Actual C++ Projects

### Example 1
Diff: {EXAMPLE_1_DIFF}
Commit message: {EXAMPLE_1_MESSAGE}

## CRITICAL INSTRUCTIONS

RESPOND WITH ONLY A SINGLE-LINE COMMIT MESSAGE
NO EXPLANATIONS
NO THINKING PROCESS

Output EXACTLY ONE line.
Length: 5-20 words.

Return ONLY the commit message."""

    def generate_variant2_prompt(self, entry: Dict) -> str:
        """Generate prompt for Variant 2: XML Content Only."""
        xml_contents = []
        for xml_file_entry in entry.get('xml_files', []):
            xml_content = self.read_xml_file(xml_file_entry.get('xml_path', ''))
            if xml_content:
                xml_contents.append(xml_content)
        
        modifications = "\n\n".join(xml_contents) if xml_contents else "[XML not available]"
        
        return f"""You are an expert software engineer analyzing code changes using srcML semantic diff format.

## File Information
Language: C++
File: {entry.get('file_name', 'source.cpp')}

## UNDERSTANDING srcML DIFF MARKUP
In srcML format, structural changes are marked with diff tags:
- <diff:delete>: Code/structure that was REMOVED (old version)
- <diff:insert>: Code/structure that was ADDED (new version)
- Look for these tags to identify what CHANGED in the code structure
- Understand dependencies (e.g., new #includes required by new code)

## Changes (srcML Semantic Diff)
{modifications}

## Real Examples from Actual C++ Projects

### Example 1: Function Signature Change
{EXAMPLE_1_XML}
Commit message: {EXAMPLE_1_XML_MSG}

### Example 2: Constructor Refactoring
{EXAMPLE_2_XML}
Commit message: {EXAMPLE_2_XML_MSG}

## CRITICAL INSTRUCTIONS

1. Focus on <diff:delete> and <diff:insert> tags
2. Understand the semantic meaning (WHY the change was made)
3. Identify related changes (e.g., include additions with code changes)
4. RESPOND WITH ONLY A SINGLE-LINE COMMIT MESSAGE
5. NO EXPLANATIONS, NO THINKING PROCESS

Output EXACTLY ONE line.
Length: 5-20 words.

Return ONLY the commit message."""

    def generate_variant3_prompt(self, entry: Dict) -> str:
        """Generate prompt for Variant 3: Combined Diff + XML."""
        xml_contents = []
        for xml_file_entry in entry.get('xml_files', []):
            xml_content = self.read_xml_file(xml_file_entry.get('xml_path', ''))
            if xml_content:
                xml_contents.append(xml_content)
        
        diff_part = entry.get('diff', '[diff not available]')
        xml_part = "\n\n".join(xml_contents) if xml_contents else "[XML not available]"
        combined = f"{diff_part}\n\n---XML---\n\n{xml_part}"
        
        return f"""You are an expert software engineer analyzing code changes to generate a high-quality conventional commit message.

## File Information
Language: C++
File: {entry.get('file_name', 'source.cpp')}

## Changes (Diff + XML)
{combined}

## Real Examples from Actual C++ Projects

### Example 1 (Combined)
Diff: {EXAMPLE_1_DIFF}
XML: {EXAMPLE_1_XML}
Commit message: {EXAMPLE_1_MESSAGE}


## CRITICAL INSTRUCTIONS

RESPOND WITH ONLY A SINGLE-LINE COMMIT MESSAGE
NO EXPLANATIONS
NO THINKING PROCESS

Output EXACTLY ONE line.
Length: 5-20 words.

Return ONLY the commit message."""

    def generate_variant4_prompt(self, entry: Dict) -> str:
        """Generate prompt for Variant 4: Diff + Selective XML (IMPROVED)."""
        # Extract selective XML focusing only on changes
        selective_xml = extract_xml_for_commit(
            entry.get('commit_id', ''),
            entry.get('xml_files', [])
        )
        
        diff_part = entry.get('diff', '[diff not available]')
        
        return f"""You are an expert software engineer analyzing code changes to generate a high-quality conventional commit message.

## File Information
Language: C++
File: {entry.get('file_name', 'source.cpp')}

## Changes Overview (Diff)
{diff_part}

## Semantic Structure Changes (Selective srcML Excerpts)
Below are ONLY the relevant parts of the code that changed (marked with diff:insert/diff:delete):

{selective_xml}

## INSTRUCTION
1. Read the diff to understand WHAT changed
2. Read the selective XML excerpts to understand structural/semantic impact
3. Combine both perspectives for comprehensive understanding
4. Generate a clear, concise commit message

## Real Examples from Actual C++ Projects

### Example 1
Diff: {EXAMPLE_1_DIFF}
Semantic Changes: {EXAMPLE_1_XML}
Commit message: {EXAMPLE_1_MESSAGE}

## CRITICAL INSTRUCTIONS

RESPOND WITH ONLY A SINGLE-LINE COMMIT MESSAGE
NO EXPLANATIONS
NO THINKING PROCESS

Output EXACTLY ONE line.
Length: 5-20 words.

Return ONLY the commit message."""

    def process_entries(self, dataset: List[Dict], variants: List[str], num_entries: Optional[int] = None):
        """Process entries through all specified variants and models."""
        if num_entries:
            dataset = dataset[:num_entries]
        
        # Prepare output storage - separate output list for each variant
        outputs = {v: [] for v in variants}
        
        for entry_idx, entry in enumerate(dataset, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Entry {entry_idx}/{len(dataset)} | Commit: {entry.get('commit_id', 'unknown')[:8]}...")
            
            # Process each variant separately
            for variant in variants:
                logger.info(f"  {variant}:")
                
                # Generate prompt for this variant
                if variant == "variant1":
                    prompt = self.generate_variant1_prompt(entry)
                elif variant == "variant2":
                    prompt = self.generate_variant2_prompt(entry)
                elif variant == "variant3":
                    prompt = self.generate_variant3_prompt(entry)
                else:  # variant4
                    prompt = self.generate_variant4_prompt(entry)
                
                # Save prompt
                self.save_prompt(variant, entry_idx - 1, prompt)
                
                # Get responses from all models for THIS variant
                variant_responses = {}
                for model in MODELS:
                    response = self.ollama_client.generate(model, prompt)
                    model_key = model_to_key(model)
                    status = "OK" if response else "FAIL"
                    logger.info(f"    {model}: {status}")
                    variant_responses[model_key] = response if response else "[ERROR]"
                
                # Save entry with ONLY this variant's responses
                output_entry = {
                    "commit_id": entry.get('commit_id'),
                    "file_name": entry.get('file_name'),
                    "commit_message": entry.get('commit_message'),
                    "prompt_type": variant,
                    "responses": variant_responses
                }
                
                outputs[variant].append(output_entry)
        
        # Save all outputs
        for variant in variants:
            self.save_output(variant, outputs[variant])
        
        logger.info(f"\n{'='*60}")
        logger.info("Complete!")
        logger.info(f"Results: {OUTPUTS_DIR}/")
        logger.info(f"Prompts: {PROMPTS_DIR}/")
    
    def run(self, variants: List[str] = None, test_entries: Optional[int] = None):
        """Run the experiment."""
        if variants is None:
            variants = ["variant1", "variant2", "variant3"]
        
        # Check Ollama connection
        if not self.ollama_client.check_connection():
            logger.error("ERROR: Cannot connect to Ollama at http://localhost:11434")
            sys.exit(1)
        
        logger.info("Connected to Ollama")
        logger.info(f"Models: {', '.join(MODELS)}")
        
        # Load dataset
        dataset = self.load_dataset()
        logger.info(f"Dataset: {len(dataset)} entries")
        logger.info(f"Running: {len(variants)} variant(s), {test_entries or len(dataset)} entry(ies)")
        
        # Process entries
        self.process_entries(dataset, variants, test_entries)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate commit messages")
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=["variant1", "variant2", "variant3", "variant4"],
        default=["variant1", "variant2", "variant3", "variant4"],
        help="Variants to run (default: all 4)"
    )
    parser.add_argument(
        "--test-entries",
        type=int,
        default=None,
        help="Process only N entries (for testing)"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("COMMIT MESSAGE GENERATION SYSTEM")
    logger.info("="*60)
    logger.info(f"Variants: {', '.join(args.variants)}")
    logger.info(f"Models: {', '.join(MODELS)}")
    if args.test_entries:
        logger.info(f"Test: {args.test_entries} entries")
    
    generator = CommitGenerator()
    
    try:
        generator.run(args.variants, args.test_entries)
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
