#!/usr/bin/env python3

"""
Loom Agent integration for SWE-bench inference.
This module provides functionality to run inference using Loom Agent API
which is OpenAI-compatible.
"""

import json
import os
import time
import requests
import traceback
from pathlib import Path
from tqdm.auto import tqdm
from argparse import ArgumentParser
import logging
from typing import Dict, List, Optional, Set
from swebench.inference.make_datasets.utils import extract_diff
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Loom Agent model configurations
LOOM_AGENT_MODELS = {
    "loom-agent": 200_000,
    "loom-agent-claude": 200_000,
}

# Cost estimation (adjust based on actual pricing)
LOOM_AGENT_COST_PER_INPUT = {
    "loom-agent": 0.000003,
    "loom-agent-claude": 0.000003,
}

LOOM_AGENT_COST_PER_OUTPUT = {
    "loom-agent": 0.000015,
    "loom-agent-claude": 0.000015,
}


def calc_cost(model_name, input_tokens, output_tokens):
    """Calculate the cost of API call."""
    if model_name not in LOOM_AGENT_COST_PER_INPUT:
        model_name = "loom-agent"

    cost = (
        LOOM_AGENT_COST_PER_INPUT[model_name] * input_tokens
        + LOOM_AGENT_COST_PER_OUTPUT[model_name] * output_tokens
    )
    logger.info(
        f"input_tokens={input_tokens}, output_tokens={output_tokens}, cost={cost:.2f}"
    )
    return cost


@retry(wait=wait_random_exponential(min=30, max=600), stop=stop_after_attempt(3))
def call_loom_agent(
    base_url: str,
    messages: List[Dict],
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.2,
    client: str = "swebench",
    session_id: str = "1",
    workspace_path: str = "/tmp/swebench",
    stream: bool = False,
    timeout: int = 600,
    **kwargs
) -> Optional[Dict]:
    """
    Call Loom Agent API with OpenAI-compatible interface.

    Args:
        base_url: Base URL of the API endpoint
        messages: List of message dictionaries with 'role' and 'content'
        model: Model name to use
        temperature: Sampling temperature
        client: Client identifier for x-loom-client header
        session_id: Session ID for x-loom-sessionid header
        workspace_path: Workspace path for x-loom-workspacepath header
        stream: Whether to use streaming (set to False for simplicity)
        timeout: Request timeout in seconds
        **kwargs: Additional arguments

    Returns:
        Dict containing response data or None if failed
    """
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-loom-client": client,
        "x-loom-sessionid": session_id,
        "x-loom-workspacepath": workspace_path,
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }

    if stream:
        payload["stream_options"] = {}

    try:
        logger.info("=" * 60)
        logger.info(f"📡 Calling Loom Agent API")
        logger.info(f"   URL: {base_url}")
        logger.info(f"   Model: {model}")
        logger.info(f"   Temperature: {temperature}")
        logger.info(f"   Headers: x-loom-client={client}, x-loom-sessionid={session_id}")
        logger.info("=" * 60)

        if stream:
            # Handle streaming response
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            )
            response.raise_for_status()

            full_content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                full_content += content
                        except json.JSONDecodeError:
                            continue

            # Construct response format
            result = {
                "content": full_content,
                "usage": {
                    "prompt_tokens": 0,  # Will be estimated
                    "completion_tokens": 0,  # Will be estimated
                }
            }

            # Rough token estimation
            result["usage"]["prompt_tokens"] = sum(len(m.get("content", "")) // 4 for m in messages)
            result["usage"]["completion_tokens"] = len(full_content) // 4

            return result
        else:
            # Handle non-streaming response
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info("✅ Loom Agent API call successful")
            logger.info(f"   Response model: {result.get('model', 'N/A')}")

            # Extract content from OpenAI-compatible format
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})

                return {
                    "content": content,
                    "usage": usage,
                    "model": result.get("model", model),
                }
            else:
                logger.error(f"Unexpected response format: {result}")
                return None

    except requests.exceptions.Timeout:
        logger.error(f"Loom Agent API call timed out after {timeout} seconds")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Loom Agent API call failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Loom Agent API: {e}")
        traceback.print_exc()
        return None


