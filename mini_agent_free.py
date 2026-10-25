#!/usr/bin/env python3
"""Mini-agent CLI - FREE version using Ollama (local, no API key)."""

import json
import os
import re
import sys
import urllib.request
import urllib.error

MAX_STEPS = 10
ALLOWED_DIR = os.path.abspath(".")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"  # or "mistral", "phi3", "gemma2"

SYSTEM = """You are a helpful assistant with access to tools. For each step:
1. Think about what to do
2. If you need to use a tool, output EXACTLY this format:
   TOOL: tool_name
   INPUT: {"param": "value"}
3. Wait for the result, then continue
4. When done, output: FINAL: your answer

Available tools:
- read_file: Read a file. INPUT: {"path": "filename"}
- write_file: Write to a file. INPUT: {"path": "filename", "content": "text"}

IMPORTANT: Output ONLY ONE tool call at a time. Wait for results before the next action."""

def is_safe_path(path: str) -> bool:
    return os.path.abspath(path).startswith(ALLOWED_DIR)

def read_file(path: str) -> str:
    if not is_safe_path(path):
        return "Error: Path outside allowed directory"
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 10000:
            return f"File too large ({len(content)} chars). First 1000:\n{content[:1000]}"
        return content
    except Exception as e:
        return f"Error: {e}"

def write_file(path: str, content: str) -> str:
    if not is_safe_path(path):
        return "Error: Path outside allowed directory"
    print(f"\n⚠️  Write request: {path}")
    print(f"   Content: {content[:100]}{'...' if len(content)>100 else ''}")
    try:
        resp = input("   Allow? (y/n): ").strip().lower()
        if resp != 'y':
            return "Error: User denied permission"
    except EOFError:
        pass
    try:
        d = os.path.dirname(path)
        if d: os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

def run_tool(name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(args.get("path", ""))
    elif name == "write_file":
        return write_file(args.get("path", ""), args.get("content", ""))
    return f"Unknown tool: {name}"

def parse_tool_call(text: str):
    tool_match = re.search(r'TOOL:\s*(\w+)', text)
    input_match = re.search(r'INPUT:\s*(\{[^}]+\})', text, re.DOTALL)
    if tool_match and input_match:
        try:
            return tool_match.group(1), json.loads(input_match.group(1))
        except json.JSONDecodeError:
            pass
    return None, None

def parse_final(text: str):
    match = re.search(r'FINAL:\s*(.+)', text, re.DOTALL)
    return match.group(1).strip() if match else None

def call_ollama(prompt: str) -> str:
    data = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }).encode()
    
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot connect to Ollama: {e}")

def run_agent(task: str):
    if not task.strip():
        print("No task provided.")
        return
    
    history = f"Task: {task}"
    print(f"\n🎯 Task: {task}\n" + "-"*50)
    
    for step in range(1, MAX_STEPS + 1):
        print(f"\n📍 Step {step}/{MAX_STEPS}")
        
        prompt = f"{SYSTEM}\n\n{history}\n\nYour response:"
        
        try:
            response = call_ollama(prompt)
        except ConnectionError as e:
            print(f"\n❌ {e}")
            print("\nMake sure Ollama is running: ollama serve")
            return
        
        print(f"\n💬 {response[:300]}{'...' if len(response)>300 else ''}")
        
        final = parse_final(response)
        if final:
            print("\n" + "="*50)
            print("✅ FINAL ANSWER:", final)
            return
        
        tool_name, tool_input = parse_tool_call(response)
        if tool_name:
            print(f"\n🔧 Tool: {tool_name}")
            print(f"   Input: {json.dumps(tool_input)}")
            result = run_tool(tool_name, tool_input)
            print(f"   Result: {result[:200]}")
            history += f"\n\nAssistant: {response}\n\nTool Result: {result}"
        else:
            history += f"\n\nAssistant: {response}"
            if "FINAL" not in response.upper():
                history += "\n\nPlease either use a tool or provide FINAL: answer"
    
    print(f"\n⚠️ Stopped after {MAX_STEPS} steps")

def main():
    if len(sys.argv) < 2:
        print("Usage: python mini_agent_free.py \"<task>\"")
        print("\nRequires Ollama running locally:")
        print("  1. Install: https://ollama.com")
        print("  2. Run: ollama pull llama3.2")
        print("  3. Start: ollama serve")
        print(f"\nUsing model: {MODEL}")
        return
    
    try:
        run_agent(sys.argv[1])
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted")

if __name__ == "__main__":
    main()
