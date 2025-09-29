#!/usr/bin/env python3

"""
DeepSeek integration for SWE-bench inference.
This module provides functionality to run inference using DeepSeek models via OpenAI-compatible API.
Supports both DeepSeek cloud API and local deployments.
"""

import json
import os
import time
from pathlib import Path
from tqdm.auto import tqdm
from argparse import ArgumentParser
import logging
from typing import Dict, List, Optional, Set
from swebench.inference.make_datasets.utils import extract_diff
import openai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# DeepSeek model configurations
DEEPSEEK_MODELS = {
    # DeepSeek Cloud API models
    "deepseek-chat": 64000,         # Latest chat model (64K context)
    "deepseek-coder": 64000,        # Specialized coding model (64K context)
    "deepseek-reasoner": 64000,     # Reasoning-optimized model
    # DeepSeek V3
    "deepseek-v3": 64000,
    # DeepSeek V2.5
    "deepseek-v2.5": 64000,
    "deepseek-v2.5-0928": 64000,
    # DeepSeek Coder V2
    "deepseek-coder-v2-0724": 128000,
    "deepseek-coder-v2-instruct": 128000,
    # Local model names (if using vLLM/TGI)
    "deepseek-coder-33b-instruct": 16000,
    "deepseek-coder-6.7b-instruct": 16000,
}

# Cost per 1M tokens (approximate, in USD)
# Updated pricing as of 2024
DEEPSEEK_COST_PER_INPUT = {
    "deepseek-chat": 0.14,
    "deepseek-coder": 0.14,
    "deepseek-reasoner": 0.55,  # Input pricing
    "deepseek-v3": 0.27,
    "deepseek-v2.5": 0.14,
    "deepseek-v2.5-0928": 0.14,
    "deepseek-coder-v2-0724": 0.14,
    "deepseek-coder-v2-instruct": 0.14,
    # Free for local deployments
    "deepseek-coder-33b-instruct": 0.0,
    "deepseek-coder-6.7b-instruct": 0.0,
}

DEEPSEEK_COST_PER_OUTPUT = {
    "deepseek-chat": 0.28,
    "deepseek-coder": 0.28,
    "deepseek-reasoner": 2.19,  # Output pricing
    "deepseek-v3": 1.10,
    "deepseek-v2.5": 0.28,
    "deepseek-v2.5-0928": 0.28,
    "deepseek-coder-v2-0724": 0.28,
    "deepseek-coder-v2-instruct": 0.28,
    "deepseek-coder-33b-instruct": 0.0,
    "deepseek-coder-6.7b-instruct": 0.0,
}


def setup_deepseek_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> openai.OpenAI:
    """
    Setup OpenAI client for DeepSeek API.

    Args:
        api_key: DeepSeek API key (default: from DEEPSEEK_API_KEY env)
        base_url: API base URL (default: DeepSeek official endpoint)

    Returns:
        OpenAI client configured for DeepSeek
    """
    # Get API key from environment or parameter
    # DeepSeek can use DashScope API key if hosted on Alibaba Cloud
    if api_key is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY") or \
                  os.environ.get("DASHSCOPE_API_KEY") or \
                  os.environ.get("QWEN_API_KEY")

    if not api_key:
        raise ValueError(
            "DeepSeek API key not found. Please set DEEPSEEK_API_KEY, DASHSCOPE_API_KEY, "
            "or QWEN_API_KEY environment variable, or pass api_key parameter."
        )

    # Default to DashScope (Alibaba Cloud) or DeepSeek official endpoint
    if base_url is None:
        base_url = os.environ.get(
            "DEEPSEEK_API_BASE",
            os.environ.get(
                "DASHSCOPE_API_BASE",
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        )

    logger.info(f"Initializing DeepSeek client with base_url: {base_url}")

    return openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )


def prepare_deepseek_prompt(datum: Dict) -> str:
    """
    Prepare the prompt for DeepSeek models, optimizing for code generation tasks.

    Args:
        datum: The dataset instance containing the problem text

    Returns:
        str: Formatted prompt for DeepSeek
    """
    base_prompt = datum.get("text", "")

    # Add specific instructions for patch generation
    # DeepSeek Coder works well with clear, structured prompts
    enhanced_prompt = f"""{base_prompt}

Please provide a complete patch to fix this issue. Your response should include:
1. A clear explanation of the problem
2. The solution approach
3. A properly formatted diff/patch

Format your patch using standard diff format with proper file paths."""

    return enhanced_prompt


