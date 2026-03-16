# Debugging and Analysis Guide

## Script Architecture

### Main Components

1. **OllamaClient** - Handles communication with Ollama API
   - Connection validation
   - Model API calls
   - Error handling for network failures
   - 10-minute timeout for long-running generations

2. **PromptGenerator** - Creates experiment-specific prompts
   - Variant 1: Raw diff only prompts
   - Variant 2: XML content only prompts
   - Variant 3: Combined diff + XML prompts
   - XML file reading and handling
   - Example extraction from dataset

3. **CheckpointManager** - Tracks processing progress
   - Saves state.json with progress
   - Enables resuming interrupted experiments
   - Tracks entries processed per variant

4. **CommitGenerator** - Main orchestrator
   - Loads dataset
   - Processes each variant
   - Calls all 5 models
   - Saves outputs and prompts
   - Updates checkpoints

## Debug Modes

### 1. Preview Prompts Without API Calls
Fastest way to verify prompt generation:
```bash
python commit_generator.py --debug --test-entries 2 --variants variant1
```

**Output**: `prompts/variant1/entry_*.json` (no API calls)
**Time**: ~1 second
**Use**: Verify prompts look correct before expensive API calls

### 2. Test with 1-2 Real Entries
Good balance of testing and speed:
```bash
python commit_generator.py --test-entries 2
```

**Output**: `outputs/*_output.json` with real model responses
**Time**: ~5-10 minutes
**Use**: Verify entire workflow works end-to-end

### 3. Analyze Saved Prompts

After running, examine the exact prompts sent to models:

```bash
# View a specific variant1 prompt
type prompts\variant1\entry_0000.json

# View all variant1 prompts
dir prompts\variant1\*.json | for-each { type $_ }
```

### 4. Compare Model Responses

Open output file and look at the `response` object:
```bash
type outputs\raw_diff_output.json | more
```

Example differences you might see:
```json
{
  "commit_id": "f7e7fa0983e83b922cb6336ff3a55d33b2873943",
  "response": {
    "deepseek_coder_33b_instruct": "Fix ReusableStringStream to access container under lock",
    "llama3_70b_instruct": "Add std::pair return type to StringStreams::add method",
    "codeqwen_7b_chat": "Refactor ReusableStringStream constructor initialization",
    "mistral_7b_instruct": "Fix concurrency issue in ReusableStringStream pool",
    "llama3_8b": "Change return type for thread-safe stream access"
  }
}
```

## Debugging Specific Issues

### Issue: Prompt Contains "[XML content not found]"

**Problem**: XML file referenced in dataset doesn't exist
**Debug**:
1. Open a prompt file: `type prompts\variant2\entry_0000.json`
2. Look for `"xml_path": "path/to/file.xml"`
3. Check if file exists: `test-path "xml_outputs/..."`

**Solution**:
- Verify XML file paths in processed_dataset.json are correct
- Check that XML files exist in xml_outputs/ directory

### Issue: Model Responses Are Too Short/Long

**Problem**: Generated messages don't meet word count constraint (5-20 words)
**Debug**:
1. Count words in response
2. Compare to original ground truth: `"commit_message": "..."`
3. Check if model respected the constraint

**Solution**:
- Try different prompting strategies
- Adjust constraints in PROMPT_TEMPLATE
- Use models with better instruction-following

### Issue: Script Stops Unexpectedly

**Debug**:
1. Check log file: `tail commit_generator.log -f`
2. Look for error messages
3. Check Ollama connection: `python test_ollama_connection.py`

**Common causes**:
- Ollama crashed: Restart `ollama serve`
- Out of memory: Use smaller models or fewer entries
- Network timeout: Check Ollama response time

### Issue: Very Slow Model Responses

**Benchmark** (expected times per model, per entry):
- `llama3:8b`: ~15 seconds
- `mistral:7b-instruct`: ~20 seconds
- `codeqwen:7b-chat`: ~18 seconds
- `deepseek-coder:33b-instruct`: ~45 seconds
- `llama3:70b-instruct`: ~60 seconds

**If slower**:
- Check system resources: CPU/memory usage
- Run on dedicated GPU if available
- Use smaller models for testing

## Performance Analysis

### Measuring End-to-End Time

1. **Record start time** when launching
2. **Monitor progress**: Check output `dir outputs/`
3. **Calculate per-entry time**:
   - Total time ÷ number of entries ÷ 5 models = average per-model time

### Optimizing Performance

1. **Parallel Model Calls** (future enhancement):
   - Current: Sequential (Model 1, 2, 3, 4, 5 for each entry)
   - Could be: Parallel (all 5 at once)
   - ~5x speedup possible

