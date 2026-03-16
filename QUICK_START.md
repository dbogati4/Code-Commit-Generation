# Quick Start Guide

## Setup (One Time)

1. **Ensure Ollama is Running**
   ```bash
   ollama serve
   ```
   Verify all models are available:
   ```bash
   python test_ollama_connection.py
   ```

2. **Dataset is in Place**
   - `processed_dataset.json` ✓
   - `checkpoints/state.json` ✓
   - `xml_outputs/` directory ✓

3. **Python Environment**
   - Virtual environment `.venv/` ✓
   - Packages installed (`requests`) ✓

## Running Experiments

### Option 1: Test with 1 Entry Only
Good for quick testing and debugging:
```bash
python commit_generator.py --test-entries 1
```

### Option 2: Test with 5 Entries
Better representation:
```bash
python commit_generator.py --test-entries 5
```

### Option 3: Run Full Dataset
Process all 69 entries:
```bash
python commit_generator.py
```

### Option 4: Test Single Variant
Just Variant 1 (fastest):
```bash
python commit_generator.py --variants variant1 --test-entries 2
```

### Option 5: Preview Prompts Without API Calls (Debug Mode)
See what prompts will be sent (instant):
```bash
python commit_generator.py --debug --test-entries 2 --variants variant1
```

Then examine the prompts in:
- `prompts/variant1/entry_0000.json`
- `prompts/variant1/entry_0001.json`

## Monitoring Progress

While experiments run:

1. **Watch the Log File**
   ```bash
   # PowerShell
   Get-Content commit_generator.log -Tail 20 -Wait
   ```

2. **Check Checkpoint Status**
   ```bash
   # View current progress
   type checkpoints\state.json
   ```

3. **Monitor Output Directory**
   ```bash
   # Will appear once processing completes
   dir outputs\
   ```

## Understanding the Output

### 1. View Generated Commit Messages
```bash
type outputs\raw_diff_output.json | more
```

### 2. Compare Model Responses
Open `outputs/raw_diff_output.json` in a text editor and look at the `response` field for each entry:
```json
{
  "commit_id": "...",
  "response": {
    "deepseek_coder_33b_instruct": "Generated message 1",
    "llama3_70b_instruct": "Generated message 2",
    "codeqwen_7b_chat": "Generated message 3",
    "mistral_7b_instruct": "Generated message 4",
    "llama3_8b": "Generated message 5"
  }
}
```

### 3. Review Prompts Sent to Models
```bash
dir prompts\variant1\
# Each file contains the exact prompt sent to models:
type prompts\variant1\entry_0000.json
```

## Common Use Cases

### Analyze Variant 1 Results
```bash
python commit_generator.py --variants variant1
```
Output: `outputs/raw_diff_output.json`

### Analyze Variant 2 Results
```bash
python commit_generator.py --variants variant2
```
Output: `outputs/xml_content_output.json`

### Analyze Both Variants
```bash
python commit_generator.py --variants variant1 variant2
```

### Skip a Specific Variant
```bash
python commit_generator.py --skip-variant variant3
```

### Run Only Variant 3
```bash
python commit_generator.py --variants variant3
```

## Expected Timing

Each model takes time to generate a response:
- **Time per entry**: ~60-120 seconds (5 models × 12-24 sec each)
- **For 5 entries**: ~5-10 minutes
- **For 69 entries**: ~1-2 hours (depends on model sizes)

**Tips for faster testing:**
- Use `--test-entries 1` or `2` for quick tests
- Use `--debug` mode to preview prompts instantly
- Fastest models: `llama3:8b`, `mistral:7b-instruct`

## Output Files

After running, check these files:

1. **Experiment Results**
   - `outputs/raw_diff_output.json` - Variant 1 results
   - `outputs/xml_content_output.json` - Variant 2 results
   - `outputs/combined_output.json` - Variant 3 results

2. **Saved Prompts**
   - `prompts/variant1/entry_*.json` - All variant 1 prompts
   - `prompts/variant2/entry_*.json` - All variant 2 prompts
   - `prompts/variant3/entry_*.json` - All variant 3 prompts

3. **Execution Log**
   - `commit_generator.log` - Complete execution timeline
   
4. **Progress Tracking**
   - `checkpoints/state.json` - Processing checkpoint

## Troubleshooting

### Script Won't Start
```
Error: Cannot connect to Ollama
Solution: Start Ollama first: ollama serve
```

### Models Missing
```
Error: Model not found
Solution: Pull the model: ollama pull model-name
```

### Takes Too Long
```
Solution: Use --test-entries with a small number for quick testing
```

### Want to Resume Interrupted Run
```
The checkpoint system saves progress automatically.
Just run the same command again - it will resume from where it stopped.
```

## File Structure After Running

```
dataset/
├── outputs/          # Generated outputs
│   ├── raw_diff_output.json
│   ├── xml_content_output.json
│   └── combined_output.json
├── prompts/          # Saved prompts
│   ├── variant1/
│   ├── variant2/
│   └── variant3/
├── checkpoints/      # Progress tracking
│   └── state.json
├── commit_generator.log  # Execution log
└── README.md         # Full documentation
```

## Next Steps

1. **Run a quick test**
   ```bash
   python commit_generator.py --debug --test-entries 2
   # Takes ~1 second, shows prompts without API calls
   ```

2. **Review generated prompts**
   ```bash
   type prompts\variant1\entry_0000.json
   ```

3. **Run with 1-2 real entries**
   ```bash
   python commit_generator.py --test-entries 2
   # Takes ~3-5 minutes, shows real model responses
   ```

4. **Compare results**
   ```bash
   # Open outputs/raw_diff_output.json to see responses from all 5 models
   ```

5. **Run full dataset** (when ready)
   ```bash
   python commit_generator.py
   # Takes 1-2 hours for all 69 entries
   ```

## Questions?

Refer to:
- `README.md` - Full documentation
- `commit_generator.log` - Execution details
- `prompts/*/entry_*.json` - Exact prompts used