def call_deepseek_api(
    client: openai.OpenAI,
    prompt: str,
    model_name: str,
    timeout: int = 300,
    max_tokens: int = 8000,
    temperature: float = 0.1,
    **kwargs
) -> Optional[Dict]:
    """
    Call DeepSeek API with the given prompt and parameters.

    Args:
        client: OpenAI client configured for DeepSeek
        prompt: The input prompt
        model_name: DeepSeek model to use
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional arguments

    Returns:
        Dict containing response data or None if failed
    """
    start_time = time.time()

    try:
        logger.info(f"Calling DeepSeek API with model: {model_name}")

        # Special handling for deepseek-reasoner which uses different parameters
        if "reasoner" in model_name:
            # DeepSeek Reasoner uses thinking process
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer. Analyze the code issue carefully and generate a precise patch."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                **kwargs
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer. Your task is to analyze code issues and generate precise patches to fix them."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                **kwargs
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract response
        full_output = response.choices[0].message.content

        # For reasoner model, also capture reasoning process if available
        reasoning_content = ""
        if "reasoner" in model_name and hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning_content = response.choices[0].message.reasoning_content

        # Calculate cost
        usage = response.usage
        input_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0
        output_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
        total_tokens = usage.total_tokens if hasattr(usage, 'total_tokens') else (input_tokens + output_tokens)

        # For reasoner, count reasoning tokens separately if available
        prompt_cache_hit_tokens = 0
        prompt_cache_miss_tokens = 0
        if "reasoner" in model_name:
            if hasattr(usage, 'prompt_cache_hit_tokens'):
                prompt_cache_hit_tokens = getattr(usage, 'prompt_cache_hit_tokens', 0)
            if hasattr(usage, 'prompt_cache_miss_tokens'):
                prompt_cache_miss_tokens = getattr(usage, 'prompt_cache_miss_tokens', 0)

        cost_per_input = DEEPSEEK_COST_PER_INPUT.get(model_name, 0.14) / 1_000_000
        cost_per_output = DEEPSEEK_COST_PER_OUTPUT.get(model_name, 0.28) / 1_000_000
        cost = input_tokens * cost_per_input + output_tokens * cost_per_output

        logger.info(f"DeepSeek API call successful (latency: {latency_ms}ms, cost: ${cost:.4f})")

        # Prepare detailed response data
        result = {
            "full_output": full_output,
            "latency_ms": latency_ms,
            "cost": cost,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "prompt_tokens": input_tokens,  # Alias for compatibility
                "completion_tokens": output_tokens,  # Alias for compatibility
                "prompt_cache_hit_tokens": prompt_cache_hit_tokens,
                "prompt_cache_miss_tokens": prompt_cache_miss_tokens
            },
            "model": model_name,
            "finish_reason": response.choices[0].finish_reason,
            "response_id": response.id if hasattr(response, 'id') else None,
            "system_fingerprint": response.system_fingerprint if hasattr(response, 'system_fingerprint') else None,
            "created": response.created if hasattr(response, 'created') else None
        }

        # Add reasoning content for reasoner model
        if reasoning_content:
            result["reasoning_content"] = reasoning_content

        return result

    except openai.APITimeoutError:
        logger.error(f"DeepSeek API call timed out after {timeout} seconds")
        return None
    except openai.APIError as e:
        logger.error(f"DeepSeek API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling DeepSeek API: {e}")
        return None


