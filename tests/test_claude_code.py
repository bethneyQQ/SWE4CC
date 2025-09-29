#!/usr/bin/env python3

"""
Test cases for Claude Code integration with SWE-bench.
"""

import json
import os
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from swebench.inference.run_claude_code import (
    check_claude_code_availability,
    prepare_claude_code_prompt,
    call_claude_code,
    claude_code_inference,
    parse_claude_code_args,
    CLAUDE_CODE_MODELS
)

class TestClaudeCodeAvailability:
    """Test Claude Code CLI availability checks."""

    @patch('subprocess.run')
    def test_claude_code_available(self, mock_run):
        """Test successful Claude Code CLI detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="claude 1.0.0"
        )

        assert check_claude_code_availability() is True
        mock_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('subprocess.run')
    def test_claude_code_not_available(self, mock_run):
        """Test Claude Code CLI not available."""
        mock_run.side_effect = FileNotFoundError("claude not found")

        assert check_claude_code_availability() is False

    @patch('subprocess.run')
    def test_claude_code_command_fails(self, mock_run):
        """Test Claude Code CLI command failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="command failed"
        )

        assert check_claude_code_availability() is False


class TestPromptPreparation:
    """Test Claude Code prompt preparation."""

    def test_prepare_basic_prompt(self):
        """Test basic prompt preparation."""
        datum = {"text": "Fix this bug in the code."}

        prompt = prepare_claude_code_prompt(datum)

        assert "Fix this bug in the code." in prompt
        assert "patch" in prompt.lower()
        assert "diff" in prompt.lower()

    def test_prepare_empty_prompt(self):
        """Test prompt preparation with empty input."""
        datum = {"text": ""}

        prompt = prepare_claude_code_prompt(datum)

        assert isinstance(prompt, str)
        assert "patch" in prompt.lower()

    def test_prepare_prompt_missing_text(self):
        """Test prompt preparation with missing text field."""
        datum = {}

        prompt = prepare_claude_code_prompt(datum)

        assert isinstance(prompt, str)
        assert "patch" in prompt.lower()


