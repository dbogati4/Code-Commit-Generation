# Command Reference Guide

## Common Commands

### 1. Test Ollama Connection
```bash
python test_ollama_connection.py
```
✅ Verifies Ollama is running  
✅ Lists all available models

---

### 2. Preview Prompts (No API Calls, ~1 second)
```bash
# All variants, 2 test entries
python commit_generator.py --debug --test-entries 2

# Variant 1 only
python commit_generator.py --debug --test-entries 2 --variants variant1

# Variant 2 only (with XML)
python commit_generator.py --debug --test-entries 2 --variants variant2

# Variant 3 only (combined)
python commit_generator.py --debug --test-entries 2 --variants variant3

# All variants with 5 test entries
python commit_generator.py --debug --test-entries 5
```

**Output Folder**: `prompts/variant{1,2,3}/`  
**Time**: ~1 second

---

### 3. Run Real Experiment (With Model Calls)

#### Quick Test (2 entries, ~5 minutes)
```bash
python commit_generator.py --test-entries 2
```

#### Medium Test (10 entries, ~15 minutes)
```bash
python commit_generator.py --test-entries 10
```

#### Full Dataset (69 entries, ~1-2 hours)
```bash
python commit_generator.py
```

**Output Folder**: `outputs/`  
**Contains**:
- `raw_diff_output.json` (variant 1)
- `xml_content_output.json` (variant 2)
- `combined_output.json` (variant 3)

---

### 4. Run Specific Variants Only

#### Variant 1 Only (Raw Diff)
```bash
python commit_generator.py --variants variant1
```

#### Variant 2 Only (XML Content)
```bash
python commit_generator.py --variants variant2
```

#### Variant 3 Only (Combined)
```bash
python commit_generator.py --variants variant3
```

#### Variant 1 + 2
```bash
python commit_generator.py --variants variant1 variant2
```

#### Variant 1 + 3
```bash
python commit_generator.py --variants variant1 variant3
```

---

### 5. Skip Specific Variants

#### Run all except Variant 3
```bash
python commit_generator.py --skip-variant variant3
```

#### Run all except Variant 2
```bash
python commit_generator.py --skip-variant variant2
```

#### Skip multiple variants
```bash
python commit_generator.py --skip-variant variant2 --skip-variant variant3
```

---

### 6. Combined Options

#### Test variant 1 with 5 entries
```bash
python commit_generator.py --test-entries 5 --variants variant1
```

#### Preview variant 2 prompts only
```bash
python commit_generator.py --debug --variants variant2 --test-entries 3
```

#### Run variants 1+2, skip variant 3, with 20 entries
```bash
python commit_generator.py --test-entries 20 --skip-variant variant3
```

#### Debug all variants, show prompts
```bash
python commit_generator.py --debug --test-entries 5 --variants variant1 variant2 variant3
```

---

## Monitoring and Inspection

### Check Current Progress
```bash
# View checkpoint status
type checkpoints\state.json

# View latest log entries
Get-Content commit_generator.log -Tail 20
```

### View Generated Prompts
```bash
# List variant 1 prompts
dir prompts\variant1\

# View specific prompt
type prompts\variant1\entry_0000.json

# View variant 2 prompts (with XML)
type prompts\variant2\entry_0000.json
```

### Check Output Files
```bash
# Check if outputs exist (created after processing)
dir outputs\

# View raw diff variant results
type outputs\raw_diff_output.json | more

# View XML variant results
type outputs\xml_content_output.json | more
```

---

## Analysis Commands

### Compare Responses by Entry
```bash
# Load output and inspect entry 0
$result = Get-Content outputs\raw_diff_output.json | ConvertFrom-Json
$result[0].response | Format-Table

# Compare with original message
"Original: " + $result[0].commit_message
$result[0].response | ForEach-Object { $_.Keys | ForEach-Object { "Model: $_" } }
```

### Count Model Responses
```bash
# Count total responses in output
$data = Get-Content outputs\raw_diff_output.json | ConvertFrom-Json
$data.Count
```

