#!/usr/bin/env python3
"""
Retry logic for handling malformed patches in SWE-bench inference
"""
from typing import Callable, Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class PatchRetryHandler:
    """Handle retrying patch generation when validation fails."""

    def __init__(
        self,
        max_retries: int = 2,
        validation_func: Optional[Callable] = None,
        delay_seconds: float = 1.0
    ):
        """
        Args:
            max_retries: Maximum number of retry attempts
            validation_func: Function to validate patch (should return (bool, str))
            delay_seconds: Delay between retries
        """
        self.max_retries = max_retries
        self.validation_func = validation_func
        self.delay_seconds = delay_seconds

    def generate_with_retry(
        self,
        generate_func: Callable,
        instance_id: str,
        **generate_kwargs
    ) -> Dict[str, Any]:
        """
        Generate patch with retry logic.

        Args:
            generate_func: Function that generates patch (returns dict with 'model_patch')
            instance_id: Instance identifier
            **generate_kwargs: Additional arguments for generate_func

        Returns:
            Dict with patch result and retry metadata
        """
        result = {
            'instance_id': instance_id,
            'model_patch': '',
            'full_output': '',
            'attempts': 0,
            'validation_errors': [],
            'retry_history': []
        }

        for attempt in range(self.max_retries + 1):
            result['attempts'] = attempt + 1

            # Add retry-specific instructions to prompt
            if attempt > 0:
                retry_msg = self._create_retry_message(
                    attempt,
                    result['validation_errors'][-1] if result['validation_errors'] else None
                )
                if 'prompt' in generate_kwargs:
                    generate_kwargs['prompt'] = f"{generate_kwargs['prompt']}\n\n{retry_msg}"

            # Generate patch
            logger.info(f"{instance_id}: Attempt {attempt + 1}/{self.max_retries + 1}")

            try:
                gen_result = generate_func(**generate_kwargs)

                # Extract patch
                model_patch = gen_result.get('model_patch', '')
                full_output = gen_result.get('full_output', gen_result.get('result', ''))

                result['model_patch'] = model_patch
                result['full_output'] = full_output
                result['retry_history'].append({
                    'attempt': attempt + 1,
                    'patch_size': len(model_patch),
                    'success': bool(model_patch)
                })

                # Validate if validation function provided
                if self.validation_func and model_patch:
                    is_valid, error_msg = self.validation_func(model_patch)

                    if is_valid:
                        logger.info(f"{instance_id}: Patch validated successfully")
                        result['validation_status'] = 'valid'
                        return result
                    else:
                        logger.warning(f"{instance_id}: Validation failed: {error_msg}")
                        result['validation_errors'].append(error_msg)
                        result['retry_history'][-1]['validation_error'] = error_msg

                        # If not last attempt, retry
                        if attempt < self.max_retries:
                            logger.info(f"{instance_id}: Retrying due to validation failure...")
                            time.sleep(self.delay_seconds)
                            continue
                        else:
                            result['validation_status'] = 'invalid'
                            return result
                elif model_patch:
                    # No validation, just return
                    result['validation_status'] = 'not_validated'
                    return result
                else:
                    # Empty patch
                    result['validation_errors'].append('Empty patch generated')
                    result['retry_history'][-1]['error'] = 'empty_patch'

                    if attempt < self.max_retries:
                        logger.info(f"{instance_id}: Retrying due to empty patch...")
                        time.sleep(self.delay_seconds)
                        continue

            except Exception as e:
                logger.error(f"{instance_id}: Generation error: {e}")
                result['validation_errors'].append(str(e))
                result['retry_history'].append({
                    'attempt': attempt + 1,
                    'error': str(e)
                })

                if attempt < self.max_retries:
                    time.sleep(self.delay_seconds)
                    continue

        result['validation_status'] = 'failed'
        return result

    def _create_retry_message(self, attempt: int, previous_error: Optional[str]) -> str:
        """Create a retry-specific message to guide the model."""
        msg = f"\n\n---\n**RETRY ATTEMPT {attempt}**\n\n"

        if previous_error:
            msg += f"The previous patch had validation errors:\n```\n{previous_error}\n```\n\n"

        msg += """Please fix the following issues:
1. Ensure all context lines start with a SPACE character
2. Ensure the patch ends with a newline
3. Verify hunk line numbers match the actual file
4. Use exact file paths from the problem statement
5. Include sufficient context (3+ lines before/after changes)

Generate a corrected patch following the unified diff format exactly."""

        return msg


def prepare_retry_prompt(original_prompt: str, error_message: str, attempt: int) -> str:
    """
    Prepare a retry prompt with error feedback.

    Args:
        original_prompt: The original prompt
        error_message: Error message from validation
        attempt: Current attempt number

    Returns:
        Enhanced prompt with retry instructions
    """
    retry_msg = f"""

---
**RETRY ATTEMPT {attempt}** - Previous patch had validation errors

**Error**: {error_message}

**Please fix these issues**:
1. Ensure all context lines start with a SPACE character (not tab)
2. Ensure the patch ends with a newline character
3. Verify hunk line numbers match the actual file
4. Use exact file paths
5. Include sufficient context (3+ lines before/after changes)
6. READ the actual files to get correct line numbers - don't guess!

Generate a corrected patch following unified diff format exactly.
"""

    return original_prompt + retry_msg


def create_validation_chain(*validators):
    """
    Create a validation function that runs multiple validators.

    Args:
        *validators: Validation functions (each returns (bool, str))

    Returns:
        Combined validation function
    """
    def validate(patch_content: str, **kwargs) -> tuple:
        for validator in validators:
            is_valid, error = validator(patch_content, **kwargs)
            if not is_valid:
                return False, error
        return True, ""

    return validate