class TestClaudeCodeCall:
    """Test Claude Code CLI calls."""

    @patch('subprocess.run')
    def test_successful_call(self, mock_run):
        """Test successful Claude Code call."""
        mock_response = {
            "content": "Here's the fix:\n```diff\n...\n```",
            "usage": {"input_tokens": 100, "output_tokens": 200}
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response)
        )

        result = call_claude_code(
            prompt="Fix this bug",
            model_name="claude-3.5-sonnet",
            timeout=300,
            max_tokens=8192,
            temperature=0.1
        )

        assert result == mock_response
        mock_run.assert_called_once()

        # Check command construction
        call_args = mock_run.call_args[0][0]
        assert "claude" in call_args
        assert "-p" in call_args
        assert "Fix this bug" in call_args
        assert "--json" in call_args
        assert "--model" in call_args
        assert "claude-3.5-sonnet" in call_args

    @patch('subprocess.run')
    def test_call_with_custom_params(self, mock_run):
        """Test Claude Code call with custom parameters."""
        mock_response = {"content": "Response"}

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response)
        )

        call_claude_code(
            prompt="Test prompt",
            model_name="claude-4",
            timeout=600,
            max_tokens=4096,
            temperature=0.5
        )

        call_args = mock_run.call_args[0][0]
        assert "--max-tokens" in call_args
        assert "4096" in call_args
        assert "--temperature" in call_args
        assert "0.5" in call_args

    @patch('subprocess.run')
    def test_call_timeout(self, mock_run):
        """Test Claude Code call timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 300)

        result = call_claude_code(
            prompt="Test",
            model_name="claude-3.5-sonnet"
        )

        assert result is None

    @patch('subprocess.run')
    def test_call_json_parse_error(self, mock_run):
        """Test Claude Code call with invalid JSON response."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="invalid json"
        )

        result = call_claude_code(
            prompt="Test",
            model_name="claude-3.5-sonnet"
        )

        assert result is None

    @patch('subprocess.run')
    def test_call_command_error(self, mock_run):
        """Test Claude Code call with command error."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="API key invalid"
        )

        result = call_claude_code(
            prompt="Test",
            model_name="claude-3.5-sonnet"
        )

        assert result is None


class TestArgumentParsing:
    """Test model argument parsing."""

    def test_parse_empty_args(self):
        """Test parsing empty arguments."""
        result = parse_claude_code_args("")
        assert result == {}

    def test_parse_none_args(self):
        """Test parsing None arguments."""
        result = parse_claude_code_args(None)
        assert result == {}

    def test_parse_basic_args(self):
        """Test parsing basic arguments."""
        args = "max_tokens=8192,temperature=0.1"
        result = parse_claude_code_args(args)

        expected = {
            "max_tokens": 8192,
            "temperature": 0.1
        }
        assert result == expected

    def test_parse_boolean_args(self):
        """Test parsing boolean arguments."""
        args = "debug=true,verbose=false"
        result = parse_claude_code_args(args)

        expected = {
            "debug": True,
            "verbose": False
        }
        assert result == expected

    def test_parse_string_args(self):
        """Test parsing string arguments."""
        args = "model=claude-4,output_format=json"
        result = parse_claude_code_args(args)

        expected = {
            "model": "claude-4",
            "output_format": "json"
        }
        assert result == expected

    def test_parse_none_value(self):
        """Test parsing None value."""
        args = "max_cost=none"
        result = parse_claude_code_args(args)

        assert result["max_cost"] is None


class TestClaudeCodeInference:
    """Test Claude Code inference functionality."""

    def create_mock_dataset(self, instances):
        """Create a mock dataset for testing."""
        class MockDataset:
            def __init__(self, data):
                self.data = data

            def __iter__(self):
                return iter(self.data)

        return MockDataset(instances)

    @patch('swebench.inference.run_claude_code.check_claude_code_availability')
    @patch('swebench.inference.run_claude_code.call_claude_code')
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_inference_success(self, mock_call, mock_check):
        """Test successful inference."""
        # Setup mocks
        mock_check.return_value = True
        mock_call.return_value = {
            "content": "Fixed the bug:\n```diff\n...\n```",
            "usage": {"input_tokens": 100, "output_tokens": 200}
        }

        # Create test data
        test_instances = [
            {"instance_id": "test__test-1", "text": "Fix this bug"}
        ]
        test_dataset = self.create_mock_dataset(test_instances)

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            output_file = f.name

        try:
            # Run inference
            claude_code_inference(
                test_dataset=test_dataset,
                model_name_or_path="claude-3.5-sonnet",
                output_file=output_file,
                model_args={},
                existing_ids=set()
            )

            # Check output
            with open(output_file, 'r') as f:
                result = json.loads(f.readline())

            assert result["instance_id"] == "test__test-1"
            assert result["model_name_or_path"] == "claude-3.5-sonnet"
            assert "full_output" in result
            assert "model_patch" in result
            assert "claude_code_meta" in result

        finally:
            os.unlink(output_file)

    @patch('swebench.inference.run_claude_code.check_claude_code_availability')
    def test_inference_claude_not_available(self, mock_check):
        """Test inference when Claude Code is not available."""
        mock_check.return_value = False

        with pytest.raises(RuntimeError, match="Claude Code CLI is not available"):
            claude_code_inference(
                test_dataset=[],
                model_name_or_path="claude-3.5-sonnet",
                output_file="test.jsonl",
                model_args={},
                existing_ids=set()
            )

    def test_inference_no_api_key(self):
        """Test inference without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable must be set"):
                claude_code_inference(
                    test_dataset=[],
                    model_name_or_path="claude-3.5-sonnet",
                    output_file="test.jsonl",
                    model_args={},
                    existing_ids=set()
                )

    @patch('swebench.inference.run_claude_code.check_claude_code_availability')
    @patch('swebench.inference.run_claude_code.call_claude_code')
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_inference_skip_existing(self, mock_call, mock_check):
        """Test inference skips existing IDs."""
        mock_check.return_value = True

        test_instances = [
            {"instance_id": "test__test-1", "text": "Fix this bug"},
            {"instance_id": "test__test-2", "text": "Fix another bug"}
        ]
        test_dataset = self.create_mock_dataset(test_instances)

        existing_ids = {"test__test-1"}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            output_file = f.name

        try:
            claude_code_inference(
                test_dataset=test_dataset,
                model_name_or_path="claude-3.5-sonnet",
                output_file=output_file,
                model_args={},
                existing_ids=existing_ids
            )

            # Should only call Claude Code once (for test-2)
            assert mock_call.call_count == 1

        finally:
            os.unlink(output_file)


class TestConstants:
    """Test constants and configuration."""

    def test_claude_code_models(self):
        """Test Claude Code model constants."""
        assert "claude-4" in CLAUDE_CODE_MODELS
        assert "claude-code" in CLAUDE_CODE_MODELS
        assert "claude-3.5-sonnet" in CLAUDE_CODE_MODELS

        # Check token limits are reasonable
        for model, limit in CLAUDE_CODE_MODELS.items():
            assert isinstance(limit, int)
            assert limit > 0


class TestIntegration:
    """Integration tests (require actual Claude Code CLI)."""

    @pytest.mark.integration
    def test_real_claude_code_check(self):
        """Test real Claude Code availability check."""
        # This test requires Claude Code CLI to be installed
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                assert check_claude_code_availability() is True
            else:
                pytest.skip("Claude Code CLI not available")
        except FileNotFoundError:
            pytest.skip("Claude Code CLI not installed")

    @pytest.mark.integration
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_real_api_call(self):
        """Test real API call (requires valid API key)."""
        # Skip if no real API key
        if os.environ.get('ANTHROPIC_API_KEY') == 'test-key':
            pytest.skip("No real API key available")

        # This would make a real API call - use with caution
        pytest.skip("Real API test disabled to avoid costs")


if __name__ == "__main__":
    pytest.main([__file__])