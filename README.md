# Claude Code Clone - Python Implementation
A Python implementation of a Claude-like coding assistant with file system and shell access capabilities. This project demonstrates building an LLM-powered agent that can read/write files and execute shell commands through an interactive conversation loop.

## 🚀 Features
* Read Tool: Read and display contents of any file

* Write Tool: Create or modify files with specified content

* Bash Tool: Execute shell commands safely

* Agent Loop: Continuous conversation with the LLM until task completion

* Tool Integration: Automatic tool detection and execution

* OpenRouter API: Compatible with various LLM models


## 📋 Prerequisites
* Python 3.7+

* OpenRouter API key

* pip package manager

## 🔧 Installation
1. Clone the repository:
```sh
git clone https://github.com/yourusername/claude-code-python.git
cd claude-code-python
```

2. Install dependencies:
```sh
pip install openai
```

3. Set up environment variable:
```sh
export OPENROUTER_API_KEY="your-api-key-here"
```

## 🎮 Usage
Run the assistant with a prompt:
```sh
./your_program.sh -p "Read README.md and summarize it"
```
Or directly with Python:
```sh
python claude_code.py -p "Delete README_old.md and create a new file"
```

## Example Interactions

### Read a file:
```sh
./your_program.sh -p "What's in main.py?"
```

### Write a file:
```sh
./your_program.sh -p "Create hello.py with print('Hello World')"
```

### Execute shell command:
```sh
./your_program.sh -p "List files in current directory"
```

### Complex task:
```sh
./your_program.sh -p "Check if config.json exists, if not create it with default settings"
```


## 🛠️ How It Works
### Agent Loop Architecture
1. Initialization: User prompt starts the conversation

2. Tool Advertisement: LLM sees available tools (Read, Write, Bash)

3. Tool Execution: When LLM requests a tool, it's executed locally

4. Result Feedback: Tool outputs are sent back to the LLM

5. Completion: Loop continues until LLM provides final answer

### Tool Specifications
* Read: {"file_path": "string"}

* Write: {"file_path": "string", "content": "string"}

* Bash: {"command": "string"}

## 🔒 Security Considerations
> ⚠️ Warning: This tool executes shell commands and file operations. Use with caution:

* The Bash tool runs commands in your current directory

* Files can be overwritten or deleted

* Only use with trusted LLM providers

* Consider running in a sandboxed environment

## 🧪 Testing
The project includes comprehensive tests for:

* File reading/writing operations

* Shell command execution

* Multi-step agent conversations

* Error handling

Run tests:
```sh
codecrafters submit
```

## 🌟 Extensions & Future Work
Potential enhancements:

* Session Persistence: Save/load conversation history

* Multi-Model Support: Switch between different LLMs

* Web Search: Add internet access capabilities

* GUI Interface: Build a visual interface

* Plugin System: Allow custom tool development

## 🙏 Acknowledgements
- Built for CodeCrafters.io "Build Your Own Claude Code" challenge

- Uses OpenRouter API for LLM access

- Inspired by Anthropic's Claude Code implementation