### Extract Model Responses Only
```bash
# Get all model responses
$data = Get-Content outputs\raw_diff_output.json | ConvertFrom-Json
$data | ForEach-Object { $_.response }
```

---

## Troubleshooting Commands

### Verify Ollama Running
```bash
python test_ollama_connection.py
```

✅ If successful: Ollama is running and ready  
❌ If failed: Start Ollama with `ollama serve`

### Check Script Syntax
```bash
python -m py_compile commit_generator.py
```

✅ No output = script is valid  
❌ Error output = syntax problems

### View Full Log
```bash
type commit_generator.log
```

### Clear Previous Results (Advanced)
```bash
# Remove old outputs
rm outputs\*.json

# Remove old prompts
rm prompts\variant*\*.json

# Reset checkpoint (will reprocess all entries)
rm checkpoints\state.json
```

---

## Recommended Workflow

### Day 1: Verify Setup (5 min)
```bash
# 1. Test Ollama
python test_ollama_connection.py

# 2. Preview prompts without API calls
python commit_generator.py --debug --test-entries 2
```

### Day 2: Test End-to-End (15 min)
```bash
# 3. Run small test with variant 1
python commit_generator.py --test-entries 2 --variants variant1

# 4. Inspect results
type outputs\raw_diff_output.json
```

### Day 3: Full Experiment (2 hours)
```bash
# 5. Run full dataset with all variants
python commit_generator.py
```

### Day 4: Analysis
```bash
# 6. Compare results across variants and models
# Review outputs in outputs/ folder
# Analyze prompts in prompts/ folder
```

---

## Performance Tips

### Fastest Setup
```bash
# 1. Test with 1 entry first
python commit_generator.py --test-entries 1 --variants variant1

# Minimal time: ~60-120 seconds
```

### For Development/Testing
```bash
# 2. Use 2-5 test entries
python commit_generator.py --test-entries 5 --variants variant1

# Time: ~5-15 minutes
```

### For Production
```bash
# 3. Run full dataset
python commit_generator.py

# Time: ~1-2 hours for all 69 entries
```

### Fastest Models (for testing)
```bash
# If you want faster iteration, note these are quickest:
# - llama3:8b
# - mistral:7b-instruct
```

---

## One-Liners for Quick Tasks

### Quick test all three variants
```bash
python commit_generator.py --test-entries 1
```

### Generate variant 1 prompts only (inspect before running)
```bash
python commit_generator.py --debug --test-entries 2 --variants variant1
```

### Run variant 1 and 2 (skip expensive variant 3)
```bash
python commit_generator.py --skip-variant variant3 --test-entries 5
```

### Resume processing after interruption
```bash
python commit_generator.py
# Automatically resumes from where it left off
```

### Process with progress tracking
```bash
python commit_generator.py
# Check checkpoints\state.json to see progress
```

---

## Help and Documentation

### Get Script Help
```bash
python commit_generator.py --help
```

### Full Documentation
- Overview: `README.md`
- Quick Reference: `QUICK_START.md`
- Advanced Debugging: `DEBUGGING.md`
- Complete Summary: `SUMMARY.md`
- This File: `COMMANDS.md`

---

## Useful File Paths

### Input Files
```
processed_dataset.json       # Main dataset (69 entries)
checkpoints/state.json       # Progress tracker
xml_outputs/Catch2/**/*.xml  # Input XML files
```

### Output Files
```
outputs/raw_diff_output.json         # Variant 1 results
outputs/xml_content_output.json      # Variant 2 results
outputs/combined_output.json         # Variant 3 results
outputs/commit_generator.log         # Execution log
```

### Prompt Files
```
prompts/variant1/entry_*.json  # Variant 1 prompts
prompts/variant2/entry_*.json  # Variant 2 prompts (with XML)
prompts/variant3/entry_*.json  # Variant 3 prompts (combined)
```

---

## Next Steps

1. **Verify**: `python test_ollama_connection.py`
2. **Preview**: `python commit_generator.py --debug --test-entries 2`
3. **Test**: `python commit_generator.py --test-entries 2`
4. **Analyze**: Check results in `outputs/`
5. **Run Full**: `python commit_generator.py` (when ready)
