#!/usr/bin/env python3
"""Mini-agent CLI - standalone version using Anthropic API directly."""

import anthropic
import json
import os
import sys

MAX_STEPS = 10
ALLOWED_DIR = os.path.abspath(".")

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
        pass  # Auto-approve in non-interactive mode
    try:
        d = os.path.dirname(path)
        if d: os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to write to"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    }
]

def run_tool(name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(args.get("path", ""))
    elif name == "write_file":
        return write_file(args.get("path", ""), args.get("content", ""))
    return f"Unknown tool: {name}"

def run_agent(task: str):
    if not task.strip():
        print("No task provided. Please provide a task.")
        return
    
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
    messages = [{"role": "user", "content": task}]
    
    print(f"\n🎯 Task: {task}\n" + "-"*50)
    
    for step in range(1, MAX_STEPS + 1):
        print(f"\n📍 Step {step}/{MAX_STEPS}")
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=TOOLS,
                messages=messages
            )
        except anthropic.AuthenticationError:
            print("\n❌ Invalid API key. Set ANTHROPIC_API_KEY environment variable.")
            return
        except anthropic.APIConnectionError:
            print("\n❌ Network error. Check your internet connection.")
            return
        except anthropic.APIError as e:
            print(f"\n❌ API Error: {e}")
            return
        
        content = response.content
        has_tool = False
        tool_results = []
        
        for block in content:
            if block.type == "text" and block.text:
                print(f"\n💬 {block.text[:300]}{'...' if len(block.text)>300 else ''}")
            elif block.type == "tool_use":
                has_tool = True
                print(f"\n🔧 Tool: {block.name}")
                print(f"   Input: {json.dumps(block.input)}")
                result = run_tool(block.name, block.input)
                print(f"   Result: {result[:200]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        
        if has_tool:
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": tool_results})
        
        if response.stop_reason == "end_turn" and not has_tool:
            print("\n" + "="*50)
            print("✅ FINAL ANSWER:")
            for block in content:
                if block.type == "text":
                    print(block.text)
            return
        
        if not has_tool:
            break
    
    print(f"\n⚠️ Stopped after {MAX_STEPS} steps")

def main():
    if len(sys.argv) < 2:
        print("Usage: python mini_agent_standalone.py \"<task>\"")
        print("\nExamples:")
        print('  python mini_agent_standalone.py "how many lines in notes.txt?"')
        print('  python mini_agent_standalone.py "what is 2+2?"')
        print("\nRequires: ANTHROPIC_API_KEY environment variable")
        return
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set")
        print("\nSet it with:")
        print("  Windows: set ANTHROPIC_API_KEY=sk-...")
        print("  Linux/Mac: export ANTHROPIC_API_KEY=sk-...")
        return
    
    try:
        run_agent(sys.argv[1])
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")

if __name__ == "__main__":
    main()