def deepseek_inference(
    test_dataset,
    model_name_or_path: str,
    output_file: str,
    model_args: Dict,
    existing_ids: Set[str],
    max_cost: Optional[float] = None,
):
    """
    Run inference on a dataset using DeepSeek models.

    Args:
        test_dataset: The dataset to run inference on
        model_name_or_path: DeepSeek model name
        output_file: Path to output file
        model_args: Model configuration arguments
        existing_ids: Set of already processed instance IDs
        max_cost: Maximum cost limit
    """
    # Setup DeepSeek client
    api_key = model_args.pop("api_key", None)
    base_url = model_args.pop("base_url", None)
    client = setup_deepseek_client(api_key, base_url)

    # Extract model arguments
    timeout = model_args.pop("timeout", 300)
    max_tokens = model_args.pop("max_tokens", DEEPSEEK_MODELS.get(model_name_or_path, 8000))
    temperature = model_args.pop("temperature", 0.1)
    max_instances = model_args.pop("max_instances", None)

    logger.info(f"Starting DeepSeek inference with model: {model_name_or_path}")
    logger.info(f"Configuration: timeout={timeout}s, max_tokens={max_tokens}, temperature={temperature}")

    total_processed = 0
    total_successful = 0
    total_cost = 0.0

    with open(output_file, "a+") as f:
        for datum in tqdm(test_dataset, desc=f"DeepSeek inference ({model_name_or_path})"):
            instance_id = datum["instance_id"]

            # Skip if already processed
            if instance_id in existing_ids:
                continue

            # Check cost limit
            if max_cost and total_cost >= max_cost:
                logger.warning(f"Reached maximum cost limit: ${max_cost:.2f}")
                break

            logger.info(f"Processing instance: {instance_id}")

            # Prepare prompt
            prompt = prepare_deepseek_prompt(datum)

            # Call DeepSeek API
            response_data = call_deepseek_api(
                client=client,
                prompt=prompt,
                model_name=model_name_or_path,
                timeout=timeout,
                max_tokens=max_tokens,
                temperature=temperature,
                **model_args
            )

            if response_data:
                full_output = response_data["full_output"]
                model_patch = extract_diff(full_output)
                cost = response_data["cost"]
                total_cost += cost

                # Prepare output dictionary in standard SWE-bench format
                output_dict = {
                    "instance_id": instance_id,
                    "model_name_or_path": model_name_or_path,
                    "full_output": full_output,
                    "model_patch": model_patch,
                    "latency_ms": response_data["latency_ms"],
                    "cost": cost,
                    "deepseek_meta": {
                        "usage": response_data["usage"],
                        "model_info": response_data["model"],
                        "finish_reason": response_data["finish_reason"],
                        "total_cost_accumulated": total_cost,
                        "response_id": response_data.get("response_id"),
                        "system_fingerprint": response_data.get("system_fingerprint"),
                        "created": response_data.get("created"),
                        "provider": "DeepSeek",
                        "api_version": "OpenAI-compatible"
                    }
                }

                # Add reasoning content if available (for reasoner model)
                if "reasoning_content" in response_data:
                    output_dict["deepseek_meta"]["reasoning_content"] = response_data["reasoning_content"]

                # Write to output file
                print(json.dumps(output_dict), file=f, flush=True)
                total_successful += 1
                logger.info(f"Successfully processed {instance_id} (cost: ${cost:.4f}, total: ${total_cost:.4f})")

            else:
                logger.warning(f"Failed to process {instance_id} - DeepSeek API call failed")

            total_processed += 1

            # Check if we've reached the maximum number of instances
            if max_instances and total_processed >= max_instances:
                logger.info(f"Reached maximum instances limit: {max_instances}")
                break

    logger.info(f"DeepSeek inference completed: {total_successful}/{total_processed} successful, total cost: ${total_cost:.4f}")


def parse_deepseek_args(model_args: str) -> Dict:
    """
    Parse DeepSeek specific model arguments.

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
    """Main entry point for DeepSeek inference."""
    parser = ArgumentParser(description="Run SWE-bench inference using DeepSeek models")
    parser.add_argument("--dataset_name_or_path", required=True, help="Dataset name or path")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--model_name_or_path", required=True,
                       help="DeepSeek model name (e.g., deepseek-chat, deepseek-coder, deepseek-reasoner)")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--model_args", help="Model arguments (key=value,key=value)")
    parser.add_argument("--max_cost", type=float, help="Maximum cost in USD")

    args = parser.parse_args()

    # Parse model arguments
    model_args = parse_deepseek_args(args.model_args)

    # Set up output file
    output_file = Path(args.output_dir) / f"{args.model_name_or_path}__{args.dataset_name_or_path.split('/')[-1]}__{args.split}.jsonl"
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
    deepseek_inference(
        test_dataset=test_dataset,
        model_name_or_path=args.model_name_or_path,
        output_file=str(output_file),
        model_args=model_args,
        existing_ids=existing_ids,
        max_cost=args.max_cost
    )


if __name__ == "__main__":
    main()