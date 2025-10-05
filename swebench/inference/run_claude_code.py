#!/usr/bin/env python3

"""
Claude Code integration for SWE-bench inference.
This module provides functionality to run inference using the Claude Code CLI
for enhanced coding capabilities beyond the standard Anthropic API.
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from tqdm.auto import tqdm
from argparse import ArgumentParser
import logging
from typing import Dict, List, Optional, Set
from swebench.inference.make_datasets.utils import extract_diff

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Claude Code model limits and configurations
CLAUDE_CODE_MODELS = {
    "claude-4": 200_000,
    "claude-code": 200_000,
    "claude-3.5-sonnet": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
}

def check_claude_code_availability():
    """Check if Claude Code CLI is installed and available."""
    try:
        # Try to find claude in PATH first
        import shutil
        claude_path = shutil.which("claude")
        if not claude_path:
            # Fallback to common locations
            claude_path = "/home/zqq/.nvm/versions/node/v22.20.0/bin/claude"

        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"Claude Code CLI available: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Claude Code CLI check failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Claude Code CLI not found: {e}")
        return False

def prepare_claude_code_prompt(datum: Dict) -> str:
    """
    Prepare the prompt for Claude Code, optimizing for code generation tasks.

    Based on SWE-bench best practices:
    - Explicit planning increases pass rate by 4%
    - Clear tool descriptions and step-by-step instructions
    - Unified diff format with complete context blocks
    - GPT-4.1 agentic harness achieves 55% on SWE-bench Verified

    Args:
        datum: The dataset instance containing the problem text

    Returns:
        str: Formatted prompt for Claude Code
    """
    # SWE-bench uses "problem_statement" field, not "text"
    base_prompt = datum.get("problem_statement", datum.get("text", ""))

    # Enhanced prompt - concise but effective version
    enhanced_prompt = f"""{base_prompt}

---

**IMPORTANT: Patch Format Requirements**

Generate a patch in unified diff format that follows these CRITICAL rules:

1. **Context lines MUST start with a SPACE** ` ` (not nothing!)
2. Deleted lines start with `-`
3. Added lines start with `+`
4. Include 3+ lines of context before/after changes
5. Show complete code blocks (full functions preferred)

**Correct Format Example:**
```diff
--- a/file.py
+++ b/file.py
@@ -10,7 +10,8 @@
 def function(value):
     # Context line (note the leading space!)
     if value is None:
-        return False
+        return None
+    if not value:
+        return False
     return True
```

**Common Error:** Forgetting the leading space on context lines → malformed patch!