2. **Batch Processing** (future enhancement):
   - Could reduce prompt processing overhead
   - Batch multiple entries per API call

3. **Model Selection**:
   - Use smaller models for quick testing
   - Use larger models only for final runs

## Analyzing Results

### Quality Metrics

Compare against ground truth:

```python
# Pseudo-code to compare
import json

with open('outputs/raw_diff_output.json') as f:
    results = json.load(f)

for entry in results:
    original = entry['commit_message']
    for model, generated in entry['response'].items():
        # Compare using:
        # 1. String similarity (BLEU, ROUGE)
        # 2. Word count
        # 3. Presence of key terms from original
        # 4. Conventional commit format (type: message)
```

### Variant Comparison

Compare which variant produces best results:
1. Load all 3 output files
2. Compare responses for same commit_id
3. Measure quality metrics per variant
4. Statistical analysis of differences

### Model Comparison

Compare which model performs best:
```python
# For each model across all entries
# Calculate:
# 1. Average quality score
# 2. Consistency (variance)
# 3. Semantic similarity to ground truth
# 4. Response diversity
```

## Logging Details

### Log Levels

All logs go to `commit_generator.log`:

```
INFO  - Major operations (start, complete, transitions)
ERROR - Failures (missing files, API errors)
```

### Log Entries Explained

```
INFO - Running variants: ['variant1']
  → Script started with these variants

INFO - Loaded 2 entries from dataset
  → Dataset successfully read

INFO - Calling model: deepseek-coder:33b-instruct
  → About to call this model

ERROR - Failed to connect to Ollama
  → Ollama is not running or unreachable

INFO - Saved output to outputs/raw_diff_output.json
  → Processing complete, results saved
```

## Checkpoint Management

### Understanding state.json

```json
{
  "scanned_commits": 4717,          // Total commits initially scanned
  "valid_entries": 69,               // Valid entries in dataset
  "skipped_commits": 4648,           // Commits without valid entries
  "processed_entries_var1": 0,       // Entries completed for variant 1
  "processed_entries_var2": 0,       // Entries completed for variant 2
  "processed_entries_var3": 0,       // Entries completed for variant 3
  "last_update": "2026-03-13T..."    // When last updated
}
```

### Resuming After Interrupt

**Automatic Resume**: If script stops and you run it again:
1. Script reads state.json
2. Sees which entries were completed
3. Skips those entries
4. Continues from last checkpoint

**Important**: Only variant entries are tracked separately, so you can resume each variant independently.

## Inspecting a Single Entry

### Get Full Data for Entry

1. Find entry ID from output file
2. Extract from dataset:

```bash
# Using PowerShell and JSON manipulation
$dataset = Get-Content processed_dataset.json | ConvertFrom-Json
$entry = $dataset | Where-Object { $_.commit_id -eq "f7e7fa0983e83b922cb6336ff3a55d33b2873943" }

# View diff
$entry.diff

# View original message
$entry.commit_message

# View model responses
$output = Get-Content outputs/raw_diff_output.json | ConvertFrom-Json
$output_entry = $output | Where-Object { $_.commit_id -eq "..." }
$output_entry.response
```

## Common Analysis Examples

### Example 1: Model Performance Ranking

```bash
# For variant1 results, count how many times each model matches original message
type outputs/raw_diff_output.json | more

# Manually check each response vs original commit_message
# Count matches per model
```

### Example 2: Prompt Effectiveness

```bash
# Compare prompts across variants
# Do longer prompts (variant3) get better results?

# Check word counts in responses
# Group by variant
# Calculate average word count
```

### Example 3: Finding Failures

```bash
# Look for error responses in output
# Search for "[ERROR" or empty responses

# Check corresponding prompt to debug
# Verify XML file exists if variant2 or 3
```

## Remote Debugging

If running on remote machine:

1. **Check log file remotely**:
   ```bash
   scp user@host:dataset/commit_generator.log ./
   type commit_generator.log
   ```

2. **Download output files**:
   ```bash
   scp user@host:dataset/outputs/*.json ./
   ```

3. **Download prompts for analysis**:
   ```bash
   scp -r user@host:dataset/prompts/ ./
   ```

## Next Steps

1. **Run debug mode first**: `--debug --test-entries 2`
2. **Review prompts**: Check `prompts/variant1/entry_0000.json`
3. **Run small test**: `--test-entries 2` to verify end-to-end
4. **Analyze results**: Compare responses with ground truth
5. **Run full dataset**: When confident in setup
6. **Evaluate quality**: Use metrics from "Analyzing Results" section
