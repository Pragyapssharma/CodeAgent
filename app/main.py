import argparse
import json
import os
import sys

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def execute_read_tool(arguments):
    """Execute the Read tool and return the file contents."""
    file_path = arguments.get("file_path")
    if not file_path:
        raise RuntimeError("file_path parameter is missing")

    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        raise RuntimeError(f"File not found: {file_path}")
    except IOError as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")


def execute_write_tool(arguments):
    """Execute the Write tool to write content to a file."""
    file_path = arguments.get("file_path")
    content = arguments.get("content")

    if not file_path:
        raise RuntimeError("file_path parameter is missing")
    if content is None:  # content could be empty string, which is valid
        raise RuntimeError("content parameter is missing")

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write content to file
        with open(file_path, 'w') as file:
            file.write(content)
        return f"Successfully wrote to {file_path}"
    except IOError as e:
        raise RuntimeError(f"Error writing to file {file_path}: {e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # Initialize conversation history with user's message
    messages = [
        {"role": "user", "content": args.p}
    ]

    # Define the Read and Write tool specifications
    tools = [
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
        }
    ]

    # Agent loop
    while True:
        # Send current conversation history to the model
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=tools
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        # Get the assistant's message
        message = chat.choices[0].message

        # Add the assistant's message to conversation history
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": getattr(message, 'tool_calls', None)
        })

        # Check if the assistant wants to use tools
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # Execute each tool call
            for tool_call in message.tool_calls:
                # Check if it's a function call
                if tool_call.type == "function":
                    function_name = tool_call.function.name

                    # Parse the arguments JSON string
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        raise RuntimeError(f"Failed to parse arguments: {tool_call.function.arguments}")

                    # Execute the appropriate tool
                    if function_name.lower() in ["read", "readfile", "read_file"]:
                        result = execute_read_tool(arguments)
                    elif function_name.lower() in ["write", "writefile", "write_file"]:
                        result = execute_write_tool(arguments)
                    else:
                        raise RuntimeError(f"Unsupported function: {function_name}")

                    # Add tool result to conversation history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                else:
                    raise RuntimeError(f"Unsupported tool call type: {tool_call.type}")
        else:
            # No tool calls - we have the final answer!
            if message.content:
                print(message.content, end="")
            else:
                # If there's no content, print empty string
                print("", end="")
            break  # Exit the loop


if __name__ == "__main__":
    main()