# Mini-Agent

A simple AI agent CLI for testing agent harness capabilities. Uses Anthropic Claude via omp's subscription (ReAct-style).

## Features

- ✅ `read_file` / `write_file` tools
- ✅ Permission prompts for writes
- ✅ Path restriction (current directory only)
- ✅ 10-step loop limit
- ✅ Prompt injection resistant
- ✅ Unicode support (emoji, Chinese, etc.)
- ✅ Graceful error handling
## Usage

### Standalone (any system)
```bash
# Install
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-...  # Linux/Mac
set ANTHROPIC_API_KEY=sk-...     # Windows

# Run
python mini_agent_standalone.py "how many lines in notes.txt?"
python mini_agent_standalone.py "make hello.txt that says hi"
python mini_agent_standalone.py "what is 2+2?"
```

### In omp (uses your subscription)
```python
%load mini_agent.py
await run_agent("your task here")
```
## Test Results

| Level | Tests | Status |
|-------|-------|--------|
| 1. Basics | #1-4 | ✅ |
| 2. Narration | #5-7 | ✅ |
| 3. Multi-step | #8-10 | ✅ |
| 4. Errors | #11-16 | ✅ (14-15 need manual) |
| 5. Safety | #17-22 | ✅ (21 needs manual) |

**18/22 tests passing** in automated testing.

## Test Files

- `notes.txt` - 5 fruits for basic tests
- `unicode.txt` - Emoji and Chinese text
- `trap.txt` - Prompt injection test
- `sub/deep.txt` - Nested file with secret code
- `big.txt` - Large file (generate with `python -c "print('line ' * 100000)" > big.txt`)

## License

MIT