def loom_agent_inference(
    test_dataset,
    model_name_or_path: str,
    output_file: str,
    model_args: Dict,
    existing_ids: Set[str],
    max_cost: Optional[float] = None,
):
    """
    Run inference on a dataset using Loom Agent API.

    Args:
        test_dataset: The dataset to run inference on
        model_name_or_path: Model name identifier
        output_file: Path to output file
        model_args: Model configuration arguments
        existing_ids: Set of already processed instance IDs
        max_cost: Maximum cost limit
    """
    # Get API configuration from environment or model_args
    base_url = model_args.pop("base_url", os.environ.get(
        "LOOM_AGENT_BASE_URL",
        "http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions"
    ))

    # Get model configuration
    # If your API doesn't require model parameter, you can set it to None or empty string
    actual_model = model_args.pop("model", "claude-sonnet-4-20250514")  # Default backend model
    temperature = model_args.pop("temperature", 0.2)
    client = model_args.pop("client", "swebench")
    session_id = model_args.pop("session_id", "1")
    workspace_path = model_args.pop("workspace_path", "/tmp/swebench")
    stream = model_args.pop("stream", True)  # API requires stream=true
    timeout = model_args.pop("timeout", 600)
    max_instances = model_args.pop("max_instances", None)

    logger.info("=" * 80)
    logger.info("🚀 Starting Loom Agent inference")
    logger.info("=" * 80)
    logger.info(f"📍 API Endpoint: {base_url}")
    logger.info(f"🤖 Backend Model: {actual_model}")
    logger.info(f"⚙️  Configuration: temperature={temperature}, timeout={timeout}s, stream={stream}")
    logger.info(f"👤 Client: {client}, Session: {session_id}, Workspace: {workspace_path}")
    logger.info("=" * 80)

    total_cost = 0
    total_processed = 0
    total_successful = 0

    with open(output_file, "a+") as f:
        for datum in tqdm(test_dataset, desc=f"Loom Agent inference ({model_name_or_path})"):
            instance_id = datum["instance_id"]

            # Skip if already processed
            if instance_id in existing_ids:
                continue

            logger.info(f"Processing instance: {instance_id}")

            # Prepare messages in OpenAI format
            system_message = datum["text"].split("\n", 1)[0] if "\n" in datum["text"] else ""
            user_message = datum["text"].split("\n", 1)[1] if "\n" in datum["text"] else datum["text"]

            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": user_message})

            # Call Loom Agent API
            try:
                response_data = call_loom_agent(
                    base_url=base_url,
                    messages=messages,
                    model=actual_model,
                    temperature=temperature,
                    client=client,
                    session_id=f"{session_id}_{instance_id}",
                    workspace_path=workspace_path,
                    stream=stream,
                    timeout=timeout,
                    **model_args
                )

                if response_data:
                    full_output = response_data.get("content", "")
                    usage = response_data.get("usage", {})

                    # Extract diff/patch
                    model_patch = extract_diff(full_output)

                    # Calculate cost
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    cost = calc_cost(model_name_or_path, input_tokens, output_tokens)
                    total_cost += cost

                    logger.info(f"Total Cost: {total_cost:.2f}")

                    # Prepare output dictionary
                    output_dict = {
                        "instance_id": instance_id,
                        "model_name_or_path": model_name_or_path,
                        "text": datum["text"],
                        "full_output": full_output,
                        "model_patch": model_patch,
                        "cost": cost,
                        "usage": usage,
                    }

                    # Write to output file
                    print(json.dumps(output_dict), file=f, flush=True)
                    total_successful += 1
                    logger.info(f"Successfully processed {instance_id}")

                    # Check max cost
                    if max_cost is not None and total_cost >= max_cost:
                        logger.info(f"Reached max cost {max_cost}, exiting")
                        break
                else:
                    logger.warning(f"Failed to process {instance_id} - API call failed")

            except Exception as e:
                logger.error(f"Error processing {instance_id}: {e}")
                traceback.print_exc()
                continue

            total_processed += 1

            # Check max instances
            if max_instances and total_processed >= max_instances:
                logger.info(f"Reached maximum instances limit: {max_instances}")
                break

    logger.info("=" * 80)
    logger.info(f"✅ Loom Agent inference completed!")
    logger.info(f"   Success rate: {total_successful}/{total_processed} instances")
    logger.info(f"   Total cost: ${total_cost:.2f}")
    logger.info("=" * 80)


def main():
    """Main entry point for Loom Agent inference."""
    parser = ArgumentParser(description="Run SWE-bench inference using Loom Agent API")
    parser.add_argument("--dataset_name_or_path", required=True, help="Dataset name or path")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--model_name_or_path", required=True,
                       choices=list(LOOM_AGENT_MODELS.keys()),
                       help="Model identifier")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--model_args", help="Model arguments (key=value,key=value)")
    parser.add_argument("--max_cost", type=float, help="Maximum cost")
    parser.add_argument("--base_url", help="API base URL")

    args = parser.parse_args()

    # Parse model arguments
    from swebench.inference.run_api import parse_model_args
    model_args = parse_model_args(args.model_args)

    # Override base_url if provided
    if args.base_url:
        model_args["base_url"] = args.base_url

    # Set up output file
    output_file = Path(args.output_dir) / f"loom_agent__{args.dataset_name_or_path.split('/')[-1]}__{args.split}.jsonl"
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
    loom_agent_inference(
        test_dataset=test_dataset,
        model_name_or_path=args.model_name_or_path,
        output_file=str(output_file),
        model_args=model_args,
        existing_ids=existing_ids,
        max_cost=args.max_cost
    )


if __name__ == "__main__":
    main()