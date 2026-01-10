'''SecureChatAI client for Cappy Code agentic loop.'''

import os
from typing import Optional
import requests
from dotenv import load_dotenv

from cappy.logger import log_action

# Restoring tiktoken import:
import tiktoken

load_dotenv()

# Default model for agentic code tasks
DEFAULT_MODEL = "o1"

# Model info for computing dynamic max tokens
MODEL_SPECS = {
    'o1': {
        'context': 200000,
        'output_max': 100000,
        'param': 'max_completion_tokens',
        'buffer': 25000
    },
    'gpt-4.1': {
        'context': 1000000,
        'output_max': 128000,
        'param': 'max_tokens',
        'buffer': 2000
    },
    'o3-mini': {
        'context': 200000,
        'output_max': 100000,
        'param': 'max_completion_tokens',
        'buffer': 25000
    },
    'gpt-5': {
        'context': 400000,
        'output_max': 128000,
        'param': 'max_tokens',
        'buffer': 2000
    }
}

def estimate_tokens(text: str, model: str) -> int:
    # tiktoken requires a valid encoding name; we'll pick one that approximates for now.
    # In real usage, we might map to a model-specific encoder.
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def compute_dynamic_max_tokens(model: str, prompt: str) -> (str, int, int):
    spec = MODEL_SPECS.get(model)
    if not spec:
        # fallback to old default (32000)
        return ("max_tokens", 32000, 0)

    prompt_tokens = estimate_tokens(prompt, model)
    available = spec['context'] - prompt_tokens - spec['buffer']
    final = min(available, spec['output_max'])
    if final < 512:
        final = 512  # minimal fallback

    # Absolutely minimal single-line output for final_max_tokens
    # We'll log it as a separate minimal entry with blank lines before/after
    log_action(
        "simple_line",
        {"line": f"\n\nfinal_max_tokens = {final}\n\n"},
        {},
        success=True
    )

    return (spec['param'], final, prompt_tokens)

# Models suitable for agentic loops with JSON schema support
# These models support json_schema parameter for structured output enforcement
AGENTIC_MODELS = [
    "gpt-4.1",       # Strong coding, good default
    "gpt-5",         # Latest OpenAI (schema support TBD)
    "o1",            # Deep reasoning, complex planning
    "o3-mini",       # Reasoning, faster/cheaper
]

# All available models (including non-agentic and non-schema models)
ALL_MODELS = AGENTIC_MODELS + [
    "gpt-4o",        # Fast but no schema support
    "claude",        # Anthropic, no schema support
    "deepseek",      # Strong at code, no schema support
    "llama-Maverick",
    "gemini25pro",
    "gemini20flash",
]

def chat_completion(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 32000,
    system_prompt: Optional[str] = None,
    json_schema: Optional[dict] = None,
    timeout: int = 120,
) -> dict:
    '''
    Send prompt to SecureChatAI via REDCap External Module API.

    Args:
        prompt: The user prompt to send
        model: Model identifier (default: gpt-4.1)
        temperature: Sampling temperature (lower = more deterministic)
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt to prepend
        json_schema: Optional JSON schema for structured output (only for schema-capable models)
        timeout: Request timeout in seconds

    Returns:
        dict with keys:
            - success: bool
            - content: str (the AI response)
            - model: str (model used)
            - error: str (if failed)
    '''
    # Fetch env vars fresh each call (allows runtime updates)
    redcap_api_url = os.getenv("REDCAP_API_URL")
    redcap_api_token = os.getenv("REDCAP_API_TOKEN")

    if not redcap_api_url:
        return {
            "success": False,
            "content": "",
            "error": "Missing REDCAP_API_URL in environment. See .env.example",
        }

    if not redcap_api_token:
        return {
            "success": False,
            "content": "",
            "error": "Missing REDCAP_API_TOKEN in environment. See .env.example",
        }

    resolved_model = model or DEFAULT_MODEL

    # Validate model
    if resolved_model not in ALL_MODELS:
        return {
            "success": False,
            "content": "",
            "error": f"Unknown model: {resolved_model}. Available: {ALL_MODELS}",
        }

    # Build prompt with optional system prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    # Dynamically compute max tokens based on model specs
    param_name, dynamic_max_tokens, prompt_tokens = compute_dynamic_max_tokens(
        resolved_model,
        full_prompt
    )
    # Overwrite the user-provided max_tokens unconditionally or conditionally
    # For simplicity, let's always override
    max_tokens = dynamic_max_tokens

    payload = {
        "token": redcap_api_token,
        "content": "externalModule",
        "prefix": "secure_chat_ai",
        "action": "callAI",
        "format": "json",
        "returnFormat": "json",
        "model": resolved_model,
        "model_hint": resolved_model,
        "temperature": str(temperature)
    }

    # set either 'max_tokens' or 'max_completion_tokens' as needed
    if param_name == "max_completion_tokens":
        payload["max_completion_tokens"] = str(max_tokens)
    else:
        payload["max_tokens"] = str(max_tokens)

    payload["prompt"] = full_prompt

    # Add JSON schema if provided (for schema-capable models)
    if json_schema:
        import json as json_lib
        payload["json_schema"] = json_lib.dumps(json_schema)

    # Log the request (token redacted by logger)
    inputs = {
        "model": resolved_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "prompt_length": len(full_prompt),
        "has_system_prompt": system_prompt is not None,
        "has_json_schema": json_schema is not None,
    }

    try:
        resp = requests.post(redcap_api_url, data=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "success":
            result = {
                "success": False,
                "content": "",
                "model": resolved_model,
                "error": f"API returned error: {data}",
            }
            log_action("ai_chat", inputs, result, success=False)
            return result

        result = {
            "success": True,
            "content": data.get("content", ""),
            "model": resolved_model,
        }
        log_action("ai_chat", inputs, result, success=True)
        return result

    except requests.exceptions.Timeout:
        result = {
            "success": False,
            "content": "",
            "model": resolved_model,
            "error": f"Request timed out after {timeout}s",
        }
        log_action("ai_chat", inputs, result, success=False)
        return result

    except requests.exceptions.RequestException as e:
        result = {
            "success": False,
            "content": "",
            "model": resolved_model,
            "error": f"Request failed: {e}",
        }
        log_action("ai_chat", inputs, result, success=False)
        return result

    except Exception as e:
        result = {
            "success": False,
            "content": "",
            "model": resolved_model,
            "error": f"Unexpected error: {e}",
        }
        log_action("ai_chat", inputs, result, success=False)
        return result

def test_connection(model: Optional[str] = None) -> dict:
    '''
    Test SecureChatAI connection with a simple prompt.

    Returns dict with success status and response or error.
    '''
    return chat_completion(
        prompt="Say 'Connection OK' and nothing else.",
        model=model,
        max_tokens=20,
        temperature=0,
    )
