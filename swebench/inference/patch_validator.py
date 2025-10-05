#!/usr/bin/env python3
"""
Patch validation utilities for SWE-bench
"""
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional


def validate_patch_format(patch_content: str) -> Tuple[bool, str]:
    """
    Validate patch format without applying it.

    Returns:
        (is_valid, error_message)
    """
    if not patch_content:
        return False, "Empty patch"

    lines = patch_content.split('\n')

    # Check basic structure
    has_header = False
    has_hunk = False

    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            has_header = True
        if line.startswith('@@'):
            has_hunk = True

    if not has_header:
        return False, "Missing patch header (--- / +++)"

    if not has_hunk:
        return False, "Missing hunk header (@@)"

    # Check trailing newline
    if patch_content and not patch_content.endswith('\n'):
        return False, "Missing trailing newline"

    # Check hunk line format
    in_hunk = False
    for i, line in enumerate(lines, 1):
        if line.startswith('@@'):
            in_hunk = True
            continue

        if in_hunk and line and not line.startswith(('---', '+++')):
            first_char = line[0] if line else ''
            if first_char not in [' ', '+', '-', '\\']:
                return False, f"Line {i}: Invalid hunk line (must start with space/+/-/\\)"

    return True, ""


def dry_run_patch(patch_content: str, repo_path: str) -> Tuple[bool, str]:
    """
    Test if a patch can be applied without actually applying it.

    Args:
        patch_content: The patch content
        repo_path: Path to the repository

    Returns:
        (can_apply, error_message)
    """
    if not patch_content:
        return False, "Empty patch"

    # First validate format
    is_valid, error = validate_patch_format(patch_content)
    if not is_valid:
        return False, f"Format error: {error}"

    # Write patch to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch_content)
        patch_file = f.name

    try:
        # Run patch --dry-run
        result = subprocess.run(
            ['patch', '--dry-run', '-p1', '-i', patch_file],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, ""
        else:
            # Extract error message
            error_msg = result.stderr or result.stdout
            return False, error_msg.strip()

    except subprocess.TimeoutExpired:
        return False, "Patch validation timeout"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
    finally:
        # Clean up temp file
        Path(patch_file).unlink(missing_ok=True)


def analyze_patch_complexity(patch_content: str) -> Dict[str, int]:
    """
    Analyze patch complexity metrics.

    Returns:
        Dict with: files_changed, hunks, lines_added, lines_removed, context_lines
    """
    stats = {
        'files_changed': 0,
        'hunks': 0,
        'lines_added': 0,
        'lines_removed': 0,
        'context_lines': 0
    }

    if not patch_content:
        return stats

    lines = patch_content.split('\n')

    for line in lines:
        if line.startswith('+++'):
            stats['files_changed'] += 1
        elif line.startswith('@@'):
            stats['hunks'] += 1
        elif line.startswith('+') and not line.startswith('+++'):
            stats['lines_added'] += 1
        elif line.startswith('-') and not line.startswith('---'):
            stats['lines_removed'] += 1
        elif line.startswith(' '):
            stats['context_lines'] += 1

    return stats


def is_patch_too_complex(patch_content: str, max_files: int = 5, max_hunks: int = 10) -> Tuple[bool, str]:
    """
    Check if patch is too complex and should be split.

    Returns:
        (is_too_complex, reason)
    """
    stats = analyze_patch_complexity(patch_content)

    if stats['files_changed'] > max_files:
        return True, f"Too many files changed: {stats['files_changed']} > {max_files}"

    if stats['hunks'] > max_hunks:
        return True, f"Too many hunks: {stats['hunks']} > {max_hunks}"

    total_changes = stats['lines_added'] + stats['lines_removed']
    if total_changes > 200:
        return True, f"Too many changes: {total_changes} lines > 200"

    return False, ""


def verify_hunk_line_numbers(patch_content: str, repo_path: str) -> Tuple[bool, str]:
    """
    Verify that hunk line numbers in patch match actual file content.

    Returns:
        (is_valid, error_message)
    """
    import re

    lines = patch_content.split('\n')
    current_file = None
    errors = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Track current file being patched
        if line.startswith('+++'):
            # Extract filename: "+++ b/path/to/file.py"
            match = re.match(r'\+\+\+ b/(.+)', line)
            if match:
                current_file = match.group(1)

        # Check hunk header
        elif line.startswith('@@'):
            if not current_file:
                errors.append(f"Line {i+1}: Hunk header without file context")
                i += 1
                continue

            # Parse hunk header: @@ -start,count +start,count @@
            match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
            if not match:
                errors.append(f"Line {i+1}: Invalid hunk header format")
                i += 1
                continue

            old_start = int(match.group(1))
            old_count = int(match.group(2))

            # Read actual file and check if line numbers make sense
            file_path = Path(repo_path) / current_file
            if not file_path.exists():
                errors.append(f"Line {i+1}: File not found: {current_file}")
                i += 1
                continue

            try:
                with open(file_path, 'r') as f:
                    file_lines = f.readlines()

                total_file_lines = len(file_lines)

                # Check if hunk start is within file bounds
                if old_start < 1:
                    errors.append(f"Line {i+1}: Invalid start line {old_start} (must be >= 1)")
                elif old_start > total_file_lines + 1:
                    errors.append(f"Line {i+1}: Start line {old_start} beyond file end ({total_file_lines} lines)")

                # Verify context lines match
                # Collect context and deleted lines from hunk
                j = i + 1
                hunk_old_lines = []
                while j < len(lines):
                    hunk_line = lines[j]
                    if hunk_line.startswith('@@') or hunk_line.startswith('---') or hunk_line.startswith('+++'):
                        break
                    if hunk_line.startswith(' ') or hunk_line.startswith('-'):
                        # Context or deleted line
                        hunk_old_lines.append(hunk_line[1:] if hunk_line else '')
                    j += 1

                # Compare first few context lines
                if hunk_old_lines and old_start <= total_file_lines:
                    actual_line = file_lines[old_start - 1].rstrip('\n') if old_start - 1 < len(file_lines) else ''
                    expected_line = hunk_old_lines[0]
                    if actual_line != expected_line:
                        errors.append(
                            f"Line {i+1}: Context mismatch at line {old_start}\n"
                            f"  Expected: {repr(expected_line)}\n"
                            f"  Actual:   {repr(actual_line)}"
                        )

            except Exception as e:
                errors.append(f"Line {i+1}: Error reading {current_file}: {e}")

        i += 1

    if errors:
        return False, "\n".join(errors)

    return True, ""


def split_patch_by_file(patch_content: str) -> Dict[str, str]:
    """
    Split a multi-file patch into separate patches per file.

    Returns:
        Dict mapping filename to its patch content
    """
    import re

    patches = {}
    current_file = None
    current_patch_lines = []

    for line in patch_content.split('\n'):
        # New file starts
        if line.startswith('---'):
            # Save previous file's patch
            if current_file and current_patch_lines:
                patches[current_file] = '\n'.join(current_patch_lines) + '\n'

            current_patch_lines = [line]
            current_file = None

        elif line.startswith('+++'):
            # Extract filename
            match = re.match(r'\+\+\+ b/(.+)', line)
            if match:
                current_file = match.group(1)
            current_patch_lines.append(line)

        elif current_file:
            current_patch_lines.append(line)

    # Save last file's patch
    if current_file and current_patch_lines:
        patches[current_file] = '\n'.join(current_patch_lines) + '\n'

    return patches


def split_patch_by_hunk(patch_content: str, max_hunks_per_patch: int = 3) -> list:
    """
    Split a patch with many hunks into smaller patches.

    Args:
        patch_content: Original patch
        max_hunks_per_patch: Maximum hunks per split patch

    Returns:
        List of patch contents
    """
    lines = patch_content.split('\n')
    patches = []
    current_patch = []
    header_lines = []
    hunk_count = 0

    for line in lines:
        # File headers (--- and +++)
        if line.startswith('---') or line.startswith('+++'):
            header_lines.append(line)
            if current_patch:
                # New file, save previous
                patches.append('\n'.join(current_patch) + '\n')
                current_patch = []
                hunk_count = 0
            continue

        # Hunk header
        if line.startswith('@@'):
            hunk_count += 1
            if hunk_count > max_hunks_per_patch:
                # Too many hunks, split here
                if current_patch:
                    patches.append('\n'.join(current_patch) + '\n')
                current_patch = header_lines.copy()
                hunk_count = 1

            if not current_patch:
                current_patch = header_lines.copy()

        current_patch.append(line)

    # Save last patch
    if current_patch:
        patches.append('\n'.join(current_patch) + '\n')

    return patches if len(patches) > 1 else [patch_content]
