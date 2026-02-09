import argparse
import json
import os
import sys
import subprocess
from typing import Dict, Any

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def execute_read_tool(arguments: Dict[str, Any]) -> str:
    """Execute the Read tool and return the file contents."""
    file_path = arguments.get("file_path")
    if not file_path:
        raise RuntimeError("file_path parameter is missing")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise RuntimeError(f"File not found: {file_path}")
    except IOError as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")


def execute_write_tool(arguments: Dict[str, Any]) -> str:
    """Execute the Write tool to write content to a file."""
    file_path = arguments.get("file_path")
    content = arguments.get("content")

    if not file_path:
        raise RuntimeError("file_path parameter is missing")
    if content is None:  # content could be empty string, which is valid
        raise RuntimeError("content parameter is missing")

    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"Successfully wrote to {file_path}"
    except IOError as e:
        raise RuntimeError(f"Error writing to file {file_path}: {e}")


def execute_bash_tool(arguments: Dict[str, Any]) -> str:
    """Execute the Bash tool to run a shell command."""
    command = arguments.get("command")
    if not command:
        raise RuntimeError("command parameter is missing")

    try:
        # Execute the command and capture both stdout and stderr
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=".",  # Run in current working directory
            encoding='utf-8'
        )

        # Combine stdout and stderr
        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(result.stderr)

        output = '\n'.join(output_parts).strip()

        # If command failed, include exit code
        if result.returncode != 0:
            if output:
                output = f"Exit code: {result.returncode}\n{output}"
            else:
                output = f"Exit code: {result.returncode}"

        return output

    except Exception as e:
        raise RuntimeError(f"Error executing command '{command}': {e}")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "required": ["file_path", "content"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    }
                }
            }
        }
    }
]


def execute_tool_call(tool_call: Any) -> str:
    """Execute a single tool call and return the result."""
    if tool_call.type != "function":
        raise RuntimeError(f"Unsupported tool call type: {tool_call.type}")

    function_name = tool_call.function.name.lower()

    # Parse the arguments JSON string
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse arguments: {tool_call.function.arguments}")

    # Execute the appropriate tool
    if function_name in ["read", "readfile", "read_file"]:
        return execute_read_tool(arguments)
    elif function_name in ["write", "writefile", "write_file"]:
        return execute_write_tool(arguments)
    elif function_name in ["bash", "shell", "command", "run"]:
        return execute_bash_tool(arguments)
    else:
        raise RuntimeError(f"Unsupported function: {tool_call.function.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM Agent with file and shell operations")
    parser.add_argument("-p", required=True, help="Prompt for the LLM")
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # Initialize conversation history with user's message
    messages = [{"role": "user", "content": args.p}]

    # Agent loop
    while True:
        try:
            # Send current conversation history to the model
            chat = client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                tools=TOOLS
            )

            if not chat.choices or len(chat.choices) == 0:
                raise RuntimeError("No choices in response")

            # Get the assistant's message
            message = chat.choices[0].message

            # Add the assistant's message to conversation history
            assistant_message = {
                "role": "assistant",
                "content": message.content
            }
            if hasattr(message, 'tool_calls') and message.tool_calls:
                assistant_message["tool_calls"] = message.tool_calls
            messages.append(assistant_message)

            # Check if the assistant wants to use tools
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Execute each tool call
                for tool_call in message.tool_calls:
                    result = execute_tool_call(tool_call)

                    # Add tool result to conversation history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                # No tool calls - we have the final answer!
                final_output = message.content if message.content else ""
                print(final_output, end="")
                break  # Exit the loop

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()