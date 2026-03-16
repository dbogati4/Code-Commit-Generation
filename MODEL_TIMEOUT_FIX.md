# Model Timeout Troubleshooting

## Issue: Models Timing Out / Slow Responses

### Symptoms
- Log shows: `Read timed out. (read timeout=600)`
- Or: `Read timed out. (read timeout=300)`
- Script hangs for 5-10 minutes per model
- No output generated

### Root Cause
The larger models (`deepseek-coder:33b-instruct`, `llama3:70b-instruct`) require significant:
- GPU memory (24GB+ VRAM)
- Computation time (5-10 minutes per inference)
- Complex prompt processing

## Solutions (Try in Order)

### ✅ Solution 1: Use FAST Models ONLY (Recommended for Testing)
Edit `MODELS` list in `commit_generator.py`:

```python
MODELS = [
    "llama3:8b",              # ~15 seconds per response
    "mistral:7b-instruct",    # ~20 seconds per response
]
```

Then run:
```bash
python commit_generator.py --test-entries 1
```

**Time**: ~1-2 minutes total (vs 20+ minutes with large models)

### ✅ Solution 2: Use FASTER Model Order
Models are now ordered fastest-first by default:
```python
MODELS = [
    "llama3:8b",                    # FASTEST ⚡
    "mistral:7b-instruct",          # FAST
    "codeqwen:7b-chat",             # MEDIUM
    "deepseek-coder:33b-instruct",  # SLOW (33B)
    "llama3:70b-instruct"           # SLOWEST (70B)
]
```

Just run normally:
```bash
python commit_generator.py --test-entries 1
```

### ✅ Solution 3: Increase Timeout (If You Want Large Models)
If you have 24GB+ GPU and want to use large models:

Edit in `commit_generator.py`:
```python
def __init__(self, base_url: str = OLLAMA_BASE_URL):
    self.base_url = base_url
    self.timeout = 1200  # 20 minutes (was 300)
```

### ✅ Solution 4: Test with Just the Smallest Model
```bash
python commit_generator.py --debug --test-entries 1
# Then run with just llama3:8b to test inference
```

## Model Speed Comparison

| Model | Speed | Memory | Good For |
|-------|-------|--------|----------|
| llama3:8b | ⚡⚡⚡⚡⚡ ~15s | 8GB | Testing ✅ |
| mistral:7b | ⚡⚡⚡⚡ ~20s | 8GB | Testing ✅ |
| codeqwen:7b | ⚡⚡⚡⚡ ~18s | 8GB | Testing ✅ |
| deepseek:33b | ⚡⚡ ~2-3min | 24GB | Production |
| llama3:70b | ⚡ ~5-10min | 40GB | Production |

## Recommended Approach

### Phase 1: Testing & Development
Use ONLY fast 7B models:
```bash
python commit_generator.py --test-entries 5
# Total time: ~5-10 minutes
```

### Phase 2: Quality Runs
Add medium models:
```bash
# Edit MODELS to include fast + codeqwen
python commit_generator.py --test-entries 5
# Total time: ~15-20 minutes
```

### Phase 3: Full Production
Use all models (if 24GB+ GPU):
```bash
# With 20 minute timeout, edit MODELS to include all
python commit_generator.py
# Total time: 1-3 hours for 69 entries
```

## Current Status

**Default behavior (RECOMMENDED)**:
- Timeout: 300 seconds (5 minutes)
- Model order: Fast to slow
- Best for: Quick testing with good quality
- Expected time: ~1-2 minutes per entry

---

## If Script is Still Running...

Check if the script is still processing:
```bash
# View live log
Get-Content commit_generator.log -Tail 10 -Wait

# Check checkpoint progress
type checkpoints\state.json
```

If it's still running, you can:
1. **Let it finish** (depends on which models are running)
2. **Interrupt it**: Press Ctrl+C (saves progress)
3. **Run again**: Will resume from last checkpoint

## Quick Fix: Run Fastest Model Only
To get results in ~1 minute:

```bash
# Edit commit_generator.py MODELS to:
MODELS = ["llama3:8b"]

# Run it:
python commit_generator.py --test-entries 1
```

This will:
- Complete in ~30-60 seconds
- Generate 1 successful output file
- Prove the system works
- You can then add more models

---

## For Production Use

If you have a good GPU (24GB+ VRAM):
- Keep all models in the list
- Increase timeout to 1200 seconds (20 min)
- Run overnight or during idle time
- Full results in 1-3 hours

If you have limited GPU memory:
- Use only the 7B models (~8GB each)
- Run parallelized if possible
- Get results in 10-20 minutes per entry

---

See `QUICK_START.md` for more commands.
