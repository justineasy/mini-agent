#!/usr/bin/env python3
"""Runner for mini-agent - paste this into omp eval or run via: omp -p "run run_agent.py with task X" """

import json
import os

MAX_STEPS = 10
ALLOWED_DIR = os.path.abspath(".")

def is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(path)
    return abs_path.startswith(ALLOWED_DIR)

def read_file(path: str) -> str:
    if not is_safe_path(path):
        return f"Error: Cannot read outside allowed directory: {path}"
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 10000:
            return f"Error: File too large ({len(content)} chars). Showing first 1000:\n{content[:1000]}"
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str, ask_user=True) -> str:
    if not is_safe_path(path):
        return f"Error: Cannot write outside allowed directory: {path}"
    if ask_user:
        print(f"⚠️  Agent wants to write to: {path}")
        print(f"   Preview: {content[:100]}{'...' if len(content)>100 else ''}")
        resp = input("   Allow? (y/n): ").strip().lower()
        if resp != 'y':
            return "Error: User denied permission"
    try:
        d = os.path.dirname(path)
        if d: os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

TOOLS = [
    {"name": "read_file", "description": "Read file contents",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write to file", 
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}
]

def run_tool(name, args):
    if name == "read_file": return read_file(args["path"])
    if name == "write_file": return write_file(args["path"], args["content"])
    return f"Unknown tool: {name}"

async def run_agent(task: str):
    if not task.strip():
        print("No task provided.")
        return
    
    messages = [{"role": "user", "content": task}]
    print(f"\n🎯 Task: {task}\n" + "-"*50)
    
    for step in range(1, MAX_STEPS + 1):
        print(f"\n📍 Step {step}/{MAX_STEPS}")
        
        # Use omp's completion via tool helper
        resp = await tool._raw_anthropic(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=messages,
            tools=TOOLS
        )
        
        content = resp.get("content", [])
        has_tool = False
        tool_results = []
        
        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text: print(f"\n💬 {text}")
            elif block.get("type") == "tool_use":
                has_tool = True
                name, inp, tid = block["name"], block["input"], block["id"]
                print(f"\n🔧 {name}: {json.dumps(inp)}")
                result = run_tool(name, inp)
                print(f"   → {result[:200]}")
                tool_results.append({"type": "tool_result", "tool_use_id": tid, "content": result})
        
        if has_tool:
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": tool_results})
        
        if resp.get("stop_reason") == "end_turn" and not has_tool:
            print("\n" + "="*50 + "\n✅ FINAL ANSWER:")
            for b in content:
                if b.get("type") == "text": print(b.get("text", ""))
            return
        
        if not has_tool: break
    
    print(f"\n⚠️ Stopped after {MAX_STEPS} steps")

# Usage: await run_agent("your task here")
