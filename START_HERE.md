# Commit Message Generation System - START HERE

## Welcome! 👋

You now have a complete, tested system for generating commit messages using Ollama language models.

**Status**: ✅ Production Ready

---

## What You Have

### 🔧 Core Components
- **commit_generator.py** - Main experiment script (480+ lines)
- **test_ollama_connection.py** - Connection verification utility
- **processed_dataset.json** - 69 commit entries with diffs and XML
- **checkpoints/state.json** - Progress tracking system

### 📚 Documentation (Choose Your Learning Style)

| Document | Purpose | Read If... |
|----------|---------|-----------|
| **START_HERE.md** | This file - Overview & quick links | First time here |
| **QUICK_START.md** | Fast commands & examples | Want to run code now |
| **COMMANDS.md** | Command reference & oneliners | Need specific commands |
| **README.md** | Complete technical documentation | Want full details |
| **DEBUGGING.md** | Troubleshooting & analysis guide | Something goes wrong |
| **SUMMARY.md** | Project summary & status | Want full context |

### 📁 Generated Folders
- **prompts/** - Saved prompts for inspection (40 files after debug mode)
- **outputs/** - Generated model responses (created after running)
- **checkpoints/** - Processing state tracking

---

## Getting Started (3 Steps)

### Step 1: Verify Setup (30 seconds)
```bash
python test_ollama_connection.py
```

**Expected Output:**
```
✓ Successfully connected to Ollama!
Available models (15):
  - llama3:8b
  - llama3:70b-instruct
  - deepseek-coder:33b-instruct
  - codeqwen:7b-chat
  - mistral:7b-instruct
  - [... others ...]
```

✅ If you see this → **Go to Step 2**  
❌ If connection fails → Start Ollama: `ollama serve`

---

### Step 2: Preview Prompts (1 second)
See what the system will do without using the API:
```bash
python commit_generator.py --debug --test-entries 2
```

**What This Does:**
- Loads 2 test entries
- Generates prompts for all 3 variants
- Saves prompts to `prompts/variant{1,2,3}/`
- Does NOT call any Ollama models (instant)

**Output**: Check `prompts/variant1/entry_0000.json` to see the exact prompt

---

### Step 3: Run Real Experiment (5-10 minutes)
```bash
python commit_generator.py --test-entries 2
```

**What This Does:**
- Processes 2 entries
- Calls all 5 models (deepseek, llama3:70b, codeqwen, mistral, llama3:8b)
- Saves responses to `outputs/raw_diff_output.json`, etc.
- Creates 3 experiment output files

**Output**: Check `outputs/raw_diff_output.json` to see model responses

---

## Quick Command Reference

Pick what you want to do:

### "I want to test quickly"
```bash
python commit_generator.py --test-entries 1 --variants variant1
# Time: ~1-2 minutes
```

### "I want to see the prompts first"
```bash
python commit_generator.py --debug --test-entries 2
# Time: ~1 second (no API calls)
```

### "I want to run all variants"
```bash
python commit_generator.py
# Time: ~1-2 hours (full 69 entries)
```

### "I want just variant 1 and 2"
```bash
python commit_generator.py --variants variant1 variant2 --test-entries 5
# Time: ~5-10 minutes
```

**👉 See `COMMANDS.md` for 50+ command examples**

---

## The Three Experiment Variants

### Variant 1: Raw Diff Only
Generates commit messages from code diffs  
**Output**: `outputs/raw_diff_output.json`  
**Speed**: Fastest

### Variant 2: XML Content Only
Generates from structured code representation  
**Output**: `outputs/xml_content_output.json`  
**Handles**: Multiple XML files per commit

### Variant 3: Combined Diff + XML
Generates from both diff and XML together  
**Output**: `outputs/combined_output.json`  
**Complexity**: Most information provided

---

## The Five Models

1. 🏆 **deepseek-coder:33b-instruct** - Best for code (slower)
2. 💪 **llama3:70b-instruct** - Largest, comprehensive (slowest)
3. ⚡ **codeqwen:7b-chat** - Code-optimized, medium speed
4. 🎯 **mistral:7b-instruct** - Balanced performance
5. 🚀 **llama3:8b** - Fastest, lightweight

**Each model generates a commitment for each entry**

---

## What Happens When You Run

### 1. Script Starts
- Connects to Ollama
- Loads 69 dataset entries
- Starts processing

### 2. For Each Entry
- Generates prompt (variant-specific)
- Calls 5 models sequentially
- Stores 5 responses
- Saves prompt for inspection
- Updates progress checkpoint

### 3. When Complete
- Saves `outputs/raw_diff_output.json` (etc.)
- Creates `commit_generator.log`
- Updates `checkpoints/state.json`

### Output File Example
```json
{
  "commit_id": "f7e7fa0983e83b922cb6336ff3a55d33b2873943",
  "commit_message": "Fix ReusableStringStream to access the container under the lock (#3031)",
  "response": {
    "deepseek_coder_33b_instruct": "generated message 1",
    "llama3_70b_instruct": "generated message 2",
    "codeqwen_7b_chat": "generated message 3",
    "mistral_7b_instruct": "generated message 4",
    "llama3_8b": "generated message 5"
  }
}
```

---

## Expected Timeline

| Task | Time |
|------|------|
| Test Ollama connection | 30 seconds |
| Preview prompts (2 entries) | 1 second |
| Real test run (2 entries) | 5-10 minutes |
| Test run (5 entries) | 15 minutes |
| Test run (10 entries) | 25 minutes |
| Full dataset (69 entries) | 1-2 hours |

**Faster Testing**:
- Use `--test-entries 1` or `2` for quick feedback
- Debug mode is instant (no API calls)
- Can interrupt anytime (saves progress)

---

## Key Features

✅ **Three Experiment Variants** - Raw diff, XML, Combined  
✅ **Five Models** - Deepseek, Llama3:70b, CodeQwen, Mistral, Llama3:8b  
✅ **Progress Tracking** - Resume after interruption  
✅ **Prompt Saving** - Inspect what's sent to models  
✅ **Multi-File XML** - Handles multiple XMLs per commit  
✅ **Error Handling** - Graceful for missing files  
✅ **Comprehensive Logging** - Track everything  
✅ **Test Mode** - Run with limited entries  
✅ **Debug Mode** - Generate prompts without API calls  

---

## First-Time Recommended Steps

1. ✅ **Read**: This file (you're doing it!)
2. ✅ **Run**: `python test_ollama_connection.py`
3. ✅ **Preview**: `python commit_generator.py --debug --test-entries 2`
4. ✅ **Test**: `python commit_generator.py --test-entries 2`
5. ✅ **Analyze**: Open `outputs/raw_diff_output.json`
6. ✅ **Run Full**: `python commit_generator.py` (when ready)

---

## Documentation Quick Links

**Start Here** (you are here)  
↓  
**Next**: [QUICK_START.md](QUICK_START.md) - Fast commands  
**Then**: [README.md](README.md) - Full documentation  
**Ref**: [COMMANDS.md](COMMANDS.md) - All commands  
**Help**: [DEBUGGING.md](DEBUGGING.md) - Troubleshooting  
**Summary**: [SUMMARY.md](SUMMARY.md) - Project status  

---

## Common Questions

### Q: How long does it take?
**A**: 
- Testing script: ~1 second
- Testing with models: 5-10 minutes  
- Full dataset: 1-2 hours

### Q: What if Ollama crashes?
**A**: Just run the script again. It will resume from where it stopped.

### Q: Can I run just one variant?
**A**: Yes! `python commit_generator.py --variants variant1`

### Q: Where are the results?
**A**: In `outputs/` folder as JSON files with model responses.

### Q: Can I see what prompts are sent?
**A**: Yes! They're saved in `prompts/variant1/`, etc.

### Q: Something went wrong, what do I check?
**A**: See `DEBUGGING.md` for troubleshooting guide.

---

## System Requirements Checklist

- ✅ Ollama running locally (`ollama serve`)
- ✅ All 5 required models available (check with test script)
- ✅ Python 3.11 with requests library (already installed)
- ✅ ~500MB disk space for outputs/prompts
- ✅ Stable system (Ctrl+C safe, checkpointing works)

---

## Next Action

**Choose one and run it:**

### To Test Everything Fast (1 second)
```bash
python commit_generator.py --debug --test-entries 2
```

### To Test With Real Models (5-10 minutes)
```bash
python commit_generator.py --test-entries 2
```

### To Run Full Experiment (1-2 hours)
```bash
python commit_generator.py
```

---

## Files in This Directory

```
commit_generator.py          ← Main script (RUN THIS)
test_ollama_connection.py    ← Connection tester
processed_dataset.json       ← Input data
README.md                    ← Full documentation
QUICK_START.md               ← Fast reference
COMMANDS.md                  ← Command examples
DEBUGGING.md                 ← Troubleshooting
SUMMARY.md                   ← Project summary
START_HERE.md                ← This file

[After running, created automatically:]
outputs/                     ← Results here
prompts/                     ← Saved prompts here
checkpoints/state.json       ← Progress tracking
commit_generator.log         ← Execution log
```

---

## Support Resources

| Issue | Solution |
|-------|----------|
| Ollama won't connect | Run `ollama serve` in another terminal |
| Models not found | Run `python test_ollama_connection.py` to list models |
| Script won't run | Check Python environment: `python --version` |
| Something failed | Check `commit_generator.log` for details |
| Need help | See `DEBUGGING.md` for troubleshooting |

---

**You're all set! Pick a command above and get started.** 🚀

Questions? Check the documentation files - they have detailed answers.

---

*Last Updated: March 13, 2026*  
*Status: ✅ Production Ready*  
*Tested: Ollama connection verified, all models available*
