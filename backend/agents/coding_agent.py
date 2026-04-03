import os
import subprocess
from pathlib import Path
from anthropic import AsyncAnthropic

# Ensure workspace exists
WORKSPACE_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent-workspace')))
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def is_safe_path(target_path: str) -> bool:
    """Path traversal guard. Returns True if target path resolves strictly within the agent workspace."""
    # Resolve the path relative to the workspace, eliminating any ../../ components
    resolved_path = os.path.abspath(os.path.join(WORKSPACE_DIR, target_path))
    # Confirm it still mathematically falls within the workspace absolute root
    return resolved_path.startswith(os.path.abspath(WORKSPACE_DIR))

async def handle_tool_call(tool_name: str, tool_kwargs: dict):
    # Route tool executions
    if tool_name == "bash_execute":
        command = tool_kwargs.get("command", "")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=WORKSPACE_DIR, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Process failed: {str(e)}"
            
    elif tool_name == "read_file":
        filepath = tool_kwargs.get("filepath", "")
        if not is_safe_path(filepath):
            return "ACCESS DENIED: Path traversal detected. Operations strictly limited to agent-workspace/."
        target = Path(WORKSPACE_DIR) / filepath
        if not target.exists():
            return "Error: File does not exist."
        return target.read_text(encoding="utf-8")
        
    elif tool_name == "write_file":
        filepath = tool_kwargs.get("filepath", "")
        content = tool_kwargs.get("content", "")
        if not is_safe_path(filepath):
            return "ACCESS DENIED: Path traversal detected. Operations strictly limited to agent-workspace/."
        target = Path(WORKSPACE_DIR) / filepath
        # Ensure parent directories exist dynamically
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return "File successfully written."
        
    return "Error: Tool not found."

async def invoke_coding_agent(task_query: str) -> str:
    """Executes the Coding Agent loop via Anthropic API until it yields a final text answer."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "[Error] ANTHROPIC_API_KEY is missing from environment."

    client = AsyncAnthropic(api_key=api_key)
    
    system_prompt = (
        "You are a sandboxed Coding Agent. You have access to bash, read, and write tools. "
        "Your working directory is agent-workspace/. You cannot access files outside this directory. "
        "You must execute the user's instructions and summarize exactly what you changed when finished."
    )
    
    tools = [
        {
            "name": "bash_execute",
            "description": "Execute a shell command within the sandboxed workspace. Do not use interactive commands.",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"]
            }
        },
        {
            "name": "read_file",
            "description": "Read contents of a file within the workspace.",
            "input_schema": {
                "type": "object",
                "properties": {"filepath": {"type": "string"}},
                "required": ["filepath"]
            }
        },
        {
            "name": "write_file",
            "description": "Write or overwrite a file within the workspace.",
            "input_schema": {
                "type": "object",
                "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}},
                "required": ["filepath", "content"]
            }
        }
    ]

    messages = [{"role": "user", "content": task_query}]
    
    print(f"\n[CodingAgent] Booting Anthropic tool execution loop with {len(tools)} tools...")
    
    # Allow multiple loop iterations to handle sequential tool calls (read -> think -> write)
    for iteration in range(10):
        # We handle any potential API timeouts
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tools
            )
        except Exception as api_err:
            return f"[Error] Anthropic API failure: {api_err}"
            
        final_text = ""
        tool_results = []
        
        # Append the assistant's block to maintain state
        messages.append({"role": "assistant", "content": response.content})
        
        for block in response.content:
            if block.type == "text":
                final_text += block.text
            elif block.type == "tool_use":
                print(f"[CodingAgent] Executing tool: {block.name}({block.input})")
                result_str = await handle_tool_call(block.name, block.input)
                # Maximize string output limit if it blasts the console
                if len(result_str) > 10000:
                    result_str = result_str[:10000] + "\n...[TRUNCATED]"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str
                })
                
        if not tool_results:
            # Assistant yielded text without calling more tools = Goal satisfied
            return final_text
            
        # Give context of the tool results back for the next iteration
        messages.append({"role": "user", "content": tool_results})
        
    return "[Error] Coding agent exceeded max tool iterations."