Provide: 1) Brief analysis, 2) Your patch in ```diff``` block.
The patch will be automatically tested - format errors = instant failure."""

    return enhanced_prompt

def call_claude_code(
    prompt: str,
    model_name: str,
    timeout: int = 300,
    max_tokens: int = 8192,
    temperature: float = 0.1,
    **kwargs
) -> Optional[Dict]:
    """
    Call Claude Code CLI with the given prompt and parameters.

    Args:
        prompt: The input prompt
        model_name: Claude model to use
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional arguments

    Returns:
        Dict containing response data or None if failed
    """
    # Build Claude Code command with absolute path
    import shutil
    claude_path = shutil.which("claude")
    if not claude_path:
        claude_path = "/home/zqq/.nvm/versions/node/v22.20.0/bin/claude"

    # Use temporary file for prompt to avoid "Argument list too long" error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prompt_file:
        prompt_file.write(prompt)
        prompt_file_path = prompt_file.name

    try:
        cmd = [
            claude_path,
            "-p", f"@{prompt_file_path}",
            "--output-format", "json",
            "--model", model_name
        ]

        # Note: Claude Code CLI doesn't directly support max_tokens and temperature parameters
        # These may be configured through Claude Code settings or system prompts

        logger.info(f"Calling Claude Code with model: {model_name}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,  # Explicitly close stdin to avoid CLI trying to read from it
            env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")}
        )

        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                logger.info("Claude Code call successful")
                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude Code JSON response: {e}")
                logger.error(f"Raw output: {result.stdout}")
                return None
        else:
            logger.error(f"Claude Code call failed with code {result.returncode}")
            logger.error(f"Error stderr: {result.stderr}")
            logger.error(f"Error stdout: {result.stdout}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"Claude Code call timed out after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Claude Code: {e}")
        return None
    finally:
        # Clean up temporary file
        if os.path.exists(prompt_file_path):
            os.unlink(prompt_file_path)

def claude_code_inference(
    test_dataset,
    model_name_or_path: str,
    output_file: str,
    model_args: Dict,
    existing_ids: Set[str],
    max_cost: Optional[float] = None,
):
    """
    Run inference on a dataset using Claude Code with ENHANCED features.

    Enhanced features:
    - Repo access at base_commit
    - Repo cache for performance
    - Enhanced prompts guiding tool usage
    - 3-layer patch validation
    - Intelligent retry with error feedback

    Args:
        test_dataset: The dataset to run inference on
        model_name_or_path: Claude model name
        output_file: Path to output file
        model_args: Model configuration arguments
        existing_ids: Set of already processed instance IDs
        max_cost: Maximum cost limit (currently not implemented for Claude Code)
    """
    # Check Claude Code availability
    if not check_claude_code_availability():
        raise RuntimeError("Claude Code CLI is not available. Please install it with: npm install -g @anthropic-ai/claude-code")

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

    # Map SWE-bench model names to Claude Code CLI model aliases/names
    model_name_mapping = {
        "claude-3-haiku": "haiku",
        "claude-3-sonnet": "sonnet",
        "claude-3-opus": "opus",
        "claude-3.5-sonnet": "sonnet",
        "claude-code": "sonnet",
        "claude-4": "sonnet",
        "claude-4.5-sonnet": "sonnet",
        "claude-sonnet-4-5": "sonnet",
        "claude-sonnet-4-5-20250929": "sonnet",
    }
    actual_model_name = model_name_mapping.get(model_name_or_path, model_name_or_path)

    # Extract model arguments
    timeout = model_args.pop("timeout", 300)
    # Set max_tokens based on model (Haiku has 4096 limit, others 8192)
    default_max_tokens = 4096 if "haiku" in actual_model_name.lower() else 8192
    max_tokens = model_args.pop("max_tokens", default_max_tokens)
    temperature = model_args.pop("temperature", 0.1)
    max_instances = model_args.pop("max_instances", None)

    # Enhanced features configuration
    use_enhanced = model_args.pop("enhanced", True)  # Default: use enhanced
    use_cache = model_args.pop("use_cache", True)     # Default: use cache
    validate_hunks = model_args.pop("validate_hunks", True)  # Default: validate
    max_retries = model_args.pop("max_retries", 2)    # Default: 2 retries
    cleanup = model_args.pop("cleanup", False)        # Default: keep repos

    logger.info(f"Starting Claude Code inference with model: {model_name_or_path}")
    logger.info(f"Configuration: timeout={timeout}s, max_tokens={max_tokens}, temperature={temperature}")

    # Enhanced features configuration
    if use_enhanced:
        logger.info("🚀 ENHANCED MODE: Using all optimizations")
        logger.info(f"  - Repo access: ✅")
        logger.info(f"  - Repo cache: {'✅' if use_cache else '❌'}")
        logger.info(f"  - Patch validation: {'✅' if validate_hunks else '❌'}")
        logger.info(f"  - Max retries: {max_retries}")

        # Import enhanced modules
        from swebench.inference.repo_manager import RepoManager
        from swebench.inference.enhanced_prompts import prepare_enhanced_claude_code_prompt
        from swebench.inference.patch_validator import validate_patch_format, verify_hunk_line_numbers
        from swebench.inference.retry_handler import prepare_retry_prompt

        # Setup repo manager
        repo_manager = RepoManager(use_cache=use_cache)
        logger.info(f"📁 Repo manager initialized: {repo_manager.base_dir}")
        if use_cache:
            logger.info(f"📦 Cache directory: {repo_manager.cache_dir}")
    else:
        logger.info("⚠️  BASIC MODE: No repo access or validation")
        repo_manager = None

    total_processed = 0
    total_successful = 0

    with open(output_file, "a+") as f:
        for datum in tqdm(test_dataset, desc=f"Claude Code inference ({model_name_or_path})"):
            instance_id = datum["instance_id"]

            # Skip if already processed
            if instance_id in existing_ids:
                continue

            logger.info(f"Processing instance: {instance_id}")

            # Enhanced: Setup repo and change directory
            original_cwd = os.getcwd()
            repo_path = None

            if use_enhanced:
                try:
                    # Setup repo at base_commit
                    repo_path = repo_manager.setup_repo(datum)
                    logger.info(f"  Repo setup at: {repo_path}")

                    # Change to repo directory so Claude Code can access files
                    os.chdir(repo_path)

                    # Prepare enhanced prompt
                    prompt = prepare_enhanced_claude_code_prompt(datum, repo_path)
                except Exception as e:
                    logger.error(f"  Failed to setup repo for {instance_id}: {e}")
                    # Fallback to basic prompt
                    prompt = prepare_claude_code_prompt(datum)
                    os.chdir(original_cwd)
            else:
                # Basic prompt without repo access
                prompt = prepare_claude_code_prompt(datum)

            # Try with retries
            response_data = None
            validation_errors = []

            for attempt in range(max_retries + 1):
                if attempt > 0:
                    logger.info(f"  Retry attempt {attempt}/{max_retries}")
                    # Prepare retry prompt with error feedback
                    if use_enhanced and validation_errors:
                        prompt = prepare_retry_prompt(
                            original_prompt=prompt,
                            error_message="; ".join(validation_errors),
                            attempt=attempt
                        )

                # Call Claude Code with actual model name
                response_data = call_claude_code(
                    prompt=prompt,
                    model_name=actual_model_name,
                    timeout=timeout,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **model_args
                )

                if response_data:
                    # Extract content from Claude Code CLI response
                    full_output = response_data.get("result", "")
                    if not full_output and "content" in response_data:
                        full_output = response_data.get("content", "")

                    model_patch = extract_diff(full_output)

                    # Enhanced: Validate patch
                    validation_errors = []
                    patch_valid = True

                    if use_enhanced and model_patch and (validate_hunks or attempt > 0):
                        # Layer 1: Format validation
                        is_valid, error_msg = validate_patch_format(model_patch)
                        if not is_valid:
                            validation_errors.append(f"Format error: {error_msg}")
                            patch_valid = False
                            logger.warning(f"  Validation failed: {error_msg}")

                        # Layer 2: Line number validation
                        if patch_valid and validate_hunks and repo_path:
                            is_valid, error_msg = verify_hunk_line_numbers(model_patch, repo_path)
                            if not is_valid:
                                validation_errors.append(f"Line number error: {error_msg}")
                                patch_valid = False
                                logger.warning(f"  Line number validation failed: {error_msg}")

                    # If validation passed or no validation, break retry loop
                    if patch_valid or not use_enhanced:
                        logger.info(f"  ✅ Patch validation passed")
                        break
                    elif attempt < max_retries:
                        logger.info(f"  ❌ Patch validation failed, will retry...")
                        continue

            # Restore working directory
            if use_enhanced and repo_path:
                os.chdir(original_cwd)

            # Prepare output
            if response_data:
                usage = response_data.get("usage", {})
                cost = response_data.get("total_cost_usd")
                if cost is None and usage:
                    input_tokens = usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    if "haiku" in actual_model_name.lower():
                        cost = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
                    else:
                        cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000

                output_dict = {
                    "instance_id": instance_id,
                    "model_name_or_path": model_name_or_path,
                    "full_output": full_output if response_data else "",
                    "model_patch": model_patch if response_data else "",
                    "latency_ms": response_data.get("duration_ms", 0),
                    "cost": cost if cost is not None else 0.0,
                    "claude_code_meta": {
                        "enhanced": use_enhanced,
                        "tools_available": use_enhanced,
                        "repo_path": repo_path if use_enhanced else None,
                        "validation_errors": validation_errors if use_enhanced else [],
                        "attempts": attempt + 1 if response_data else 0,
                        "response_data": response_data if response_data else {},
                    }
                }

                print(json.dumps(output_dict), file=f, flush=True)
                total_successful += 1
                logger.info(f"✅ Successfully processed {instance_id}")

            else:
                logger.warning(f"❌ Failed to process {instance_id} - Claude Code call failed")

            # Cleanup repo if requested
            if use_enhanced and cleanup and repo_path:
                repo_manager.cleanup_repo(instance_id)

            total_processed += 1

            # Check if we've reached the maximum number of instances
            if max_instances and total_processed >= max_instances:
                logger.info(f"Reached maximum instances limit: {max_instances}")
                break

    logger.info(f"Claude Code inference completed: {total_successful}/{total_processed} successful")

def parse_claude_code_args(model_args: str) -> Dict:
    """
    Parse Claude Code specific model arguments.

    Args:
        model_args: Comma-separated key=value pairs

    Returns:
        Dict of parsed arguments
    """
    kwargs = {}
    if model_args:
        for arg in model_args.split(","):
            if "=" in arg:
                key, value = arg.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Type conversion
                if value.lower() in {"true", "false"}:
                    kwargs[key] = value.lower() == "true"
                elif value.isdigit():
                    kwargs[key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    kwargs[key] = float(value)
                elif value.lower() == "none":
                    kwargs[key] = None
                else:
                    kwargs[key] = value

    return kwargs

def main():
    """Main entry point for Claude Code inference."""
    parser = ArgumentParser(description="Run SWE-bench inference using Claude Code")
    parser.add_argument("--dataset_name_or_path", required=True, help="Dataset name or path")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--model_name_or_path", required=True,
                       choices=list(CLAUDE_CODE_MODELS.keys()),
                       help="Claude Code model name")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--model_args", help="Model arguments (key=value,key=value)")
    parser.add_argument("--max_cost", type=float, help="Maximum cost (not implemented)")

    args = parser.parse_args()

    # Parse model arguments
    model_args = parse_claude_code_args(args.model_args)

    # Set up output file
    output_file = Path(args.output_dir) / f"claude_code__{args.dataset_name_or_path.split('/')[-1]}__{args.split}.jsonl"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing results
    existing_ids = set()
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    existing_ids.add(data["instance_id"])
                except json.JSONDecodeError:
                    continue

    logger.info(f"Found {len(existing_ids)} existing results")

    # Load dataset
    from datasets import load_dataset, load_from_disk

    if Path(args.dataset_name_or_path).exists():
        dataset = load_from_disk(args.dataset_name_or_path)
    else:
        dataset = load_dataset(args.dataset_name_or_path)

    if args.split not in dataset:
        raise ValueError(f"Split '{args.split}' not found in dataset")

    test_dataset = dataset[args.split]

    # Filter out existing IDs
    if existing_ids:
        test_dataset = test_dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering existing IDs"
        )

    # Run inference
    claude_code_inference(
        test_dataset=test_dataset,
        model_name_or_path=args.model_name_or_path,
        output_file=str(output_file),
        model_args=model_args,
        existing_ids=existing_ids,
        max_cost=args.max_cost
    )

if __name__ == "__main__":
    main()