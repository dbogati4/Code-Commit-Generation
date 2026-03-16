# Commit Message Generation Experiment

## Overview

This system generates commit messages using multiple Ollama-based language models. It processes a dataset of code commits with diffs and XML-structured code information, generating commit messages through three different experiment variants.

## System Architecture

### Dataset Structure

The main input file is `processed_dataset.json`, which contains entries with:
- **commit_id**: Unique identifier for the commit
- **repo**: Repository name
- **diff**: Raw GitHub diff of the changes
- **commit_message**: Human-written original commit message (ground truth)
- **xml_files**: Array of XML files with structured code information
  - **file_name**: Name of the source file
  - **xml_path**: Path to srcML XML representation of the code

### Checkpoint Management

The `checkpoints/state.json` file tracks processing progress:
```json
{
  "scanned_commits": 4717,
  "valid_entries": 69,
  "skipped_commits": 4648,
  "processed_entries_var1": 0,
  "processed_entries_var2": 0,
  "processed_entries_var3": 0,
  "last_update": "2026-03-13T00:08:13.586"
}
```

## Experiment Variants

### Variant 1: Raw Diff Only
- **Input**: Raw diff from `diff` field
- **Output**: `outputs/raw_diff_output.json`
- **Prompt**: Contains only the code diff
- **Use Case**: Testing how well models can infer changes from diff alone

### Variant 2: XML Content Only
- **Input**: XML files referenced in `xml_path`
- **Output**: `outputs/xml_content_output.json`
- **Prompt**: Contains structured XML representation with diff markers
- **Use Case**: Testing how well models understand structured code representation
- **Note**: Handles multiple XML files per entry automatically

### Variant 3: Combined Diff + XML
- **Input**: Both raw diff AND XML content
- **Output**: `outputs/combined_output.json`
- **Prompt**: Contains both diff and XML information
- **Use Case**: Testing if combined input improves commit message generation

## Models

The system uses 5 Ollama models:
1. `deepseek-coder:33b-instruct` - CodeQwen specialized model
2. `llama3:70b-instruct` - Large instruction-tuned model
3. `codeqwen:7b-chat` - Code-specific chat model
4. `mistral:7b-instruct` - Mistral instruction-tuned model
5. `llama3:8b` - Smaller Llama model for efficiency

## Prompt Template

All variants use the following structure:

```
You are an expert software engineer analyzing code changes 
to generate a high-quality conventional commit message.

## File Information
Language: C++
File: {file_name}

## Detailed Changes
### Modifications
{variant-specific content}

## CRITICAL INSTRUCTIONS
RESPOND WITH ONLY A SINGLE-LINE COMMIT MESSAGE
NO EXPLANATIONS
NO THINKING PROCESS
NO EXTRA TEXT

## Real Examples from Actual C++ Projects
{2 real examples with diffs/XML and commit messages}

## FINAL INSTRUCTION
Output EXACTLY ONE line.
Length must be greater than 5 and less than 20 words.
```

## Output Format

Each output file maintains the original dataset structure with added `response` field:

```json
[
  {
    "commit_id": "...",
    "repo": "...",
    "diff": "...",
    "commit_message": "...",
    "xml_files": [...],
    "response": {
      "deepseek_coder_33b_instruct": "generated message",
      "llama3_70b_instruct": "generated message",
      "codeqwen_7b_chat": "generated message",
      "mistral_7b_instruct": "generated message",
      "llama3_8b": "generated message"
    }
  }
]
```

## Running the Experiment

### Prerequisites

1. **Ollama Running**: Models must be available via Ollama API
   ```bash
   ollama serve
   ```

2. **Dataset**: Place `processed_dataset.json` in the working directory

3. **Python Environment**: Virtual environment with dependencies
   ```bash
   pip install requests
   ```

### Usage

#### Run All Variants
```bash
python commit_generator.py
```

#### Run Specific Variants
```bash
python commit_generator.py --variants variant1 variant2
```

#### Skip Variants
```bash
python commit_generator.py --skip-variant variant3
```

#### Debug Mode (Generate Prompts Without API Calls)
```bash
python commit_generator.py --debug --test-entries 2
```

