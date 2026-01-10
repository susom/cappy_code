# Cappy Code

## What is Cappy Code?
Cappy Code is a PHI-safe agentic code runner (similar to Claude Code) that executes tasks in a controlled, auditable manner. It handles local file operations, shell commands, and more, but maintains guardrails for privacy and compliance.

## Local Setup

1. **Clone or Copy the Repo**
   ```bash
   git clone git@github.com:susom/cappy_code.git
   cd cappy_code
   ```

2. **Install Dependencies**
   ```bash
   pip install -e .
   ```
   This installs Cappy Code in editable mode. It will also install any required Python libraries from requirements.txt.

3. **Set up SecureChatAI Credentials**
   - Copy `.env.example` to `.env`.
   - Open `.env` and set the required environment variables (like `REDCAP_API_URL`, `REDCAP_API_TOKEN`), ensuring you keep these secrets out of source control.
- IMPORTANT: You must also have a REDCap API token issued for the project PID 34345 to use the SecureChatAI features.

4. **Find your Python Bin Directory**
   ```bash
   which cappy
   ```
   If it doesn’t show a path, try `which python3` to find your Python bin directory.

5. **Add to Path**
   For macOS (Zsh):
   ```bash
   echo 'export PATH="/path/to/your/python/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```
   Adjust accordingly for your shell/OS.

6. **Verify Installation**
   ```bash
   cappy chat
   ```
   This command should launch an interactive chat session if everything is configured correctly.


## Project Requirements
- Python 3.10+
- The `patch` command (on Linux/macOS by default)
- `.env` file with valid credentials for SecureChatAI
- `CAPPY.md` in your project directory (for context)
- (Optional) `.cappyignore` to filter out certain files in scanning/search

With these in place, you can run Cappy’s agent with:
```bash
cappy agent "Your task here"
```
or the interactive chat with:
```bash
cappy chat
```

That’s it! Enjoy using Cappy Code for secure agentic automation.