#### Test With Limited Entries
```bash
python commit_generator.py --test-entries 10
```

### Testing Ollama Connection

```bash
python test_ollama_connection.py
```

This verifies:
- Ollama is running and accessible
- All required models are available
- Lists all installed models

## Directory Structure

After running, the workspace will contain:

```
dataset/
├── commit_generator.py           # Main script
├── test_ollama_connection.py     # Connection tester
├── processed_dataset.json        # Input dataset
├── checkpoints/
│   └── state.json               # Processing state
├── prompts/                     # Saved prompts for inspection
│   ├── variant1/
│   ├── variant2/
│   └── variant3/
├── outputs/                     # Generated outputs
│   ├── raw_diff_output.json
│   ├── xml_content_output.json
│   ├── combined_output.json
│   └── commit_generator.log     # Execution log
└── xml_outputs/                 # Input XML files
    └── Catch2/
```

## Features

### 1. Multi-Model Support
- Calls 5 different models for each entry
- Stores all responses for comparison
- Models run sequentially (can be parallelized)

### 2. Progress Tracking
- Checkpoint system saves progress
- Can resume interrupted experiments
- Tracks processed entries per variant

### 3. Prompt Saving
- All generated prompts saved in `prompts/` directory
- Organized by variant
- Includes commit IDs for traceability
- Useful for debugging and analysis

### 4. Error Handling
- Graceful handling of missing XML files
- Ollama connection validation
- Timeout protection for long-running requests
- Keyboard interrupt support (Ctrl+C) with checkpoint saving

### 5. Logging
- Comprehensive logging to file and console
- Timestamp information for all operations
- Separate logs for debugging

## Extending the System

### Adding More Models
Edit `MODELS` list in script:
```python
MODELS = [
    "deepseek-coder:33b-instruct",
    "llama3:70b-instruct",
    "your_new_model:size",
    # ...
]
```

### Modifying Prompts
Edit `PromptGenerator.PROMPT_TEMPLATE` to adjust:
- System prompt
- Input format
- Examples
- Output constraints

### Different Prompting Strategies
Currently uses single-shot prompting (2 examples). To extend:
1. Zero-shot: Remove examples
2. Few-shot: Add more examples
3. Chain-of-thought: Add reasoning steps

## Performance Considerations

### Model Selection Tips
- **Fastest**: `llama3:8b`, `mistral:7b-instruct`
- **Best Quality**: `deepseek-coder:33b-instruct`, `llama3:70b-instruct`
- **Balanced**: `codeqwen:7b-chat`

### Optimization
- Use `--test-entries N` for quick testing
- Run variants sequentially or in parallel
- Monitor system resources during large runs
- Consider batch processing for very large datasets

## Troubleshooting

### Ollama Connection Failed
```
Error: Cannot connect to Ollama. Make sure Ollama is running on http://localhost:11434
```
**Solution**: Start Ollama service
```bash
ollama serve
```

### Model Not Found
```
Error: Model 'model-name' not available
```
**Solution**: Pull the model first
```bash
ollama pull model-name
```

### XML File Not Found
- Logged as warning, experiment continues
- Check `xml_path` in dataset
- Verify file exists in `xml_outputs/` directory

### Out of Memory
- Use fewer entries: `--test-entries 10`
- Use smaller models: `llama3:8b`
- Reduce concurrent operations

## Experiment Tracking

Each run creates:
1. **Output JSON**: Raw model responses
2. **Prompts JSON**: Exact prompts sent to models
3. **Log File**: Execution timeline and statistics
4. **Checkpoint**: Progress tracking

This enables:
- Reproducibility
- Analysis of prompt engineering
- Model comparison
- Quality assessment

## Future Enhancements

1. **Parallel Model Calls**: Use async/threading for faster execution
2. **Prompt Variations**: Test different system prompts
3. **Few-Shot Optimization**: Dynamically select best examples
4. **Response Evaluation**: Automated quality metrics
5. **Model Fine-tuning**: Create specialized commit message models
6. **Cost Analysis**: Track token usage per variant

## References

- **Ollama**: https://ollama.ai/
- **srcML**: https://www.srcml.org/
- **Conventional Commits**: https://www.conventionalcommits.org/
